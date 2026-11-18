"""隔离密钥与配置回归。Created by Jobs on 2026年11月4日，星期三."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor

from jobs_ssh_key_mgr.core import SshSetup, SetupError, SetupResult, default_email, github_auth_issue, read_public_key


class StubRunner:
    def __init__(self):
        self.calls = []
        self.remote_email = 'person@example.com'
        self.remote_keys = ''
        self.authenticated = 'person'

    def __call__(self, args, **options):
        self.calls.append((args, options))
        name = Path(args[0]).name
        output, code = '', 0
        if name == 'ssh-keygen':
            if '-t' in args:
                target = Path(args[args.index('-f') + 1])
                email = args[args.index('-C') + 1]
                algorithm = args[args.index('-t') + 1]
                public = ('ssh-ed25519' if algorithm == 'ed25519' else 'ssh-rsa') + ' AAAA ' + email
                target.write_text(public)
                Path(str(target) + '.pub').write_text(public)
            elif '-y' in args:
                output = Path(args[args.index('-f') + 1]).read_text()
            elif '-lf' in args:
                output = '4096 SHA256:test comment (RSA)'
            elif '-F' in args:
                code = 0
        elif name == 'gh':
            if 'status' in args:
                output = json.dumps({'hosts': {'github.com': [{'active': True, 'state': 'success'}]}})
            elif args[-1] == 'user':
                output = json.dumps({'login': 'person'})
            elif 'user/emails' in args:
                output = self.remote_email + '\n'
            elif 'user/keys' in args:
                output = self.remote_keys
        elif name == 'ssh' and '-T' in args:
            output, code = f"Hi {self.authenticated}! You've successfully authenticated, but GitHub does not provide shell access.", 1
        return subprocess.CompletedProcess(args, code, output, '')


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.home = Path(self.temporary.name)
        self.events = []
        self.runner = StubRunner()
        self.engine = SshSetup(home=self.home, emit=self.events.append, runner=self.runner,
                               platform='darwin', log_file=self.home / 'test.log')
        self.discovery = patch('jobs_ssh_key_mgr.core.command_path', side_effect=lambda name: '/stub/' + name)
        self.discovery.start()

    def tearDown(self):
        self.discovery.stop()
        self.temporary.cleanup()

    def prepare(self):
        self.engine.prepare('person@example.com', 'ed25519')

    def test_invalid_email_has_no_write(self):
        with patch('jobs_ssh_key_mgr.core.run_command', side_effect=AssertionError('must not read Git')):
            self.assertEqual(default_email(), '295060456@qq.com')
        with self.assertRaises(SetupError):
            self.engine.prepare('not email', 'ed25519')
        self.assertFalse(self.engine.folder.exists())

    def test_conflicting_key_is_not_overwritten_and_matching_key_reused(self):
        self.prepare()
        existing = self.engine.folder / 'id_ed25519_personal'
        existing.write_text('original account key')
        key = self.engine.key_pair('person@example.com', 'ed25519')
        self.assertNotEqual(key, existing)
        self.assertEqual(existing.read_text(), 'original account key')
        self.assertEqual(self.engine.key_pair('person@example.com', 'ed25519'), key)
        self.assertEqual(len([args for args, _ in self.runner.calls if '-t' in args]), 1)

    def test_config_preserves_original_and_is_idempotent(self):
        self.prepare()
        config = self.engine.folder / 'config'
        original = b'ServerAliveInterval 30\nHost example.test\n  User other\n'
        config.write_bytes(original)
        key = self.engine.folder / 'id_ed25519_personal'
        self.engine.configure(key)
        first = config.read_bytes()
        self.engine.configure(key)
        self.assertEqual(config.read_bytes(), first)
        self.assertTrue(first.endswith(original))
        self.assertIn(b'Host *\n# <<<', first)
        backups = list(self.engine.folder.glob('config.jobs-backup-*'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), original)

    def test_readme_describes_files_and_actual_key_without_reading_private_content(self):
        self.prepare()
        key = self.engine.folder / 'id_rsa_personal_example_1'
        key.write_text('private-body-must-not-appear')
        self.engine.write_readme(key)
        readme = self.engine.folder / 'README.md'
        text = readme.read_text()
        for name in ('config', 'id_ed25519_personal', 'id_ed25519_personal.pub', 'known_hosts', key.name, key.name + '.pub'):
            self.assertIn(name, text)
        self.assertIn('RSA 4096', text)
        self.assertIn('[toc]', text)
        self.assertNotIn('private-body-must-not-appear', text)
        self.assertNotIn(str(self.home), text)
        self.assertEqual(self.events[-1].key, 'ssh_readme_created')
        self.assertFalse(list(self.engine.folder.glob('.jobs-readme-*')))

    def test_existing_readme_is_skipped_without_any_content_metadata_or_permission_changes(self):
        self.prepare()
        readme = self.engine.folder / 'README.md'
        original = b'Existing personal notes\r\n\xff\x00'
        readme.write_bytes(original)
        readme.chmod(0o400)
        os.utime(readme, ns=(1000000000, 2000000000))
        before = readme.stat()
        with patch('jobs_ssh_key_mgr.core.tempfile.TemporaryDirectory', side_effect=AssertionError('existing README must be skipped immediately')):
            self.engine.write_readme(self.engine.folder / 'id_ed25519_personal')
        after = readme.stat()
        self.assertEqual(readme.read_bytes(), original)
        self.assertEqual((after.st_mtime_ns, after.st_mode, after.st_ino), (before.st_mtime_ns, before.st_mode, before.st_ino))
        self.assertEqual(self.events[-1].key, 'ssh_readme_skipped')

    def test_readme_symlink_dangling_link_and_directory_are_preserved(self):
        self.prepare()
        readme = self.engine.folder / 'README.md'
        target = self.home / 'outside.md'
        target.write_text('outside notes')
        for dangling in (False, True):
            with self.subTest(dangling=dangling):
                readme.symlink_to(self.home / 'missing.md' if dangling else target)
                link = readme.readlink()
                self.engine.write_readme(self.engine.folder / 'id_ed25519_personal')
                self.assertTrue(readme.is_symlink())
                self.assertEqual(readme.readlink(), link)
                self.assertEqual(self.events[-1].key, 'ssh_readme_skipped')
                readme.unlink()
        readme.mkdir()
        self.engine.write_readme(self.engine.folder / 'id_ed25519_personal')
        self.assertTrue(readme.is_dir())
        self.assertEqual(target.read_text(), 'outside notes')
        self.assertEqual(self.events[-1].key, 'ssh_readme_skipped')

    def test_readme_creation_race_preserves_the_competing_file(self):
        self.prepare()
        readme = self.engine.folder / 'README.md'
        real_link = os.link
        def competing_link(source, destination):
            readme.write_bytes(b'concurrent personal notes')
            return real_link(source, destination)
        with patch('jobs_ssh_key_mgr.core.os.link', side_effect=competing_link):
            self.engine.write_readme(self.engine.folder / 'id_ed25519_personal')
        self.assertEqual(readme.read_bytes(), b'concurrent personal notes')
        self.assertEqual(self.events[-1].key, 'ssh_readme_skipped')
        self.assertFalse(list(self.engine.folder.glob('.jobs-readme-*')))

    def test_concurrent_readme_writers_publish_exactly_once(self):
        self.prepare()
        other = SshSetup(home=self.home, emit=self.events.append, log_file=self.home / 'other.log')
        self.events.clear()
        with ThreadPoolExecutor(max_workers=2) as workers:
            futures = [workers.submit(engine.write_readme, self.engine.folder / name)
                       for engine, name in ((self.engine, 'id_ed25519_personal'), (other, 'id_rsa_personal'))]
            for future in futures:
                future.result()
        self.assertCountEqual([event.key for event in self.events], ['ssh_readme_created', 'ssh_readme_skipped'])
        self.assertTrue((self.engine.folder / 'README.md').read_text().endswith('</a>\n'))

    def test_readme_failure_does_not_abort_configuration_or_recreate_the_key(self):
        with patch('jobs_ssh_key_mgr.core.os.link', side_effect=PermissionError('private diagnostic')):
            self.prepare()
            self.engine.write_readme(self.engine.folder / 'id_ed25519_personal')
        self.assertEqual(self.events[-1].key, 'ssh_readme_failed')
        self.assertNotIn('private diagnostic', self.engine.log_file.read_text())
        self.assertFalse((self.engine.folder / 'README.md').exists())
        self.assertFalse(list(self.engine.folder.glob('.jobs-readme-*')))
        real_link = os.link
        def fail_only_readme(source, destination):
            if Path(destination).name == 'README.md':
                raise PermissionError('private diagnostic')
            return real_link(source, destination)
        with patch('jobs_ssh_key_mgr.core.os.link', side_effect=fail_only_readme), patch.object(self.engine, 'host_keys', return_value=True):
            result = self.engine.execute('person@example.com', 'ed25519')
        self.assertTrue(result.authenticated)
        self.assertTrue((self.engine.folder / 'config').is_file())
        self.assertTrue(result.key.is_file())
        self.assertEqual(len([args for args, _ in self.runner.calls if '-t' in args]), 1)

    def test_incomplete_managed_config_is_preserved(self):
        self.prepare()
        config = self.engine.folder / 'config'
        original = '# >>> Jobs personal GitHub SSH >>>\nHost broken\n'
        config.write_text(original)
        with self.assertRaises(SetupError):
            self.engine.configure(self.engine.folder / 'key')
        self.assertEqual(config.read_text(), original)

    def test_mismatched_github_email_prevents_upload(self):
        self.prepare()
        key = self.engine.key_pair('person@example.com', 'ed25519')
        self.runner.remote_email = 'other@example.com'
        self.engine.github_registration(key, 'person@example.com')
        self.assertFalse(any('ssh-key' in args for args, _ in self.runner.calls))
        self.assertIn('github_email_mismatch', [event.key for event in self.events])

    def test_github_authentication_reports_missing_cli_without_running_it(self):
        with patch('jobs_ssh_key_mgr.core.command_path', return_value=''):
            self.engine.github_registration(self.home / 'key', 'person@example.com')
        self.assertEqual(self.events[-1].key, 'github_cli_missing')
        self.assertFalse(self.runner.calls)

    def test_github_authentication_classifies_structured_failures_without_upload_or_secret_logs(self):
        scenarios = (
            ({'hosts': {}}, 0, 'github_not_logged_in'),
            ({'hosts': {}}, 1, 'github_not_logged_in'),
            ({'hosts': {'github.com': [{'active': True, 'state': 'error', 'error': 'HTTP 401: Bad credentials'}]}}, 0, 'github_auth_invalid'),
            ({'hosts': {'github.com': [{'active': True, 'state': 'error', 'error': 'HTTP 403: Forbidden'}]}}, 0, 'github_auth_forbidden'),
            ({'hosts': {'github.com': [{'active': True, 'state': 'error', 'error': 'dial tcp: no such host'}]}}, 0, 'github_auth_network'),
            ({'hosts': {'github.com': [{'active': True, 'state': 'timeout', 'error': 'context deadline exceeded'}]}}, 0, 'github_auth_timeout'),
            ({'hosts': {'github.com': [{'active': True, 'state': 'error', 'error': 'HTTP 502: Bad gateway'}]}}, 0, 'github_auth_check_failed'),
            ({'hosts': {'github.com': [{'active': True, 'state': 'error', 'error': 'unrecognized ghp_do_not_log_this_token'}]}}, 0, 'github_auth_check_failed'),
            ({'hosts': []}, 0, 'github_auth_check_failed'),
            ({'hosts': {'github.com': {}}}, 0, 'github_auth_check_failed'),
            ({'hosts': {'github.com': [{'active': False, 'state': 'success'}]}}, 0, 'github_auth_check_failed'),
        )
        for document, exit_code, expected in scenarios:
            with self.subTest(expected=expected, document=document):
                self.events.clear()
                response = subprocess.CompletedProcess([], exit_code, json.dumps(document), '')
                with patch.object(self.engine, 'command', return_value=response) as command:
                    self.engine.github_registration(self.home / 'key', 'person@example.com')
                self.assertEqual(self.events[-1].key, expected)
                self.assertEqual(command.call_count, 1)
                self.assertIn('--active', command.call_args.args)
                self.assertIn('--json', command.call_args.args)
                self.assertNotIn('ghp_do_not_log_this_token', self.engine.log_file.read_text())

    def test_github_authentication_distinguishes_timeout_and_execution_or_parse_failure(self):
        failures = ((subprocess.TimeoutExpired(['gh'], 20), 'github_auth_timeout'),
                    (OSError('contains ghp_do_not_log_this_token'), 'github_auth_check_failed'))
        for error, expected in failures:
            with self.subTest(error=type(error).__name__):
                with patch.object(self.engine, 'command', side_effect=error):
                    self.assertFalse(self.engine.github_authentication())
                self.assertEqual(self.events[-1].key, expected)
        for output in ('not json ghp_do_not_log_this_token', '[]', '{}', 'null'):
            with patch.object(self.engine, 'command', return_value=subprocess.CompletedProcess([], 1, output, '')):
                self.assertFalse(self.engine.github_authentication())
            self.assertEqual(self.events[-1].key, 'github_auth_check_failed')
        self.assertNotIn('ghp_do_not_log_this_token', self.engine.log_file.read_text())

    def test_github_authentication_uses_active_account_and_checks_json_error_even_on_exit_zero(self):
        active = {'active': True, 'state': 'success'}
        inactive = {'active': False, 'state': 'error', 'error': 'HTTP 401: Bad credentials'}
        response = subprocess.CompletedProcess([], 0, json.dumps({'hosts': {'github.com': [inactive, active]}}), '')
        self.assertIsNone(github_auth_issue(response))
        active.update(state='error', error='HTTP 401: Bad credentials')
        response.stdout = json.dumps({'hosts': {'github.com': [active]}})
        self.assertEqual(github_auth_issue(response).key, 'github_auth_invalid')

    def test_github_authentication_avoids_synthetic_host_for_logged_out_users(self):
        self.engine.environment['GH_HOST'] = 'enterprise.invalid'
        def logged_out(args, **options):
            self.assertNotIn('GH_HOST', options['environment'])
            self.assertEqual(args[args.index('--hostname') + 1], 'github.com')
            return subprocess.CompletedProcess(args, 0, '{"hosts":{}}', '')
        self.engine.runner = logged_out
        self.assertFalse(self.engine.github_authentication())
        self.assertEqual(self.events[-1].key, 'github_not_logged_in')
        self.assertEqual(self.engine.environment['GH_HOST'], 'github.com')

    def test_upload_host_is_fixed_and_existing_key_is_not_uploaded_twice(self):
        self.prepare()
        key = self.engine.key_pair('person@example.com', 'ed25519')
        self.engine.environment['GH_HOST'] = 'enterprise.invalid'
        self.engine.github_registration(key, 'person@example.com')
        uploads = [(args, options) for args, options in self.runner.calls if 'ssh-key' in args]
        self.assertEqual(len(uploads), 1)
        self.assertEqual(uploads[0][1]['environment']['GH_HOST'], 'github.com')
        self.runner.calls.clear()
        self.runner.remote_keys = 'ssh-ed25519 AAAA'
        self.engine.github_registration(key, 'person@example.com')
        self.assertFalse(any('ssh-key' in args for args, _ in self.runner.calls))

    def test_ssh_success_checks_current_key_and_account(self):
        self.prepare()
        key = self.engine.folder / 'key'
        with patch.object(self.engine, 'host_keys', return_value=True):
            self.assertTrue(self.engine.verify(key))
            args, _ = self.runner.calls[-1]
            self.assertIn('IdentityAgent=none', args)
            self.assertIn('IdentitiesOnly=yes', args)
            self.assertEqual(args[args.index('-i') + 1], str(key))
            self.engine.account = 'expected-account'
            self.assertFalse(self.engine.verify(key))

    def test_windows_config_excludes_apple_directive(self):
        self.prepare()
        self.engine.platform = 'win32'
        self.engine.configure(self.engine.folder / 'key')
        self.assertNotIn('UseKeychain', (self.engine.folder / 'config').read_text())

    def test_legacy_filename_is_reuse_only_for_new_ed25519(self):
        self.prepare()
        base = self.engine.folder / 'id_ed25519_personal'
        base.write_text('foreign private')
        key = self.engine.key_pair('person@example.com', 'ed25519')
        self.assertTrue(key.name.startswith('id_ed25519_personal_'))
        self.assertFalse((self.engine.folder / 'id_rsa_personal').exists())

    def test_publication_race_preserves_competitor_and_removes_owned_half(self):
        self.prepare()
        import os
        real_link = os.link
        base = self.engine.folder / 'id_ed25519_personal'
        competitor = Path(str(base) + '.pub')
        calls = []
        def race(source, destination):
            calls.append(str(destination))
            if len(calls) == 2:
                competitor.write_text('concurrent public key')
                raise FileExistsError(str(destination))
            return real_link(source, destination)
        with patch('jobs_ssh_key_mgr.core.os.link', side_effect=race):
            key = self.engine.key_pair('person@example.com', 'ed25519')
        self.assertFalse(base.exists())
        self.assertEqual(competitor.read_text(), 'concurrent public key')
        self.assertNotEqual(key, base)

    def test_partial_result_survives_configuration_failure(self):
        with patch.object(self.engine, 'configure', side_effect=SetupError('config_invalid')):
            with self.assertRaises(SetupError):
                self.engine.execute('person@example.com', 'ed25519')
        result = self.engine.last_result
        self.assertIsNotNone(result)
        self.assertFalse(result.authenticated)
        self.assertEqual(result.public_key, Path(str(result.key) + '.pub').read_text())

    def test_public_reader_rejects_private_content_in_pub_file(self):
        self.prepare()
        private = self.engine.folder / 'key'
        private.write_text('must never be read')
        public = Path(str(private) + '.pub')
        public.write_text('-----BEGIN OPENSSH PRIVATE KEY-----\nsecret')
        with self.assertRaises(SetupError) as caught:
            read_public_key(private)
        self.assertEqual(caught.exception.event.key, 'public_file_invalid')
        self.assertNotIn('secret', str(caught.exception))

    def test_sourcetree_mac_aliases_are_relative_and_idempotent(self):
        import os
        self.prepare()
        key = self.engine.key_pair('person@example.com', 'ed25519')
        self.engine.authenticated_account = 'ActualAccount'
        native = os.symlink
        with patch('jobs_ssh_key_mgr.core.os.symlink', wraps=native) as linked:
            notice = self.engine.sourcetree_aliases(key)
            self.assertEqual(notice.key, 'sourcetree_linked')
            self.assertEqual(linked.call_count, 2)
            again = self.engine.sourcetree_aliases(key)
            self.assertEqual(again.key, 'sourcetree_linked')
            self.assertEqual(linked.call_count, 2)
        alias = self.engine.folder / 'ActualAccount-GitHub'
        self.assertEqual(os.readlink(alias), key.name)
        self.assertEqual(os.readlink(Path(str(alias) + '.pub')), key.name + '.pub')
        self.assertTrue(alias.samefile(key))
        self.assertFalse((self.engine.folder / 'person-GitHub').exists())

    def test_sourcetree_windows_uses_native_hardlinks(self):
        import os
        self.prepare()
        key = self.engine.key_pair('person@example.com', 'ed25519')
        self.engine.platform = 'win32'
        self.engine.authenticated_account = 'ActualAccount'
        native = os.link
        with patch('jobs_ssh_key_mgr.core.os.link', wraps=native) as linked:
            self.assertEqual(self.engine.sourcetree_aliases(key).key, 'sourcetree_linked')
            self.assertEqual(linked.call_count, 2)
            self.engine.sourcetree_aliases(key)
            self.assertEqual(linked.call_count, 2)
        alias = self.engine.folder / 'ActualAccount-GitHub'
        self.assertFalse(alias.is_symlink())
        self.assertTrue(alias.samefile(key))
        self.assertTrue(Path(str(alias) + '.pub').samefile(Path(str(key) + '.pub')))

    def test_sourcetree_conflict_preserves_files_without_invalidating_authentication(self):
        self.prepare()
        conflict = self.engine.folder / 'person-GitHub.pub'
        conflict.write_text('another account public key')
        with patch.object(self.engine, 'host_keys', return_value=True), patch('jobs_ssh_key_mgr.core.os.symlink') as linked:
            result = self.engine.execute('person@example.com', 'ed25519')
            self.assertTrue(result.authenticated)
            linked.assert_not_called()
        self.assertEqual(conflict.read_text(), 'another account public key')
        self.assertFalse((self.engine.folder / 'person-GitHub').exists())
        self.assertIn('sourcetree_conflict', [event.key for event in self.events])

    def test_sourcetree_link_failure_keeps_ssh_success(self):
        self.engine.platform = 'win32'
        # 只让兼容别名原语失败，正常密钥原子发布仍使用真实临时目录原语。
        import os
        native = os.link
        def link(source, target):
            if Path(target).name.endswith('-GitHub') or Path(target).name.endswith('-GitHub.pub'):
                raise PermissionError('native hardlink denied')
            return native(source, target)
        with patch.object(self.engine, 'host_keys', return_value=True), patch('jobs_ssh_key_mgr.core.os.link', side_effect=link):
            result = self.engine.execute('person@example.com', 'ed25519')
        self.assertTrue(result.authenticated)
        self.assertIn('sourcetree_link_failed', [event.key for event in self.events])

    def test_sourcetree_requires_strict_authentication_and_never_guesses_email(self):
        self.prepare()
        key = self.engine.key_pair('person@example.com', 'ed25519')
        self.engine.account = 'ApiKnownAccount'
        self.assertIsNone(self.engine.sourcetree_aliases(key))
        self.assertFalse(list(self.engine.folder.glob('*-GitHub*')))
        self.runner.authenticated = 'different-account'
        with patch.object(self.engine, 'host_keys', return_value=True):
            result = self.engine.execute('person@example.com', 'ed25519')
        self.assertFalse(result.authenticated)
        self.assertEqual(self.engine.authenticated_account, '')
        self.assertFalse(list(self.engine.folder.glob('*-GitHub*')))

    def test_zero_start_then_web_registration_and_retest_complete_both_platforms(self):
        from contextlib import ExitStack
        for platform in ('darwin', 'win32'):
            with self.subTest(platform=platform):
                home = self.home / platform
                home.mkdir()
                runner = StubRunner()
                runner.authenticated = 'VerifiedLogin'
                registered = False
                def run(args, **options):
                    response = runner(args, **options)
                    if Path(args[0]).name == 'ssh' and '-T' in args and not registered:
                        return subprocess.CompletedProcess(args, 255, '', 'git@github.com: Permission denied (publickey).')
                    return response
                events = []
                engine = SshSetup(home=home, emit=events.append, runner=run, platform=platform,
                                  log_file=home / 'setup.log')
                def host_keys():
                    (engine.folder / 'known_hosts').write_text('github.com ssh-ed25519 TEST\n')
                    return True
                with patch('jobs_ssh_key_mgr.core.command_path', side_effect=lambda name: '' if name == 'gh' else '/stub/' + name), patch.object(engine, 'host_keys', side_effect=host_keys):
                    self.assertFalse(engine.folder.exists())
                    initial = engine.execute('person@example.com', 'ed25519')
                self.assertFalse(initial.authenticated)
                self.assertFalse(list(engine.folder.glob('*-GitHub*')))
                original = {name: ((engine.folder / name).read_bytes(), (engine.folder / name).stat().st_mtime_ns)
                            for name in ('config', initial.key.name, initial.key.name + '.pub', 'known_hosts', 'README.md')}
                registered = True
                reopened = SshSetup(home=home, emit=events.append, runner=run, platform=platform,
                                    log_file=home / 'retest.log')
                with ExitStack() as stack:
                    for method in ('prepare', 'key_pair', 'configure', 'load_agent', 'github_registration', 'write_readme', 'host_keys'):
                        stack.enter_context(patch.object(reopened, method, side_effect=AssertionError(method + ' must not repeat')))
                    tested = reopened.test_and_configure_sourcetree(initial)
                    reopened.test_and_configure_sourcetree(tested)
                self.assertTrue(tested.authenticated)
                self.assertEqual(tested.account, 'VerifiedLogin')
                for suffix in ('', '.pub'):
                    alias = engine.folder / ('VerifiedLogin-GitHub' + suffix)
                    target = Path(str(initial.key) + suffix)
                    self.assertTrue(alias.samefile(target))
                    self.assertEqual(alias.is_symlink(), platform == 'darwin')
                self.assertEqual(original, {name: ((engine.folder / name).read_bytes(), (engine.folder / name).stat().st_mtime_ns) for name in original})
                self.assertEqual(len([args for args, _ in runner.calls if '-t' in args]), 1)
                self.assertIn('sourcetree_linked', [event.key for event in events])

    def test_retest_does_not_create_aliases_when_authentication_fails(self):
        previous, _ = self.existing_connection_fixture()
        with patch.object(self.engine, 'verify', return_value=False), patch.object(self.engine, 'sourcetree_aliases') as aliases:
            tested = self.engine.test_and_configure_sourcetree(previous)
        self.assertFalse(tested.authenticated)
        aliases.assert_not_called()
        self.assertFalse(list(self.engine.folder.glob('*-GitHub*')))

    def test_zero_start_with_github_authorization_prepares_aliases_on_first_configuration(self):
        self.assertFalse(self.engine.folder.exists())
        with patch.object(self.engine, 'host_keys', return_value=True):
            result = self.engine.execute('person@example.com', 'ed25519')
        self.assertTrue(result.authenticated)
        self.assertEqual(result.account, 'person')
        for suffix in ('', '.pub'):
            self.assertTrue((self.engine.folder / ('person-GitHub' + suffix)).samefile(Path(str(result.key) + suffix)))

    def test_retest_alias_creation_error_preserves_authentication_success(self):
        previous, _ = self.existing_connection_fixture()
        with patch('jobs_ssh_key_mgr.core.os.symlink', side_effect=PermissionError('alias access denied')):
            result = self.engine.test_and_configure_sourcetree(previous)
        self.assertTrue(result.authenticated)
        self.assertEqual(self.events[-1].key, 'sourcetree_link_failed')

    def test_retest_preserves_conflicting_alias_and_ssh_authentication_success(self):
        previous, _ = self.existing_connection_fixture()
        self.runner.authenticated = 'VerifiedLogin'
        conflict = self.engine.folder / 'VerifiedLogin-GitHub.pub'
        conflict.write_text('preserve existing account public key')
        tested = self.engine.test_and_configure_sourcetree(previous)
        self.assertTrue(tested.authenticated)
        self.assertEqual(conflict.read_text(), 'preserve existing account public key')
        self.assertFalse((self.engine.folder / 'VerifiedLogin-GitHub').exists())
        self.assertEqual(self.events[-1].key, 'sourcetree_conflict')

    def test_sourcetree_windows_reparse_conflict_is_preserved(self):
        from types import SimpleNamespace
        import stat
        self.prepare()
        key = self.engine.key_pair('person@example.com', 'ed25519')
        self.engine.platform = 'win32'
        self.engine.authenticated_account = 'ActualAccount'
        alias = self.engine.folder / 'ActualAccount-GitHub'
        alias.write_text('preserve reparse target')
        native_lstat = Path.lstat
        def metadata(path):
            actual = native_lstat(path)
            if path == alias:
                return SimpleNamespace(st_mode=actual.st_mode, st_file_attributes=getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 1024))
            return actual
        with patch('jobs_ssh_key_mgr.core.Path.lstat', metadata), patch('jobs_ssh_key_mgr.core.os.link') as linked:
            self.assertEqual(self.engine.sourcetree_aliases(key).key, 'sourcetree_conflict')
            linked.assert_not_called()
        self.assertEqual(alias.read_text(), 'preserve reparse target')

    def existing_connection_fixture(self):
        self.engine.folder.mkdir()
        key = self.engine.folder / 'id_ed25519_personal'
        key.write_text('PRIVATE-CONTENT-MUST-NOT-BE-READ')
        current_public = 'ssh-ed25519 AAAA current@example.com'
        Path(str(key) + '.pub').write_text(current_public)
        result = SetupResult(key, 'ssh-ed25519 BBBB cached@example.com', True, 'cached-account')
        native = self.runner
        def runner(args, **options):
            if Path(args[0]).name == 'ssh-keygen' and '-y' in args:
                native.calls.append((args, options))
                return subprocess.CompletedProcess(args, 0, current_public, '')
            return native(args, **options)
        self.engine.runner = runner
        return result, current_public

    def test_existing_connection_is_strict_readonly_and_uses_actual_account(self):
        from contextlib import ExitStack
        previous, current_public = self.existing_connection_fixture()
        self.runner.authenticated = 'ActualGitHubAccount'
        self.engine.account = 'unrelated-gh-account'
        config = self.engine.folder / 'config'
        known_hosts = self.engine.folder / 'known_hosts'
        config.write_text('preserved config')
        known_hosts.write_text('preserved known_hosts')
        before = {path.name:path.read_bytes() for path in self.engine.folder.iterdir()}
        read_text = Path.read_text
        def checked_read(path, *arguments, **options):
            if path == previous.key:
                raise AssertionError('application must not read the private key body')
            return read_text(path,*arguments,**options)
        with ExitStack() as stack:
            for name in ('prepare','key_pair','write_readme','configure','load_agent','github_registration','sourcetree_aliases','host_keys'):
                stack.enter_context(patch.object(self.engine,name,side_effect=AssertionError(name+' is forbidden')))
            stack.enter_context(patch('jobs_ssh_key_mgr.core.Path.read_text',checked_read))
            result = self.engine.test_existing_connection(previous)
        self.assertTrue(result.authenticated)
        self.assertEqual(result.key,previous.key)
        self.assertEqual(result.public_key,current_public)
        self.assertEqual(result.account,'ActualGitHubAccount')
        self.assertEqual(previous.account,'cached-account')
        self.assertEqual(previous.public_key,'ssh-ed25519 BBBB cached@example.com')
        self.assertEqual({path.name:path.read_bytes() for path in self.engine.folder.iterdir()},before)
        ssh_calls = [(args,options) for args,options in self.runner.calls if Path(args[0]).name=='ssh']
        self.assertEqual(len(ssh_calls),1)
        args,options = ssh_calls[0]
        self.assertEqual(args[args.index('-i')+1],str(previous.key))
        for option in ('IdentityAgent=none','IdentitiesOnly=yes','BatchMode=yes','StrictHostKeyChecking=yes','UpdateHostKeys=no','ConnectTimeout=10','ConnectionAttempts=1'):
            self.assertIn(option,args)
        self.assertEqual(options['timeout'],20)
        derived = next(options for args,options in self.runner.calls if '-y' in args)
        self.assertEqual(derived['timeout'],10)
        self.assertEqual([event.key for event in self.events],['testing_connection','auth_success'])

    def test_existing_connection_validation_failure_preserves_state(self):
        previous,_ = self.existing_connection_fixture()
        self.engine.last_result = previous
        self.engine.account = 'retained-account'
        self.engine.authenticated_account = 'retained-account'
        previous.key.unlink()
        with self.assertRaises(SetupError):
            self.engine.test_existing_connection(previous)
        self.assertIs(self.engine.last_result,previous)
        self.assertEqual(self.engine.account,'retained-account')
        self.assertEqual(self.engine.authenticated_account,'retained-account')
        self.assertFalse(self.runner.calls)

    def test_existing_connection_rejects_outside_and_link_sources(self):
        previous,_ = self.existing_connection_fixture()
        outside = self.home/'outside-key'
        outside.write_text('outside key')
        with self.assertRaises(SetupError):
            self.engine.test_existing_connection(SetupResult(outside,'ssh-ed25519 AAAA',False))
        linked = self.engine.folder/'Account-GitHub'
        linked.symlink_to(previous.key.name)
        with self.assertRaises(SetupError):
            self.engine.test_existing_connection(SetupResult(linked,'ssh-ed25519 AAAA',False))
        self.assertFalse(self.runner.calls)

    def test_existing_connection_rejects_mismatched_public_private_pair(self):
        previous,_ = self.existing_connection_fixture()
        self.engine.last_result = previous
        Path(str(previous.key)+'.pub').write_text('ssh-ed25519 BBBB changed@example.com')
        with self.assertRaises(SetupError) as caught:
            self.engine.test_existing_connection(previous)
        self.assertEqual(caught.exception.event.key,'failed')
        self.assertIn('E_SSH_KEY_PAIR',caught.exception.event.values['detail'])
        self.assertFalse(any(Path(args[0]).name=='ssh' for args,_ in self.runner.calls))
        self.assertIs(self.engine.last_result,previous)

    def test_existing_connection_network_failure_returns_current_public_without_side_effects(self):
        previous,current_public = self.existing_connection_fixture()
        runner = self.engine.runner
        def timeout(args,**options):
            if Path(args[0]).name=='ssh':
                raise subprocess.TimeoutExpired(args,options['timeout'])
            return runner(args,**options)
        self.engine.runner = timeout
        with patch.object(self.engine,'host_keys',side_effect=AssertionError('host keys must be read only')):
            result = self.engine.test_existing_connection(previous)
        self.assertFalse(result.authenticated)
        self.assertEqual(result.key,previous.key)
        self.assertEqual(result.public_key,current_public)
        self.assertEqual(result.account,'')
        self.assertTrue(previous.authenticated)
        self.assertIn('auth_failed',[event.key for event in self.events])

    def test_existing_connection_cancel_restores_previous_engine_and_result(self):
        previous,_ = self.existing_connection_fixture()
        self.engine.last_result = previous
        self.engine.account = 'retained-account'
        self.engine.authenticated_account = 'retained-account'
        runner = self.engine.runner
        def cancel(args,**options):
            if Path(args[0]).name=='ssh':
                raise KeyboardInterrupt()
            return runner(args,**options)
        self.engine.runner = cancel
        with self.assertRaises(KeyboardInterrupt):
            self.engine.test_existing_connection(previous)
        self.assertIs(self.engine.last_result,previous)
        self.assertEqual(self.engine.account,'retained-account')
        self.assertEqual(self.engine.authenticated_account,'retained-account')
        self.assertTrue(previous.authenticated)

    def test_existing_connection_requires_github_success_exit_code(self):
        previous,_ = self.existing_connection_fixture()
        runner = self.engine.runner
        def wrong_exit(args,**options):
            if Path(args[0]).name=='ssh':
                return subprocess.CompletedProcess(args,0,"Hi person! You've successfully authenticated",'')
            return runner(args,**options)
        self.engine.runner = wrong_exit
        result = self.engine.test_existing_connection(previous)
        self.assertFalse(result.authenticated)
        self.assertEqual(result.account,'')
        self.assertIn('auth_failed',[event.key for event in self.events])

    def test_existing_connection_windows_uses_null_config_without_host_preparation(self):
        previous,_ = self.existing_connection_fixture()
        self.engine.platform = 'win32'
        with patch.object(self.engine,'host_keys',side_effect=AssertionError('must not prepare hosts')):
            result = self.engine.test_existing_connection(previous)
        self.assertTrue(result.authenticated)
        args = next(args for args,_ in self.runner.calls if Path(args[0]).name=='ssh')
        self.assertEqual(args[args.index('-F')+1],'NUL')

    def test_execute_announces_automatic_connection_test_before_verify(self):
        def verify(key):
            self.assertEqual(self.events[-1].key,'testing_connection')
            return False
        with patch.object(self.engine,'verify',side_effect=verify):
            result = self.engine.execute('person@example.com','ed25519')
        self.assertFalse(result.authenticated)
        self.assertIn('testing_connection',[event.key for event in self.events])
