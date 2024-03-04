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

import qasync
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLineEdit, QPushButton, QPlainTextEdit, QApplication, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QTextEdit
from PyQt5.QtGui import QTextCursor, QFont, QTextCharFormat
from datetime import datetime

from interfaces.bluetooth.ble_handler import BLEHandler
from resources.indexer import ConsoleIndex
from helpers.pushbutton_helper import ToggleButton, SimpleButton
from resources.theme_config import *
import helpers.theme_helper as th

class ConsoleWindow(QWidget):
	def __init__(self, main_window, stream_interface: BLEHandler, title, console_index: ConsoleIndex):
		super().__init__()
	
		self.main_window = main_window # MainWindow Reference
		self.stream_interface = stream_interface # BLE Reference
		self.win_title = title # Original title of the tab
		self.console_index = console_index # Console information

		self.main_window.debug_log("ConsoleWindow: Initializing ...")
		self.main_window.debug_log(f"ConsoleWindow: {self.console_index.name}")
		self.main_window.debug_log(f"ConsoleWindow: {self.console_index.service.uuid}")
		self.main_window.debug_log(f"ConsoleWindow: {self.console_index.tx_characteristic.uuid}")
		self.main_window.debug_log(f"ConsoleWindow: {self.console_index.txs_characteristic.uuid}")
		self.main_window.debug_log(f"ConsoleWindow: {self.console_index.rx_characteristic.uuid}")
		self.main_window.debug_log("------------------------------------------")

		# Async BLE Signals
		self.stream_interface.connectionCompleted.connect(self.callback_connection_complete)
		self.stream_interface.deviceDisconnected.connect(self.callback_disconnected)
		self.stream_interface.notificationReceived.connect(self.callback_handle_notification)
		self.main_window.themeChanged.connect(self.callback_update_theme)

		# Globals
		self.icons_dir = self.main_window.icon_path()
		self.data_tab_counter = 0
		self.scroll_locked = True
		self.console_paused = False
		self.logging_enabled = False
		self.user_log_path = None

		self.total_lines = 0
		self.total_bytes_received = 0
		self.last_received_timestamp = 0
		self.total_data_counter = 0

		self.setup_layout()

	# GUI Functions ------------------------------------------------------------------------------------------
	
	# Layout and Widgets
	def setup_layout(self):

		# Start and Stop buttons
		start_button = QPushButton("Start", self)
		start_button.clicked.connect(self.start_console)
		stop_button = QPushButton("Stop", self)
		stop_button.clicked.connect(self.pause_console)
		clear_button = QPushButton("Clear", self)
		clear_button.clicked.connect(self.clear_text)
		copy_button = QPushButton("Copy", self)
		copy_button.clicked.connect(self.copy_text)
		self.log_button = QPushButton("Log", self)
		self.log_button.clicked.connect(self.log_text)

		# Toggle lock button
		self.lock_button = ToggleButton(self,
			icons=(f"{self.icons_dir}/lock_open_right_FILL0_wght400_GRAD0_opsz24.svg", f"{self.icons_dir}/lock_FILL0_wght400_GRAD0_opsz24.svg"),
			size=(DEFAULT_PUSH_BUTTON_HEIGHT, DEFAULT_PUSH_BUTTON_HEIGHT),
			style=th.get_style("default_button_style"),
			callback=self.toggle_lock,
			toggled=True
		)

		# Main text area for accumulating text
		self.text_edit_printf = QPlainTextEdit(self)
		self.text_edit_printf.setFont(QFont("Inconsolata"))
		self.text_edit_printf.installEventFilter(self)
		self.text_edit_printf.setReadOnly(True)
		
		# Create an overlay
		self.status_overlay = QLineEdit(self)
		self.status_overlay.setFont(QFont("Inconsolata"))
		self.status_overlay.setStyleSheet(th.get_style("console_status_line_edit_style"))
		self.status_overlay.setGeometry(self.text_edit_printf.geometry())
		self.status_overlay.setReadOnly(True)
		self.status_overlay.setAlignment(Qt.AlignCenter)
		self.status_overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
		self.set_overlay_geometry()
		self.update_status()

		# Single line text area for displaying info
		self.line_edit_singlef = QLineEdit(self)
		self.line_edit_singlef.setFont(QFont("Inconsolata"))
		self.line_edit_singlef.setFixedHeight(DEFAULT_LINE_EDIT_HEIGHT)
		self.line_edit_singlef.setReadOnly(True)

		# Layout for buttons
		buttons_layout = QHBoxLayout()
		buttons_layout.addWidget(start_button)
		buttons_layout.addWidget(stop_button)
		buttons_layout.addWidget(clear_button)
		buttons_layout.addWidget(copy_button)
		buttons_layout.addWidget(self.log_button)
		buttons_layout.addWidget(self.lock_button)

		# Input text box for sending data
		self.line_edit_send = QLineEdit(self)
		self.line_edit_send.setFont(QFont("Inconsolata"))
		self.line_edit_send.setFixedHeight(DEFAULT_LINE_EDIT_HEIGHT)
		self.line_edit_send.setStyleSheet(th.get_style("console_send_line_edit_style"))
		self.line_edit_send.setPlaceholderText("Insert data to send ...")

		# Simple send button
		self.send_button = SimpleButton(self,
			icon=f"{self.icons_dir}/play_arrow_FILL0_wght400_GRAD0_opsz24.svg",
			size=(DEFAULT_PUSH_BUTTON_HEIGHT, DEFAULT_PUSH_BUTTON_HEIGHT),
			style=th.get_style("default_button_style"),
			callback=self.send_data
		)

		# Layout for input text box and send button
		send_data_layout = QHBoxLayout()
		send_data_layout.addWidget(self.line_edit_send)
		send_data_layout.addWidget(self.send_button)

		# Update the main layout
		console_win_layout = QVBoxLayout()
		console_win_layout.addLayout(buttons_layout)
		console_win_layout.addWidget(self.text_edit_printf)
		console_win_layout.addWidget(self.line_edit_singlef)
		console_win_layout.addLayout(send_data_layout)
		self.setLayout(console_win_layout)

	def start_console(self):
		self.console_paused = False

	def pause_console(self):
		self.console_paused = True

	# Lock and unlock the scrollbar
	def toggle_lock(self, status):
		self.scroll_locked = status
	
	# Reset the tab counter
	def resetCounter(self):
		self.data_tab_counter = 0
		self.update_tab_title()
	
	# Update the tab title
	def update_tab_title(self):
		new_title = f"{self.win_title} ({self.data_tab_counter})" if self.data_tab_counter > 0 else self.win_title
		self.main_window.update_tab_title(self, new_title)

	def check_tab_focus(self):
		current_widget = self.main_window.tab_widget.currentWidget()
		return current_widget == self

	# Async BLE Functions ------------------------------------------------------------------------------------------

	@qasync.asyncSlot()
	async def send_data(self):
		data = self.line_edit_send.text()
		if data:
			await self.stream_interface.writeCharacteristic(self.console_index.rx_characteristic.uuid, data.encode())
			self.line_edit_send.clear()

	# Callbacks -----------------------------------------------------------------------------------------------

	# Callback connection success
	def callback_connection_complete(self, connected):
		if connected:
			self.update_data(f"[ {self.main_window.default_title}: Remote device connected ]\n")
	
	# Callback device disconnected
	def callback_disconnected(self, client):
		self.update_data(f"[ {self.main_window.default_title}: Remote device disconnected ]\n")

	# Callback handle input notification
	def callback_handle_notification(self, sender, data):
		# Redirect the data to the printf text box
		if sender == self.console_index.tx_characteristic.uuid:
			self.update_data(data)
		elif sender == self.console_index.txs_characteristic.uuid:
			self.update_info(data)

	# Window Functions ------------------------------------------------------------------------------------------

	def set_overlay_geometry(self):
		# Calculate the geometry based on the main text area
		text_edit_geom = self.text_edit_printf.geometry()
		overlay_width = DEFAULT_STATUS_LEDIT_WIDTH
		overlay_height = DEFAULT_STATUS_LEDIT_HEIGH

		# Center the overlay within text_edit_printf
		overlay_x = text_edit_geom.x() + (text_edit_geom.width() - overlay_width) // 2
		overlay_y = text_edit_geom.y() + text_edit_geom.height() - overlay_height

		# Set the geometry for the status overlay
		self.status_overlay.setGeometry(overlay_x, overlay_y, overlay_width, overlay_height)

	# Overlay text
	def update_status(self):
		current_time = datetime.now()

		# Calculate latency in milliseconds
		if self.last_received_timestamp:
			latency = int((current_time - self.last_received_timestamp).total_seconds() * 1000)
			latency_text = f"{latency:3.0f} ms"
		else:
			latency_text = "N/A"

		status_text = (f"Lines: {self.total_lines} | "
					f"Inputs: {self.total_data_counter} | "
					f"Bytes: {self.total_bytes_received} B | "
					f"Delta: {latency_text} | "
					f"Last: {self.last_received_timestamp.strftime('%H:%M:%S') if self.last_received_timestamp else 'N/A'}")
		
		self.status_overlay.setText(status_text)

	def update_data(self, data, line_limit=1000):
		if self.console_paused:
			return

		# New data received - update metrics
		self.total_bytes_received += len(data.encode('utf-8'))

		# Save the current position of the scrollbar
		scrollbar = self.text_edit_printf.verticalScrollBar()
		current_pos = scrollbar.value()

		# Reset the text format to default before inserting new data
		cursor = self.text_edit_printf.textCursor()
		cursor.movePosition(QTextCursor.End)
		reset_format = QTextCharFormat()
		cursor.setCharFormat(reset_format)

		# Insert the new data
		self.text_edit_printf.setTextCursor(cursor)
		self.text_edit_printf.insertPlainText(data)

		# Log the data if logging is enabled
		if self.logging_enabled and self.user_log_path:
			try:
				with open(self.user_log_path, 'a') as log_file:
					log_file.write(data)
			except Exception as e:
				self.main_window.debug_log(f"Error writing to log file: {e}")

		# Limit the number of lines
		text = self.text_edit_printf.toPlainText()
		lines = text.split('\n')
		if len(lines) > line_limit:
			lines = lines[-line_limit:]
			self.text_edit_printf.setPlainText('\n'.join(lines))

		# Scroll to the bottom if the lock button is pressed
		if self.scroll_locked:
			scrollbar.setValue(scrollbar.maximum())
		else:
			scrollbar.setValue(current_pos)
		
		# Increment the tab counter
		if not self.check_tab_focus():
			self.data_tab_counter += 1
			self.update_tab_title()

		# Update the total lines
		self.total_data_counter += 1
		self.total_lines = len(self.text_edit_printf.toPlainText().split('\n'))
		
		# Update stats bar
		self.update_status()
		self.last_received_timestamp = datetime.now()

	# Update the info text box (singlef)
	def update_info(self, info):
		if "ARCTIC_COMMAND_SHOW" in info:
			self.main_window.visibility_tab(self, True)
			return
		if "ARCTIC_COMMAND_HIDE" in info:
			self.main_window.visibility_tab(self, False)
			return
		if "ARCTIC_COMMAND_REQ_NAME" in info:
			return
		self.line_edit_singlef.setText(info)
	
	# Copy the text from the main text box
	def copy_text(self):
		clipboard = QApplication.clipboard()
		clipboard.setText(self.text_edit_printf.toPlainText())
	
	# Clear the text from the main text box
	def clear_text(self):
		self.text_edit_printf.clear()
		self.line_edit_singlef.clear()

		# Clears status bar
		self.total_lines = 0
		self.total_bytes_received = 0
		self.last_received_timestamp = 0
		self.total_data_counter = 0
		self.update_status()
	
	# Save the text from the main text box
	def log_text(self):
		if not self.logging_enabled:
			if self.select_log_file():
				self.logging_enabled = True
				self.log_button.setStyleSheet("color: #ffffff; background-color: rgba(0, 100, 0, 128)")
		else:
			self.logging_enabled = False
			self.log_button.setStyleSheet(th.get_style("default_button_style"))

	def select_log_file(self):
		# Use the native file dialog
		fileName, _ = QFileDialog.getSaveFileName(self, "Select Log File", self.win_title, "Text Files (*.txt)")
		if fileName:
			self.user_log_path = fileName
			return True
		return False
	
	def callback_update_theme(self, theme):
		# Reload stylesheets (background for buttons)
		self.line_edit_send.setStyleSheet(th.get_style("console_send_line_edit_style"))
		if not self.logging_enabled:
			self.log_button.setStyleSheet(th.get_style("default_button_style"))
		self.lock_button.setStyleSheet(th.get_style("default_button_style"))
		self.send_button.setStyleSheet(th.get_style("default_button_style"))
		self.status_overlay.setStyleSheet(th.get_style("console_status_line_edit_style"))

		# Update special widgets by theme
		if theme == "dark":
			self.lock_button.changeIconColor("#ffffff")
			self.send_button.changeIconColor("#ffffff")
		elif theme == "light":
			self.lock_button.changeIconColor("#000000")
			self.send_button.changeIconColor("#000000")
	
	# Qt Functions ------------------------------------------------------------------------------------------

	def resizeEvent(self, event):
		self.set_overlay_geometry()
		super().resizeEvent(event)

	# Reimplement the keyPressEvent
	def keyPressEvent(self, event):
		if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
			if self.line_edit_send.hasFocus():
				self.send_data()