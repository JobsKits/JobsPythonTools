"""Packaging boundaries are checked in disposable directories, never real dist."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build = load_module('hotspot_build_tests', 'build.py/build.py')
shortcuts = load_module('hotspot_shortcuts_tests', 'artifact_shortcuts.py/artifact_shortcuts.py')


class BuildSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='热点 构建安全 ')
        self.addCleanup(self.temporary.cleanup)
        self.outer = Path(self.temporary.name).resolve() / 'JobsHotspot.py'
        self.root = self.outer / 'JobsHotspot'
        self.root.mkdir(parents=True)
        self.addCleanup(patch.stopall)
        patch.object(build, 'ROOT', self.root).start()
        patch.object(build, 'OUTER', self.outer).start()

    def test_only_fixed_dist_is_cleaned(self):
        dist = self.outer / 'dist'
        dist.mkdir()
        (dist / 'old.txt').write_text('old')
        keep = self.outer / 'keep.txt'
        keep.write_text('keep')
        build.clean_dist(dist)
        self.assertFalse(dist.exists())
        self.assertEqual(keep.read_text(), 'keep')
        for refused in (self.root, self.outer, Path(self.temporary.name), Path('')):
            with self.subTest(refused=refused), self.assertRaises(RuntimeError):
                build.clean_dist(refused)

    def test_symlink_output_is_rejected(self):
        outside = Path(self.temporary.name) / 'outside'
        outside.mkdir()
        (outside / 'keep.txt').write_text('keep')
        (self.outer / 'dist').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(RuntimeError):
            build.clean_dist(self.outer / 'dist')
        self.assertTrue((outside / 'keep.txt').exists())

    def test_symlink_delivery_root_is_rejected(self):
        alias = Path(self.temporary.name) / 'alias'
        alias.symlink_to(self.outer, target_is_directory=True)
        with patch.object(build, 'ROOT', alias / 'JobsHotspot'), patch.object(build, 'OUTER', alias):
            with self.assertRaises(RuntimeError):
                build.fixed_directory('dist')

    def test_failed_cleanup_stops(self):
        dist = self.outer / 'dist'
        dist.mkdir()
        with patch.object(build.shutil, 'rmtree', side_effect=PermissionError('blocked')):
            with self.assertRaises(PermissionError):
                build.clean_dist(dist)
        self.assertTrue(dist.exists())

    def test_required_resources_checked_before_mutation(self):
        assets = self.root / 'src/jobs_hotspot/assets'
        assets.mkdir(parents=True)
        with patch.object(build.sys, 'platform', 'darwin'):
            with self.assertRaises(RuntimeError):
                build.check_ui_resources()
            (assets / 'icon.png').write_bytes(b'png')
            (assets / 'app.icns').write_bytes(b'icon')
            build.check_ui_resources()

    def test_spec_follows_moved_source(self):
        work = self.outer / 'work'
        work.mkdir()
        for target_platform in ('darwin', 'win32'):
            with self.subTest(platform=target_platform), patch.object(build.sys, 'platform', target_platform):
                spec = build.write_spec(work, '0.1.0')
                text = spec.read_text()
                compile(text, str(spec), 'exec')
                self.assertIn(str(self.root / 'src'), text)
                self.assertIn('jobs_hotspot.backends.windows', text)
                self.assertIn('jobs_hotspot.backends.macos', text)
                self.assertIn(str(self.root / 'scripts/launch.py/launch.py'), text)
                self.assertNotIn('JobsSSHKeyMgr', text)
                if target_platform == 'darwin':
                    self.assertIn('NSAppleEventsUsageDescription', text)

    def test_install_cancel_on_spaces_and_eof(self):
        stream = Mock()
        stream.isatty.return_value = True
        with patch.object(build.sys, 'stdin', stream):
            with patch('builtins.input', return_value=' '), self.assertRaises(RuntimeError):
                build.confirm('check')
            with patch('builtins.input', side_effect=EOFError), self.assertRaises(RuntimeError):
                build.confirm('check')
        with patch.object(build.sys, 'stdin', Mock(isatty=lambda: False)):
            with self.assertRaises(RuntimeError):
                build.confirm('check')

    def test_smoke_failure_and_timeout_propagate(self):
        with patch.object(build.subprocess, 'run', return_value=Mock(returncode=1, stdout='', stderr='bad')):
            with self.assertRaises(RuntimeError):
                build.smoke_application(Path('app'))
        with patch.object(build.subprocess, 'run', side_effect=subprocess.TimeoutExpired('app', 45)):
            with self.assertRaises(subprocess.TimeoutExpired):
                build.smoke_application(Path('app'))

    def test_managed_environment_outside_project(self):
        environment = build.managed_environment()
        self.assertFalse(environment.is_relative_to(self.outer))
        self.assertIn('BuildEnvironments', environment.parts)

    @unittest.skipIf(sys.platform == 'win32', 'POSIX symlink protection; Windows COM needs native validation')
    def test_shortcuts_preserve_unrelated_file_and_link(self):
        dist = self.outer / 'dist' / '2026.11.05 10-20-30'
        dist.mkdir(parents=True)
        artifact = dist / 'JobsHotspot.app'
        artifact.mkdir()
        unrelated = self.outer / 'keep.app'
        unrelated.write_text('preserve')
        foreign_target = self.outer / 'foreign'
        foreign_target.mkdir()
        foreign_link = self.outer / 'other.app'
        foreign_link.symlink_to(foreign_target, target_is_directory=True)
        shortcuts.publish_shortcuts(self.outer, [artifact])
        generated = self.outer / artifact.name
        self.assertFalse(generated.readlink().is_absolute())
        self.assertEqual(generated.resolve(), artifact)
        shortcuts.clear_shortcuts(self.outer)
        self.assertFalse(generated.is_symlink())
        self.assertTrue(foreign_link.is_symlink())
        self.assertEqual(unrelated.read_text(), 'preserve')

    @unittest.skipIf(sys.platform == 'win32', 'POSIX symlink protection; Windows COM needs native validation')
    def test_shortcut_never_overwrites_real_file(self):
        artifact = self.outer / 'dist' / '2026.11.05 10-20-30' / 'JobsHotspot.dmg'
        artifact.parent.mkdir(parents=True)
        artifact.write_text('package')
        collision = self.outer / artifact.name
        collision.write_text('keep')
        with self.assertRaises(RuntimeError):
            shortcuts.publish_shortcuts(self.outer, [artifact])
        self.assertEqual(collision.read_text(), 'keep')


if __name__ == '__main__':
    unittest.main()
