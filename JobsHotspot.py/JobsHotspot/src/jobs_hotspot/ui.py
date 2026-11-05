"""Local hotspot dashboard and tray lifecycle. Created by Jobs."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QEvent, QLocale, QRectF, QSettings, QSize, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPalette, QPen
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QMenu, QMessageBox, QPlainTextEdit, QPushButton, QScrollArea,
    QSystemTrayIcon, QToolButton, QVBoxLayout, QWidget)

from .controls import PreferenceButton, preference_icon
from .core import RateTracker, format_bytes, valid_credentials
from .i18n import LANGUAGES, issue_key, tr
from .models import ActionResult, Issue, Snapshot

ASSETS = Path(__file__).resolve().parent / 'assets'


class Worker(QThread):
    completed = Signal(object, object)

    def __init__(self, backend, operation, upstream, ssid='', password='', parent=None):
        super().__init__(parent)
        self.backend, self.operation, self.upstream = backend, operation, upstream
        self.ssid, self.password = ssid, password

    def run(self):
        result = None
        try:
            if self.operation == 'start':
                result = self.backend.start(self.upstream, self.ssid, self.password)
            elif self.operation == 'stop':
                result = self.backend.stop()
            elif self.operation == 'permissions':
                self.backend.open_permissions()
            elif self.operation == 'settings':
                self.backend.open_settings()
            snapshot = self.backend.snapshot(self.upstream)
        except Exception as error:
            # Discard stale capabilities after every failed observation.
            snapshot = Snapshot(sys.platform, issues=[Issue('probe_failed', str(error))])
            result = ActionResult(False, 'probe_failed', str(error))
        finally:
            self.password = ''
        self.completed.emit(snapshot, result)


class ShareButton(QAbstractButton):
    """A picture-only circular control with an accessible action name."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.active = False
        self.dark = False
        self.setFixedSize(176, 176)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def hitButton(self, point):
        return (point.x() - 88) ** 2 + (point.y() - 88) ** 2 <= 78 ** 2

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        enabled = self.isEnabled()
        color = '#1ac99a' if self.active else '#5977f5'
        if not enabled:
            color = '#667386' if self.dark else '#b1bbc9'
        painter.setPen(Qt.PenStyle.NoPen)
        halo = QColor(color)
        halo.setAlpha(24)
        painter.setBrush(halo)
        painter.drawEllipse(QRectF(0, 0, 176, 176))
        painter.setBrush(QColor(color))
        painter.drawEllipse(QRectF(10, 10, 156, 156))
        painter.setPen(QPen(QColor('#ffffff'), 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QRectF(19, 19, 138, 138))
        symbol = 'wifi' if self.active else ('power_settings_new' if enabled else 'portable_wifi_off')
        icon = preference_icon(symbol, '#ffffff')
        icon.paint(painter, 53, 51, 70, 70)
        if self.hasFocus():
            painter.setPen(QPen(QColor('#e6b550'), 3))
            painter.drawEllipse(QRectF(4, 4, 168, 168))
        painter.end()


class TrafficCard(QFrame):
    def __init__(self, role, parent=None):
        super().__init__(parent)
        self.role = role
        self.setObjectName('card')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        top = QHBoxLayout()
        self.symbol = QLabel()
        self.symbol.setFixedSize(38, 38)
        self.heading = QLabel()
        self.heading.setObjectName('eyebrow')
        top.addWidget(self.symbol)
        top.addWidget(self.heading, 1)
        layout.addLayout(top)
        self.name = QLabel()
        self.name.setWordWrap(True)
        self.name.setObjectName('adapterName')
        layout.addWidget(self.name)
        self.address = QLabel('—')
        self.address.setObjectName('muted')
        layout.addWidget(self.address)
        self.speed = QLabel('—')
        self.speed.setObjectName('speed')
        layout.addWidget(self.speed)
        self.total = QLabel('—')
        self.total.setObjectName('muted')
        layout.addWidget(self.total)
        self.state = QLabel()
        layout.addWidget(self.state)
        layout.addStretch()

    def render(self, locale, dark, interface, rates):
        self.heading.setText(tr(locale, self.role))
        self.symbol.setPixmap(preference_icon('settings_ethernet' if self.role == 'input' else 'wifi',
            '#1ac99a' if self.role == 'input' else '#8d9fff').pixmap(36, 36))
        self.name.setText(interface.name if interface else tr(locale, 'no_input' if self.role == 'input' else 'no_wifi'))
        self.address.setText(interface.ipv4 if interface and interface.ipv4 else '—')
        direction = 0 if self.role == 'input' else 1
        value = rates.get(interface.id, (None, None))[direction] if interface else None
        self.speed.setText(format_bytes(value, rate=True))
        total = (interface.received if direction == 0 else interface.sent) if interface else None
        self.total.setText(('↓ ' if direction == 0 else '↑ ') + format_bytes(total))
        self.state.setText(('●  ' + tr(locale, 'connected')) if interface and interface.up
            else ('○  ' + tr(locale, 'disconnected')))


class MainWindow(QWidget):
    def __init__(self, backend, *, demo=False, smoke=False, settings=None):
        super().__init__()
        self.backend, self.demo, self.smoke = backend, demo, smoke
        self.settings = settings or QSettings('Jobs', 'JobsHotspot')
        available = dict(LANGUAGES)
        language = str(self.settings.value('language', QLocale.system().name()))
        if language not in available:
            language = next((key for key in available if key == language.split('_')[0]), 'en')
        self.locale = language
        self.theme = str(self.settings.value('theme', 'system'))
        if self.theme not in ('system', 'light', 'dark'):
            self.theme = 'system'
        self.snapshot = Snapshot(sys.platform)
        self.tracker = RateTracker()
        self.rates = {}
        self.worker = None
        self.busy = False
        self.observed = False
        self.quit_after_stop = False
        self.last_result = None
        self.failure_visible = False
        self.setWindowTitle('Jobs Hotspot')
        self.resize(1060, 810)
        self.setMinimumSize(820, 650)
        self.setWindowIcon(QIcon(str(ASSETS / 'icon.png')))
        self.build_ui()
        self.build_tray()
        self.language.setCurrentIndex(self.language.findData(self.locale))
        self.appearance.setCurrentIndex(self.appearance.findData(self.theme))
        self.language.currentIndexChanged.connect(self.language_changed)
        self.appearance.currentIndexChanged.connect(self.theme_changed)
        QApplication.instance().styleHints().colorSchemeChanged.connect(self.apply_theme)
        self.apply_theme()
        self.translate()
        self.timer = QTimer(self)
        self.timer.setInterval(3500)
        self.timer.timeout.connect(self.refresh)
        if not smoke:
            self.timer.start()
            QTimer.singleShot(0, self.refresh)

    def build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 26, 32, 20)
        layout.setSpacing(18)
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel('Jobs Hotspot')
        title.setObjectName('title')
        title_box.addWidget(title)
        self.subtitle = QLabel()
        self.subtitle.setWordWrap(True)
        self.subtitle.setObjectName('muted')
        title_box.addWidget(self.subtitle)
        header.addLayout(title_box, 1)
        self.language = PreferenceButton()
        self.language.setMinimumHeight(34)
        for locale, name in LANGUAGES:
            self.language.addItem(name, locale)
        self.appearance = PreferenceButton()
        self.appearance.setMinimumHeight(34)
        for mode in ('system', 'light', 'dark'):
            self.appearance.addItem(mode, mode)
        header.addWidget(self.language)
        header.addWidget(self.appearance)
        layout.addLayout(header)
        flow = QHBoxLayout()
        flow.setSpacing(18)
        self.input_card = TrafficCard('input')
        self.output_card = TrafficCard('output')
        flow.addWidget(self.input_card, 1)
        center = QVBoxLayout()
        center.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.toggle = ShareButton()
        self.toggle.clicked.connect(self.toggle_sharing)
        center.addWidget(self.toggle, alignment=Qt.AlignmentFlag.AlignCenter)
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setObjectName('status')
        center.addWidget(self.status)
        flow.addLayout(center)
        flow.addWidget(self.output_card, 1)
        layout.addLayout(flow)
        self.counter_note = QLabel()
        self.counter_note.setObjectName('muted')
        self.counter_note.setWordWrap(True)
        layout.addWidget(self.counter_note)
        self.input_choice = QComboBox()
        self.input_choice.setMinimumHeight(36)
        self.input_choice.currentIndexChanged.connect(self.input_changed)
        layout.addWidget(self.input_choice)
        self.mac_note = QLabel()
        self.mac_note.setWordWrap(True)
        layout.addWidget(self.mac_note)
        self.permissions_button = QPushButton()
        self.permissions_button.setMinimumHeight(36)
        self.permissions_button.clicked.connect(lambda: self.launch('permissions'))
        layout.addWidget(self.permissions_button)
        self.credentials = QWidget()
        row = QHBoxLayout(self.credentials)
        row.setContentsMargins(0, 0, 0, 0)
        self.ssid = QLineEdit(str(self.settings.value('ssid', 'Jobs Hotspot')))
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        for field in (self.ssid, self.password):
            field.setMinimumHeight(38)
            field.textChanged.connect(self.render_state)
            row.addWidget(field)
        layout.addWidget(self.credentials)
        self.alert = QFrame()
        self.alert.setObjectName('alert')
        alert_row = QHBoxLayout(self.alert)
        alert_row.setContentsMargins(18, 14, 18, 14)
        self.alert_icon = QLabel()
        alert_row.addWidget(self.alert_icon, alignment=Qt.AlignmentFlag.AlignTop)
        self.alert_text = QLabel()
        self.alert_text.setWordWrap(True)
        self.alert_text.setTextFormat(Qt.TextFormat.PlainText)
        alert_row.addWidget(self.alert_text, 1)
        layout.addWidget(self.alert)
        tools = QHBoxLayout()
        self.refresh_button = QPushButton()
        self.refresh_button.clicked.connect(self.refresh)
        self.settings_button = QPushButton()
        self.settings_button.clicked.connect(lambda: self.launch('settings'))
        self.hide_button = QPushButton()
        self.hide_button.clicked.connect(self.hide_to_tray)
        for button in (self.refresh_button, self.settings_button, self.hide_button):
            button.setMinimumHeight(38)
            tools.addWidget(button)
        layout.addLayout(tools)
        self.detail_button = QToolButton()
        self.detail_button.setCheckable(True)
        self.detail_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.detail_button.setArrowType(Qt.ArrowType.RightArrow)
        layout.addWidget(self.detail_button)
        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        self.details.setMaximumHeight(130)
        self.details.hide()
        self.detail_button.toggled.connect(self.show_details)
        layout.addWidget(self.details)
        layout.addStretch()
        self.footer = QLabel()
        self.footer.setWordWrap(True)
        self.footer.setObjectName('muted')
        layout.addWidget(self.footer)
        scroll.setWidget(content)
        outer.addWidget(scroll)

    def build_tray(self):
        self.tray = QSystemTrayIcon(self.windowIcon(), self)
        self.tray_menu = QMenu(self)
        self.show_action = self.tray_menu.addAction('')
        self.show_action.triggered.connect(self.show_window)
        self.stop_action = self.tray_menu.addAction('')
        self.stop_action.triggered.connect(lambda: self.launch('stop'))
        self.tray_menu.addSeparator()
        self.quit_action = self.tray_menu.addAction('')
        self.quit_action.triggered.connect(self.request_quit)
        self.tray.setContextMenu(self.tray_menu)
        self.tray.activated.connect(self.tray_activated)
        self.tray_available = not self.smoke and QSystemTrayIcon.isSystemTrayAvailable()
        if self.tray_available:
            self.tray.show()
        self.hide_button.setEnabled(self.tray_available)

    def tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.show_window()

    def show_window(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def show_details(self, checked):
        self.details.setVisible(checked)
        self.detail_button.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow)

    def translate(self):
        font = QFont('Noto Serif Tibetan') if self.locale == 'bo' else QApplication.instance().font()
        self.setFont(font)
        for widget, key in ((self.subtitle,'subtitle'), (self.counter_note,'counter_note'),
            (self.mac_note,'mac_setup'), (self.permissions_button,'permissions'), (self.refresh_button,'refresh'),
            (self.settings_button,'settings'), (self.hide_button,'hide'),
            (self.detail_button,'details'), (self.show_action,'show'),
            (self.stop_action,'stop'), (self.quit_action,'quit')):
            widget.setText(tr(self.locale, key))
        self.language.setAccessibleName(tr(self.locale, 'language'))
        for index, mode in enumerate(('system','light','dark')):
            self.appearance.setItemText(index, tr(self.locale, mode))
        self.ssid.setPlaceholderText(tr(self.locale, 'ssid'))
        self.ssid.setAccessibleName(tr(self.locale, 'ssid'))
        self.password.setPlaceholderText(tr(self.locale, 'password'))
        self.password.setAccessibleName(tr(self.locale, 'password'))
        self.input_choice.setAccessibleName(tr(self.locale, 'input'))
        self.footer.setText(tr(self.locale, 'demo' if self.demo else 'local'))
        if self.input_choice.count() == 1 and not self.input_choice.itemData(0):
            self.input_choice.setItemText(0, tr(self.locale, 'no_input'))
        self.render_state()

    def language_changed(self, index):
        self.locale = self.language.currentData()
        self.settings.setValue('language', self.locale)
        self.translate()

    def theme_changed(self, index):
        self.theme = self.appearance.currentData()
        self.settings.setValue('theme', self.theme)
        self.apply_theme()

    def apply_theme(self, *args):
        dark = self.theme == 'dark' or (self.theme == 'system' and
            QApplication.instance().styleHints().colorScheme() == Qt.ColorScheme.Dark)
        self.dark = dark
        bg, card, fg, muted, border = (('#101722','#182232','#edf3ff','#9baec7','#2d3a50') if dark
            else ('#f3f6fb','#ffffff','#1c2b43','#60708a','#dce3ed'))
        palette = QPalette()
        for role, value in ((QPalette.ColorRole.Window,bg),(QPalette.ColorRole.WindowText,fg),
            (QPalette.ColorRole.Base,card),(QPalette.ColorRole.AlternateBase,bg),
            (QPalette.ColorRole.Text,fg),(QPalette.ColorRole.Button,card),
            (QPalette.ColorRole.ButtonText,fg),(QPalette.ColorRole.ToolTipBase,card),
            (QPalette.ColorRole.ToolTipText,fg),(QPalette.ColorRole.Highlight,'#5977f5'),
            (QPalette.ColorRole.HighlightedText,'#ffffff'),(QPalette.ColorRole.PlaceholderText,muted)):
            palette.setColor(role, QColor(value))
            palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(muted if role in (
                QPalette.ColorRole.Text,QPalette.ColorRole.ButtonText,QPalette.ColorRole.WindowText) else value))
        QApplication.instance().setPalette(palette)
        QApplication.instance().setStyleSheet(f'''
            QWidget {{ color:{fg}; font-size:14px; }}
            QWidget#card {{ background:{card}; border:1px solid {border}; border-radius:18px; }}
            QScrollArea, QScrollArea > QWidget > QWidget {{ background:{bg}; }}
            QLabel {{ background:transparent; }}
            QLabel#title {{ font-size:29px; font-weight:700; }}
            QLabel#muted {{ color:{muted}; font-size:12px; }}
            QLabel#eyebrow {{ color:{muted}; font-size:13px; font-weight:600; }}
            QLabel#adapterName {{ font-size:17px; font-weight:600; }}
            QLabel#speed {{ font-size:30px; font-weight:650; padding-top:12px; }}
            QLabel#status {{ font-size:17px; font-weight:600; padding:8px; }}
            QFrame#alert {{ background:{'#2e2830' if dark else '#fff3e6'}; border:1px solid {'#604633' if dark else '#efd6ba'}; border-radius:12px; }}
            QPushButton, QComboBox, QLineEdit {{ background:{card}; border:1px solid {border}; border-radius:8px; padding:7px 12px; }}
            QPushButton:hover {{ border-color:#5977f5; }}
            QPushButton:disabled, QLineEdit:disabled, QComboBox:disabled {{ color:{muted}; background:{bg}; }}
            QLineEdit:focus, QComboBox:focus {{ border-color:#5977f5; }}
            QMenu, QComboBox QAbstractItemView {{ background:{card}; color:{fg}; border:1px solid {border}; padding:6px; }}
            QMenu::item {{ padding:8px 24px; }} QMenu::item:selected {{ background:#5977f5; color:white; border-radius:5px; }}
            QPlainTextEdit {{ background:{card}; color:{fg}; border:1px solid {border}; border-radius:8px; padding:8px; }}
            QToolButton {{ border:0; background:transparent; padding:4px; color:{muted}; }}
            QScrollBar:vertical {{ background:{bg}; width:10px; }}
            QScrollBar::handle:vertical {{ background:{border}; border-radius:5px; min-height:30px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
        ''')
        self.toggle.dark = dark
        self.language.setIcon(preference_icon('translate', fg))
        self.appearance.setIcon(preference_icon({'system':'computer','light':'light_mode','dark':'dark_mode'}[self.theme], fg))
        self.refresh_button.setIcon(preference_icon('refresh', fg))
        self.alert_icon.setPixmap(preference_icon('error_outline', '#d69647' if dark else '#a76519').pixmap(32,32))
        self.render_state()

    def render_state(self, *args):
        snapshot = self.snapshot
        active = snapshot.state == 'on'
        windows = snapshot.platform in ('win32','Windows','windows')
        self.credentials.setVisible(windows)
        self.mac_note.setVisible(not windows)
        self.permissions_button.setVisible(not windows and any(item.code == 'mac_permission' for item in snapshot.issues))
        self.permissions_button.setEnabled(not self.busy)
        creds_ok = not windows or valid_credentials(self.ssid.text(), self.password.text())
        can_start = snapshot.can_start and not snapshot.issues and creds_ok
        self.toggle.setEnabled(not self.busy and (snapshot.can_stop if active else can_start))
        self.toggle.active = active
        action = tr(self.locale, 'stop' if active else 'start')
        self.toggle.setAccessibleName(action)
        self.toggle.setToolTip(action if self.toggle.isEnabled() else tr(self.locale, 'blocked'))
        self.toggle.update()
        key = ('waiting' if self.busy else 'checking' if not self.observed else 'on' if active
            else 'ready' if can_start else 'unknown' if snapshot.state in ('unknown','transition') else 'blocked')
        self.status.setText(tr(self.locale, key))
        self.tray.setToolTip('Jobs Hotspot · ' + tr(self.locale, key))
        self.stop_action.setEnabled(active and snapshot.can_stop and not self.busy)
        for button in (self.refresh_button, self.settings_button):
            button.setEnabled(not self.busy)
        self.input_choice.setEnabled(not self.busy and not active)
        for field in (self.ssid,self.password):
            field.setEnabled(not self.busy and not active)
        self.input_card.render(self.locale, self.dark, snapshot.interface(snapshot.upstream_id), self.rates)
        self.output_card.render(self.locale, self.dark, snapshot.interface(snapshot.wifi_id), self.rates)
        messages = list(dict.fromkeys(tr(self.locale, issue_key(issue.code)) for issue in snapshot.issues))
        if windows and not active and not creds_ok:
            messages.append(tr(self.locale, 'credentials'))
        if self.failure_visible:
            messages.insert(0, tr(self.locale, 'error'))
        if not messages and not can_start and not active and self.observed:
            messages.append(tr(self.locale, 'unknown'))
        self.alert.setVisible(bool(messages))
        self.alert_text.setText('\n'.join(messages + [tr(self.locale, 'help')]) if messages else '')

    def input_changed(self, index):
        if not self.busy:
            self.refresh()

    def refresh(self):
        self.launch('snapshot')

    def toggle_sharing(self):
        if self.toggle.isEnabled():
            self.launch('stop' if self.snapshot.state == 'on' else 'start')

    def launch(self, operation):
        if self.busy or self.smoke:
            return
        if operation == 'start' and not self.toggle.isEnabled():
            return
        if operation == 'stop' and not (self.snapshot.state == 'on' and self.snapshot.can_stop):
            return
        self.busy = True
        upstream = self.input_choice.currentData() or ''
        self.worker = Worker(self.backend, operation, upstream, self.ssid.text(), self.password.text(), self)
        self.worker.completed.connect(self.received)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.finished.connect(self.worker_finished)
        self.render_state()
        self.worker.start()

    def received(self, snapshot, result):
        self.snapshot = snapshot
        self.observed = True
        self.rates = self.tracker.update(snapshot)
        if result is not None:
            self.last_result = result
            self.failure_visible = not result.ok
        elif not snapshot.issues:
            self.failure_visible = False
        self.input_choice.blockSignals(True)
        self.input_choice.clear()
        for interface in snapshot.interfaces:
            if interface.kind in ('ethernet','usb'):
                self.input_choice.addItem(interface.name + '  ·  ' + (interface.ipv4 or '—'), interface.id)
        if self.input_choice.count() == 0:
            self.input_choice.addItem(tr(self.locale, 'no_input'), '')
        self.input_choice.setCurrentIndex(max(0,self.input_choice.findData(snapshot.upstream_id)))
        self.input_choice.blockSignals(False)
        diagnostics = [snapshot.platform + ' · ' + snapshot.state, snapshot.detail]
        diagnostics += [f'{issue.code}: {issue.detail}' for issue in snapshot.issues]
        if self.last_result:
            diagnostics += [f'{self.last_result.code}: {self.last_result.detail}']
        self.details.setPlainText('\n'.join(item for item in diagnostics if item))
        if result is not None and not result.ok:
            self.detail_button.setChecked(True)
        self.render_state()

    def worker_finished(self):
        self.busy = False
        self.worker = None
        self.render_state()
        if self.quit_after_stop:
            self.quit_after_stop = False
            if self.last_result and self.last_result.ok and self.snapshot.state == 'off':
                self.finish_quit()

    def hide_to_tray(self):
        if self.tray_available:
            self.hide()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange and self.isMinimized() and self.tray_available:
            QTimer.singleShot(0, self.hide_to_tray)

    def closeEvent(self, event):
        event.ignore()
        if self.tray_available:
            self.hide_to_tray()
        else:
            self.request_quit()

    def request_quit(self):
        if self.busy:
            QMessageBox.information(self, 'Jobs Hotspot', tr(self.locale, 'waiting'))
            return
        if self.snapshot.state != 'off':
            box = QMessageBox(self)
            box.setWindowTitle('Jobs Hotspot')
            box.setText(tr(self.locale, 'quit_question') if self.snapshot.state == 'on' else tr(self.locale,'unknown'))
            stop = box.addButton(tr(self.locale,'stop_quit'), QMessageBox.ButtonRole.AcceptRole)
            stop.setEnabled(self.snapshot.state == 'on' and self.snapshot.can_stop)
            leave = box.addButton(tr(self.locale,'leave'), QMessageBox.ButtonRole.DestructiveRole)
            cancel = box.addButton(tr(self.locale,'cancel'), QMessageBox.ButtonRole.RejectRole)
            box.setDefaultButton(cancel)
            box.exec()
            if box.clickedButton() == stop:
                self.quit_after_stop = True
                self.launch('stop')
                return
            if box.clickedButton() != leave:
                return
        self.finish_quit()

    def finish_quit(self):
        self.timer.stop()
        self.settings.setValue('ssid', self.ssid.text())
        self.settings.sync()
        self.tray.hide()
        QApplication.instance().exit(0)
