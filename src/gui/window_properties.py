#
# This file is part of ArcticStream Library.
# Copyright (C) 2023 Alejandro Nicolini
#
# ArcticStream is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ArcticStream is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ArcticStream. If not, see <https://www.gnu.org/licenses/>.
#

from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QLabel, QWidget, QHBoxLayout
from PyQt5.QtGui import QPainter, QPolygon, QColor

import resources.config as app_config
from helpers.pushbutton_helper import ToggleButton, SimpleButton
import helpers.theme_helper as th


class SSCWindowProperties(QMainWindow):
    windowClose = pyqtSignal()


    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.mw.themeChanged.connect(self.cb_update_theme)

        # Removes native title bar
        self.setWindowFlags(Qt.FramelessWindowHint)

        # Globals
        self.icons_dir = self.mw.icon_path()
        self.mouse_pressed = False
        self.resize_direction = None
        self.start_position = None
        self.window_rect = None

    # GUI Functions

    # Set the custom title bar
    def set_custom_title(self, title):
        self.custom_bar_widget = QWidget(self)
        self.custom_bar_widget.setFixedHeight(
            app_config.globals["gui"]["custom_bar_height"]
        )
        self.custom_bar_widget.setStyleSheet(th.get_style("custom_bar_widget"))

        custom_bar_layout = QHBoxLayout()
        custom_bar_layout.setContentsMargins(0, 0, 0, 0)
        custom_bar_layout.setSpacing(0)

        # Simple logo button
        self.logo_button = SimpleButton(
            self,
            icon=f"{self.icons_dir}/chevron_right_FILL0_wght400_GRAD0_opsz24.svg",
            size=app_config.globals["gui"]["custom_bar_button_size"],
            style=th.get_style("custom_bar_button"),
            callback=self.toggle_debug,
        )

        # Title label
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # Toggle color mode button
        self.color_mode_button = ToggleButton(
            self,
            icons=(
                f"{self.icons_dir}/dark_mode_FILL0_wght400_GRAD0_opsz24.svg",
                f"{self.icons_dir}/light_mode_FILL0_wght400_GRAD0_opsz24.svg",
            ),
            size=app_config.globals["gui"]["custom_bar_button_size"],
            style=th.get_style("custom_bar_button"),
            callback=self.toggle_theme,
            toggled=False,
        )

        # Toggle accumulator button
        self.accumulator_button = ToggleButton(
            self,
            icons=(
                f"{self.icons_dir}/variables_FILL0_wght400_GRAD0_opsz24.svg",
                f"{self.icons_dir}/variable_add_FILL0_wght400_GRAD0_opsz24.svg",
            ),
            size=app_config.globals["gui"]["custom_bar_button_size"],
            style=th.get_style("custom_bar_button"),
            callback=self.toggle_accumulator,
            toggled=False,
        )

        # Toggle hint button
        self.top_hint_button = ToggleButton(
            self,
            icons=(
                f"{self.icons_dir}/move_down_FILL0_wght400_GRAD0_opsz24.svg",
                f"{self.icons_dir}/move_up_FILL0_wght400_GRAD0_opsz24.svg",
            ),
            size=app_config.globals["gui"]["custom_bar_button_size"],
            style=th.get_style("custom_bar_button"),
            callback=self.toggle_hint,
            toggled=False,
        )

        # Autosync button
        self.autosync_button = ToggleButton(
            self,
            icons=(
                f"{self.icons_dir}/sync_disabled_FILL0_wght400_GRAD0_opsz24.svg",
                f"{self.icons_dir}/sync_FILL0_wght400_GRAD0_opsz24.svg",
            ),
            size=app_config.globals["gui"]["custom_bar_button_size"],
            style=th.get_style("custom_bar_button"),
            callback=self.toggle_autosync,
            toggled=True,
        )

        # Status text with colored background
        self.con_status_button = SimpleButton(
            self,
            icon=None,
            size=app_config.globals["gui"]["custom_bar_button_size"],
            style=th.get_style("custom_bar_button"),
            callback=None,
        )
        # Size adjustment for the connect/disconnect label
        self.con_status_button.setFixedSize(130, 20)

        # Simple minimize button
        self.minimize_button = SimpleButton(
            self,
            icon=f"{self.icons_dir}/minimize_FILL0_wght400_GRAD0_opsz24.svg",
            size=app_config.globals["gui"]["custom_bar_button_size"],
            style=th.get_style("custom_bar_button"),
            callback=self.toggle_minimize,
        )

        # Toggle fullscreen button
        self.fullscreen_button = ToggleButton(
            self,
            icons=(
                f"{self.icons_dir}/expand_content_FILL0_wght400_GRAD0_opsz24.svg",
                f"{self.icons_dir}/collapse_content_FILL0_wght400_GRAD0_opsz24.svg",
            ),
            size=app_config.globals["gui"]["custom_bar_button_size"],
            style=th.get_style("custom_bar_button"),
            callback=self.fullscreen,
            toggled=False,
        )

        # Simple close button
        self.close_button = SimpleButton(
            self,
            icon=f"{self.icons_dir}/close_FILL0_wght400_GRAD0_opsz24.svg",
            size=app_config.globals["gui"]["custom_bar_button_size"],
            style=th.get_style("custom_bar_close_button"),
            callback=self.close_window,
        )

        # Layout
        custom_bar_layout.addWidget(self.logo_button)
        custom_bar_layout.addWidget(self.title_label)
        custom_bar_layout.addWidget(self.color_mode_button)
        custom_bar_layout.addWidget(self.accumulator_button)
        custom_bar_layout.addWidget(self.top_hint_button)
        custom_bar_layout.addWidget(self.autosync_button)
        custom_bar_layout.addWidget(self.con_status_button)
        custom_bar_layout.addWidget(self.minimize_button)
        custom_bar_layout.addWidget(self.fullscreen_button)
        custom_bar_layout.addWidget(self.close_button)

        self.custom_bar_widget.setLayout(custom_bar_layout)
        self.setMenuWidget(self.custom_bar_widget)

    # Window Functions

    def get_resize_direction(self, position):
        rect = self.rect()
        bottom_right_rect = QRect(
            rect.right() - app_config.globals["gui"]["resize_corner_size"],
            rect.bottom() - app_config.globals["gui"]["resize_corner_size"],
            app_config.globals["gui"]["resize_corner_size"],
            app_config.globals["gui"]["resize_corner_size"],
        )
        if bottom_right_rect.contains(position):
            return Qt.BottomRightCorner
        return None

    def set_cursor_direction(self, direction):
        if direction == Qt.BottomRightCorner:
            self.setCursor(Qt.SizeFDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    # Resize and move the window
    def resize_window(self, globalPos):
        if not self.isFullScreen():  # Resize not allowed in fullscreen
            if self.resize_direction == Qt.BottomRightCorner:
                newWidth = max(
                    self.minimumWidth(), globalPos.x() - self.window_rect.left()
                )
                newHeight = max(
                    self.minimumHeight(), globalPos.y() - self.window_rect.top()
                )
                self.resize(newWidth, newHeight)

    def move_window(self, globalPos):
        self.move(globalPos)

    # Compact the window to just show the title bar
    def toggle_minimize(self):
        self.showMinimized()
    
    def toggle_accumulator(self, status):
        self.mw.accumulatorChanged.emit(status)

    def toggle_hint(self, status):
        if status:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(Qt.FramelessWindowHint)
        self.show()

    def fullscreen(self, status):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def cb_update_theme(self, theme):
        # Reload stylesheets (background for SVG buttons)
        self.custom_bar_widget.setStyleSheet(th.get_style("custom_bar_widget"))
        self.logo_button.setStyleSheet(th.get_style("custom_bar_button"))
        self.title_label.setStyleSheet(th.get_style("custom_bar_button"))
        self.color_mode_button.setStyleSheet(th.get_style("custom_bar_button"))
        self.accumulator_button.setStyleSheet(th.get_style("custom_bar_button"))
        self.top_hint_button.setStyleSheet(th.get_style("custom_bar_button"))
        self.autosync_button.setStyleSheet(th.get_style("custom_bar_button"))
        self.minimize_button.setStyleSheet(th.get_style("custom_bar_button"))
        self.fullscreen_button.setStyleSheet(th.get_style("custom_bar_button"))
        self.close_button.setStyleSheet(th.get_style("custom_bar_close_button"))

        # Update special widgets by theme
        if theme == "dark":
            self.logo_button.changeIconColor("#ffffff")
            self.color_mode_button.changeIconColor("#ffffff")
            self.accumulator_button.changeIconColor("#ffffff")
            self.top_hint_button.changeIconColor("#ffffff")
            self.autosync_button.changeIconColor("#ffffff")
            self.minimize_button.changeIconColor("#ffffff")
            self.fullscreen_button.changeIconColor("#ffffff")
            self.close_button.changeIconColor("#ffffff")
        elif theme == "light":
            self.logo_button.changeIconColor("#303030")
            self.color_mode_button.changeIconColor("#303030")
            self.accumulator_button.changeIconColor("#303030")
            self.top_hint_button.changeIconColor("#303030")
            self.autosync_button.changeIconColor("#303030")
            self.minimize_button.changeIconColor("#303030")
            self.fullscreen_button.changeIconColor("#303030")
            self.close_button.changeIconColor("#303030")

    # Qt event

    # Qt function
    def mousePressEvent(self, event):
        self.mouse_pressed = True
        self.start_position = event.globalPos()
        self.window_rect = self.geometry()

        rect = self.rect()
        bottom_right_rect = QRect(
            rect.right() - app_config.globals["gui"]["resize_corner_size"],
            rect.bottom() - app_config.globals["gui"]["resize_corner_size"],
            app_config.globals["gui"]["resize_corner_size"],
            app_config.globals["gui"]["resize_corner_size"],
        )

        if bottom_right_rect.contains(event.pos()):
            self.resize_direction = Qt.BottomRightCorner
        elif event.pos().y() <= app_config.globals["gui"]["custom_bar_height"]:
            self.resize_direction = "custom_bar_widget"
        else:
            self.resize_direction = None

    # Qt function
    def mouseReleaseEvent(self, event):
        self.mouse_pressed = False
        self.resize_direction = None

    # Qt function
    def mouseMoveEvent(self, event):
        if self.mouse_pressed and event.buttons() == Qt.LeftButton:
            if self.resize_direction == "custom_bar_widget" and self.isFullScreen():
                self.fullscreen_button.manual_toggle()
                self.fullscreen(True)

                cursor_offset_x = self.width() // 2
                cursor_offset_y = app_config.globals["gui"]["custom_bar_height"] // 2

                newX = event.globalPos().x() - cursor_offset_x - self.width() // 2
                newY = event.globalPos().y() - cursor_offset_y * 2

                new_position = QPoint(newX, newY)
                self.move(new_position)

                self.start_position = event.globalPos() - QPoint(
                    cursor_offset_x, cursor_offset_y
                )
                self.window_rect = self.geometry()

            elif self.resize_direction == Qt.BottomRightCorner:
                self.resize_window(event.globalPos())
            elif self.resize_direction == "custom_bar_widget":
                self.move_window(
                    event.globalPos() - self.start_position + self.window_rect.topLeft()
                )

        else:
            self.set_cursor_direction(self.get_resize_direction(event.pos()))

    # Qt function
    def paintEvent(self, event):
        if not self.isFullScreen():
            painter = QPainter(self)
            orangeColor = QColor(255, 165, 0)
            painter.setBrush(orangeColor)
            triangle = QPolygon(
                [
                    QPoint(
                        self.width() - app_config.globals["gui"]["resize_corner_size"],
                        self.height(),
                    ),
                    QPoint(self.width(), self.height()),
                    QPoint(
                        self.width(),
                        self.height() - app_config.globals["gui"]["resize_corner_size"],
                    ),
                ]
            )
            painter.drawPolygon(triangle)

    # Qt function
    def mouseDoubleClickEvent(self, event):
        if event.pos().y() > app_config.globals["gui"]["custom_bar_height"]:
            return
        self.fullscreen_button.manual_toggle()
        self.fullscreen(True)
        event.accept()

    def close_window(self):
        self.windowClose.emit()
        self.close()

    def closeEvent(self, event):
        self.windowClose.emit()
        super().closeEvent(event)
