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

import sys
from pathlib import Path

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLineEdit

from bluetooth.ble_handler import BLEHandler
from gui.window_properties import SSCWindowProperties
from gui.connection_window import ConnectionWindow
from gui.console_window import ConsoleWindow
from resources.styles import *

# Default window properties
DEFAULT_TITLE = "ArcticStream"
DEFAULT_SIZE = (800, 410)
DEBUG_WINDOW = True

class MainWindow(SSCWindowProperties):
	def __init__(self):
		super().__init__(self)
		self.ble_handler = BLEHandler()
		self.ble_handler.connectionCompleted.connect(self.callback_connection_success)
		self.ble_handler.deviceDisconnected.connect(self.callback_disconnected)

		# Window initialization
		self.setWindowTitle(DEFAULT_TITLE)
		self.set_custom_title(DEFAULT_TITLE)
		self.resize(*DEFAULT_SIZE)

		# Set the status label
		self.set_status_bar("Disconnected")
		self.setContentsMargins(2, 2, 2, 2)

		self.setup_layout()

	# GUI Functions ------------------------------------------------------------------------------------------

	def setup_layout(self):
		self.tab_widget = QTabWidget(self)
		self.tab_widget.currentChanged.connect(self.callback_tab_change)

		# Single line text area for displaying debug info
		self.line_edit_debug = QLineEdit(self)
		self.line_edit_debug.setStyleSheet(dark_theme_qle_debugf)
		self.line_edit_debug.setReadOnly(True)
		self.line_edit_debug.setVisible(DEBUG_WINDOW)
		self.line_edit_debug.setText("> Debug info")

		# Central widget to hold the layout
		main_window_layout = QVBoxLayout()
		main_window_layout.addWidget(self.tab_widget)
		main_window_layout.addWidget(self.line_edit_debug)
		
		central_widget = QWidget()
		central_widget.setLayout(main_window_layout)
		self.setCentralWidget(central_widget)

		# Connection tab
		self.connection_tab = ConnectionWindow(self, self.ble_handler, "BLE")
		self.connection_tab.signal_closing_complete.connect(self.callback_finalize_close)

	# Window Functions ---------------------------------------------------------------------------------------

	# Update the debug info
	def debug_info(self, text):
		print(text)
		self.line_edit_debug.setText(f"> {text}")

	# Add a connection tab dynamically
	def add_connection_tab(self, console_widget, title):
		tabIndex = self.tab_widget.addTab(console_widget, title)
		return tabIndex

	# Add a console tab dynamically
	def add_console_tab(self, console_widget, title):
		tabIndex = self.tab_widget.addTab(console_widget, title)
		return tabIndex

	# Add a updater tab dynamically
	def add_updater_tab(self, console_widget, title):
		tabIndex = self.tab_widget.addTab(console_widget, title)
		return tabIndex

	def update_tab_title(self, console, title):
		index = self.tab_widget.indexOf(console)
		if index != -1:
			self.tab_widget.setTabText(index, title)

	def set_status_bar(self, mode):
		if mode == "Connected":
			self.setStyleSheet("MainWindow {border: 2px solid darkgreen;}")
			self.set_title_status("Connected")
		elif mode == "Disconnected":
			self.setStyleSheet("MainWindow {border: 2px solid darkred;}")
			self.set_title_status("Disconnected")

	# Get the icon path
	def icon_path(self):
		if getattr(sys, 'frozen', False):
			application_path = Path(sys._MEIPASS)
		else:
			application_path = Path(__file__).resolve().parent.parent
		icons_dir = application_path / "resources" / "icons"
		return icons_dir

	# Callbacks ----------------------------------------------------------------------------------------------

	def callback_tab_change(self, index):
		console = self.tab_widget.widget(index)
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
	
	# Qt Events ----------------------------------------------------------------------------------------------

	# Reimplement the resizeEvent
	def resizeEvent(self, event):
		super(MainWindow, self).resizeEvent(event)

	def closeEvent(self, event):
		if not self.connection_tab.is_closing:
			self.signal_window_close.emit()  # Emit the signal to start closing tasks
			event.ignore()  # Ignore the close event initially
		else:
			event.accept()  # Accept the close event if already closing

	def callback_finalize_close(self):
		self.close()  # Now safe to close the MainWindow