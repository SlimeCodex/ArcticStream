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
from PyQt5.QtGui import QPainter, QPolygon, QColor, QIcon

from resources.styles import *

class SSCWindowProperties(QMainWindow):
	windowCloseEvent = pyqtSignal()
	
	def __init__(self, main_window):
		super().__init__()
		self.mainWindow = main_window
		
		# Set the window flags to allow resizing and moving
		self.setWindowFlags(Qt.FramelessWindowHint)
		self._mousePressed = False
		self._resizeDirection = None
		self._margin = 10  # Margin for the resize area
		self._startPosition = None
		self._windowRect = None
		self._storedSize = None
		self._storedMinSize = None
		self.isCompact = False
		self.toggleFrontStatus = False
		self.icons_dir = self.mainWindow.icon_path()
		self._windowBarHeight = 30

	# Mouse events for moving and resizing the window
	def mousePressEvent(self, event):
		self._mousePressed = True
		self._startPosition = event.globalPos()
		self._windowRect = self.geometry()
		self._resizeDirection = self.getResizeDirection(event.pos())

	def mouseMoveEvent(self, event):
		if self._mousePressed and event.buttons() == Qt.LeftButton:
			if self.isFullScreen():
				self.fullscreen()

				cursorOffsetX = self.width() // 2
				cursorOffsetY = self._windowBarHeight // 2

				newX = event.globalPos().x() - cursorOffsetX - self.width() // 2
				newY = event.globalPos().y() - cursorOffsetY * 2

				newPosition = QPoint(newX, newY)
				self.move(newPosition)

				self._startPosition = event.globalPos() - QPoint(cursorOffsetX, cursorOffsetY)
				self._windowRect = self.geometry()

			elif self._resizeDirection:
				self.resizeWindow(event.globalPos())
			else:
				self.moveWindow(event.globalPos() - self._startPosition + self._windowRect.topLeft())
		else:
			self.setCursorDirection(self.getResizeDirection(event.pos()))

	def mouseReleaseEvent(self, event):
		self._mousePressed = False
		self._resizeDirection = None

	def getResizeDirection(self, position):
		rect = self.rect()
		bottomRightRect = QRect(rect.right() - self._margin, rect.bottom() - self._margin, self._margin, self._margin)
		if bottomRightRect.contains(position):
			return Qt.BottomRightCorner
		return None

	def setCursorDirection(self, direction):
		if direction == Qt.BottomRightCorner:
			self.setCursor(Qt.SizeFDiagCursor)
		else:
			self.setCursor(Qt.ArrowCursor)

	# Resize and move the window
	def resizeWindow(self, globalPos):
		if self._resizeDirection == Qt.BottomRightCorner:
			newWidth = max(self.minimumWidth(), globalPos.x() - self._windowRect.left())
			newHeight = max(self.minimumHeight(), globalPos.y() - self._windowRect.top())
			self.resize(newWidth, newHeight)

	def moveWindow(self, globalPos):
		self.move(globalPos)

	# Paint the triangle in the bottom right corner
	def paintEvent(self, event):
		painter = QPainter(self)
		orangeColor = QColor(255, 165, 0)
		painter.setBrush(orangeColor)
		triangleSize = 10
		triangle = QPolygon([
			QPoint(self.width() - triangleSize, self.height()),
			QPoint(self.width(), self.height()),
			QPoint(self.width(), self.height() - triangleSize)
		])
		painter.drawPolygon(triangle)

	# Set the custom title bar
	def setCustomTitle(self, title):
		titleBar = QWidget(self)
		titleBar.setFixedHeight(self._windowBarHeight)
		titleBar.setStyleSheet("background-color: #333333;")

		# Toggle front button
		self.logoButton = QPushButton(self)
		self.logoButton.setStyleSheet(dark_theme_qpb_title)
		self.logoButton.setFixedSize(self._windowBarHeight, self._windowBarHeight)
		self.svgIcon = QIcon(f"{self.icons_dir}/chevron_right_FILL0_wght400_GRAD0_opsz24.svg")
		self.logoButton.setIcon(self.svgIcon)

		titleLayout = QHBoxLayout()
		titleLayout.setContentsMargins(0, 0, 0, 0)
		titleLayout.setSpacing(0)

		self.titleLabel = QLabel()
		self.titleLabel.setStyleSheet("font-size: 13px;")
		self.titleLabel.setText(title)
		self.titleLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

		# Toggle front button
		self.toggleFrontButton = QPushButton(self)
		self.toggleFrontButton.setStyleSheet(dark_theme_qpb_title)
		self.toggleFrontButton.setFixedSize(self._windowBarHeight, self._windowBarHeight)
		self.toggleFrontButton.clicked.connect(self.toggleFront)
		self.svgIcon = QIcon(f"{self.icons_dir}/move_down_FILL0_wght400_GRAD0_opsz24.svg")
		self.toggleFrontButton.setIcon(self.svgIcon)

		# Fullscreen button
		self.fullscreenButton = QPushButton(self)
		self.fullscreenButton.setStyleSheet(dark_theme_qpb_title)
		self.fullscreenButton.setFixedSize(self._windowBarHeight, self._windowBarHeight)
		self.fullscreenButton.clicked.connect(self.fullscreen)
		self.svgIcon = QIcon(f"{self.icons_dir}/expand_content_FILL0_wght400_GRAD0_opsz24.svg")
		self.fullscreenButton.setIcon(self.svgIcon)

		# Minimize button
		self.minimizeButton = QPushButton(self)
		self.minimizeButton.setStyleSheet(dark_theme_qpb_title)
		self.minimizeButton.setFixedSize(self._windowBarHeight, self._windowBarHeight)
		self.minimizeButton.clicked.connect(self.toggleCompact)
		self.svgIcon = QIcon(f"{self.icons_dir}/minimize_FILL0_wght400_GRAD0_opsz24.svg")
		self.minimizeButton.setIcon(self.svgIcon)

		# Close button
		closeButton = QPushButton(self)
		closeButton.setStyleSheet(close_button_style)
		closeButton.setFixedSize(self._windowBarHeight, self._windowBarHeight)
		closeButton.clicked.connect(self.close_window)
		self.svgIcon = QIcon(f"{self.icons_dir}/close_FILL0_wght400_GRAD0_opsz24.svg")
		closeButton.setIcon(self.svgIcon)

		# Status text with colored background
		self.statusButton = TriangleButton()  # Use TriangleButton instead of QPushButton
		self.statusButton.setTriangleColor("#333333") # Hide both corners of the button
		self.statusButton.setFixedSize(150, self._windowBarHeight)

		# Layout
		titleLayout.addWidget(self.logoButton)
		titleLayout.addWidget(self.titleLabel, 0)
		titleLayout.addWidget(self.toggleFrontButton)
		titleLayout.addWidget(self.statusButton)
		titleLayout.addWidget(self.minimizeButton)
		titleLayout.addWidget(self.fullscreenButton)
		titleLayout.addWidget(closeButton)

		titleBar.setLayout(titleLayout)
		self.setMenuWidget(titleBar)

	# Compact the window to just show the title bar
	def toggleCompact(self):
		self.showMinimized()
	
	def setTitleStatus(self, status):
		self.statusButton.setText(status)
		if status == "Connected":
			self.statusButton.setStyleSheet("font-size: 13px; background-color: darkgreen; border-radius: 0px;")
		elif status == "Disconnected":
			self.statusButton.setStyleSheet("font-size: 13px; background-color: darkred; border-radius: 0px;")
	
	def toggleFront(self):
		self.toggleFrontStatus = not self.toggleFrontStatus
		if self.toggleFrontStatus:
			self.svgIcon = QIcon(f"{self.icons_dir}/move_up_FILL0_wght400_GRAD0_opsz24.svg")
			self.toggleFrontButton.setIcon(self.svgIcon)

			self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
			self.show()
		else:
			self.svgIcon = QIcon(f"{self.icons_dir}/move_down_FILL0_wght400_GRAD0_opsz24.svg")
			self.toggleFrontButton.setIcon(self.svgIcon)
			
			self.setWindowFlags(Qt.FramelessWindowHint)
			self.show()
		
	def fullscreen(self):
		if self.isFullScreen():
			self.svgIcon = QIcon(f"{self.icons_dir}/expand_content_FILL0_wght400_GRAD0_opsz24.svg")
			self.fullscreenButton.setIcon(self.svgIcon)
			self.showNormal()
		else:
			self.svgIcon = QIcon(f"{self.icons_dir}/collapse_content_FILL0_wght400_GRAD0_opsz24.svg")
			self.fullscreenButton.setIcon(self.svgIcon)
			self.showFullScreen()

	def mouseDoubleClickEvent(self, event):
		if self.isFullScreen():
			self.svgIcon = QIcon(f"{self.icons_dir}/expand_content_FILL0_wght400_GRAD0_opsz24.svg")
			self.fullscreenButton.setIcon(self.svgIcon)
			self.showNormal()
		else:
			self.svgIcon = QIcon(f"{self.icons_dir}/collapse_content_FILL0_wght400_GRAD0_opsz24.svg")
			self.fullscreenButton.setIcon(self.svgIcon)
			self.showFullScreen()
		event.accept()

	def close_window(self):
		self.windowCloseEvent.emit()
		self.close()

	def closeEvent(self, event):
		self.windowCloseEvent.emit()
		super().closeEvent(event)

# Little -maybe not the best- trick to add a triangle to the connect/disconnect button
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