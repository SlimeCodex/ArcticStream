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

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLineEdit, QPushButton, QTextEdit, QApplication, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog
from PyQt5.QtGui import QTextCursor, QIcon

from bluetooth.ble_handler import BLEHandler
from resources.indexer import ConsoleIndex
from resources.styles import *

from pathlib import Path
import asyncio
import qasync

class ConsoleWindow(QWidget):
	def __init__(self, main_window, ble_handler: BLEHandler, title, console_index: ConsoleIndex):
		super().__init__()
		self.mainWindow = main_window # MainWindow Reference
		self.bleHandler = ble_handler # BLE Reference
		self.winTitle = title # Original title of the tab
		self.consoleIndex = console_index # Console information

		print("ConsoleWindow: Initializing ...")
		print(f"ConsoleWindow: {self.consoleIndex.name}")
		print(f"ConsoleWindow: {self.consoleIndex.service.uuid}")
		print(f"ConsoleWindow: {self.consoleIndex.tx_characteristic.uuid}")
		print(f"ConsoleWindow: {self.consoleIndex.txs_characteristic.uuid}")
		print(f"ConsoleWindow: {self.consoleIndex.rx_characteristic.uuid}")
		print(f"ConsoleWindow: {self.consoleIndex.name_characteristic.uuid}")
		print("------------------------------------------")

		# Async BLE Signals
		self.bleHandler.notificationReceived.connect(self.callback_handle_notification)

		# Globals
		self.dataCounter = 0
		self.isLocked = True
		self.isPaused = False
		self.isLogging = False
		self.logFilePath = None
		self.icons_dir = self.mainWindow.icon_path()

		self.setup_layout()

	# GUI Functions ------------------------------------------------------------------------------------------
	
	# Layout and Widgets
	def setup_layout(self):

		# Start and Stop buttons
		self.startButton = QPushButton("Start", self)
		self.startButton.clicked.connect(self.start_console)
		self.stopButton = QPushButton("Stop", self)
		self.stopButton.clicked.connect(self.pause_console)
		self.clearButton = QPushButton("Clear", self)
		self.clearButton.clicked.connect(self.clear_text)
		self.copyButton = QPushButton("Copy", self)
		self.copyButton.clicked.connect(self.copy_text)
		self.logButton = QPushButton("Log", self)
		self.logButton.clicked.connect(self.log_text)

		# Lock button
		self.lockButton = QPushButton(self)
		self.lockButton.setFixedSize(25, 25)
		self.lockButton.clicked.connect(self.togglelLock)
		self.svgIcon = QIcon(f"{self.icons_dir}/lock_FILL0_wght400_GRAD0_opsz24.svg")
		self.lockButton.setIcon(self.svgIcon)

		# Main text area for accumulating text
		self.qte_printf = QTextEdit(self)
		self.qte_printf.setMaximumSize
		self.qte_printf.setStyleSheet(dark_theme_qte_printf)
		self.qte_printf.setReadOnly(True)

		# Single line text area for displaying info
		self.qte_singlef = QLineEdit(self)
		self.qte_singlef.setStyleSheet(dark_theme_qle_singlef)
		self.qte_singlef.setReadOnly(True)

		# Layout for Start and Stop buttons
		buttonLayout = QHBoxLayout()
		buttonLayout.addWidget(self.startButton)
		buttonLayout.addWidget(self.stopButton)
		buttonLayout.addWidget(self.clearButton)
		buttonLayout.addWidget(self.copyButton)
		buttonLayout.addWidget(self.logButton)
		buttonLayout.addWidget(self.lockButton)

		# Input text box for sending data
		self.qle_send = QLineEdit(self)
		self.qle_send.setStyleSheet(dark_theme_qle_send_data)
		self.qle_send.setPlaceholderText("Insert data to send ...")

		# Send button for input text box
		self.sendButton = QPushButton(self)
		self.sendButton.setFixedSize(25, 25)
		self.sendButton.clicked.connect(self.send_data)
		self.svgIcon = QIcon(f"{self.icons_dir}/play_arrow_FILL0_wght400_GRAD0_opsz24.svg")
		self.sendButton.setIcon(self.svgIcon)

		# Layout for input text box and send button
		inputLayout = QHBoxLayout()
		inputLayout.addWidget(self.qle_send)
		inputLayout.addWidget(self.sendButton)

		# Update the main layout
		mainLayout = QVBoxLayout()
		mainLayout.addLayout(buttonLayout)
		mainLayout.addWidget(self.qte_printf)
		mainLayout.addWidget(self.qte_singlef)
		mainLayout.addLayout(inputLayout)
		self.setLayout(mainLayout)

	def start_console(self):
		self.isPaused = False

	def pause_console(self):
		self.isPaused = True

	# Lock and unlock the scrollbar
	def togglelLock(self):
		self.isLocked = not self.isLocked
		if self.isLocked:
			self.svgIcon = QIcon(f"{self.icons_dir}/lock_FILL0_wght400_GRAD0_opsz24.svg")
			self.lockButton.setIcon(self.svgIcon)
		else:
			self.svgIcon = QIcon(f"{self.icons_dir}/lock_open_right_FILL0_wght400_GRAD0_opsz24.svg")
			self.lockButton.setIcon(self.svgIcon)
	
	# Reset the tab counter
	def resetCounter(self):
		self.dataCounter = 0
		self.updateTabTitle()
	
	# Update the tab title
	def updateTabTitle(self):
		newTitle = f"{self.winTitle} ({self.dataCounter})" if self.dataCounter > 0 else self.winTitle
		self.mainWindow.updateTabTitle(self, newTitle)

	def isTabInFocus(self):
		currentWidget = self.mainWindow.tabWidget.currentWidget()
		return currentWidget == self

	# Async BLE Functions ------------------------------------------------------------------------------------------

	@qasync.asyncSlot()
	async def send_data(self):
		data = self.qle_send.text()
		if data:
			await self.bleHandler.writeCharacteristic(self.consoleIndex.rx_characteristic.uuid, data.encode())
			self.qle_send.clear()

	# Callbacks -----------------------------------------------------------------------------------------------

	# Callback handle input notification
	def callback_handle_notification(self, sender, data):

		# Redirect the data to the printf text box
		if sender == self.consoleIndex.tx_characteristic.uuid:
			self.update_data(data)
		elif sender == self.consoleIndex.txs_characteristic.uuid:
			self.update_info(data)

	# Window Functions ------------------------------------------------------------------------------------------

	# Update the main text box (printf)
	def update_data(self, data):
		if self.isPaused:
			return

		# Save the current position of the scrollbar
		scrollbar = self.qte_printf.verticalScrollBar()
		current_pos = scrollbar.value()

		# Insert the new data
		self.qte_printf.moveCursor(QTextCursor.End)
		self.qte_printf.insertPlainText(data)

		# Scroll to the bottom if the lock button is pressed
		if self.isLocked:
			scrollbar.setValue(scrollbar.maximum())
		else:
			scrollbar.setValue(current_pos)
		
		# Increment the tab counter
		if not self.isTabInFocus():
			self.dataCounter += 1
			self.updateTabTitle()

		# Log data to file if logging is enabled
		if self.isLogging and self.logFilePath:
			with open(self.logFilePath, 'a') as file:
				file.write(data)

	# Update the info text box (singlef)
	def update_info(self, info):
		self.qte_singlef.setText(info)
	
	# Copy the text from the main text box
	def copy_text(self):
		clipboard = QApplication.clipboard()
		clipboard.setText(self.qte_printf.toPlainText())
	
	# Clear the text from the main text box
	def clear_text(self):
		self.qte_printf.clear()
		self.qte_singlef.clear()
	
	# Save the text from the main text box
	def log_text(self):
		if not self.isLogging:
			if self.select_log_file():
				self.isLogging = True
				self.logButton.setStyleSheet("background-color: darkgreen")
		else:
			self.isLogging = False
			self.logButton.setStyleSheet("")

	def select_log_file(self):
		# Use the native file dialog
		fileName, _ = QFileDialog.getSaveFileName(self, "Select Log File", self.winTitle, "Text Files (*.txt)")
		if fileName:
			self.logFilePath = fileName
			return True
		return False

	# Reimplement the keyPressEvent
	def keyPressEvent(self, event):
		if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
			if self.qle_send.hasFocus():
				self.send_data()