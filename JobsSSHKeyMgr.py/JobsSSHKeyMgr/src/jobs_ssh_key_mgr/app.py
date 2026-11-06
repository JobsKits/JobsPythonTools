"""跨端 SSH 图形窗口。Created by Jobs on 2026年11月4日，星期三."""
from __future__ import annotations
import sys
from pathlib import Path

from PySide6.QtCore import QLocale, QRect, QSettings, QThread, QTimer, QUrl, Qt, Signal
from PySide6.QtGui import QColor, QDesktopServices, QFont, QFontDatabase, QPalette
from PySide6.QtWidgets import (QApplication, QComboBox, QFormLayout, QFrame, QGridLayout,
                               QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QProgressBar,
                               QMessageBox, QPushButton, QSizePolicy, QSplitter, QVBoxLayout, QWidget)

from .core import EMAIL, PUBLIC_KEY, Event, SetupError, SetupResult, SshSetup, default_email
from .controls import PreferenceButton, preference_icon
from .existing_public import find_existing_public_key
from .translations import LANGUAGE_NAMES, resolve_language, tr


class SetupWorker(QThread):
    event = Signal(object)
    completed = Signal(object)

    def __init__(self, email, algorithm, parent=None):
        super().__init__(parent)
        self.email, self.algorithm = email, algorithm

    def run(self):
        engine = SshSetup(emit=self.event.emit)
        try:
            result = engine.execute(self.email, self.algorithm)
        except SetupError as error:
            self.event.emit(error.event)
            result = engine.last_result
        except Exception as error:
            self.event.emit(Event('failed', {'detail': str(error)}))
            result = engine.last_result
        self.completed.emit(result)


class ConnectionTestWorker(QThread):
    """验证现有密钥并补齐 Sourcetree 识别配置，不重复生成密钥。"""
    event = Signal(object)
    completed = Signal(object)

    def __init__(self, result, parent=None):
        super().__init__(parent)
        self.result = result

    def run(self):
        engine = SshSetup(emit=self.event.emit)
        try:
            result = engine.test_and_configure_sourcetree(self.result)
        except SetupError as error:
            self.event.emit(error.event)
            result = SetupResult(self.result.key, self.result.public_key, False)
        except Exception as error:
            self.event.emit(Event('auth_failed', {'detail': str(error)}))
            result = SetupResult(self.result.key, self.result.public_key, False)
        self.completed.emit(result)


class PublicKeyPanel(QWidget):
    """主窗口常驻公钥面板，显式复制，不创建额外窗口。"""
    copied = Signal()

    def __init__(self, parent):
        super().__init__(parent)
        self.owner = parent
        self.public_key = ''
        self.status_key = 'no_public'
        self.setMinimumHeight(168)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        header = QHBoxLayout()
        self.heading = QLabel()
        self.copy_button = QPushButton()
        self.copy_button.setEnabled(False)
        header.addWidget(self.heading, 1)
        layout.addLayout(header)
        self.path = QLineEdit()
        self.path.setReadOnly(True)
        self.path.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.path)
        self.content = QPlainTextEdit()
        self.content.setObjectName('terminal')
        self.content.setReadOnly(True)
        self.content.setMinimumHeight(64)
        self.content.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(self.content, 1)
        self.status = QLabel()
        self.status.setObjectName('publicStatus')
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.copy_button.clicked.connect(self.copy)

    def set_public_key(self, result):
        if not PUBLIC_KEY.fullmatch(result.public_key):
            raise SetupError('public_file_invalid')
        self.public_key = result.public_key.strip()
        self.path.setText(str(result.key) + '.pub')
        self.content.setPlainText(self.public_key)
        self.copy_button.setEnabled(True)
        self.status_key = 'copy_ready'
        self.sync_appearance()

    def clear_public_key(self, status='no_public'):
        self.public_key = ''
        self.path.clear()
        self.content.clear()
        self.copy_button.setEnabled(False)
        self.status_key = status
        self.sync_appearance()

    def sync_appearance(self):
        text = self.owner.text
        self.heading.setText(text('public_title'))
        self.heading.setToolTip(text('public_intro'))
        self.path.setAccessibleName(text('public_key_path', path='').strip())
        self.path.setPlaceholderText(text('public_key_path', path='').strip())
        self.content.setAccessibleName(text('public_content'))
        self.content.setPlaceholderText(text('public_empty'))
        self.content.setToolTip(text('public_intro'))
        self.copy_button.setText(text('copy_public'))
        self.status.setText(text(self.status_key))
        self.setFont(self.owner.font())

    def copy(self):
        if not self.public_key:
            return
        QApplication.clipboard().setText(self.public_key)
        self.status_key = 'copy_success'
        self.status.setText(self.owner.text(self.status_key))
        self.copied.emit()


class Window(QWidget):
    def __init__(self, settings=None, worker_factory=SetupWorker, test_worker_factory=ConnectionTestWorker,
                 public_key_loader=None):
        super().__init__()
        # 沿用旧的设置域，保留用户已保存的邮箱、语言、主题和算法。
        self.settings = settings or QSettings('Jobs', 'SSHKeyManager')
        self.worker_factory = worker_factory
        self.test_worker_factory = test_worker_factory
        self.public_key_loader = public_key_loader or find_existing_public_key
        self.worker = None
        self.pending_result = None
        self.last_result = None
        self.has_existing_key = False
        self.events = [Event('ready')]
        self.system_locale = QLocale.system().name()
        self._updating_layout = False
        self.setMinimumSize(760, 610)
        self.resize(900, 760)
        self.build_ui()
        self.apply_language()
        self.apply_theme()
        QApplication.instance().styleHints().colorSchemeChanged.connect(self.system_theme_changed)
        self.locale_timer = QTimer(self)
        self.locale_timer.setInterval(2000)
        self.locale_timer.timeout.connect(self.system_language_changed)
        self.locale_timer.start()
        self.restore_existing_public_key()

    def restore_existing_public_key(self):
        try:
            result = self.public_key_loader(preferred_name=str(self.settings.value('last_key_name', '')),
                                            algorithm=self.algorithm.currentData(),
                                            email=self.email.text().strip())
            if result is None:
                return
            self.public_panel.set_public_key(result)
            self.last_result = result
            self.has_existing_key = True
            self.settings.setValue('last_key_name', result.key.name)
            self.test_connection_button.setEnabled(True)
            self.events = [event for event in self.events if event.key != 'ready']
            self.receive(Event('public_restored', {'path': str(result.key) + '.pub'}))
        except (OSError, ValueError, SetupError):
            self.last_result = None
            self.public_panel.clear_public_key()
            self.test_connection_button.setEnabled(False)
            self.receive(Event('public_restore_failed'))
        finally:
            self.sync_generate_action()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 26, 30, 26)
        layout.setSpacing(18)
        header = QHBoxLayout()
        self.heading = QLabel()
        self.heading.setObjectName('heading')
        self.heading.setWordWrap(True)
        header.addWidget(self.heading, 1)
        preferences = QHBoxLayout()
        preferences.setSpacing(8)
        self.language, self.theme = PreferenceButton(), PreferenceButton()
        for selector, width in ((self.language, 132), (self.theme, 148)):
            selector.setObjectName('preference')
            selector.setFixedSize(width, 30)
            preferences.addWidget(selector)
        for code, name in LANGUAGE_NAMES.items():
            self.language.addItem(name, code)
        for mode in ('system', 'light', 'dark'):
            self.theme.addItem('', mode)
        self.language.setCurrentIndex(max(0, self.language.findData(self.settings.value('language', 'system'))))
        self.theme.setCurrentIndex(max(0, self.theme.findData(self.settings.value('theme', 'system'))))
        header.addLayout(preferences)
        header.setAlignment(preferences, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header)
        self.subtitle = QLabel()
        self.subtitle.setObjectName('subtitle')
        self.subtitle.setWordWrap(True)
        layout.addWidget(self.subtitle)
        form = QFormLayout()
        form.setVerticalSpacing(14)
        self.email_label, self.algorithm_label = QLabel(), QLabel()
        self.email = QLineEdit(str(self.settings.value('email', default_email())))
        self.email.setMinimumHeight(40)
        self.algorithm = QComboBox()
        self.algorithm.addItem('ED25519', 'ed25519')
        self.algorithm.addItem('RSA 4096', 'rsa')
        self.algorithm.setCurrentIndex(max(0, self.algorithm.findData(self.settings.value('algorithm', 'ed25519'))))
        self.algorithm.setMinimumHeight(40)
        self.algorithm.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        form.addRow(self.email_label, self.email)
        self.algorithm_field = QWidget()
        self.algorithm_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        algorithm_layout = QVBoxLayout(self.algorithm_field)
        algorithm_layout.setContentsMargins(0, 0, 0, 0)
        algorithm_layout.setSpacing(6)
        algorithm_layout.addWidget(self.algorithm)
        self.algorithm_description = QLabel()
        self.algorithm_description.setObjectName('subtitle')
        self.algorithm_description.setWordWrap(True)
        self.algorithm_description.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.algorithm_description.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.algorithm_description.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        algorithm_layout.addWidget(self.algorithm_description)
        form.addRow(self.algorithm_label, self.algorithm_field)
        layout.addLayout(form)
        self.result_label = QLabel()
        result_header = QHBoxLayout()
        result_header.addWidget(self.result_label, 1)
        self.test_connection_button = QPushButton()
        self.test_connection_button.setEnabled(False)
        self.test_connection_button.setIconSize(self.language.iconSize())
        self.test_connection_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        result_header.addWidget(self.test_connection_button)
        layout.addLayout(result_header)
        self.terminal_splitter = QSplitter(Qt.Orientation.Vertical)
        self.terminal_splitter.setChildrenCollapsible(False)
        self.terminal_splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Ignored)
        self.terminal_splitter.setMinimumHeight(238)
        self.terminal_splitter.setHandleWidth(6)
        self.output = QPlainTextEdit()
        self.output.setObjectName('terminal')
        self.output.setReadOnly(True)
        self.output.setMinimumHeight(64)
        self.output.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.terminal_splitter.addWidget(self.output)
        self.public_panel = PublicKeyPanel(self)
        self.public_panel.copied.connect(lambda: self.receive(Event('copied')))
        self.terminal_splitter.addWidget(self.public_panel)
        self.terminal_splitter.setStretchFactor(0, 1)
        self.terminal_splitter.setStretchFactor(1, 1)
        self.terminal_splitter.setSizes([100, 180])
        layout.addWidget(self.terminal_splitter, 1)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setMaximumHeight(5)
        self.progress.setTextVisible(False)
        self.progress.hide()
        layout.addWidget(self.progress)
        buttons = QGridLayout()
        buttons.setSpacing(12)
        self.generate, self.folder, self.github, self.tokens = (QPushButton() for _ in range(4))
        self.copy_button = self.public_panel.copy_button
        self.generate.setObjectName('primary')
        self.action_buttons = [self.copy_button, self.folder, self.github, self.tokens]
        self.buttons = [self.generate, *self.action_buttons]
        for button in self.buttons:
            button.setMinimumHeight(44)
        buttons.addWidget(self.generate, 0, 0, 1, 2)
        for index, button in enumerate(self.action_buttons):
            button.setIconSize(self.language.iconSize())
            buttons.addWidget(button, 1 + index // 2, index % 2)
        buttons.setColumnStretch(0, 1)
        buttons.setColumnStretch(1, 1)
        layout.addLayout(buttons)
        self.language.currentIndexChanged.connect(self.change_language)
        self.theme.currentIndexChanged.connect(self.change_theme)
        self.algorithm.currentIndexChanged.connect(self.update_algorithm_description)
        self.email.textChanged.connect(self.update_email_style)
        self.generate.clicked.connect(self.start)
        self.folder.clicked.connect(self.open_folder)
        self.github.clicked.connect(self.open_github)
        self.tokens.clicked.connect(self.open_tokens)
        self.test_connection_button.clicked.connect(self.start_connection_test)

    def current_language(self):
        code = self.language.currentData()
        return resolve_language(QLocale.system().name()) if code == 'system' else code

    def text(self, key, **values):
        return tr(self.current_language(), key, **values)

    def change_language(self):
        self.settings.setValue('language', self.language.currentData())
        self.apply_language()

    def apply_language(self):
        for widget, key in ((self.subtitle, 'subtitle'),
                            (self.email_label, 'email'), (self.algorithm_label, 'algorithm'),
                            (self.folder, 'open_folder'),
                            (self.github, 'open_github'),
                            (self.tokens, 'open_tokens'),
                            (self.test_connection_button, 'test_connection'),
                            (self.result_label, 'result')):
            widget.setText(self.text(key))
        self.heading.setText('🔑' + self.text('title'))
        self.setWindowTitle('🔑' + self.text('title'))
        self.test_connection_button.setToolTip(self.text('test_connection_hint'))
        self.email.setPlaceholderText(self.text('email_placeholder'))
        self.language.setAccessibleName(self.text('language'))
        self.language.setToolTip(self.text('language'))
        self.theme.setAccessibleName(self.text('theme'))
        self.theme.setToolTip(self.text('theme'))
        self.algorithm.setItemText(self.algorithm.findData('ed25519'), self.text('algorithm_ed25519'))
        self.update_algorithm_description()
        self.language.setItemText(self.language.findData('system'), self.text('system'))
        for index in range(self.theme.count()):
            self.theme.setItemText(index, self.text(self.theme.itemData(index)))
        font = QApplication.font()
        if self.current_language() == 'bo':
            available = set(QFontDatabase.families())
            families = [name for name in ('Kailasa', 'Microsoft Himalaya', 'Noto Serif Tibetan', 'Noto Sans Tibetan') if name in available]
            if families:
                font.setFamilies(families + [QApplication.font().family()])
            else:
                self.language.setToolTip(self.text('font_missing'))
                if not any(event.key == 'font_missing' for event in self.events):
                    self.events.append(Event('font_missing'))
        else:
            self.language.setToolTip(self.text('language'))
        self.setFont(font)
        self.sync_minimum_height()
        self.render_events()
        self.public_panel.sync_appearance()
        self.sync_generate_action()
        self.sync_preference_icons()

    def sync_generate_action(self):
        key = 'regenerate' if self.has_existing_key else 'generate'
        self.generate.setText(self.text(key))
        name = 'danger' if self.has_existing_key else 'primary'
        if self.generate.objectName() != name:
            self.generate.setObjectName(name)
            self.generate.style().unpolish(self.generate)
            self.generate.style().polish(self.generate)
            self.generate.update()

    def confirm_regeneration(self):
        dialog = QMessageBox(self)
        dialog.setOption(QMessageBox.Option.DontUseNativeDialog, True)
        dialog.setFont(self.font())
        dialog.setWindowTitle(self.text('regenerate_title'))
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.setTextFormat(Qt.TextFormat.PlainText)
        # MacOS 会省略消息框的窗口标题，确认标题也必须出现在正文中。
        dialog.setText(self.text('regenerate_title'))
        details = self.text('regenerate_details', email=self.email.text().strip(),
                            algorithm=self.algorithm.currentText())
        dialog.setInformativeText(self.text('regenerate_prompt') + '\n\n' + details)
        confirm = dialog.addButton(self.text('regenerate'), QMessageBox.ButtonRole.AcceptRole)
        confirm.setObjectName('danger')
        confirm.style().unpolish(confirm)
        confirm.style().polish(confirm)
        cancel = dialog.addButton(self.text('cancel'), QMessageBox.ButtonRole.RejectRole)
        dialog.setDefaultButton(cancel)
        dialog.setEscapeButton(cancel)
        dialog.exec()
        accepted = dialog.clickedButton() is confirm
        dialog.deleteLater()
        return accepted

    def sync_preference_icons(self):
        color = self.palette().color(QPalette.ColorRole.PlaceholderText).name()
        self.language.setIcon(preference_icon('translate', color))
        mode = self.theme.currentData()
        icon_name = {'light': 'light_mode', 'dark': 'dark_mode', 'system': 'computer'}[mode]
        self.theme.setIcon(preference_icon(icon_name, color))
        for button, name in ((self.copy_button, 'content_copy'), (self.folder, 'folder_open'),
                             (self.github, 'open_in_new'), (self.tokens, 'open_in_new'),
                             (self.test_connection_button, 'network_check')):
            button.setIcon(preference_icon(name, color))

    def update_algorithm_description(self):
        key = 'algorithm_ed25519_description' if self.algorithm.currentData() == 'ed25519' else 'algorithm_rsa_description'
        self.algorithm_description.setText(self.text(key))
        self.sync_minimum_height()

    def sync_minimum_height(self):
        layout = self.layout()
        if layout is None or self._updating_layout:
            return
        self._updating_layout = True
        try:
            layout.invalidate()
            layout.activate()
            required_width = max(760, layout.minimumSize().width())
            if self.minimumWidth() != required_width:
                self.setMinimumWidth(required_width)
                layout.activate()
            # 按实际字体和字段宽度测量，避免 QLabel 的换行缓存保留旧语言的多行高度。
            description = self.algorithm_description
            text_rect = description.fontMetrics().boundingRect(
                QRect(0, 0, max(1, description.contentsRect().width()), 100000),
                int(Qt.TextFlag.TextWordWrap), description.text())
            required_height = max(description.fontMetrics().lineSpacing(),
                                  text_rect.height())
            if description.minimumHeight() != required_height or description.maximumHeight() != required_height:
                description.setFixedHeight(required_height)
            combo_height = max(40, self.algorithm.sizeHint().height())
            self.algorithm.setFixedHeight(combo_height)
            self.algorithm_field.setFixedHeight(combo_height + 6 + required_height)
            layout.activate()
            required = layout.totalHeightForWidth(self.width())
            # Splitter 忽略偏大的 preferred size，但仍必须计入两块内容区的真实最小高度。
            required += self.terminal_splitter.minimumHeight()
            if required > 0 and self.minimumHeight() != max(610, required):
                self.setMinimumHeight(max(610, required))
        finally:
            self._updating_layout = False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.sync_minimum_height()

    def render_events(self):
        scrollbar = self.output.verticalScrollBar()
        previous = scrollbar.value()
        at_bottom = previous >= scrollbar.maximum() - 1
        self.output.setPlainText('\n'.join(self.text(event.key, **event.values) for event in self.events))
        scrollbar.setValue(scrollbar.maximum() if at_bottom else min(previous, scrollbar.maximum()))

    def receive(self, event):
        self.events.append(event)
        self.render_events()

    def system_language_changed(self):
        locale_name = QLocale.system().name()
        if locale_name != self.system_locale:
            self.system_locale = locale_name
            if self.language.currentData() == 'system':
                self.apply_language()

    def change_theme(self):
        self.settings.setValue('theme', self.theme.currentData())
        self.apply_theme()

    def system_theme_changed(self, scheme):
        if self.theme.currentData() == 'system':
            self.apply_theme(scheme)

    def apply_theme(self, system_scheme=None):
        app = QApplication.instance()
        mode = self.theme.currentData()
        scheme = system_scheme if system_scheme is not None else app.styleHints().colorScheme()
        dark = mode == 'dark' or (mode == 'system' and scheme == Qt.ColorScheme.Dark)
        colors = {'background': '#171b24' if dark else '#f3f5f9',
                  'surface': '#242a36' if dark else '#ffffff',
                  'text': '#edf1f7' if dark else '#202c3d',
                  'muted': '#a7b3c7' if dark else '#52647d',
                  'border': '#3a4559' if dark else '#cbd4e1',
                  'disabled': '#768298' if dark else '#7a8494',
                  'terminal_background': '#000000' if dark else '#ffffff',
                  'terminal_text': '#00ff00' if dark else '#202c3d',
                  'terminal_placeholder': '#00bb00' if dark else '#64748b'}
        palette = QPalette()
        roles = QPalette.ColorRole
        for role, value in ((roles.Window, colors['background']), (roles.WindowText, colors['text']),
                            (roles.Base, colors['surface']), (roles.AlternateBase, colors['background']),
                            (roles.Text, colors['text']), (roles.Button, colors['surface']),
                            (roles.ButtonText, colors['text']), (roles.PlaceholderText, colors['muted']),
                            (roles.ToolTipBase, colors['surface']), (roles.ToolTipText, colors['text']),
                            (roles.Highlight, '#2769d7'), (roles.HighlightedText, '#ffffff')):
            palette.setColor(role, QColor(value))
        for role in (roles.Text, roles.WindowText, roles.ButtonText):
            palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(colors['disabled']))
        app.setPalette(palette)
        self.setStyleSheet('''
            QWidget { background: %(background)s; color: %(text)s; font-size: 14px; }
            QLabel#heading { font-size: 25px; font-weight: 650; }
            QLabel#subtitle { color: %(muted)s; }
            QLineEdit, QComboBox, QPlainTextEdit { background: %(surface)s; border: 1px solid %(border)s; border-radius: 7px; padding: 7px; selection-background-color: #2769d7; selection-color: white; }
            QPlainTextEdit#terminal { background-color: %(terminal_background)s; color: %(terminal_text)s; selection-background-color: #245e9d; selection-color: #ffffff; }
            QLabel#publicStatus { color: %(muted)s; font-size: 12px; }
            QLineEdit#defaultEmail { color: %(muted)s; }
            QLineEdit#defaultEmail:disabled { color: %(disabled)s; }
            QComboBox QAbstractItemView { background: %(surface)s; color: %(text)s; selection-background-color: #2769d7; selection-color: white; }
            QPushButton#preference { font-size: 12px; font-weight: 400; padding: 3px 6px; color: %(muted)s; }
            QMenu { background: %(surface)s; color: %(text)s; border: 1px solid %(border)s; padding: 4px; }
            QMenu::item { padding: 6px 20px; }
            QMenu::item:selected { background: #2769d7; color: #ffffff; }
            QPushButton { background: %(surface)s; border: 1px solid %(border)s; border-radius: 8px; padding: 8px 16px; font-weight: 600; }
            QPushButton:hover { border-color: #4384ee; }
            QPushButton#primary { background: #2168d5; color: white; border-color: #2168d5; }
            QPushButton#primary:hover { background: #1855b5; }
            QPushButton#primary:disabled { background: %(surface)s; color: %(disabled)s; border-color: %(border)s; }
            QPushButton#danger { background: #c91f3b; color: #ffffff; border-color: #c91f3b; }
            QPushButton#danger:hover { background: #af1932; border-color: #af1932; }
            QPushButton#danger:pressed { background: #95152a; border-color: #95152a; }
            QPushButton#danger:disabled { background: %(surface)s; color: %(disabled)s; border-color: %(border)s; }
            QPushButton:disabled, QLineEdit:disabled, QComboBox:disabled { color: %(disabled)s; }
            QProgressBar { background: %(surface)s; border: none; }
            QProgressBar::chunk { background: #4384ee; }
            QScrollBar { background: %(background)s; }
            QScrollBar::handle { background: %(border)s; border-radius: 4px; min-height: 24px; min-width: 24px; }
            QScrollBar::add-line, QScrollBar::sub-line { border: none; background: %(background)s; }
            QToolTip { background: %(surface)s; color: %(text)s; border: 1px solid %(border)s; }
        ''' % colors)
        for terminal in (self.output, self.public_panel.content):
            terminal_palette = QPalette(app.palette())
            terminal_palette.setColor(QPalette.ColorRole.Base, QColor(colors['terminal_background']))
            terminal_palette.setColor(QPalette.ColorRole.Text, QColor(colors['terminal_text']))
            terminal_palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(colors['terminal_placeholder']))
            terminal_palette.setColor(QPalette.ColorRole.Highlight, QColor('#245e9d'))
            terminal_palette.setColor(QPalette.ColorRole.HighlightedText, QColor('#ffffff'))
            terminal.setPalette(terminal_palette)
        self.update_email_style()
        self.sync_preference_icons()
        self.sync_minimum_height()
        self.public_panel.sync_appearance()

    def update_email_style(self):
        self.email.setObjectName('defaultEmail' if self.email.text() == default_email() else 'email')
        self.email.style().unpolish(self.email)
        self.email.style().polish(self.email)
        self.email.update()

    def start(self):
        if self.worker is not None:
            return
        address = self.email.text().strip()
        if not EMAIL.fullmatch(address):
            self.receive(Event('invalid_email'))
            return
        if self.has_existing_key and not self.confirm_regeneration():
            return
        self.last_result = None
        self.test_connection_button.setEnabled(False)
        self.public_panel.clear_public_key('busy')
        self.settings.setValue('email', address)
        self.settings.setValue('algorithm', self.algorithm.currentData())
        self.events = [Event('busy')]
        self.render_events()
        for widget in (self.email, self.algorithm, *self.buttons):
            widget.setEnabled(False)
        self.progress.show()
        self.worker = self.worker_factory(address, self.algorithm.currentData(), self)
        self.launch_worker()

    def start_connection_test(self):
        if self.worker is not None or self.last_result is None:
            return
        for widget in (self.email, self.algorithm, *self.buttons, self.test_connection_button):
            if widget is not self.copy_button:
                widget.setEnabled(False)
        self.progress.show()
        self.worker = self.test_worker_factory(self.last_result, self)
        self.launch_worker()

    def launch_worker(self):
        self.worker.event.connect(self.receive)
        self.worker.completed.connect(self.capture_result)
        self.worker.finished.connect(self.finished)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def capture_result(self, result):
        self.pending_result = result

    def finished(self):
        result = self.pending_result
        self.pending_result = None
        for widget in (self.email, self.algorithm, *self.buttons):
            widget.setEnabled(True)
        self.progress.hide()
        self.worker = None
        self.last_result = result
        if result:
            try:
                self.public_panel.set_public_key(result)
                self.has_existing_key = True
                self.settings.setValue('last_key_name', result.key.name)
            except SetupError as error:
                self.last_result = None
                self.public_panel.clear_public_key()
                self.receive(error.event)
        else:
            self.public_panel.clear_public_key()
        self.test_connection_button.setEnabled(self.last_result is not None)
        self.sync_generate_action()

    def open_folder(self):
        try:
            folder = Path.home() / '.ssh'
            folder.mkdir(mode=0o700, exist_ok=True)
            if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder))):
                self.receive(Event('open_failed', {'detail': str(folder)}))
        except OSError as error:
            self.receive(Event('open_failed', {'detail': str(error)}))

    def open_github(self):
        address = 'https://github.com/settings/ssh/new'
        if not QDesktopServices.openUrl(QUrl(address)):
            self.receive(Event('open_failed', {'detail': address}))

    def open_tokens(self):
        address = 'https://github.com/settings/tokens'
        if not QDesktopServices.openUrl(QUrl(address)):
            self.receive(Event('open_failed', {'detail': address}))

    def closeEvent(self, event):
        if self.worker is not None:
            self.receive(Event('busy_close'))
            event.ignore()
            return
        self.settings.sync()
        super().closeEvent(event)


def main(argv=None):
    app = QApplication(sys.argv if argv is None else argv)
    app.setStyle('Fusion')
    app.setOrganizationName('Jobs')
    app.setApplicationName('SSHKeyMgr')
    app.setApplicationDisplayName('Jobs SSH Key Mgr')
    window = Window()
    window.show()
    return app.exec()
