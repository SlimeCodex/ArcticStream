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
from PyQt5.QtWidgets import QLineEdit, QPushButton, QTextEdit, QApplication, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog
from PyQt5.QtGui import QTextCursor, QFont

from bluetooth.ble_handler import BLEHandler
from resources.indexer import ConsoleIndex
from helpers.pushbutton_helper import ToggleButton, SimpleButton
from resources.theme_config import *
import helpers.theme_helper as th

class ConsoleWindow(QWidget):
	def __init__(self, main_window, ble_handler: BLEHandler, title, console_index: ConsoleIndex):
		super().__init__()
		self.main_window = main_window # MainWindow Reference
		self.ble_handler = ble_handler # BLE Reference
		self.win_title = title # Original title of the tab
		self.console_index = console_index # Console information

		print("ConsoleWindow: Initializing ...")
		print(f"ConsoleWindow: {self.console_index.name}")
		print(f"ConsoleWindow: {self.console_index.service.uuid}")
		print(f"ConsoleWindow: {self.console_index.tx_characteristic.uuid}")
		print(f"ConsoleWindow: {self.console_index.txs_characteristic.uuid}")
		print(f"ConsoleWindow: {self.console_index.rx_characteristic.uuid}")
		print("------------------------------------------")

		# Async BLE Signals
		self.ble_handler.notificationReceived.connect(self.callback_handle_notification)
		self.main_window.themeChanged.connect(self.callback_update_theme)

		# Globals
		self.icons_dir = self.main_window.icon_path()
		self.data_counter = 0
		self.scroll_locked = True
		self.console_paused = False
		self.logging_enabled = False
		self.user_log_path = None

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
		self.text_edit_printf = QTextEdit(self)
		self.text_edit_printf.setFont(QFont("Inconsolata"))
		self.text_edit_printf.installEventFilter(self)
		self.text_edit_printf.setReadOnly(True)

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
		self.data_counter = 0
		self.update_tab_title()
	
	# Update the tab title
	def update_tab_title(self):
		new_title = f"{self.win_title} ({self.data_counter})" if self.data_counter > 0 else self.win_title
		self.main_window.update_tab_title(self, new_title)

	def isTabInFocus(self):
		current_widget = self.main_window.tab_widget.currentWidget()
		return current_widget == self

	# Async BLE Functions ------------------------------------------------------------------------------------------

	@qasync.asyncSlot()
	async def send_data(self):
		data = self.line_edit_send.text()
		if data:
			await self.ble_handler.writeCharacteristic(self.console_index.rx_characteristic.uuid, data.encode())
			self.line_edit_send.clear()

	# Callbacks -----------------------------------------------------------------------------------------------

	# Callback handle input notification
	def callback_handle_notification(self, sender, data):

		# Redirect the data to the printf text box
		if sender == self.console_index.tx_characteristic.uuid:
			self.update_data(data)
		elif sender == self.console_index.txs_characteristic.uuid:
			self.update_info(data)

	# Window Functions ------------------------------------------------------------------------------------------

	def update_data(self, data, line_limit=1000):
		if self.console_paused:
			return

		# Save the current position of the scrollbar
		scrollbar = self.text_edit_printf.verticalScrollBar()
		current_pos = scrollbar.value()

		# Insert the new data
		self.text_edit_printf.moveCursor(QTextCursor.End)
		self.text_edit_printf.insertPlainText(data)

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
		if not self.isTabInFocus():
			self.data_counter += 1
			self.update_tab_title()

		# Log data to file if logging is enabled
		if self.logging_enabled and self.user_log_path:
			with open(self.user_log_path, 'a') as file:
				file.write(data)

	# Update the info text box (singlef)
	def update_info(self, info):
		self.line_edit_singlef.setText(info)
	
	# Copy the text from the main text box
	def copy_text(self):
		clipboard = QApplication.clipboard()
		clipboard.setText(self.text_edit_printf.toPlainText())
	
	# Clear the text from the main text box
	def clear_text(self):
		self.text_edit_printf.clear()
		self.line_edit_singlef.clear()
	
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

		# Update special widgets by theme
		if theme == "dark":
			self.lock_button.changeIconColor("#ffffff")
			self.send_button.changeIconColor("#ffffff")
		elif theme == "light":
			self.lock_button.changeIconColor("#000000")
			self.send_button.changeIconColor("#000000")
	
	# Qt Functions ------------------------------------------------------------------------------------------

	# Reimplement the keyPressEvent
	def keyPressEvent(self, event):
		if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
			if self.line_edit_send.hasFocus():
				self.send_data()