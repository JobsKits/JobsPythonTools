"""个人 SSH 密钥配置内核。Created by Jobs on 2026年11月4日，星期三."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Callable
from urllib.request import Request, urlopen

from .ssh_readme import directory_readme

BEGIN = '# >>> Jobs personal GitHub SSH >>>'
END = '# <<< Jobs personal GitHub SSH <<<'
EMAIL = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
PUBLIC_KEY = re.compile(r'^(ssh-ed25519|ssh-rsa) [A-Za-z0-9+/]+={0,3}(?: [^\r\n]*)?\r?\n?$')

@dataclass
class Event:
    key: str
    values: dict[str, str] = field(default_factory=dict)

@dataclass
class SetupResult:
    key: Path
    public_key: str
    authenticated: bool
    account: str = ''

class SetupError(RuntimeError):
    def __init__(self, key: str, **values: str):
        self.event = Event(key, values)
        super().__init__(key)


def command_path(name: str) -> str:
    """兼容 Finder 简化 PATH 及 Windows 原生 OpenSSH。"""
    if name in ('ssh', 'ssh-keygen', 'ssh-add', 'ssh-agent'):
        native_folder = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32' / 'OpenSSH' if sys.platform == 'win32' else Path('/usr/bin')
        native = native_folder / (name + '.exe' if sys.platform == 'win32' else name)
        if native.is_file():
            return str(native)
    existing = shutil.which(name)
    if existing:
        return existing
    folders = ['/opt/homebrew/bin', '/usr/local/bin', '/usr/bin']
    if sys.platform == 'win32':
        folders.insert(0, str(Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32' / 'OpenSSH'))
    for folder in folders:
        candidate = Path(folder) / (name + '.exe' if sys.platform == 'win32' else name)
        if candidate.is_file():
            return str(candidate)
    return ''


def run_command(arguments, *, timeout=35, environment=None):
    """参数列表执行，不拼接 Shell，不显示 Windows 子进程黑窗。"""
    return subprocess.run(arguments, capture_output=True, text=True, encoding='utf-8',
                          errors='replace', timeout=timeout, env=environment,
                          stdin=subprocess.DEVNULL,
                          creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)


def default_email():
    """使用用户指定的可编辑默认邮箱，不受 Git 全局配置影响。"""
    return '295060456@qq.com'


def read_public_key(key: Path) -> str:
    """只读取明确的 .pub 文件；拒绝链接、超大内容与私钥格式。"""
    public = Path(str(key) + '.pub')
    try:
        if not public.is_file() or public.is_symlink() or public.stat().st_size > 32768:
            raise SetupError('public_file_invalid')
        content = public.read_text(encoding='utf-8')
    except (OSError, UnicodeError) as error:
        raise SetupError('public_unavailable', detail=str(error)) from error
    if not PUBLIC_KEY.fullmatch(content):
        raise SetupError('public_file_invalid')
    return content.strip()


def github_auth_issue(result) -> Event | None:
    """读取 gh 的结构化状态；诊断只返回分类和 HTTP 码，不回显授权内容。"""
    try:
        document = json.loads(result.stdout)
        hosts = document['hosts']
        if not isinstance(hosts, dict):
            raise ValueError('hosts')
        accounts = hosts.get('github.com', [])
        if not isinstance(accounts, list) or not all(isinstance(account, dict) for account in accounts):
            raise ValueError('accounts')
    except (ValueError, KeyError, TypeError):
        return Event('github_auth_check_failed', {'detail': 'E_GH_AUTH_RESPONSE'})
    if not accounts and result.returncode in (0, 1):
        return Event('github_not_logged_in')
    active = [account for account in accounts if account.get('active') is True]
    if len(active) != 1:
        return Event('github_auth_check_failed', {'detail': 'E_GH_ACTIVE_ACCOUNT'})
    account = active[0]
    if account.get('state') == 'success' and result.returncode == 0:
        return None
    if account.get('state') == 'timeout':
        return Event('github_auth_timeout')
    # JSON 模式即使授权失败也可返回 0，必须检查当前账户的 state 与 error。
    diagnostic = str(account.get('error', ''))
    http = re.search(r'\bHTTP\s+(\d{3})\b', diagnostic, re.IGNORECASE)
    if http:
        code = http.group(1)
        if code == '401':
            return Event('github_auth_invalid')
        if code == '403':
            return Event('github_auth_forbidden')
        return Event('github_auth_check_failed', {'detail': 'HTTP ' + code})
    network_errors = ('error connecting to', 'dial tcp', 'no such host', 'connection refused',
                      'connection reset', 'network is unreachable', 'tls handshake', 'x509:',
                      'proxyconnect', 'i/o timeout', 'context deadline exceeded', 'timeout', 'lookup ')
    if any(message in diagnostic.casefold() for message in network_errors):
        return Event('github_auth_network')
    return Event('github_auth_check_failed', {'detail': 'E_GH_AUTH_STATE'})


class SshSetup:
    def __init__(self, *, home=None, emit=None, runner=run_command, platform=None, log_file=None):
        self.home = home or Path.home()
        self.folder = self.home / '.ssh'
        self.emit = emit or (lambda event: None)
        self.runner = runner
        self.platform = platform or sys.platform
        self.log_file = log_file or Path(tempfile.gettempdir()) / 'JobsSSHKeyMgr.log'
        self.tools = {}
        self.environment = dict(os.environ)
        self.account = ''
        self.authenticated_account = ''
        self.last_result = None

    def report(self, key, **values):
        self.emit(Event(key, values))
        # 只记录消息标识与诊断，不记录私钥、令牌或完整环境。
        with self.log_file.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'time': datetime.now().isoformat(), 'key': key,
                                     'values': values}, ensure_ascii=False) + '\n')

    def command(self, name, *arguments, timeout=35):
        executable = self.tools.get(name) or command_path(name)
        if not executable:
            raise SetupError('missing_tool', tool=name)
        return self.runner([executable, *arguments], timeout=timeout, environment=self.environment)

    def prepare(self, email, algorithm):
        if not EMAIL.fullmatch(email):
            raise SetupError('invalid_email')
        if algorithm not in ('ed25519', 'rsa'):
            raise SetupError('unsupported_algorithm')
        for tool in ('ssh-keygen', 'ssh', 'ssh-add', 'ssh-agent'):
            self.tools[tool] = command_path(tool)
            if not self.tools[tool]:
                raise SetupError('missing_tool', tool=tool)
        if self.folder.is_symlink():
            raise SetupError('ssh_directory_link')
        self.folder.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self.platform != 'win32':
            self.folder.chmod(0o700)

    def matches(self, key, email, algorithm):
        public = Path(str(key) + '.pub')
        if not key.is_file() or key.is_symlink() or not public.is_file() or public.is_symlink():
            return False
        try:
            parts = public.read_text(encoding='utf-8').split()
            if len(parts) != 3 or parts[2].casefold() != email.casefold():
                return False
            if parts[0] != ('ssh-ed25519' if algorithm == 'ed25519' else 'ssh-rsa'):
                return False
            fingerprint = self.command('ssh-keygen', '-lf', str(public))
            if fingerprint.returncode or (algorithm == 'rsa' and not fingerprint.stdout.startswith('4096 ')):
                return False
            derived = self.command('ssh-keygen', '-y', '-P', '', '-f', str(key))
            return derived.returncode == 0 and derived.stdout.split()[:2] == parts[:2]
        except (OSError, UnicodeError, subprocess.SubprocessError):
            return False

    def key_pair(self, email, algorithm):
        base = self.folder / f'id_{algorithm}_personal'
        digest = hashlib.sha256(email.casefold().encode()).hexdigest()[:10]
        for reusable in (base, self.folder / 'id_rsa_personal'):
            if self.matches(reusable, email, algorithm):
                self.report('reused', path=str(reusable))
                return reusable
        candidates = [base]
        candidates.extend(self.folder / f'{base.name}_{digest}_{index}' for index in range(1, 101))
        for key in candidates:
            if self.matches(key, email, algorithm):
                self.report('reused', path=str(key))
                return key
            public = Path(str(key) + '.pub')
            if key.exists() or key.is_symlink() or public.exists() or public.is_symlink():
                continue
            # 临时生成后硬链接原子发布，竞争时也不会覆盖已有文件。
            with tempfile.TemporaryDirectory(prefix='.jobs-key-', dir=self.folder) as temporary:
                generated = Path(temporary) / 'key'
                arguments = ['-t', algorithm, '-C', email, '-f', str(generated), '-N', '']
                if algorithm == 'rsa':
                    arguments += ['-b', '4096']
                result = self.command('ssh-keygen', *arguments)
                if result.returncode:
                    raise SetupError('failed', detail=result.stderr.strip() or 'ssh-keygen')
                published_private = False
                try:
                    os.link(generated, key)
                    published_private = True
                    os.link(Path(str(generated) + '.pub'), public)
                except OSError as error:
                    # 仅回收本次发布且inode未变化的半成品，不触碰竞争进程的文件。
                    if (published_private and key.exists() and not key.is_symlink()
                            and (key.lstat().st_dev, key.lstat().st_ino) == (generated.lstat().st_dev, generated.lstat().st_ino)):
                        key.unlink()
                    if isinstance(error, FileExistsError):
                        continue
                    raise
            if self.platform != 'win32':
                key.chmod(0o600)
                public.chmod(0o644)
            self.report('generated', path=str(key))
            return key
        raise SetupError('no_key_filename')

    def configure(self, key):
        config = self.folder / 'config'
        if config.is_symlink():
            raise SetupError('ssh_config_link')
        original = config.read_bytes() if config.exists() else b''
        text = original.decode('utf-8')
        if text.count(BEGIN) != text.count(END) or text.count(BEGIN) > 1:
            raise SetupError('config_incomplete')
        if BEGIN in text:
            pattern = re.compile(r'^' + re.escape(BEGIN) + r'\r?\n.*?^' + re.escape(END) + r'\r?\n?', re.M | re.S)
            text, count = pattern.subn('', text)
            if count != 1:
                raise SetupError('config_invalid')
        lines = [BEGIN, 'Host github.com github-personal', '  HostName github.com', '  User git',
                 f'  IdentityFile "~/.ssh/{key.name}"', '  IdentitiesOnly yes', '  AddKeysToAgent yes']
        if self.platform == 'darwin':
            lines.append('  UseKeychain yes')
        # 恢复原始开头全局指令对其它主机的作用范围。
        lines += ['Host *', END]
        desired = ('\n'.join(lines) + '\n' + text).encode('utf-8')
        with tempfile.NamedTemporaryFile(dir=self.folder, prefix='.jobs-config-', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(desired)
        try:
            checked = self.command('ssh', '-G', '-F', str(temporary), 'git@github.com')
            if checked.returncode:
                raise SetupError('failed', detail=checked.stderr.strip() or 'SSH config validation')
            if original != desired:
                if config.exists():
                    backup = config.with_name('config.jobs-backup-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
                    shutil.copy2(config, backup)
                    self.report('config_backup', path=str(backup))
                os.replace(temporary, config)
                if self.platform != 'win32':
                    config.chmod(0o600)
        finally:
            temporary.unlink(missing_ok=True)
        self.report('config_saved')

    def write_readme(self, key):
        """说明只发布一次，原子创建避免覆盖既有内容或并发创建者。"""
        readme = self.folder / 'README.md'
        if os.path.lexists(readme):
            self.report('ssh_readme_skipped', path=str(readme))
            return
        try:
            with tempfile.TemporaryDirectory(prefix='.jobs-readme-', dir=self.folder) as folder:
                temporary = Path(folder) / 'README.md'
                temporary.write_text(directory_readme(key), encoding='utf-8', newline='\n')
                os.link(temporary, readme)
        except FileExistsError:
            self.report('ssh_readme_skipped', path=str(readme))
        except OSError:
            self.report('ssh_readme_failed', detail='E_SSH_README_WRITE')
        else:
            self.report('ssh_readme_created', path=str(readme))

    def load_agent(self, key):
        try:
            current = self.command('ssh-add', '-l')
            if current.returncode > 1 and self.platform == 'darwin':
                started = self.command('ssh-agent', '-s')
                if started.returncode == 0:
                    for name in ('SSH_AUTH_SOCK', 'SSH_AGENT_PID'):
                        found = re.search(r'\b' + name + r'=([^;\n]+);', started.stdout)
                        if found:
                            self.environment[name] = found.group(1)
            elif current.returncode > 1 and self.platform == 'win32':
                powershell = command_path('powershell') or command_path('pwsh')
                if powershell:
                    self.runner([powershell, '-NoProfile', '-NonInteractive', '-Command',
                                 'Start-Service ssh-agent -ErrorAction Stop'], timeout=15,
                                environment=self.environment)
            added = self.command('ssh-add', str(key), timeout=15)
            self.report('agent_loaded' if added.returncode == 0 else 'agent_unavailable')
        except (OSError, subprocess.SubprocessError):
            self.report('agent_unavailable')

    def github_authentication(self):
        """区分安装、登录和请求失败，检测未通过时保留本地配置并停止自动登记。"""
        self.environment['GH_PROMPT_DISABLED'] = '1'
        self.tools['gh'] = command_path('gh')
        if not self.tools['gh']:
            self.report('github_cli_missing')
            return False
        try:
            # GH_HOST 会让未登录的主机也出现在状态表；显式 --hostname 已限定目标。
            self.environment.pop('GH_HOST', None)
            result = self.command('gh', 'auth', 'status', '--active', '--hostname', 'github.com',
                                  '--json', 'hosts', timeout=20)
        except subprocess.TimeoutExpired:
            issue = Event('github_auth_timeout')
        except (OSError, subprocess.SubprocessError):
            issue = Event('github_auth_check_failed', {'detail': 'E_GH_AUTH_EXECUTION'})
        else:
            issue = github_auth_issue(result)
        finally:
            self.environment['GH_HOST'] = 'github.com'
        if issue is not None:
            self.report(issue.key, **issue.values)
            return False
        return True

    def github_registration(self, key, email):
        if not self.github_authentication():
            return
        try:
            user = self.command('gh', 'api', '--hostname', 'github.com', 'user')
            emails = self.command('gh', 'api', '--hostname', 'github.com', 'user/emails', '--paginate', '--jq', '.[] | select(.verified == true) | .email')
            if user.returncode or emails.returncode:
                self.report('github_email_unavailable')
                return
            account = json.loads(user.stdout)['login']
            if email.casefold() not in {line.strip().casefold() for line in emails.stdout.splitlines()}:
                self.report('github_email_mismatch')
                return
            self.account = account
            remote = self.command('gh', 'api', '--hostname', 'github.com', 'user/keys', '--paginate', '--jq', '.[].key')
            if remote.returncode:
                self.report('github_register_failed', detail=remote.stderr.strip())
                return
            public = ' '.join(Path(str(key) + '.pub').read_text().split()[:2])
            if public not in [' '.join(line.split()[:2]) for line in remote.stdout.splitlines()]:
                added = self.command('gh', 'ssh-key', 'add', str(key) + '.pub', '--title', f'Jobs {email}', '--type', 'authentication')
                if added.returncode:
                    self.report('github_register_failed', detail=added.stderr.strip())
                    return
            self.report('github_registered', account=account)
        except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
            self.report('github_register_failed', detail=str(error))

    def host_keys(self):
        known = self.folder / 'known_hosts'
        if known.is_symlink():
            self.report('known_hosts_link')
            return False
        if known.exists() and self.command('ssh-keygen', '-F', 'github.com', '-f', str(known)).returncode == 0:
            return True
        try:
            self.report('host_keys_source', source='https://api.github.com/meta', path=str(known))
            request = Request('https://api.github.com/meta', headers={'User-Agent': 'JobsSSHKeyMgr'})
            with urlopen(request, timeout=15) as response:
                keys = json.loads(response.read(256000))['ssh_keys']
            pattern = re.compile(r'^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp256) [A-Za-z0-9+/]+={0,3}$')
            if not keys or not all(isinstance(key, str) and pattern.fullmatch(key) for key in keys):
                raise SetupError('host_metadata_invalid')
            with known.open('a', encoding='utf-8') as stream:
                if known.stat().st_size:
                    stream.write('\n')
                stream.write(''.join('github.com ' + key + '\n' for key in keys))
            if self.platform != 'win32':
                known.chmod(0o600)
            self.report('host_keys_ready')
            return True
        except SetupError as error:
            self.report(error.event.key, **error.event.values)
            return False
        except (OSError, ValueError, KeyError, TypeError) as error:
            self.report('host_keys_failed', detail=str(error))
            return False

    def verify(self, key, prepare_host_keys=True):
        self.authenticated_account = ''
        if prepare_host_keys and not self.host_keys():
            return False
        null = 'NUL' if self.platform == 'win32' else '/dev/null'
        result = self.command('ssh', '-F', null, '-T', '-i', str(key), '-o', 'IdentityAgent=none',
                              '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
                              '-o', 'ConnectionAttempts=1', '-o', 'StrictHostKeyChecking=yes',
                              '-o', 'UpdateHostKeys=no', 'git@github.com', timeout=20)
        output = (result.stdout + result.stderr).strip()
        matched = re.search(r"Hi ([^!\r\n]+)! You've successfully authenticated", output)
        if result.returncode == 1 and matched and (not self.account or matched.group(1) == self.account):
            self.account = matched.group(1)
            self.authenticated_account = self.account
            self.report('auth_success', account=self.account)
            return True
        self.report('auth_failed', detail=output or f'SSH exit {result.returncode}')
        return False

    def test_existing_connection(self, result: SetupResult) -> SetupResult:
        """只检查当前已有密钥与 GitHub 认证，不准备环境或修改密钥配置。"""
        previous = (self.account, self.authenticated_account, self.last_result)
        try:
            if not isinstance(result, SetupResult):
                raise SetupError('failed', detail='E_SSH_KEY_PATH')
            key = Path(result.key)
            folder = self.folder.absolute()
            if not key.is_absolute():
                raise SetupError('failed', detail='E_SSH_KEY_PATH')
            try:
                key.relative_to(folder)
                key.resolve(strict=True).relative_to(folder.resolve(strict=True))
                for candidate in (key, *key.parents):
                    metadata = candidate.lstat()
                    if (stat.S_ISLNK(metadata.st_mode)
                            or bool(getattr(metadata, 'st_file_attributes', 0)
                                    & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0))):
                        raise SetupError('failed', detail=f'E_SSH_KEY_LINK: {candidate}')
                    if candidate == folder:
                        break
                if not stat.S_ISREG(key.lstat().st_mode):
                    raise SetupError('failed', detail=f'E_SSH_KEY_FILE: {key}')
                public_file = Path(str(key) + '.pub')
                metadata = public_file.lstat()
                if bool(getattr(metadata, 'st_file_attributes', 0)
                        & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0)):
                    raise SetupError('failed', detail=f'E_SSH_KEY_LINK: {public_file}')
            except (OSError, ValueError) as error:
                raise SetupError('failed', detail=str(error)) from error
            public = read_public_key(key)
            # ssh-keygen 只返回由私钥推导的公钥，不读取或展示私钥正文。
            try:
                derived = self.command('ssh-keygen', '-y', '-P', '', '-f', str(key), timeout=10)
            except (OSError, subprocess.SubprocessError) as error:
                raise SetupError('failed', detail=str(error)) from error
            if derived.returncode or derived.stdout.split()[:2] != public.split()[:2]:
                raise SetupError('failed', detail=derived.stderr.strip() or f'E_SSH_KEY_PAIR: {public_file}')
            # 手动测试以本次 SSH 实际身份为准，不沿用缓存账户或 gh 的活跃账户。
            self.account = ''
            self.authenticated_account = ''
            self.report('testing_connection')
            try:
                authenticated = self.verify(key, prepare_host_keys=False)
            except (OSError, subprocess.SubprocessError) as error:
                self.report('auth_failed', detail=str(error))
                authenticated = False
            self.last_result = SetupResult(key, public, authenticated,
                                           self.authenticated_account if authenticated else '')
            return self.last_result
        except BaseException:
            self.account, self.authenticated_account, self.last_result = previous
            raise

    def sourcetree_aliases(self, key):
        """仅为严格认证返回的账号建立兼容文件名，不猜邮箱或改账户设置。"""
        account = self.authenticated_account
        if not account:
            return None
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,38}', account):
            return Event('sourcetree_link_failed', {'detail': 'E_GITHUB_ACCOUNT', 'account': account})
        if key.parent != self.folder:
            return Event('sourcetree_link_failed', {'detail': 'E_SSH_KEY_SOURCE', 'account': account})
        pairs = [(key, self.folder / f'{account}-GitHub'),
                 (Path(str(key) + '.pub'), self.folder / f'{account}-GitHub.pub')]

        def reparse(path):
            metadata = path.lstat()
            return path.is_symlink() or bool(getattr(metadata, 'st_file_attributes', 0)
                                            & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0))

        def matches(alias, target):
            if self.platform == 'win32' and reparse(alias):
                return False
            return alias.is_file() and alias.samefile(target)

        try:
            # 先核对整对目标，任何已知冲突都不触发新建或覆盖。
            for target, alias in pairs:
                if not target.is_file() or reparse(target):
                    return Event('sourcetree_link_failed', {'detail': 'E_SSH_KEY_SOURCE', 'account': account})
                if os.path.lexists(alias) and not matches(alias, target):
                    return Event('sourcetree_conflict', {'path': str(alias), 'account': account})
            for target, alias in pairs:
                if os.path.lexists(alias):
                    continue
                try:
                    if self.platform == 'win32':
                        # 两者都在当前 .ssh 中；硬链接不复制私钥正文且无需符号链接权限。
                        os.link(target, alias)
                    else:
                        os.symlink(target.name, alias)
                except FileExistsError:
                    # 创建期间出现的文件也只核对，不替换。
                    if not matches(alias, target):
                        return Event('sourcetree_conflict', {'path': str(alias), 'account': account})
            return Event('sourcetree_linked', {'account': account})
        except OSError as error:
            return Event('sourcetree_link_failed', {'detail': str(error), 'account': account})

    def test_and_configure_sourcetree(self, result: SetupResult) -> SetupResult:
        """网页登记后的补齐入口：先验证现有密钥，再配置认证账号的识别别名。"""
        tested = self.test_existing_connection(result)
        if tested.authenticated:
            notice = self.sourcetree_aliases(tested.key)
            if notice is not None:
                self.report(notice.key, **notice.values)
        return tested

    def execute(self, email, algorithm):
        self.prepare(email, algorithm)
        key = self.key_pair(email, algorithm)
        public = read_public_key(key)
        # 后续配置失败也保留本轮已验证公钥，GUI仍可展示和复制。
        self.last_result = SetupResult(key, public, False)
        self.write_readme(key)
        self.configure(key)
        self.load_agent(key)
        self.github_registration(key, email)
        self.report('testing_connection')
        try:
            authenticated = self.verify(key)
        except (OSError, subprocess.SubprocessError) as error:
            self.report('auth_failed', detail=str(error))
            authenticated = False
        if authenticated:
            notice = self.sourcetree_aliases(key)
            if notice is not None:
                self.report(notice.key, **notice.values)
        self.report('key_path', path=str(key))
        self.report('public_key_path', path=str(key) + '.pub')
        self.report('complete' if authenticated else 'local_complete')
        self.report('log_path', path=str(self.log_file))
        self.last_result = SetupResult(key, public, authenticated, self.account)
        return self.last_result
