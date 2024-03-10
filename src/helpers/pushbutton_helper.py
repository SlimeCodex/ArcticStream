# Desc: ToggleButton class for toggling between two states
# This file is part of ArcticStream Library.

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtSvg import QSvgRenderer


class ToggleButton(QPushButton):
    def __init__(
        self,
        parent=None,
        icons=None,
        size=None,
        style=None,
        callback=None,
        toggled=False,
    ):
        super().__init__(parent)
        self.icons = icons
        self.toggled = toggled
        self.callback = callback
        self.size = size
        self.rendered_icons = [None, None]

        if size is not None:
            self.setFixedSize(*self.size)
        self.setupButton()

        if style:
            self.setStyleSheet(style)

        self.clicked.connect(self.toggleState)

    def setupButton(self):
        icon_id = 1 if self.toggled else 0
        icon = (
            self.rendered_icons[icon_id]
            if self.rendered_icons[icon_id]
            else QIcon(self.icons[icon_id])
        )
        self.setIcon(icon)

    def toggleState(self):
        self.toggled = not self.toggled
        self.setupButton()
        if self.callback:
            self.callback(self.toggled)

    def manual_toggle(self):
        self.toggled = not self.toggled
        self.setupButton()

    def renderSvgWithColor(self, icon_id, svg_path, color):
        try:
            svg_renderer = QSvgRenderer(svg_path)
            pixmap = QPixmap(svg_renderer.defaultSize())
            pixmap.fill(Qt.transparent)

            painter = QPainter(pixmap)
            svg_renderer.render(painter)

            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.fillRect(pixmap.rect(), QColor(color))

            painter.end()
            self.rendered_icons[icon_id] = QIcon(pixmap)
        except Exception as e:
            print(f"Error rendering SVG: {e}")

    def changeIconColor(self, color):
        self.renderSvgWithColor(0, self.icons[0], color)
        self.renderSvgWithColor(1, self.icons[1], color)
        self.setupButton()


class SimpleButton(QPushButton):
    def __init__(self, parent=None, icon=None, size=None, style=None, callback=None):
        super().__init__(parent)
        self.iconPath = icon
        self.callback = callback
        self.renderedIcon = None  # Store the rendered icon

        # Set button icon
        self.updateIcon()

        # Set button size
        if size is not None:
            self.setFixedSize(*size)

        # Apply custom style if provided
        if style:
            self.setStyleSheet(style)

        # Connect the button signal
        self.clicked.connect(self.onButtonPress)

    def updateIcon(self):
        """
        Update the button icon.
        """
        icon = self.renderedIcon if self.renderedIcon else QIcon(self.iconPath)
        self.setIcon(icon)

    def onButtonPress(self):
        """
        Handle the button press event.
        """
        if self.callback:
            self.callback()

    def renderSvgWithColor(self, svg_path, color):
        """
        Render SVG with the specified color.

        :param svg_path: Path to the SVG file.
        :param color: Color in which to render the SVG (e.g., '#ff0000').
        """
        try:
            svg_renderer = QSvgRenderer(svg_path)
            pixmap = QPixmap(svg_renderer.defaultSize())
            pixmap.fill(Qt.transparent)

            painter = QPainter(pixmap)
            svg_renderer.render(painter)

            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.fillRect(pixmap.rect(), QColor(color))

            painter.end()
            self.renderedIcon = QIcon(pixmap)
            self.updateIcon()
        except Exception as e:
            print(f"Error rendering SVG: {e}")

    def changeIconColor(self, color):
        """
        Change the icon color.

        :param color: New color in hexadecimal format (e.g., '#ff0000').
        """
        self.renderSvgWithColor(self.iconPath, color)
