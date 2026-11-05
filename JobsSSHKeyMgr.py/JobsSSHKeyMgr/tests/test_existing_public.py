"""已有公钥的只读发现回归。Created by Jobs on 2026年11月5日，星期四."""
import hashlib
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from jobs_ssh_key_mgr.core import BEGIN, END
from jobs_ssh_key_mgr.existing_public import find_existing_public_key


class ExistingPublicTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.home = Path(self.temporary.name)
        self.folder = self.home / '.ssh'

    def tearDown(self):
        self.temporary.cleanup()

    def pair(self, name, content='ssh-ed25519 AAAA chosen@example.com'):
        self.folder.mkdir(exist_ok=True)
        key = self.folder / name
        key.write_text('PRIVATE FIXTURE: must not be read by discovery')
        Path(str(key) + '.pub').write_text(content)
        return key

    def config(self, name):
        self.folder.mkdir(exist_ok=True)
        path = self.folder / 'config'
        path.write_text(f'{BEGIN}\nHost github.com github-personal\n  IdentityFile "~/.ssh/{name}"\nHost *\n{END}\n')
        return path

    def find(self, **arguments):
        return find_existing_public_key(home=self.home, **arguments)

    def test_missing_directory_stays_missing_and_empty_directory_stays_empty(self):
        self.assertIsNone(self.find())
        self.assertEqual(list(self.home.iterdir()), [])
        self.folder.mkdir()
        self.assertIsNone(self.find())
        self.assertEqual(list(self.folder.iterdir()), [])

    def test_managed_config_has_priority_over_saved_name_and_algorithm_defaults(self):
        configured = self.pair('id_rsa_personal_123456abcd_2', 'ssh-rsa AAAA chosen@example.com')
        self.pair('id_ed25519_personal')
        saved = self.pair('id_ed25519_personal_012345abcd_1')
        self.config(configured.name)
        result = self.find(preferred_name=saved.name, algorithm='ed25519')
        self.assertEqual(result.key, configured)
        self.assertEqual(result.public_key, 'ssh-rsa AAAA chosen@example.com')
        self.assertFalse(result.authenticated)
        self.assertEqual(result.account, '')
        self.assertTrue(result.key.is_absolute())

    def test_saved_basename_has_priority_over_algorithm_defaults(self):
        saved = self.pair('id_rsa_personal_012345abcd_100', 'ssh-rsa AAAA saved@example.com')
        self.pair('id_ed25519_personal')
        result = self.find(preferred_name=saved.name)
        self.assertEqual(result.key, saved)

    def test_managed_cli_suffixes_are_restored_before_an_older_default_key(self):
        self.pair('id_ed25519_personal')
        for name in ('id_ed25519_personal_123456789_1',
                     'id_rsa_personal_abcdef123456', 'id_rsa_personal_abcdef123456_2'):
            with self.subTest(name=name):
                expected = self.pair(name)
                self.config(name)
                self.assertEqual(self.find().key, expected)

    def test_algorithm_defaults_and_other_algorithm_fallback(self):
        rsa = self.pair('id_rsa_personal', 'ssh-rsa AAAA rsa@example.com')
        self.assertEqual(self.find(algorithm='ed25519').key, rsa)
        ed25519 = self.pair('id_ed25519_personal')
        self.assertEqual(self.find(algorithm='rsa').key, rsa)
        self.assertEqual(self.find(algorithm='ed25519').key, ed25519)

    def test_suffixes_prefer_current_algorithm_then_matching_email_digest(self):
        email = 'Person@Example.com'
        digest = hashlib.sha256(email.casefold().encode()).hexdigest()[:10]
        self.pair('id_ed25519_personal_0000000000_1')
        expected = self.pair(f'id_ed25519_personal_{digest}_2')
        rsa = self.pair(f'id_rsa_personal_{digest}_1', 'ssh-rsa AAAA rsa@example.com')
        self.assertEqual(self.find(email=email).key, expected)
        self.assertEqual(self.find(algorithm='rsa', email=email).key, rsa)

    def test_unmanaged_config_and_external_or_traversal_names_are_ignored(self):
        expected = self.pair('id_rsa_personal', 'ssh-rsa AAAA rsa@example.com')
        other = self.pair('foreign_key')
        config = self.folder / 'config'
        for contents in (f'Host github.com\nIdentityFile "{other}"\n',
                         f'{BEGIN}\nIdentityFile "{self.home}/id_ed25519_personal"\n{END}\n',
                         f'{BEGIN}\nIdentityFile "~/.ssh/../id_ed25519_personal"\n{END}\n',
                         f'{BEGIN}\nIdentityFile "~/.ssh/id_ed25519_personal"\n'):
            config.write_text(contents)
            for preferred in ('../foreign_key', str(other), r'..\foreign_key', 'foreign_key'):
                self.assertEqual(self.find(preferred_name=preferred).key, expected)

    def test_managed_absolute_path_is_accepted_and_include_or_exec_is_never_run(self):
        expected = self.pair('id_ed25519_personal_012345abcd_1')
        self.pair('id_ed25519_personal')
        (self.folder / 'config').write_text(
            f'{BEGIN}\nInclude nonexistent\nMatch exec "touch do-not-create"\n'
            f'IdentityFile "{expected}"\n{END}\n')
        with patch('subprocess.run', side_effect=AssertionError('must not execute commands')):
            self.assertEqual(self.find().key, expected)
        self.assertFalse((self.home / 'do-not-create').exists())

    def test_broken_or_large_public_files_fall_back_without_showing_private_format(self):
        bad = self.pair('id_ed25519_personal')
        expected = self.pair('id_rsa_personal', 'ssh-rsa AAAA rsa@example.com')
        self.config(bad.name)
        public = Path(str(bad) + '.pub')
        for value in ('-----BEGIN OPENSSH PRIVATE KEY-----\nPRIVATE\n',
                      'ssh-ed25519 ' + 'A' * 32768,
                      'ssh-ed25519 AAAA first@example.com\nssh-ed25519 AAAA second@example.com'):
            public.write_text(value)
            self.assertEqual(self.find(preferred_name=bad.name).key, expected)
        public.write_bytes(b'\xff')
        self.assertEqual(self.find().key, expected)

    def test_missing_private_file_and_non_regular_private_are_not_candidates(self):
        missing = self.pair('id_ed25519_personal')
        expected = self.pair('id_rsa_personal', 'ssh-rsa AAAA rsa@example.com')
        missing.unlink()
        self.assertEqual(self.find().key, expected)
        missing.mkdir()
        self.assertEqual(self.find().key, expected)

    def test_links_on_directory_config_private_and_public_are_not_followed(self):
        expected = self.pair('id_rsa_personal', 'ssh-rsa AAAA rsa@example.com')
        private = self.pair('id_ed25519_personal')
        public = Path(str(private) + '.pub')
        outside = self.home / 'outside'
        outside.write_text('ssh-ed25519 AAAA outside@example.com')
        try:
            public.unlink()
            public.symlink_to(outside)
            self.assertEqual(self.find().key, expected)
            public.unlink()
            public.write_text('ssh-ed25519 AAAA chosen@example.com')
            private.unlink()
            private.symlink_to(outside)
            self.assertEqual(self.find().key, expected)
            config = self.folder / 'config'
            config.symlink_to(outside)
            self.assertEqual(self.find().key, expected)
            alternate = self.home / 'alternate'
            self.folder.rename(alternate)
            self.folder.symlink_to(alternate, target_is_directory=True)
            self.assertIsNone(self.find())
        except (OSError, NotImplementedError) as error:
            self.skipTest(f'Platform does not support unprivileged symbolic links: {error}')

    def test_windows_reparse_metadata_is_rejected_for_every_discovery_input(self):
        from jobs_ssh_key_mgr import existing_public
        configured = self.pair('id_ed25519_personal')
        fallback = self.pair('id_rsa_personal', 'ssh-rsa AAAA rsa@example.com')
        config = self.config(configured.name)
        metadata = existing_public._metadata
        for rejected in (self.folder, config, configured, Path(str(configured) + '.pub')):
            real_lstat = Path.lstat
            def reparse(path, *, follow_symlinks=False):
                original = real_lstat(path)
                if path == rejected:
                    return SimpleNamespace(st_mode=original.st_mode, st_file_attributes=0x400)
                return original
            with self.subTest(rejected=rejected.name), patch.object(Path, 'lstat', reparse):
                self.assertIsNone(metadata(rejected, directory=rejected == self.folder))
                result = self.find()
                if rejected == self.folder:
                    self.assertIsNone(result)
                elif rejected == config:
                    self.assertEqual(result.key, configured)
                else:
                    self.assertEqual(result.key, fallback)

    def test_discovery_never_opens_private_file_and_preserves_all_mtimes(self):
        private = self.pair('id_ed25519_personal')
        self.config(private.name)
        before = {path: path.stat().st_mtime_ns for path in self.folder.iterdir()}
        folder_mtime = self.folder.stat().st_mtime_ns
        opened = []
        real_open = os.open
        def guard(path, flags, *arguments, **keywords):
            self.assertNotEqual(Path(path), private)
            self.assertEqual(flags & (os.O_CREAT | os.O_TRUNC | os.O_WRONLY | os.O_RDWR), 0)
            opened.append(Path(path))
            return real_open(path, flags, *arguments, **keywords)
        with patch('jobs_ssh_key_mgr.existing_public.os.open', side_effect=guard):
            self.assertEqual(self.find().key, private)
        self.assertIn(Path(str(private) + '.pub'), opened)
        self.assertEqual(before, {path: path.stat().st_mtime_ns for path in self.folder.iterdir()})
        self.assertEqual(folder_mtime, self.folder.stat().st_mtime_ns)


if __name__ == '__main__':
    unittest.main()
