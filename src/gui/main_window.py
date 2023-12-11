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

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTabWidget, QLineEdit
from PyQt5.QtGui import QFontDatabase, QFont, QIcon

from bluetooth.ble_handler import BLEHandler
from gui.window_properties import SSCWindowProperties
from gui.connection_window import ConnectionWindow
from gui.console_window import ConsoleWindow

from resources.theme_config import *
import helpers.theme_helper as th

# Default window properties
DEFAULT_TITLE = "ArcticStream"
DEFAULT_SIZE = (800, 410)
MINIMUM_SIZE = (550, 320)

# Default styles
default_style_names = [
	"default_app_style",
	"default_button_style",
	"default_line_edit_style",
	"default_text_edit_style",
	"default_tab_style",
	"default_scroll_style"
]

class MainWindow(SSCWindowProperties):
	themeChanged = pyqtSignal(str)

	def __init__(self, app_main=None):
		super().__init__(self)
		self.ble_handler = BLEHandler()
		self.ble_handler.connectionCompleted.connect(self.callback_connection_success)
		self.ble_handler.deviceDisconnected.connect(self.callback_disconnected)

		# Window initialization
		self.setWindowTitle(DEFAULT_TITLE)
		self.set_custom_title(DEFAULT_TITLE)
		self.resize(*DEFAULT_SIZE)
		self.setMinimumSize(*MINIMUM_SIZE)

		# Set the stylesheet
		app_main.setStyleSheet(th.get_style(default_style_names))
		self.setWindowIcon(QIcon(f"{self.icon_path()}/main_icon.png"))

		# Load the font file (.ttf or .otf)
		QFontDatabase.addApplicationFont(f"{self.font_path()}/Ubuntu-Regular.ttf")
		QFontDatabase.addApplicationFont(f"{self.font_path()}/Inconsolata-Regular.ttf")
		app_main.setFont(QFont("Ubuntu"))

		# Set the status label
		self.set_status_bar("Disconnected")
		self.setContentsMargins(2, 2, 2, 2)

		# Globals
		self.debug_show = True

		self.setup_layout()

		 # Set the default theme
		self.theme_status = "dark"
		#self.toggle_theme()

	# GUI Functions ------------------------------------------------------------------------------------------

	def setup_layout(self):
		self.tab_widget = QTabWidget(self)
		self.tab_widget.currentChanged.connect(self.callback_tab_change)

		# Single line text area for displaying debug info
		self.line_edit_debug = QLineEdit(self)
		self.line_edit_debug.setFixedHeight(DEBUG_LINE_EDIT_HEIGHT)
		self.line_edit_debug.setStyleSheet(th.get_style("debug_bar_line_edit_style"))
		self.line_edit_debug.setReadOnly(True)
		self.line_edit_debug.setVisible(self.debug_show)
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
		self.themeChanged.emit(self.theme_status) # Update theme for new tab
		return tabIndex

	# Add a updater tab dynamically
	def add_updater_tab(self, console_widget, title):
		tabIndex = self.tab_widget.addTab(console_widget, title)
		self.themeChanged.emit(self.theme_status) # Update theme for new tab
		return tabIndex

	def update_tab_title(self, console, title):
		index = self.tab_widget.indexOf(console)
		if index != -1:
			self.tab_widget.setTabText(index, title)
	
	def visibility_tab(self, console, status):
		index = self.tab_widget.indexOf(console)
		if index != -1:
			self.tab_widget.setTabVisible(index, status)

	def set_status_bar(self, mode):
		if mode == "Connected":
			self.setStyleSheet("MainWindow {border: 2px solid rgba(0, 100, 0, 128);}")
			self.con_status_button.setStyleSheet("font-size: 13px; color: white; background-color: rgba(0, 100, 0, 128); border-radius: 0px;")
			self.con_status_button.setText("Connected")
		elif mode == "Disconnected":
			self.setStyleSheet("MainWindow {border: 2px solid rgba(139, 0, 0, 128);}")
			self.con_status_button.setStyleSheet("font-size: 13px; color: white; background-color: rgba(139, 0, 0, 128); border-radius: 0px;")
			self.con_status_button.setText("Disconnected")

	# Get the icon path
	def icon_path(self):
		if getattr(sys, 'frozen', False):
			application_path = Path(sys._MEIPASS)
		else:
			application_path = Path(__file__).resolve().parent.parent
		icons_dir = application_path / "resources" / "icons"
		return icons_dir

	# Get the font path
	def font_path(self):
		if getattr(sys, 'frozen', False):
			application_path = Path(sys._MEIPASS)
		else:
			application_path = Path(__file__).resolve().parent.parent
		font_dir = application_path / "resources" / "fonts"
		return font_dir

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

	# Callback toggle theme
	def toggle_theme(self, status=False):
		if self.theme_status == "dark":
			self.theme_status = "light"
		else:
			self.theme_status = "dark"

		th.toggle_theme() # Update global theme
		QApplication.instance().setStyleSheet(th.get_style(default_style_names))
		self.line_edit_debug.setStyleSheet(th.get_style("debug_bar_line_edit_style"))

		# Update children widgets
		self.themeChanged.emit(self.theme_status)
	
	def toggle_debug(self):
		if self.debug_show:
			self.debug_show = False
			self.line_edit_debug.setVisible(False)
		else:
			self.debug_show = True
			self.line_edit_debug.setVisible(True)
	
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