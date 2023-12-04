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

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLineEdit

from gui.window_properties import SSCWindowProperties
from gui.connection_window import ConnectionWindow
from bluetooth.ble_handler import BLEHandler
from gui.console_window import ConsoleWindow
from gui.updater_window import UpdaterWindow
from resources.styles import *

from pathlib import Path
import sys

# Enable debug window at the bottom
DEBUG_WINDOW = True

class MainWindow(SSCWindowProperties):
	def __init__(self):
		super().__init__(self)
		self.bleHandler = BLEHandler()
		self.bleHandler.connectionCompleted.connect(self.callback_connection_success)
		self.bleHandler.deviceDisconnected.connect(self.callback_disconnected)

		# Window initialization
		self.setWindowTitle("ArcticStream")
		self.setCustomTitle("ArcticStream")
		self.set_status_bar("Disconnected")
		self.setContentsMargins(2, 2, 2, 2)
		self.resize(800, 410)

		self.setup_layout()
		self.icon_path()

	# GUI Functions ------------------------------------------------------------------------------------------

	def setup_layout(self):
		self.tabWidget = QTabWidget(self)
		self.tabWidget.currentChanged.connect(self.onTabChange)

		# Single line text area for displaying debug info
		self.qle_debugf = QLineEdit(self)
		self.qle_debugf.setStyleSheet(dark_theme_qle_debugf)
		self.qle_debugf.setReadOnly(True)
		self.qle_debugf.setVisible(DEBUG_WINDOW)
		self.qle_debugf.setText("> Debug info")

		# Central widget to hold the layout
		centralWidget = QWidget()
		mainLayout = QVBoxLayout()
		mainLayout.addWidget(self.tabWidget)
		mainLayout.addWidget(self.qle_debugf)
		centralWidget.setLayout(mainLayout)
		self.setCentralWidget(centralWidget)

		# Connection tab
		self.connectionTab = ConnectionWindow(self, self.bleHandler, "BLE")
		self.connectionTab.closingCompleted.connect(self.finalizeClose)

	# Update the debug info
	def debug_info(self, text):
		print(text)
		self.qle_debugf.setText(f"> {text}")

	# Add a connection tab dynamically
	def add_connection_tab(self, console_widget, title):
		tabIndex = self.tabWidget.addTab(console_widget, title)
		return tabIndex

	# Add a console tab dynamically
	def add_console_tab(self, console_widget, title):
		tabIndex = self.tabWidget.addTab(console_widget, title)
		return tabIndex

	# Add a updater tab dynamically
	def add_updater_tab(self, console_widget, title):
		tabIndex = self.tabWidget.addTab(console_widget, title)
		return tabIndex

	# Reimplement the resizeEvent
	def resizeEvent(self, event):
		super(MainWindow, self).resizeEvent(event)

	def updateTabTitle(self, console, title):
		index = self.tabWidget.indexOf(console)
		if index != -1:
			self.tabWidget.setTabText(index, title)

	def onTabChange(self, index):
		console = self.tabWidget.widget(index)
		if isinstance(console, ConsoleWindow):
			console.resetCounter()

	# Callback connection success
	def callback_connection_success(self, connected):
		if not connected:
			return
		self.set_status_bar("Connected")
	
	# Callback device disconnected
	def callback_disconnected(self, client):
		self.set_status_bar("Disconnected")

	def set_status_bar(self, mode):
		if mode == "Connected":
			self.setStyleSheet("MainWindow {border: 2px solid darkgreen;}")
			self.setTitleStatus("Connected")
		elif mode == "Disconnected":
			self.setStyleSheet("MainWindow {border: 2px solid darkred;}")
			self.setTitleStatus("Disconnected")

	# Get the icon path
	def icon_path(self):
		if getattr(sys, 'frozen', False):
			application_path = Path(sys._MEIPASS)
		else:
			application_path = Path(__file__).resolve().parent.parent
		icons_dir = application_path / "resources" / "icons"
		return icons_dir

	def closeEvent(self, event):
		if not self.connectionTab.is_closing:
			self.windowCloseEvent.emit()  # Emit the signal to start closing tasks
			event.ignore()  # Ignore the close event initially
		else:
			event.accept()  # Accept the close event if already closing

	def finalizeClose(self):
		self.close()  # Now safe to close the MainWindow