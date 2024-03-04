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
import time
from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTabWidget, QLineEdit, QHBoxLayout, QPushButton
from PyQt5.QtGui import QFontDatabase, QFont, QIcon

from interfaces.bluetooth.ble_handler import BLEHandler
from interfaces.wifi.wifi_handler import WiFiHandler
from interfaces.uart.uart_handler import UARTHandler
from gui.window_properties import SSCWindowProperties
from gui.connection_window_ble import BLEConnectionWindow
from gui.connection_window_wifi import WiFiConnectionWindow
from gui.connection_window_uart import UARTConnectionWindow
from gui.console_window import ConsoleWindow
from helpers.pushbutton_helper import SimpleButton

from resources.theme_config import *
import helpers.theme_helper as th

# Default styles
default_style_names = [
	"default_app_style",
	"default_button_style",
	"default_line_edit_style",
	"default_text_edit_style",
	"default_ptext_edit_style",
	"default_tab_style",
	"default_scroll_style"
]

class MainWindow(SSCWindowProperties):
	themeChanged = pyqtSignal(str)

	def __init__(self, app_main=None):
		super().__init__(self)
		self.stream_interface = 0

		# Default window properties
		self.default_title = "ArcticStream"
		self.default_size = (800, 420)
		self.minimum_size = (550, 350)
		self.app_version = "v1.1.0"

		# Window initialization
		self.setWindowTitle(self.default_title)
		self.set_custom_title(self.default_title)
		self.resize(*self.default_size)
		self.setMinimumSize(*self.minimum_size)

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
		self.debug_show = False
		self.start_time = time.time()
	
		self.setup_layout()

		 # Set the default theme
		self.theme_status = "dark"
		#self.toggle_theme()

	# GUI Functions ------------------------------------------------------------------------------------------

	def setup_layout(self):
		self.tab_widget = QTabWidget(self)
		self.tab_widget.currentChanged.connect(self.callback_tab_change)
		self.tab_widget.setVisible(False)

		# Single line text area for displaying debug info
		self.line_edit_debug = QLineEdit(self)
		self.line_edit_debug.setFixedHeight(DEBUG_LINE_EDIT_HEIGHT)
		self.line_edit_debug.setStyleSheet(th.get_style("debug_bar_line_edit_style"))
		self.line_edit_debug.setReadOnly(True)
		self.line_edit_debug.setVisible(self.debug_show)
		self.line_edit_debug.setText(">")

		# Single line text area for displaying version
		self.line_edit_version = QLineEdit(self)
		self.line_edit_version.setAlignment(Qt.AlignCenter)
		self.line_edit_version.setFixedWidth(80)
		self.line_edit_version.setFixedHeight(DEBUG_LINE_EDIT_HEIGHT)
		self.line_edit_version.setStyleSheet(th.get_style("debug_bar_line_edit_style"))
		self.line_edit_version.setReadOnly(True)
		self.line_edit_version.setVisible(self.debug_show)
		self.line_edit_version.setText(self.app_version)

		# Connector BLE button
		self.ble_button = SimpleButton(self,
			icon=f"{self.icons_dir}/bluetooth_FILL0_wght300_GRAD0_opsz24.svg",
			style=th.get_style("connectors_button_style"),
			callback=self.connect_ble
		)
		self.ble_button.setIconSize(QSize(CONNECTORS_ICON_SIZE,CONNECTORS_ICON_SIZE))

		# Connector USB button
		self.usb_button = SimpleButton(self,
			icon=f"{self.icons_dir}/usb_FILL0_wght300_GRAD0_opsz24.svg",
			style=th.get_style("connectors_button_style"),
			callback=self.connect_uart
		)
		self.usb_button.setIconSize(QSize(CONNECTORS_ICON_SIZE,CONNECTORS_ICON_SIZE))

		# Connector WiFi button
		self.wifi_button = SimpleButton(self,
			icon=f"{self.icons_dir}/wifi_FILL0_wght300_GRAD0_opsz24.svg",
			style=th.get_style("connectors_button_style"),
			callback=self.connect_wifi
		)
		self.wifi_button.setIconSize(QSize(CONNECTORS_ICON_SIZE,CONNECTORS_ICON_SIZE))
		
		self.ble_descriptor = QPushButton("Bluetooth", self)
		self.ble_descriptor.setStyleSheet(th.get_style("connectors_desc_button_style"))
		self.usb_descriptor = QPushButton("USB", self)
		self.usb_descriptor.setStyleSheet(th.get_style("connectors_desc_button_style"))
		self.wifi_descriptor = QPushButton("Wifi", self)
		self.wifi_descriptor.setStyleSheet(th.get_style("connectors_desc_button_style"))

		connectors_layout = QHBoxLayout()
		connectors_layout.addWidget(self.ble_button)
		connectors_layout.addWidget(self.usb_button)
		connectors_layout.addWidget(self.wifi_button)

		descriptors_layout = QHBoxLayout()
		descriptors_layout.addWidget(self.ble_descriptor)
		descriptors_layout.addWidget(self.usb_descriptor)
		descriptors_layout.addWidget(self.wifi_descriptor)

		debug_layout = QHBoxLayout()
		debug_layout.addWidget(self.line_edit_debug)
		debug_layout.addWidget(self.line_edit_version)

		# Central widget to hold the layout
		main_window_layout = QVBoxLayout()
		main_window_layout.addWidget(self.tab_widget)
		main_window_layout.addLayout(connectors_layout)
		main_window_layout.addLayout(descriptors_layout)
		main_window_layout.addLayout(debug_layout)

		central_widget = QWidget()
		central_widget.setLayout(main_window_layout)
		self.setCentralWidget(central_widget)

	# Window Functions ---------------------------------------------------------------------------------------

	# Update the debug info
	def debug_info(self, text):
		self.line_edit_debug.setText(f"> {text}")
		
		# Log to console
		self.debug_log(text)

	# Log debug data
	def debug_log(self, text):
		elapsed_time = (time.time() - self.start_time) * 1000
		log_entry = f"[{elapsed_time:.3f}]\t{text}"
		print(log_entry)

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
		self.ble_button.setStyleSheet(th.get_style("connectors_button_style"))
		self.usb_button.setStyleSheet(th.get_style("connectors_button_style"))
		self.wifi_button.setStyleSheet(th.get_style("connectors_button_style"))

		self.ble_descriptor.setStyleSheet(th.get_style("connectors_desc_button_style"))
		self.usb_descriptor.setStyleSheet(th.get_style("connectors_desc_button_style"))
		self.wifi_descriptor.setStyleSheet(th.get_style("connectors_desc_button_style"))
		
		self.line_edit_debug.setStyleSheet(th.get_style("debug_bar_line_edit_style"))
		self.line_edit_version.setStyleSheet(th.get_style("debug_bar_line_edit_style"))

		# Update special widgets by theme
		if self.theme_status == "dark":
			self.ble_button.changeIconColor("#ffffff")
			self.usb_button.changeIconColor("#ffffff")
			self.wifi_button.changeIconColor("#ffffff")
		elif self.theme_status == "light":
			self.ble_button.changeIconColor("#303030")
			self.usb_button.changeIconColor("#303030")
			self.wifi_button.changeIconColor("#303030")
		
		# Update children widgets
		self.themeChanged.emit(self.theme_status)
	
	def toggle_debug(self):
		if self.debug_show:
			self.debug_show = False
			self.line_edit_debug.setVisible(False)
			self.line_edit_version.setVisible(False)
		else:
			self.debug_show = True
			self.line_edit_debug.setVisible(True)
			self.line_edit_version.setVisible(True)
	
	def connect_ble(self):
		self.debug_info("Interface selected: BLE")
		self.stream_interface = BLEHandler()
		self.connection_tab = BLEConnectionWindow(self, self.stream_interface, "BLE")
		self.connection_tab.signal_closing_complete.connect(self.callback_finalize_close)
		self.stream_interface.connectionCompleted.connect(self.callback_connection_success)
		self.stream_interface.deviceDisconnected.connect(self.callback_disconnected)
		self.tab_widget.setVisible(True)
		self.hide_interfaces()
	
	def connect_wifi(self):
		self.debug_info("Interface selected: WiFi")
		self.stream_interface = WiFiHandler()
		self.connection_tab = WiFiConnectionWindow(self, self.stream_interface, "WiFi")
		self.connection_tab.signal_closing_complete.connect(self.callback_finalize_close)
		self.stream_interface.connectionCompleted.connect(self.callback_connection_success)
		self.stream_interface.deviceDisconnected.connect(self.callback_disconnected)
		self.tab_widget.setVisible(True)
		self.hide_interfaces()
	
	def connect_uart(self):
		self.debug_info("Interface selected: UART")
		self.stream_interface = UARTHandler()
		self.connection_tab = UARTConnectionWindow(self, self.stream_interface, "UART")
		self.connection_tab.signal_closing_complete.connect(self.callback_finalize_close)
		self.stream_interface.connectionCompleted.connect(self.callback_connection_success)
		self.stream_interface.deviceDisconnected.connect(self.callback_disconnected)
		self.tab_widget.setVisible(True)
		self.hide_interfaces()
	
	def exit_ble(self):
		self.tab_widget.setVisible(False)
		self.show_interfaces()

	def hide_interfaces(self):
		self.ble_button.setVisible(False)
		self.usb_button.setVisible(False)
		self.wifi_button.setVisible(False)
		self.ble_descriptor.setVisible(False)
		self.usb_descriptor.setVisible(False)
		self.wifi_descriptor.setVisible(False)
	
	def show_interfaces(self):
		self.ble_button.setVisible(True)
		self.usb_button.setVisible(True)
		self.wifi_button.setVisible(True)
		self.ble_descriptor.setVisible(True)
		self.usb_descriptor.setVisible(True)
		self.wifi_descriptor.setVisible(True)

	# Qt Events ----------------------------------------------------------------------------------------------

	# Reimplement the resizeEvent
	def resizeEvent(self, event):
		super(MainWindow, self).resizeEvent(event)

	def closeEvent(self, event):
		if not self.connection_tab.is_closing:
			self.signal_window_close.emit() # Emit the signal to start closing tasks
			event.ignore() # Ignore the close event initially
		else:
			event.accept() # Accept the close event if already closing

	def callback_finalize_close(self):
		self.close() # Now safe to close the MainWindow