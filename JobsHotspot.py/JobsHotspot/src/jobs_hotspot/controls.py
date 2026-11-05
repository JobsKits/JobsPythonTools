"""紧凑的图文设置按钮与本地图标。Created by Jobs on 2026年11月5日，星期四."""
from pathlib import Path
from xml.etree import ElementTree

from PySide6.QtCore import QByteArray, QPoint, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QAction, QActionGroup, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QMenu, QPushButton


def preference_icon(name, color):
    """从随包的 SVG 渲染多尺寸图标，颜色跟随当前主题。"""
    path = Path(__file__).resolve().parent / 'assets' / (name + '.svg')
    root = ElementTree.fromstring(path.read_bytes())
    root.set('fill', color)
    for element in root.iter():
        if element.get('fill') not in (None, 'none'):
            element.set('fill', color)
    renderer = QSvgRenderer(QByteArray(ElementTree.tostring(root)))
    if not renderer.isValid():
        raise RuntimeError(f'Invalid preference icon: {path.name}')
    icon = QIcon()
    for size in (16, 20, 24, 32, 48, 64):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter, QRectF(0, 0, size, size))
        painter.end()
        icon.addPixmap(pixmap)
    return icon


class PreferenceButton(QPushButton):
    """图标在左、文字在右，点击打开可键盘操作的选项菜单。"""
    currentIndexChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._options = []
        self._current_index = -1
        self.options_menu = QMenu(self)
        self._action_group = QActionGroup(self)
        self._action_group.setExclusive(True)
        self.setIconSize(QSize(16, 16))
        # 不将菜单设为 QPushButton 的附加菜单，避免平台自动绘制向下箭头。
        self.clicked.connect(self.show_options)

    def addItem(self, text, data):
        index = len(self._options)
        action = QAction(text, self)
        action.setCheckable(True)
        action.setData(data)
        action.triggered.connect(lambda checked=False, index=index: self.setCurrentIndex(index))
        self._action_group.addAction(action)
        self.options_menu.addAction(action)
        self._options.append((data, action))
        if self._current_index < 0:
            self.setCurrentIndex(0)

    def count(self):
        return len(self._options)

    def findData(self, data):
        return next((index for index, option in enumerate(self._options) if option[0] == data), -1)

    def itemData(self, index):
        return self._options[index][0]

    def currentIndex(self):
        return self._current_index

    def currentData(self):
        return self.itemData(self._current_index) if self._current_index >= 0 else None

    def currentText(self):
        return self._options[self._current_index][1].text() if self._current_index >= 0 else ''

    def setCurrentIndex(self, index):
        if not 0 <= index < self.count() or index == self._current_index:
            return
        self._current_index = index
        self._options[index][1].setChecked(True)
        self.setText(self.currentText())
        self.currentIndexChanged.emit(index)

    def setItemText(self, index, text):
        self._options[index][1].setText(text)
        if index == self._current_index:
            self.setText(text)

    def show_options(self):
        self.options_menu.setMinimumWidth(self.width())
        self.options_menu.popup(self.mapToGlobal(QPoint(0, self.height())))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Down:
            self.show_options()
            event.accept()
            return
        super().keyPressEvent(event)
