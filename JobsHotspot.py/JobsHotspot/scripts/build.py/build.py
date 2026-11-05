# build.py | JobsHotspot
# Created by Jobs on 2026年11月5日，星期四.
"""Jobs Hotspot：本机生成 APP/DMG 或 EXE/ZIP。Created by Jobs.

运行先显示范围并等待回车；依赖缺失再次确认安装。只清理本工具固定 dist，
拒绝符号链接输出目录；成功后更新入口、打开产物位置并启动本次应用。
"""
import sys

if sys.version_info < (3, 11):
    print('✖ 构建需要 Python 3.11+；请运行外层平台打包脚本自动检查运行时。', file=sys.stderr)
    raise SystemExit(1)

import argparse
from datetime import datetime
import hashlib
import json
import logging
import os
import platform
from pathlib import Path
import plistlib
import shutil
import subprocess
import tempfile
import tomllib
import venv
import zipfile

ROOT = Path(__file__).absolute().parents[2]
OUTER = ROOT.parent
NAME = 'JobsHotspot'
LOG_FILE = Path(tempfile.gettempdir()) / (NAME + '-build.log')
REQUIREMENTS = {
    'PySide6': ('PySide6>=6.8,<7', (6, 8), (7,)),
    'PyInstaller': ('PyInstaller>=6.22,<7', (6, 22), (7,)),
}


def configure_output():
    """Windows 终端/重定向统一 UTF-8，只影响当前构建进程。"""
    if sys.platform == 'win32':
        for stream in (sys.stdout, sys.stderr):
            if stream is not None and hasattr(stream, 'reconfigure'):
                stream.reconfigure(encoding='utf-8', errors='backslashreplace')


def confirm(message):
    """回车才继续；非空输入（包含空格）、EOF 和非终端全部停止。"""
    if not sys.stdin.isatty():
        raise RuntimeError('没有可交互输入，请在终端运行；尚未安装或清理。')
    try:
        answer = input(message + '（直接回车继续；输入任意字符或 Ctrl+C 取消）：')
    except EOFError as error:
        raise RuntimeError('输入已结束，已停止。') from error
    if answer != '':
        raise RuntimeError('已取消。')


def show_intro():
    """内层直接运行同样展示清理边界和依赖安装规则。"""
    print('Jobs Hotspot · 双端本机打包\n'
          '1、MacOS 生成独立 APP/DMG，Windows 生成 EXE 目录及 ZIP；不交叉编译。\n'
          '2、将删除当前工具外层 dist 的全部旧产物；不清理源码及其它应用。\n'
          '3、健康依赖直接复用；缺失时回车安装，任意非空输入（含空格）取消。\n'
          '4、输出 dist/YYYY.MM.DD HH-mm-ss；成功后更新第一层快捷方式。\n'
          '5、验证后打开本次产物位置，再启动本次 APP/EXE。\n'
          f'日志：{LOG_FILE}\n按 Ctrl+C 取消。', flush=True)


def child_environment():
    """只对子进程移除宿主 Qt / PyInstaller 注入，避免加载其它 APP 的运行库。"""
    environment = {key: value for key, value in os.environ.items()
                   if key not in ('QT_PLUGIN_PATH', 'QT_QPA_PLATFORM_PLUGIN_PATH')
                   and not key.startswith('_PYI_')}
    environment['PYTHONDONTWRITEBYTECODE'] = '1'
    environment['PYTHONUTF8'] = '1'
    environment['PYTHONIOENCODING'] = 'utf-8'
    return environment


def run(command, cwd=ROOT):
    """完整记录子进程输出，失败立即停止后续步骤。"""
    logging.info('执行：%s', subprocess.list2cmdline([str(item) for item in command]))
    with subprocess.Popen([str(item) for item in command], cwd=cwd,
                          env=child_environment(),
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, encoding='utf-8', errors='replace') as process:
        for line in process.stdout:
            print(line, end='', flush=True)
            logging.info('%s', line.rstrip())
        if process.wait() != 0:
            raise subprocess.CalledProcessError(process.returncode, command)


def fixed_directory(name):
    """仅允许工程既定 dist / work，拒绝外层及目标目录的链接改向。"""
    if (name not in ('dist', 'work') or ROOT.name != NAME or ROOT.parent != OUTER
            or OUTER.parent == OUTER):
        raise RuntimeError('构建目录布局异常，停止。')
    if (OUTER.is_symlink() or OUTER.absolute() != OUTER.resolve() or not OUTER.is_dir()
            or ROOT.is_symlink() or ROOT.absolute() != ROOT.resolve() or not ROOT.is_dir()):
        raise RuntimeError(f'交付根目录必须是真实目录：{OUTER}')
    target = OUTER / name
    if target.is_symlink() or target.resolve().parent != OUTER or (target.exists() and not target.is_dir()):
        raise RuntimeError(f'拒绝外部、符号链接或非目录输出：{target}')
    return target


def clean_dist(target):
    """清理仅接受本应用固定 dist；失败直接抛出，禁止继续构建。"""
    expected = fixed_directory('dist')
    if not str(target) or Path(target).absolute() != expected:
        raise RuntimeError(f'拒绝清理非固定 dist：{target}')
    if expected.exists():
        shutil.rmtree(expected)
    if expected.exists() or expected.is_symlink():
        raise RuntimeError(f'dist 清理失败：{expected}')


def missing_requirements(python):
    """在目标解释器内验证版本及关键 Qt 模块，避免仅凭文件存在判断健康。"""
    probe = '''import importlib, json
requirements = %r
missing = []
for name, (requirement, minimum, maximum) in requirements.items():
    try:
        module = importlib.import_module(name)
        version = tuple(int(part) for part in module.__version__.split('.')[:2])
        assert version >= minimum and (maximum is None or version < maximum)
        if name == 'PySide6':
            from PySide6 import QtCore, QtGui, QtWidgets, QtSvg
            assert hasattr(QtGui.QStyleHints, 'setColorScheme')
    except Exception:
        missing.append(requirement)
print(json.dumps(missing))
''' % REQUIREMENTS
    result = subprocess.run([str(python), '-c', probe], capture_output=True, env=child_environment(),
                            text=True, encoding='utf-8', errors='replace')
    if result.returncode:
        raise RuntimeError(f'构建 Python 无法运行：{python}\n{result.stderr}')
    return json.loads(result.stdout)


def managed_environment():
    """公共构建依赖按用户、Python 版本和架构管理，不夹带进源码。"""
    if sys.platform == 'win32':
        base = Path(os.environ.get('LOCALAPPDATA', str(Path.home() / 'AppData/Local')))
    else:
        base = Path.home() / 'Library/Caches'
    if not base.is_absolute() or base.resolve().is_relative_to(OUTER.resolve()):
        raise RuntimeError('用户级缓存位置无效或位于源码目录内，停止环境准备。')
    return base / 'JobsPythonTools/BuildEnvironments' / (
        NAME + f'-py{sys.version_info.major}.{sys.version_info.minor}-' + platform.machine())


def bootstrap():
    """依赖链：Python → 用户级 venv → pip → Qt/PyInstaller；只修复缺失层。"""
    current = Path(sys.executable)
    if not missing_requirements(current):
        print('✔ 复用当前解释器的健康构建依赖；不安装、不升级依赖。')
        return current
    environment = managed_environment()
    if (environment.is_symlink() or environment.absolute() != environment.resolve()
            or (environment.exists() and not environment.is_dir())):
        raise RuntimeError(f'拒绝修改符号链接或非目录构建环境：{environment}')
    if environment.exists() and not (environment / 'pyvenv.cfg').is_file():
        raise RuntimeError(f'环境目录未登记为 Python 虚拟环境，保留原内容并停止：{environment}')
    python = environment / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    healthy_python = False
    if python.exists():
        try:
            healthy_python = subprocess.run([str(python), '-c',
                                            'import sys; from pathlib import Path; assert sys.version_info >= (3,11); '
                                            'assert Path(sys.prefix).resolve() == Path(sys.argv[1]).resolve(); '
                                            'assert sys.prefix != sys.base_prefix', str(environment)],
                                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=child_environment()).returncode == 0
        except OSError:
            healthy_python = False
    missing = missing_requirements(python) if healthy_python else [item[0] for item in REQUIREMENTS.values()]
    if not missing:
        print(f'✔ 复用用户级健康构建环境：{environment}；不安装、不升级依赖。')
        return python
    print('缺少或不兼容的依赖：' + '、'.join(missing))
    print(f'来源：当前 pip 配置的软件源；依赖 {"、".join(missing)}；目标：{environment}')
    confirm('将在上述用户级构建环境安装必需依赖，不升级已有健康依赖')
    if not healthy_python:
        if environment.exists():
            backup = environment.with_name(environment.name + '.backup.' + datetime.now().strftime('%Y%m%d-%H%M%S') + '.' + str(os.getpid()))
            if backup.exists() or backup.is_symlink():
                raise RuntimeError(f'虚拟环境备份名称已被占用：{backup}')
            environment.rename(backup)
            print(f'ℹ 原虚拟环境已完整保留：{backup}')
        environment.parent.mkdir(parents=True, exist_ok=True)
        venv.EnvBuilder(with_pip=True).create(environment)
    pip = subprocess.run([str(python), '-m', 'pip', '--version'], capture_output=True, env=child_environment())
    if pip.returncode:
        run([python, '-m', 'ensurepip'])
    run([python, '-m', 'pip', '--version'])
    missing = missing_requirements(python)
    if missing:
        run([python, '-m', 'pip', 'install', '--disable-pip-version-check', *missing])
    remaining = missing_requirements(python)
    if remaining:
        raise RuntimeError('安装后依赖仍不可用，已停止：' + '、'.join(remaining))
    return python


def check_platform():
    """只允许本机平台构建，并在清理前检查必需系统命令。"""
    if sys.version_info < (3, 11) or sys.platform not in ('darwin', 'win32'):
        raise RuntimeError('请在 MacOS 或 Windows 使用 Python 3.11+ 运行。')
    commands = ('hdiutil', 'open') if sys.platform == 'darwin' else ('powershell.exe', 'explorer.exe')
    for command in commands:
        if not shutil.which(command):
            raise RuntimeError(f'缺少必需系统命令：{command}；尚未清理旧产物。')


def check_ui_resources():
    """图标与授权随源码提供，缺失时在清理旧产物前停止。"""
    folder = ROOT / 'src/jobs_hotspot/assets'
    platform_icon = 'app.icns' if sys.platform == 'darwin' else 'app.ico'
    for name in ('icon.png', platform_icon):
        path = folder / name
        if not path.is_file() or path.is_symlink() or path.stat().st_size == 0:
            raise RuntimeError(f'界面资源缺失或不是普通文件：{path}；尚未清理旧产物。')


def write_spec(work, version):
    """先在 spec 固定应用标识与窗口类型，避免修改签名后的 MacOS Info.plist。"""
    spec = work / (NAME + '.spec')
    text = f'''# Generated locally by Jobs Hotspot build.py.
import sys
a = Analysis([{str(ROOT / 'scripts/launch.py/launch.py')!r}], pathex=[{str(ROOT / 'src')!r}],
             binaries=[], datas=[({str(ROOT / 'src/jobs_hotspot/assets')!r}, 'jobs_hotspot/assets')],
             hiddenimports=['jobs_hotspot.backends.macos', 'jobs_hotspot.backends.windows'],
             hookspath=[], hooksconfig={{}},
             runtime_hooks=[], excludes=[], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name={NAME!r},
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, disable_windowed_traceback=False, argv_emulation=False,
          icon={str(ROOT / 'src/jobs_hotspot/assets/app.ico')!r} if sys.platform == 'win32' else None,
          target_arch=None, codesign_identity=None, entitlements_file=None)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name={NAME!r})
'''
    if sys.platform == 'darwin':
        text += f'''app = BUNDLE(coll, name={NAME + '.app'!r}, icon={str(ROOT / 'src/jobs_hotspot/assets/app.icns')!r},
             bundle_identifier='com.jobs.hotspot',
             info_plist={{'LSUIElement': False, 'NSHighResolutionCapable': True,
                         'CFBundleDisplayName': 'Jobs Hotspot',
                         'NSAppleEventsUsageDescription': 'Control Internet Sharing in System Settings when you request a hotspot change.',
                         'CFBundleShortVersionString': {version!r}, 'CFBundleVersion': {version!r}}})
'''
    spec.write_text(text, encoding='utf-8')
    return spec


def validate_application(output):
    """检查可执行文件及 MacOS 应用配置，返回真实应用和可执行文件。"""
    if sys.platform == 'darwin':
        artifact = output / (NAME + '.app')
        executable = artifact / 'Contents/MacOS' / NAME
        with (artifact / 'Contents/Info.plist').open('rb') as stream:
            info = plistlib.load(stream)
        if info.get('LSUIElement') is not False or info.get('CFBundleIdentifier') != 'com.jobs.hotspot':
            raise RuntimeError('APP 应用配置或 Bundle ID 校验失败。')
        if not os.access(executable, os.X_OK):
            raise RuntimeError(f'APP 主程序不可执行：{executable}')
    else:
        artifact = executable = output / NAME / (NAME + '.exe')
        if not (artifact.parent / '_internal').is_dir():
            raise RuntimeError('Windows onedir 依赖目录未生成。')
    if not executable.is_file() or executable.stat().st_size == 0:
        raise RuntimeError(f'主程序未生成或为空：{executable}')
    with executable.open('rb') as stream:
        header = stream.read(4)
    if sys.platform == 'win32' and not header.startswith(b'MZ'):
        raise RuntimeError('生成的 Windows 主程序不是有效 EXE。')
    return artifact, executable


def package_application(output, artifact, work):
    """Mac 创建并验证 DMG；Windows 把完整 onedir 依赖打入 ZIP。"""
    if sys.platform == 'darwin':
        stage = work / 'dmg'
        stage.mkdir()
        shutil.copytree(artifact, stage / artifact.name, symlinks=True)
        (stage / 'Applications').symlink_to('/Applications', target_is_directory=True)
        package = output / (NAME + '.dmg')
        run(['hdiutil', 'create', '-volname', NAME, '-srcfolder', stage, '-format', 'UDZO', package])
        run(['hdiutil', 'verify', package])
    else:
        package = output / (NAME + '.zip')
        with zipfile.ZipFile(package, 'w', zipfile.ZIP_DEFLATED) as archive:
            for file in sorted(artifact.parent.rglob('*')):
                if file.is_file():
                    archive.write(file, file.relative_to(output))
        with zipfile.ZipFile(package) as archive:
            if archive.testzip() or f'{NAME}/{NAME}.exe' not in archive.namelist():
                raise RuntimeError('ZIP 完整性校验失败。')
    if not package.is_file() or package.stat().st_size == 0:
        raise RuntimeError(f'分发包未生成或为空：{package}')
    return package


def reveal_and_launch(output, artifact):
    """先打开本次磁盘位置，再启动本次生成的软件，不回退到旧包。"""
    if sys.platform == 'darwin':
        run(['open', output])
        run(['open', artifact])
    else:
        subprocess.Popen(['explorer.exe', str(output)], env=child_environment())
        subprocess.Popen([str(artifact)], cwd=artifact.parent, env=child_environment())


def smoke_application(executable):
    """成品无网络写操作的 GUI 冒烟通过后才发布快捷入口。"""
    environment = child_environment()
    environment['QT_QPA_PLATFORM'] = 'offscreen'
    result = subprocess.run([str(executable), '--smoke'], env=environment,
                            cwd=tempfile.gettempdir(), capture_output=True,
                            text=True, encoding='utf-8', errors='replace', timeout=45)
    logging.info('成品冒烟 stdout=%s stderr=%s', result.stdout, result.stderr)
    if result.returncode:
        raise RuntimeError(f'成品冒烟失败（{result.returncode}）：{result.stderr or result.stdout}')


def write_build_record(output, python, artifact, package):
    """记录实际构建环境及可分发文件摘要，便于跨机核验。"""
    probe = subprocess.run([str(python), '-c',
                            'import json,sys,PySide6,PyInstaller; '
                            'print(json.dumps({"python":sys.version,"PySide6":PySide6.__version__, '
                            '"PyInstaller":PyInstaller.__version__}))'],
                           capture_output=True, text=True, check=True, env=child_environment())
    record = json.loads(probe.stdout)
    with package.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    record.update(platform=platform.platform(), architecture=platform.machine(),
                  application=artifact.name, package=package.name,
                  package_sha256=digest,
                  signing='Local/ad-hoc build; no Developer ID notarization or Windows Authenticode signing',
                  hotspot_end_to_end='Not performed by builder')
    (output / 'build-info.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')


def build(python):
    """全部前置检查完成后清理，再生成、验证、发布和启动当次产物。"""
    sys.path.insert(0, str(ROOT / 'scripts' / 'artifact_shortcuts.py'))
    from artifact_shortcuts import clear_shortcuts, publish_shortcuts
    dist = fixed_directory('dist')
    work_root = fixed_directory('work')
    with (ROOT / 'pyproject.toml').open('rb') as stream:
        version = tomllib.load(stream)['project']['version']
    stamp = datetime.now().strftime('%Y.%m.%d %H-%M-%S')
    work = work_root / stamp
    if work.exists() or work.is_symlink():
        raise RuntimeError(f'构建工作目录已被占用，稍后重试：{work}')
    clear_shortcuts(OUTER)
    clean_dist(dist)
    output = dist / stamp
    output.mkdir(parents=True)
    work.mkdir(parents=True)
    spec = write_spec(work, version)
    run([python, '-m', 'PyInstaller', '--noconfirm', '--distpath', output,
         '--workpath', work / 'pyinstaller', spec])
    artifact, executable = validate_application(output)
    smoke_application(executable)
    package = package_application(output, artifact, work)
    write_build_record(output, python, artifact, package)
    publish_shortcuts(OUTER, [artifact, package])
    print(f'✔ 打包与校验成功：{output}', flush=True)
    reveal_and_launch(output, artifact)


def main():
    """help 无副作用；正常构建先确认，再创建日志及检查完整依赖链。"""
    configure_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared', action='store_true',
                        help='只读验证当前解释器依赖；禁止安装依赖，仍保留构建确认')
    args = parser.parse_args()
    show_intro()
    confirm('已了解构建范围及旧产物删除')
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO, encoding='utf-8',
                        format='%(asctime)s %(levelname)s %(message)s', force=True)
    check_platform()
    check_ui_resources()
    fixed_directory('dist')
    fixed_directory('work')
    if args.prepared:
        python = Path(sys.executable)
        missing = missing_requirements(python)
        if missing:
            raise RuntimeError('当前构建依赖不可用，--prepared 禁止安装：' + '、'.join(missing))
    else:
        python = bootstrap()
    build(python)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print('\n已取消。', file=sys.stderr)
        raise SystemExit(130)
    except Exception as error:
        if logging.getLogger().handlers:
            logging.exception('构建停止')
        print(f'✖ 构建停止：{error}\n日志：{LOG_FILE}', file=sys.stderr)
        raise SystemExit(1)
