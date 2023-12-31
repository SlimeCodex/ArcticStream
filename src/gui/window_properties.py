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
from PyQt5.QtWidgets import QMainWindow, QLabel, QPushButton, QWidget, QHBoxLayout
from PyQt5.QtGui import QPainter, QPolygon, QColor

from helpers.pushbutton_helper import ToggleButton, SimpleButton
from resources.theme_config import *
import helpers.theme_helper as th

class SSCWindowProperties(QMainWindow):
	signal_window_close = pyqtSignal()
	
	def __init__(self, main_window):
		super().__init__()
		self.main_window = main_window
		self.main_window.themeChanged.connect(self.callback_update_theme)
		
		# Removes native title bar
		self.setWindowFlags(Qt.FramelessWindowHint)

		# Globals
		self.icons_dir = self.main_window.icon_path()
		self.mouse_pressed = False
		self.resize_direction = None
		self.start_position = None
		self.window_rect = None

	# GUI Functions ------------------------------------------------------------------------------------------

	# Set the custom title bar
	def set_custom_title(self, title):

		self.custom_bar_widget = QWidget(self)
		self.custom_bar_widget.setFixedHeight(CUSTOM_BAR_HEIGHT)
		self.custom_bar_widget.setStyleSheet(th.get_style("custom_bar_widget_style"))

		custom_bar_layout = QHBoxLayout()
		custom_bar_layout.setContentsMargins(0, 0, 0, 0)
		custom_bar_layout.setSpacing(0)

		# Simple logo button
		self.logo_button = SimpleButton(self,
			icon=f"{self.icons_dir}/chevron_right_FILL0_wght400_GRAD0_opsz24.svg",
			size=(CUSTOM_BAR_HEIGHT, CUSTOM_BAR_HEIGHT),
			style=th.get_style("custom_bar_button_style"),
			callback=self.toggle_debug
		)

		# Title label
		self.title_label = QLabel(title)
		self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

		# Toggle color mode button
		self.color_mode_button = ToggleButton(self,
			icons=(f"{self.icons_dir}/dark_mode_FILL0_wght400_GRAD0_opsz24.svg", f"{self.icons_dir}/light_mode_FILL0_wght400_GRAD0_opsz24.svg"),
			size=(CUSTOM_BAR_HEIGHT, CUSTOM_BAR_HEIGHT),
			style=th.get_style("custom_bar_button_style"),
			callback=self.toggle_theme,
			toggled=False
		)

		# Toggle hint button
		self.top_hint_button = ToggleButton(self,
			icons=(f"{self.icons_dir}/move_down_FILL0_wght400_GRAD0_opsz24.svg", f"{self.icons_dir}/move_up_FILL0_wght400_GRAD0_opsz24.svg"),
			size=(CUSTOM_BAR_HEIGHT, CUSTOM_BAR_HEIGHT),
			style=th.get_style("custom_bar_button_style"),
			callback=self.toggle_hint,
			toggled=False
		)

		# Status text with colored background
		self.con_status_button = TriangleButton()
		self.con_status_button.setTriangleColor("#333333")
		self.con_status_button.setFixedSize(150, CUSTOM_BAR_HEIGHT)

		# Simple minimize button
		self.minimize_button = SimpleButton(self,
			icon=f"{self.icons_dir}/minimize_FILL0_wght400_GRAD0_opsz24.svg",
			size=(CUSTOM_BAR_HEIGHT, CUSTOM_BAR_HEIGHT),
			style=th.get_style("custom_bar_button_style"),
			callback=self.toggle_minimize
		)

		# Toggle fullscreen button
		self.fullscreen_button = ToggleButton(self,
			icons=(f"{self.icons_dir}/expand_content_FILL0_wght400_GRAD0_opsz24.svg", f"{self.icons_dir}/collapse_content_FILL0_wght400_GRAD0_opsz24.svg"),
			size=(CUSTOM_BAR_HEIGHT, CUSTOM_BAR_HEIGHT),
			style=th.get_style("custom_bar_button_style"),
			callback=self.fullscreen,
			toggled=False
		)

		# Simple close button
		self.close_button = SimpleButton(self,
			icon=f"{self.icons_dir}/close_FILL0_wght400_GRAD0_opsz24.svg",
			size=(CUSTOM_BAR_HEIGHT, CUSTOM_BAR_HEIGHT),
			style=th.get_style("custom_bar_close_button_style"),
			callback=self.close_window
		)

		# Layout
		custom_bar_layout.addWidget(self.logo_button)
		custom_bar_layout.addWidget(self.title_label)
		custom_bar_layout.addWidget(self.color_mode_button)
		custom_bar_layout.addWidget(self.top_hint_button)
		custom_bar_layout.addWidget(self.con_status_button)
		custom_bar_layout.addWidget(self.minimize_button)
		custom_bar_layout.addWidget(self.fullscreen_button)
		custom_bar_layout.addWidget(self.close_button)
		
		self.custom_bar_widget.setLayout(custom_bar_layout)
		self.setMenuWidget(self.custom_bar_widget)

	# Window Functions ------------------------------------------------------------------------------------------

	def get_resize_direction(self, position):
		rect = self.rect()
		bottom_right_rect = QRect(rect.right() - RESIZE_CORNER_SIZE, rect.bottom() - RESIZE_CORNER_SIZE, RESIZE_CORNER_SIZE, RESIZE_CORNER_SIZE)
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
		if not self.isFullScreen(): # Resize not allowed in fullscreen
			if self.resize_direction == Qt.BottomRightCorner:
				newWidth = max(self.minimumWidth(), globalPos.x() - self.window_rect.left())
				newHeight = max(self.minimumHeight(), globalPos.y() - self.window_rect.top())
				self.resize(newWidth, newHeight)

	def move_window(self, globalPos):
		self.move(globalPos)

	# Compact the window to just show the title bar
	def toggle_minimize(self):
		self.showMinimized()
	
	def toggle_hint(self, status):
		if status:
			self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
			self.show()
		else:
			self.setWindowFlags(Qt.FramelessWindowHint)
			self.show()
		
	def fullscreen(self, status):
		if self.isFullScreen():
			self.showNormal()
		else:
			self.showFullScreen()

	def callback_update_theme(self, theme):
		
		# Reload stylesheets (background for SVG buttons)
		self.custom_bar_widget.setStyleSheet(th.get_style("custom_bar_widget_style"))
		self.logo_button.setStyleSheet(th.get_style("custom_bar_button_style"))
		self.title_label.setStyleSheet(th.get_style("custom_bar_button_style"))
		self.color_mode_button.setStyleSheet(th.get_style("custom_bar_button_style"))
		self.top_hint_button.setStyleSheet(th.get_style("custom_bar_button_style"))
		self.minimize_button.setStyleSheet(th.get_style("custom_bar_button_style"))
		self.fullscreen_button.setStyleSheet(th.get_style("custom_bar_button_style"))
		self.close_button.setStyleSheet(th.get_style("custom_bar_close_button_style"))

		# Update special widgets by theme
		if theme == "dark":
			self.logo_button.changeIconColor("#ffffff")
			self.color_mode_button.changeIconColor("#ffffff")
			self.top_hint_button.changeIconColor("#ffffff")
			self.minimize_button.changeIconColor("#ffffff")
			self.fullscreen_button.changeIconColor("#ffffff")
			self.close_button.changeIconColor("#ffffff")
			self.con_status_button.setTriangleColor("#333333") # Same as bar background
		elif theme == "light":
			self.logo_button.changeIconColor("#303030")
			self.color_mode_button.changeIconColor("#303030")
			self.top_hint_button.changeIconColor("#303030")
			self.minimize_button.changeIconColor("#303030")
			self.fullscreen_button.changeIconColor("#303030")
			self.close_button.changeIconColor("#303030")
			self.con_status_button.setTriangleColor("#e0e0e0") # Same as bar background
		
	# Qt event ------------------------------------------------------------------------------------------

	# Qt function
	def mousePressEvent(self, event):
		self.mouse_pressed = True
		self.start_position = event.globalPos()
		self.window_rect = self.geometry()

		rect = self.rect()
		bottom_right_rect = QRect(rect.right() - RESIZE_CORNER_SIZE, rect.bottom() - RESIZE_CORNER_SIZE, RESIZE_CORNER_SIZE, RESIZE_CORNER_SIZE)

		if bottom_right_rect.contains(event.pos()):
			self.resize_direction = Qt.BottomRightCorner
		elif event.pos().y() <= CUSTOM_BAR_HEIGHT:
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
				cursor_offset_y = CUSTOM_BAR_HEIGHT // 2

				newX = event.globalPos().x() - cursor_offset_x - self.width() // 2
				newY = event.globalPos().y() - cursor_offset_y * 2

				new_position = QPoint(newX, newY)
				self.move(new_position)

				self.start_position = event.globalPos() - QPoint(cursor_offset_x, cursor_offset_y)
				self.window_rect = self.geometry()

			elif self.resize_direction == Qt.BottomRightCorner:
				self.resize_window(event.globalPos())
			elif self.resize_direction == "custom_bar_widget":
				self.move_window(event.globalPos() - self.start_position + self.window_rect.topLeft())

		else:
			self.set_cursor_direction(self.get_resize_direction(event.pos()))

	# Qt function
	def paintEvent(self, event):
		if not self.isFullScreen(): # Paint not allowed in fullscreen
			painter = QPainter(self)
			orangeColor = QColor(255, 165, 0)
			painter.setBrush(orangeColor)
			triangle = QPolygon([
				QPoint(self.width() - RESIZE_CORNER_SIZE, self.height()),
				QPoint(self.width(), self.height()),
				QPoint(self.width(), self.height() - RESIZE_CORNER_SIZE)
			])
			painter.drawPolygon(triangle)

	# Qt function
	def mouseDoubleClickEvent(self, event):
		if event.pos().y() > CUSTOM_BAR_HEIGHT:
			return
		self.fullscreen_button.manual_toggle()
		self.fullscreen(True)
		event.accept()

	def close_window(self):
		self.signal_window_close.emit()
		self.close()

	def closeEvent(self, event):
		self.signal_window_close.emit()
		super().closeEvent(event)


# Little -maybe not the best- trick to adjust the shape of connect/disconnect label
class TriangleButton(QPushButton):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def setTriangleColor(self, color):
		self.triangle_color = QColor(color)
		self.update()  # Trigger a repaint

	def paintEvent(self, event):
		super().paintEvent(event)
		painter = QPainter(self)
		painter.setBrush(self.triangle_color) 
		painter.setPen(Qt.NoPen)  # Remove borders

		# Left Triangle
		left_triangle = QPolygon([
			QPoint(0, 0),
			QPoint(int(self.height()), int(self.height())),
			QPoint(0, self.height())
		])

		# Right Triangle
		right_triangle = QPolygon([
			QPoint(self.width(), 0),
			QPoint(self.width() - int(self.height()), int(self.height())),
			QPoint(self.width(), self.height())
		])

		painter.drawPolygon(left_triangle)
		painter.drawPolygon(right_triangle)