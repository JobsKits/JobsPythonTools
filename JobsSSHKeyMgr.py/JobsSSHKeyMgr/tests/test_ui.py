"""语言、主题和布局隔离回归。Created by Jobs on 2026年11月4日，星期三."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from PySide6.QtCore import QLocale, QRect, QSettings, QTimer, Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QComboBox, QMessageBox, QPushButton, QStyle, QStyleOptionButton, QStyleOptionFrame
from jobs_ssh_key_mgr.app import Window, SetupWorker, ConnectionTestWorker
from jobs_ssh_key_mgr.core import Event, SetupError, SetupResult
from jobs_ssh_key_mgr.translations import LANGUAGE_NAMES, TR, resolve_language


class UiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyle('Fusion')

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.settings = QSettings(str(Path(self.temporary.name) / 'preferences.ini'), QSettings.Format.IniFormat)
        self.restore_patch = patch('jobs_ssh_key_mgr.app.find_existing_public_key', return_value=None)
        self.restore_patch.start()
        self.window = Window(settings=self.settings)
        self.window.show()
        self.app.processEvents()

    def tearDown(self):
        self.window.close()
        self.restore_patch.stop()
        self.temporary.cleanup()

    def test_reopening_restores_existing_public_key_for_copy_and_manual_test(self):
        result = SetupResult(Path('/test/.ssh/id_ed25519_personal'), 'ssh-ed25519 AAAA person@example.com', False)
        self.window.capture_result(result)
        self.window.finished()
        self.assertEqual(self.settings.value('last_key_name'), result.key.name)
        self.window.close()
        loader = Mock(return_value=result)
        generation = Mock(side_effect=AssertionError('startup must not generate or configure'))
        restored = Window(settings=self.settings, public_key_loader=loader, worker_factory=generation)
        try:
            self.assertEqual(restored.public_panel.content.toPlainText(), result.public_key)
            self.assertEqual(restored.public_panel.path.text(), str(result.key) + '.pub')
            self.assertTrue(restored.copy_button.isEnabled())
            self.assertTrue(restored.test_connection_button.isEnabled())
            self.assertEqual(restored.generate.text(), restored.text('regenerate'))
            self.assertFalse(restored.last_result.authenticated)
            self.assertEqual(loader.call_args.kwargs['preferred_name'], result.key.name)
            restored.copy_button.click()
            self.assertEqual(self.app.clipboard().text(), result.public_key)
            generation.assert_not_called()
            for language in TR:
                restored.language.setCurrentIndex(restored.language.findData(language))
                self.assertIn(restored.text('public_restored', path=str(result.key) + '.pub'), restored.output.toPlainText())
                self.assertEqual(restored.generate.text(), TR[language]['regenerate'])
        finally:
            restored.close()

    def test_unreadable_or_invalid_existing_public_key_leaves_safe_disabled_empty_state(self):
        for failure in (OSError('cannot read'), SetupError('public_file_invalid')):
            restored = Window(settings=self.settings, public_key_loader=Mock(side_effect=failure))
            try:
                self.assertFalse(restored.copy_button.isEnabled())
                self.assertFalse(restored.test_connection_button.isEnabled())
                self.assertIsNone(restored.last_result)
                self.assertEqual(restored.public_panel.content.toPlainText(), '')
                self.assertEqual(restored.events[-1].key, 'public_restore_failed')
            finally:
                restored.close()

    def test_all_languages_translate_the_entire_window_and_history(self):
        self.window.receive(Event('generated', {'path': '/test/key'}))
        for key in ('ssh_readme_created', 'ssh_readme_skipped'):
            self.window.receive(Event(key, {'path': '/test/.ssh/README.md'}))
        self.window.receive(Event('ssh_readme_failed', {'detail': 'E_SSH_README_WRITE'}))
        for language in TR:
            self.window.language.setCurrentIndex(self.window.language.findData(language))
            self.assertEqual(self.window.tokens.text(), TR[language]['open_tokens'])
            self.assertEqual(self.window.heading.text(), '🔑' + TR[language]['title'])
            self.assertIn(TR[language]['generated'].format(path='/test/key'), self.window.output.toPlainText())
            for key in ('ssh_readme_created', 'ssh_readme_skipped', 'ssh_readme_failed'):
                self.assertIn(TR[language][key].format(path='/test/.ssh/README.md', detail='E_SSH_README_WRITE'), self.window.output.toPlainText())
        self.assertEqual(len(LANGUAGE_NAMES), 11)

    def test_github_cli_failures_remain_distinct_when_history_language_changes(self):
        states = ('github_cli_missing', 'github_not_logged_in', 'github_auth_invalid',
                  'github_auth_forbidden', 'github_auth_network', 'github_auth_timeout',
                  'github_auth_check_failed')
        for key in states:
            self.window.receive(Event(key, {'detail': 'E_GH_AUTH_RESPONSE'} if key == 'github_auth_check_failed' else {}))
        for language, messages in TR.items():
            self.window.language.setCurrentIndex(self.window.language.findData(language))
            history = self.window.output.toPlainText()
            self.assertNotIn('github_auth_missing', messages)
            self.assertEqual(len({messages[key] for key in states}), len(states))
            for key in states:
                self.assertIn(messages[key].format(detail='E_GH_AUTH_RESPONSE'), history)

    def test_generate_row_and_four_icon_actions_with_conditional_copy(self):
        self.assertEqual(self.window.email.text(), '295060456@qq.com')
        actions = [self.window.copy_button, self.window.folder, self.window.github, self.window.tokens]
        self.assertEqual(self.window.action_buttons, actions)
        self.assertEqual(self.window.buttons, [self.window.generate, *actions])
        self.assertLess(self.window.generate.y(), self.window.copy_button.y())
        self.assertGreater(self.window.generate.width(), self.window.copy_button.width() * 1.9)
        self.assertEqual(self.window.copy_button.y(), self.window.folder.y())
        self.assertEqual(self.window.github.y(), self.window.tokens.y())
        self.assertLess(self.window.copy_button.y(), self.window.github.y())
        self.assertEqual(self.window.copy_button.x(), self.window.github.x())
        self.assertEqual(self.window.folder.x(), self.window.tokens.x())
        for button in actions:
            self.assertFalse(button.icon().isNull())
        self.assertFalse(hasattr(self.window, 'quit'))
        self.assertFalse(hasattr(self.window, 'view_public'))
        self.assertFalse(hasattr(self.window, 'public_window'))
        panel = self.window.public_panel
        self.assertTrue(panel.isVisible())
        self.assertIs(panel.copy_button, self.window.copy_button)
        self.assertIs(self.window.copy_button.parentWidget(), self.window)
        self.assertEqual(panel.content.toPlainText(), '')
        self.assertEqual(panel.content.placeholderText(), self.window.text('public_empty'))
        self.assertFalse(self.window.copy_button.isEnabled())
        self.assertFalse(self.window.test_connection_button.isEnabled())
        self.assertEqual(self.window.generate.text(), self.window.text('generate'))
        self.show_fake_public_result()
        self.assertTrue(self.window.copy_button.isEnabled())
        self.assertTrue(self.window.test_connection_button.isEnabled())
        self.assertEqual(self.window.generate.text(), self.window.text('regenerate'))

    def test_cancel_regeneration_preserves_public_result_preferences_and_history(self):
        result = self.show_fake_public_result()
        self.window.email.setText('changed@example.com')
        before_settings = {key: self.settings.value(key) for key in self.settings.allKeys()}
        before_history = self.window.output.toPlainText()
        before_status = self.window.public_panel.status.text()
        self.window.worker_factory = Mock(side_effect=AssertionError('cancel must not create worker'))
        with patch.object(self.window, 'confirm_regeneration', return_value=False) as confirmation:
            self.window.generate.click()
        confirmation.assert_called_once()
        self.window.worker_factory.assert_not_called()
        self.assertIs(self.window.last_result, result)
        self.assertEqual(self.window.public_panel.content.toPlainText(), result.public_key)
        self.assertEqual(self.window.output.toPlainText(), before_history)
        self.assertEqual(self.window.public_panel.status.text(), before_status)
        self.assertEqual({key: self.settings.value(key) for key in self.settings.allKeys()}, before_settings)
        self.assertTrue(self.window.copy_button.isEnabled())
        self.assertTrue(self.window.generate.isEnabled())
        self.assertIsNone(self.window.worker)

    def test_confirmed_regeneration_starts_once_and_busy_click_does_not_confirm_again(self):
        self.show_fake_public_result()
        self.window.worker_factory = Mock(return_value=Mock())
        with patch.object(self.window, 'confirm_regeneration', return_value=True) as confirmation, patch.object(self.window, 'launch_worker') as launch:
            self.window.start()
            self.window.start()
            confirmation.assert_called_once()
            self.window.worker_factory.assert_called_once()
            launch.assert_called_once()
        self.assertEqual(self.window.public_panel.content.toPlainText(), '')
        self.assertFalse(self.window.copy_button.isEnabled())
        self.window.worker = None

    def test_first_generation_does_not_show_regeneration_confirmation(self):
        self.window.worker_factory = Mock(return_value=Mock())
        with patch.object(self.window, 'confirm_regeneration', side_effect=AssertionError('no existing key')) as confirmation, patch.object(self.window, 'launch_worker'):
            self.window.start()
        confirmation.assert_not_called()
        self.window.worker_factory.assert_called_once()
        self.window.worker = None

    def test_regeneration_dialog_translates_and_defaults_to_cancel_in_both_themes(self):
        self.show_fake_public_result()
        for language, messages in TR.items():
            self.window.language.setCurrentIndex(self.window.language.findData(language))
            for mode in ('light', 'dark'):
                self.window.theme.setCurrentIndex(self.window.theme.findData(mode))
                for action in ('confirm', 'cancel', 'close'):
                    seen = {}
                    def respond():
                        dialog = self.app.activeModalWidget()
                        seen['dialog'] = isinstance(dialog, QMessageBox)
                        if not seen['dialog']:
                            return
                        seen['title'] = dialog.windowTitle()
                        seen['prompt'] = dialog.text()
                        seen['details'] = dialog.informativeText()
                        seen['default'] = dialog.defaultButton().text()
                        seen['escape'] = dialog.escapeButton().text()
                        seen['background'] = dialog.palette().color(QPalette.ColorRole.Window).lightness()
                        if action == 'close':
                            dialog.reject()
                        else:
                            role = QMessageBox.ButtonRole.AcceptRole if action == 'confirm' else QMessageBox.ButtonRole.RejectRole
                            next(button for button in dialog.buttons() if dialog.buttonRole(button) == role).click()
                    QTimer.singleShot(0, respond)
                    accepted = self.window.confirm_regeneration()
                    with self.subTest(language=language, theme=mode, action=action):
                        self.assertTrue(seen['dialog'])
                        self.assertEqual(accepted, action == 'confirm')
                        self.assertEqual(seen['prompt'], messages['regenerate_title'])
                        self.assertEqual(seen['details'], messages['regenerate_prompt'] + '\n\n' + messages['regenerate_details'].format(email=self.window.email.text().strip(), algorithm=self.window.algorithm.currentText()))
                        self.assertEqual(seen['default'], messages['cancel'])
                        self.assertEqual(seen['escape'], messages['cancel'])
                        self.assertEqual(seen['background'] < 128, mode == 'dark')

    def test_manual_theme_resists_system_changes_and_selection_persists(self):
        self.window.theme.setCurrentIndex(self.window.theme.findData('light'))
        self.window.language.setCurrentIndex(self.window.language.findData('fr'))
        self.app.styleHints().setColorScheme(Qt.ColorScheme.Dark)
        self.app.processEvents()
        self.assertGreater(self.app.palette().color(QPalette.ColorRole.Window).lightness(), 200)
        self.window.close()
        self.settings.setValue('email', 'saved-person@example.com')
        restored = Window(settings=self.settings)
        self.assertEqual(restored.email.text(), 'saved-person@example.com')
        self.assertEqual(restored.theme.currentData(), 'light')
        self.assertEqual(restored.language.currentData(), 'fr')
        restored.close()
        self.app.styleHints().setColorScheme(Qt.ColorScheme.Unknown)

    def test_system_theme_and_locale_mapping(self):
        self.window.theme.setCurrentIndex(self.window.theme.findData('system'))
        self.app.styleHints().setColorScheme(Qt.ColorScheme.Dark)
        self.window.system_theme_changed(Qt.ColorScheme.Dark)
        self.assertLess(self.app.palette().color(QPalette.ColorRole.Window).lightness(), 60)
        self.assertEqual(self.window.output.palette().color(QPalette.ColorRole.Base).name(), '#000000')
        self.assertEqual(self.window.public_panel.content.palette().color(QPalette.ColorRole.Text).name(), '#00ff00')
        self.app.styleHints().setColorScheme(Qt.ColorScheme.Light)
        self.window.system_theme_changed(Qt.ColorScheme.Light)
        self.assertGreater(self.app.palette().color(QPalette.ColorRole.Window).lightness(), 200)
        self.app.styleHints().setColorScheme(Qt.ColorScheme.Unknown)
        self.assertEqual(resolve_language('zh_HK'), 'zh_TW')
        self.assertEqual(resolve_language('bo_CN'), 'bo')
        self.assertEqual(resolve_language('ko_KR'), 'ko')

    def test_thread_remains_owned_until_finished(self):
        from PySide6.QtCore import QThread, Signal
        import time
        class DelayedWorker(QThread):
            event = Signal(object)
            completed = Signal(object)
            def __init__(self, email, algorithm, parent):
                super().__init__(parent)
            def run(self):
                self.completed.emit(None)
                time.sleep(0.15)
        self.window.worker_factory = DelayedWorker
        self.window.email.setText('person@example.com')
        self.window.start()
        time.sleep(0.03)
        self.app.processEvents()
        self.assertIsNotNone(self.window.worker)
        self.assertFalse(self.window.generate.isEnabled())
        self.window.close()
        self.assertTrue(self.window.isVisible())
        deadline = time.monotonic() + 3
        while self.window.worker is not None and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.01)
        if self.window.worker is not None:
            self.window.worker.wait()
            self.app.processEvents()
        self.assertIsNone(self.window.worker)
        self.assertTrue(self.window.generate.isEnabled())

    def show_fake_public_result(self):
        result = SetupResult(Path('/test/id_ed25519_personal'),
                             'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestPublicKey person@example.com', False)
        self.window.pending_result = result
        self.window.finished()
        self.app.processEvents()
        return result

    def test_inline_public_panel_keeps_key_for_repeated_explicit_copy(self):
        clipboard = Mock()
        visible = {widget for widget in QApplication.topLevelWidgets() if widget.isVisible()}
        with patch('jobs_ssh_key_mgr.app.QApplication.clipboard', return_value=clipboard):
            result = self.show_fake_public_result()
            public = self.window.public_panel
            self.assertTrue(public.isVisible())
            self.assertFalse(public.isWindow())
            self.assertEqual({widget for widget in QApplication.topLevelWidgets() if widget.isVisible()}, visible)
            self.assertEqual(public.content.toPlainText(), result.public_key)
            self.assertEqual(public.path.text(), str(result.key) + '.pub')
            clipboard.setText.assert_not_called()
            public.copy_button.click()
            clipboard.setText.assert_called_once_with(result.public_key)
            public.copy_button.click()
            self.assertEqual(clipboard.setText.call_count, 2)
            self.assertEqual(public.status.text(), self.window.text('copy_success'))
            self.assertEqual(public.content.toPlainText(), result.public_key)

    def test_public_panel_follows_all_languages_and_theme(self):
        result = self.show_fake_public_result()
        public = self.window.public_panel
        with patch('jobs_ssh_key_mgr.app.QApplication.clipboard', return_value=Mock()):
            public.copy_button.click()
        for language, messages in TR.items():
            self.window.language.setCurrentIndex(self.window.language.findData(language))
            self.assertEqual(public.copy_button.text(), messages['copy_public'])
            self.assertEqual(public.heading.text(), messages['public_title'])
            self.assertEqual(public.content.accessibleName(), messages['public_content'])
            self.assertEqual(public.status.text(), messages['copy_success'])
            self.assertEqual(public.content.toPlainText(), result.public_key)
        self.window.theme.setCurrentIndex(self.window.theme.findData('dark'))
        self.assertEqual(public.content.palette().color(QPalette.ColorRole.Base).name(), '#000000')
        self.window.theme.setCurrentIndex(self.window.theme.findData('light'))
        self.assertEqual(public.content.palette().color(QPalette.ColorRole.Base).name(), '#ffffff')

    def test_private_key_text_is_never_displayed(self):
        self.window.pending_result = SetupResult(Path('/test/key'), '-----BEGIN OPENSSH PRIVATE KEY-----\nprivate-secret', False)
        self.window.finished()
        public = self.window.public_panel
        self.assertTrue(public.isVisible())
        self.assertEqual(public.content.toPlainText(), '')
        self.assertFalse(public.copy_button.isEnabled())
        self.assertNotIn('private-secret', self.window.output.toPlainText())
        self.assertIn('public_file_invalid', [event.key for event in self.window.events])

    def test_partial_setup_returns_public_key_after_configuration_error(self):
        result = SetupResult(Path('/test/key'), 'ssh-ed25519 AAAA person@example.com', False)
        engine = Mock(last_result=result)
        engine.execute.side_effect = SetupError('config_invalid')
        worker = SetupWorker('person@example.com', 'ed25519')
        worker.event.connect(self.window.receive)
        worker.completed.connect(self.window.capture_result)
        with patch('jobs_ssh_key_mgr.app.SshSetup', return_value=engine):
            worker.run()
        self.assertIs(self.window.pending_result, result)
        self.window.finished()
        self.assertTrue(self.window.public_panel.isVisible())
        self.assertEqual(self.window.public_panel.content.toPlainText(), result.public_key)
        self.assertIn('config_invalid', [event.key for event in self.window.events])

    def test_start_clears_old_public_key_in_the_persistent_panel(self):
        from PySide6.QtCore import QThread, Signal
        import time
        class DelayedWorker(QThread):
            event = Signal(object)
            completed = Signal(object)
            def __init__(self, email, algorithm, parent):
                super().__init__(parent)
            def run(self):
                time.sleep(0.05)
                self.completed.emit(None)
        self.show_fake_public_result()
        public = self.window.public_panel
        self.window.worker_factory = DelayedWorker
        with patch.object(self.window, 'confirm_regeneration', return_value=True):
            self.window.start()
        self.assertTrue(public.isVisible())
        self.assertEqual(public.content.toPlainText(), '')
        self.assertFalse(public.copy_button.isEnabled())
        deadline = time.monotonic() + 3
        while self.window.worker is not None and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.01)
        if self.window.worker is not None:
            self.window.worker.wait()
            self.app.processEvents()
        self.assertIsNone(self.window.worker)
        self.assertFalse(public.copy_button.isEnabled())

    def test_recommendation_and_algorithm_explanation_follow_selection_and_language(self):
        for language, messages in TR.items():
            self.window.language.setCurrentIndex(self.window.language.findData(language))
            self.window.algorithm.setCurrentIndex(self.window.algorithm.findData('ed25519'))
            self.assertEqual(self.window.algorithm.currentText(), messages['algorithm_ed25519'])
            self.assertEqual(self.window.algorithm_description.text(), messages['algorithm_ed25519_description'])
            self.window.algorithm.setCurrentIndex(self.window.algorithm.findData('rsa'))
            self.assertEqual(self.window.algorithm.currentData(), 'rsa')
            self.assertEqual(self.window.algorithm_description.text(), messages['algorithm_rsa_description'])
            self.assertTrue(self.window.algorithm_description.isVisible())
            self.app.processEvents()
            self.assertGreaterEqual(self.window.generate.y(), self.window.terminal_splitter.y() + self.window.terminal_splitter.height() + 8)

    def test_algorithm_help_stays_compact_at_different_sizes_and_languages(self):
        for width, height in ((760, 710), (900, 760), (920, 1050)):
            for language in TR:
                self.window.language.setCurrentIndex(self.window.language.findData(language))
                for algorithm in ('ed25519', 'rsa'):
                    self.window.algorithm.setCurrentIndex(self.window.algorithm.findData(algorithm))
                    self.window.resize(width, height)
                    self.app.processEvents()
                    combo = self.window.algorithm
                    description = self.window.algorithm_description
                    combo_bottom = combo.mapTo(self.window, combo.rect().bottomLeft()).y() + 1
                    description_top = description.mapTo(self.window, description.rect().topLeft()).y()
                    with self.subTest(width=width, language=language, algorithm=algorithm):
                        self.assertEqual(description_top - combo_bottom, 6)
                        natural_height = description.fontMetrics().boundingRect(
                            QRect(0, 0, description.contentsRect().width(), 100000),
                            int(Qt.TextFlag.TextWordWrap), description.text()).height()
                        self.assertEqual(description.height(), max(description.fontMetrics().lineSpacing(), natural_height))
                        self.assertEqual(self.window.result_label.y() - description_top - description.height(), 18)
                        self.assertGreaterEqual(self.window.output.height(), 64)
                        self.assertGreaterEqual(self.window.public_panel.content.height(), 64)
                        self.assertGreaterEqual(self.window.generate.y(), self.window.terminal_splitter.y() + self.window.terminal_splitter.height() + 8)
            before = self.window.minimumHeight()
            for _ in range(4):
                self.window.resize(width, height)
                self.app.processEvents()
            self.assertEqual(self.window.minimumHeight(), before)

    def test_preferences_stay_small_at_top_right_beside_github_title(self):
        for width in (760, 900, 1100):
            for language, messages in TR.items():
                self.window.language.setCurrentIndex(self.window.language.findData(language))
                self.window.resize(width, 900)
                self.app.processEvents()
                with self.subTest(width=width, language=language):
                    self.assertIn('Jobs GitHub SSH', self.window.heading.text())
                    self.assertIn('SSH', self.window.windowTitle())
                    self.assertLessEqual(self.window.language.height(), 30)
                    self.assertLessEqual(self.window.theme.height(), 30)
                    self.assertLess(self.window.heading.geometry().right(), self.window.language.x())
                    self.assertEqual(self.window.language.y(), self.window.theme.y())
                    self.assertEqual(self.window.language.y(), self.window.layout().contentsMargins().top())
                    self.assertEqual(self.window.theme.geometry().right(), self.window.width() - 31)
                    self.assertEqual(self.window.language.accessibleName(), messages['language'])
                    self.assertEqual(self.window.theme.accessibleName(), messages['theme'])
                    self.assertLess(self.window.language.y(), self.window.email.y())
                    for button in self.window.action_buttons:
                        needed = button.fontMetrics().horizontalAdvance(button.text()) + button.iconSize().width() + 24
                        self.assertGreaterEqual(button.width(), needed)

    def test_preference_buttons_show_icons_and_select_checked_menu_actions(self):
        for button in (self.window.language, self.window.theme):
            self.assertIsInstance(button, QPushButton)
            self.assertNotIsInstance(button, QComboBox)
            self.assertIsNone(button.menu())
            self.assertFalse(button.icon().isNull())
            self.assertTrue(button.text())
            self.assertEqual(len(button.options_menu.actions()), button.count())
        french = self.window.language.options_menu.actions()[self.window.language.findData('fr')]
        french.trigger()
        self.assertEqual(self.window.language.currentData(), 'fr')
        self.assertEqual(self.settings.value('language'), 'fr')
        self.assertTrue(french.isChecked())
        self.assertEqual(self.window.language.text(), self.window.language.currentText())
        day_icon = self.window.theme.icon().cacheKey()
        dark = self.window.theme.options_menu.actions()[self.window.theme.findData('dark')]
        dark.trigger()
        self.assertEqual(self.window.theme.currentData(), 'dark')
        self.assertEqual(self.settings.value('theme'), 'dark')
        self.assertTrue(dark.isChecked())
        self.assertNotEqual(self.window.theme.icon().cacheKey(), day_icon)
        self.assertEqual(sum(action.isChecked() for action in self.window.theme.options_menu.actions()), 1)
        self.assertEqual(self.window.output.palette().color(QPalette.ColorRole.Base).name(), '#000000')

    def test_public_path_text_fits_current_font_style_and_language(self):
        field = self.window.public_panel.path
        for language in TR:
            self.window.language.setCurrentIndex(self.window.language.findData(language))
            for mode in ('light', 'dark'):
                self.window.theme.setCurrentIndex(self.window.theme.findData(mode))
                self.app.processEvents()
                option = QStyleOptionFrame()
                field.initStyleOption(option)
                contents = field.style().subElementRect(QStyle.SubElement.SE_LineEditContents, option, field)
                margins = field.textMargins()
                available = contents.height() - margins.top() - margins.bottom()
                with self.subTest(language=language, theme=mode):
                    self.assertGreaterEqual(available, field.fontMetrics().lineSpacing())
                    self.assertGreaterEqual(field.height(), field.minimumSizeHint().height())
                    self.assertEqual(field.placeholderText(), self.window.text('public_key_path', path='').strip())

    def test_connection_button_fits_its_icon_and_full_translation(self):
        button = self.window.test_connection_button
        for language in TR:
            self.window.language.setCurrentIndex(self.window.language.findData(language))
            for mode in ('light', 'dark'):
                self.window.theme.setCurrentIndex(self.window.theme.findData(mode))
                for enabled in (False, True):
                    button.setEnabled(enabled)
                    self.window.resize(self.window.minimumSize())
                    self.app.processEvents()
                    option = QStyleOptionButton()
                    button.initStyleOption(option)
                    contents = button.style().subElementRect(QStyle.SubElement.SE_PushButtonContents, option, button)
                    with self.subTest(language=language, theme=mode, enabled=enabled):
                        self.assertGreaterEqual(contents.height(), button.fontMetrics().lineSpacing())
                        self.assertFalse(button.icon().isNull())
                        self.assertGreaterEqual(contents.height(), button.iconSize().height())
                        needed_width = button.fontMetrics().horizontalAdvance(button.text()) + button.iconSize().width() + 4
                        self.assertGreaterEqual(contents.width(), needed_width)
                        self.assertEqual(button.text(), self.window.text('test_connection'))
                        self.assertLess(self.window.result_label.geometry().right(), button.x())
                        self.assertLess(button.geometry().bottom(), self.window.terminal_splitter.y())

    def test_token_button_opens_exact_tokens_page(self):
        with patch('jobs_ssh_key_mgr.app.QDesktopServices.openUrl', return_value=True) as opened:
            self.window.tokens.click()
            self.assertEqual(opened.call_args.args[0].toString(), 'https://github.com/settings/tokens')
        with patch('jobs_ssh_key_mgr.app.QDesktopServices.openUrl', return_value=False):
            self.window.tokens.click()
            self.assertEqual(self.window.events[-1].key, 'open_failed')
            self.assertEqual(self.window.events[-1].values['detail'], 'https://github.com/settings/tokens')

    def test_terminal_areas_are_readonly_scrollable_and_black_green_in_dark_mode(self):
        self.window.theme.setCurrentIndex(self.window.theme.findData('dark'))
        for terminal in (self.window.output, self.window.public_panel.content):
            terminal.setPlainText('\n'.join('line ' + str(index) for index in range(100)))
            self.assertTrue(terminal.isReadOnly())
            self.assertEqual(terminal.verticalScrollBarPolicy(), Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.assertEqual(terminal.palette().color(QPalette.ColorRole.Base).name(), '#000000')
            self.assertEqual(terminal.palette().color(QPalette.ColorRole.Text).name(), '#00ff00')
            self.assertNotEqual(terminal.palette().color(QPalette.ColorRole.Highlight).name(), terminal.palette().color(QPalette.ColorRole.HighlightedText).name())
        self.app.processEvents()
        self.assertGreater(self.window.output.verticalScrollBar().maximum(), 0)
        self.assertGreater(self.window.public_panel.content.verticalScrollBar().maximum(), 0)
        self.window.theme.setCurrentIndex(self.window.theme.findData('light'))
        self.assertEqual(self.window.output.palette().color(QPalette.ColorRole.Base).name(), '#ffffff')
        self.assertNotEqual(self.window.output.palette().color(QPalette.ColorRole.Text).name(), '#00ff00')

    def test_public_panel_sits_below_logs_without_hiding_buttons(self):
        for width,height in ((760,710),(900,760),(920,880)):
            self.window.resize(width,height)
            self.app.processEvents()
            output_bottom = self.window.output.mapTo(self.window,self.window.output.rect().bottomLeft()).y()
            public_top = self.window.public_panel.mapTo(self.window,self.window.public_panel.rect().topLeft()).y()
            self.assertGreater(public_top, output_bottom)
            self.assertGreater(self.window.generate.y(), self.window.terminal_splitter.geometry().bottom())
            self.assertLess(self.window.tokens.geometry().bottom(), self.window.height())
            self.assertTrue(self.window.public_panel.isVisible())

    def test_log_updates_keep_reader_scroll_position_and_follow_only_at_bottom(self):
        self.window.events = [Event('failed', {'detail': 'line ' + str(index)}) for index in range(100)]
        self.window.render_events()
        self.app.processEvents()
        scrollbar = self.window.output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum() // 3)
        position = scrollbar.value()
        self.window.receive(Event('failed', {'detail': 'new line'}))
        self.assertEqual(scrollbar.value(), position)
        self.assertLess(scrollbar.value(), scrollbar.maximum())
        scrollbar.setValue(scrollbar.maximum())
        self.window.receive(Event('failed', {'detail': 'follow line'}))
        self.assertEqual(scrollbar.value(), scrollbar.maximum())

    def test_standalone_connection_worker_verifies_and_completes_sourcetree_setup(self):
        result = SetupResult(Path('/test/key'), 'ssh-ed25519 AAAA person@example.com', False)
        tested = SetupResult(result.key, result.public_key, True, 'ExampleAccount')
        engine = Mock()
        engine.test_and_configure_sourcetree.return_value = tested
        worker = ConnectionTestWorker(result)
        received = []
        worker.completed.connect(received.append)
        with patch('jobs_ssh_key_mgr.app.SshSetup', return_value=engine):
            worker.run()
        engine.test_and_configure_sourcetree.assert_called_once_with(result)
        engine.execute.assert_not_called()
        self.assertEqual(received, [tested])
        engine.test_and_configure_sourcetree.side_effect = SetupError('public_file_invalid')
        failed = ConnectionTestWorker(result)
        retained = []
        failed.completed.connect(retained.append)
        with patch('jobs_ssh_key_mgr.app.SshSetup', return_value=engine):
            failed.run()
        self.assertEqual(retained[0].public_key, result.public_key)
        self.assertEqual(retained[0].key, result.key)
        self.assertFalse(retained[0].authenticated)

    def test_retest_keeps_public_key_and_does_not_restart_generation(self):
        from PySide6.QtCore import QThread, Signal
        import time
        result = self.show_fake_public_result()
        class TestWorker(QThread):
            event = Signal(object)
            completed = Signal(object)
            def __init__(self, value, parent):
                super().__init__(parent)
                self.value = value
            def run(self):
                self.event.emit(Event('testing_connection'))
                time.sleep(0.03)
                self.completed.emit(SetupResult(self.value.key, self.value.public_key, True, 'ExampleAccount'))
        self.window.test_worker_factory = TestWorker
        self.window.worker_factory = Mock(side_effect=AssertionError('must not generate on test'))
        self.window.test_connection_button.click()
        self.assertIsNotNone(self.window.worker)
        self.assertEqual(self.window.public_panel.content.toPlainText(), result.public_key)
        self.assertFalse(self.window.test_connection_button.isEnabled())
        self.assertTrue(self.window.copy_button.isEnabled())
        deadline = time.monotonic() + 3
        while self.window.worker is not None and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.01)
        if self.window.worker is not None:
            self.window.worker.wait()
            self.app.processEvents()
        self.assertIsNone(self.window.worker)
        self.window.worker_factory.assert_not_called()
        self.assertTrue(self.window.last_result.authenticated)
        self.assertEqual(self.window.last_result.account, 'ExampleAccount')
        self.assertTrue(self.window.copy_button.isEnabled())
        self.assertTrue(self.window.test_connection_button.isEnabled())

    def test_default_email_is_real_editable_value_with_muted_theme_color(self):
        for theme,muted,normal,disabled in [('light','#52647d','#202c3d','#7a8494'),('dark','#a7b3c7','#edf1f7','#768298')]:
            self.window.theme.setCurrentIndex(self.window.theme.findData(theme))
            self.window.email.setText('295060456@qq.com')
            self.app.processEvents()
            self.assertEqual(self.window.email.text(),'295060456@qq.com')
            self.assertEqual(self.window.email.palette().color(QPalette.ColorRole.Text).name(),muted)
            self.assertEqual(self.window.email.objectName(),'defaultEmail')
            self.window.email.setText('another@example.com')
            self.app.processEvents()
            self.assertEqual(self.window.email.palette().color(QPalette.ColorRole.Text).name(),normal)
            self.window.email.setText('295060456@qq.com')
            self.window.email.setEnabled(False)
            self.app.processEvents()
            self.assertEqual(self.window.email.palette().color(QPalette.ColorGroup.Disabled,QPalette.ColorRole.Text).name(),disabled)
            self.window.email.setEnabled(True)
            self.window.email.selectAll()
            self.assertEqual(self.window.email.selectedText(),'295060456@qq.com')
            self.assertNotEqual(self.window.email.palette().color(QPalette.ColorRole.Highlight).name(),self.window.email.palette().color(QPalette.ColorRole.HighlightedText).name())
