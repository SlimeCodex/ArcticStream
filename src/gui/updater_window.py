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
from PyQt5.QtWidgets import QLineEdit, QPushButton, QTextEdit, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QProgressBar
from PyQt5.QtGui import QTextCursor, QIcon

from bluetooth.ble_handler import BLEHandler
from resources.indexer import ConsoleIndex
from resources.styles import *

from datetime import datetime
from pathlib import Path
import hashlib
import asyncio
import qasync
import time
import os

class UpdaterWindow(QWidget):
	def __init__(self, main_window, ble_handler: BLEHandler, title, console_index: ConsoleIndex):
		super().__init__()
		self.mainWindow = main_window # MainWindow Reference
		self.bleHandler = ble_handler # BLE Reference
		self.winTitle = title # Original title of the tab
		self.consoleIndex = console_index # Console information

		print("UpdaterWindow: Initializing ...")
		print(f"ConsoleWindow: {self.consoleIndex.name}")
		print(f"ConsoleWindow: {self.consoleIndex.service.uuid}")
		print(f"ConsoleWindow: {self.consoleIndex.tx_characteristic.uuid}")
		print(f"ConsoleWindow: {self.consoleIndex.txs_characteristic.uuid}")
		print(f"ConsoleWindow: {self.consoleIndex.rx_characteristic.uuid}")
		print(f"ConsoleWindow: {self.consoleIndex.name_characteristic.uuid}")
		print("------------------------------------------")

		# Async BLE Signals
		self.bleHandler.notificationReceived.connect(self.callback_handle_notification)
		self.bleHandler.deviceDisconnected.connect(self.callback_disconnected)

		# Async Events from the device
		self.ready_event = asyncio.Event()
		self.ack_event = asyncio.Event()
		self.error_event = asyncio.Event()
		self.success_event = asyncio.Event()
		self.disconnect_event = asyncio.Event()
		self.stop_event = asyncio.Event()

		# Window usability flags
		self.setAcceptDrops(True)

		# Globals
		self.ota_running = False
		self.dataCounter = 0
		self.filePath = None
		self.chunkSize = 500
		self.start_time = 0
		self.elapsed_str = "00:00:00"
		self.icons_dir = self.mainWindow.icon_path()

		self.setup_layout()
	
	# GUI Functions ------------------------------------------------------------------------------------------

	# Layout and Widgets
	def setup_layout(self):

		# Start and Stop buttons
		self.startButton = QPushButton("Start", self)
		self.startButton.clicked.connect(self.start_ota)
		self.stopButton = QPushButton("Stop", self)
		self.stopButton.clicked.connect(self.stop_ota)
		self.clearButton = QPushButton("Clear", self)
		self.clearButton.clicked.connect(self.clear_text)
		self.copyButton = QPushButton("Reload", self)
		self.copyButton.clicked.connect(self.reload_file)

		# Folder button
		self.folderButton = QPushButton(self)
		self.folderButton.setFixedSize(25, 25)
		self.folderButton.clicked.connect(self.setPath)
		self.svgIcon = QIcon(f"{self.icons_dir}/drive_folder_upload_FILL0_wght400_GRAD0_opsz24.svg")
		self.folderButton.setIcon(self.svgIcon)

		# Main text area for accumulating text
		self.qte_ota_printf = QTextEdit(self)
		self.qte_ota_printf.setStyleSheet(dark_theme_qte_printf)
		self.qte_ota_printf.setReadOnly(True)
		
		# Placeholder text
		self.placeholderLineEdit = QLineEdit("Drag your firmware here or select your firmware path", self)
		self.placeholderLineEdit.setReadOnly(True)
		self.placeholderLineEdit.setAlignment(Qt.AlignCenter)
		self.placeholderLineEdit.setStyleSheet(dark_theme_qle_ota_placeholder)
		self.placeholderLineEdit.setGeometry(self.qte_ota_printf.geometry())  # Adjust geometry to match qte_printf
		self.placeholderLineEdit.setAttribute(Qt.WA_TransparentForMouseEvents)  # Make it non-interactive
		self.updatePlaceholderVisibility(True)  # Initially visible

		# Single line text area for displaying info
		self.qte_ota_singlef = QLineEdit(self)
		self.qte_ota_singlef.setStyleSheet(dark_theme_qle_singlef)
		self.qte_ota_singlef.setReadOnly(True)

		# Layout for Start and Stop buttons
		buttonLayout = QHBoxLayout()
		buttonLayout.addWidget(self.startButton)
		buttonLayout.addWidget(self.stopButton)
		buttonLayout.addWidget(self.clearButton)
		buttonLayout.addWidget(self.copyButton)
		buttonLayout.addWidget(self.folderButton)

		# Create the progress bar
		self.progressBar = QProgressBar(self)
		self.progressBar.setStyleSheet(dark_theme_qpb_load_bar)
		self.progressBar.setMaximum(100)
		self.progressBar.setValue(0)

		# Update the main layout
		mainLayout = QVBoxLayout()
		mainLayout.addLayout(buttonLayout)
		mainLayout.addWidget(self.qte_ota_printf)
		mainLayout.addWidget(self.qte_ota_singlef)
		mainLayout.addWidget(self.progressBar)
		self.setLayout(mainLayout)

		self.adjustPlaceholderGeometry()

	def adjustPlaceholderGeometry(self):
		self.placeholderLineEdit.setGeometry(self.qte_ota_printf.geometry())

	def resizeEvent(self, event):
		self.adjustPlaceholderGeometry()
		super().resizeEvent(event)

	def updatePlaceholderVisibility(self, visible):
		self.placeholderLineEdit.setVisible(visible)
		
	def dragEnterEvent(self, event):
		if event.mimeData().hasUrls():
			event.acceptProposedAction()
			self.highlightTextBox(True)

	def dragLeaveEvent(self, event):
		self.highlightTextBox(False)

	def dropEvent(self, event):
		self.highlightTextBox(False)
		
		urls = event.mimeData().urls()
		if urls and len(urls) > 0:
			filePath = str(urls[0].toLocalFile())
			if filePath.endswith('.bin'):
				self.filePath = filePath
				self.update_info(f"Loaded file: {self.filePath}")
				self.extractFileInfo(self.filePath)
			else:
				self.update_info("Not a .bin file")

	def highlightTextBox(self, highlight):
		if highlight:
			self.qte_ota_printf.setStyleSheet(dark_theme_qte_ota_highlight)  # Pale background
		else:
			self.qte_ota_printf.setStyleSheet(dark_theme_qte_printf)  # Original style

	# Async BLE Functions ------------------------------------------------------------------------------------------
	
	@qasync.asyncSlot()
	async def start_ota(self):

		self.start_time = datetime.now()
		self.ota_running = True

		self.ready_event.clear()
		self.ack_event.clear()
		self.error_event.clear()
		self.success_event.clear()
		self.stop_event.clear()

		# Reset the progress bar style
		self.progressBar.setStyleSheet(dark_theme_qpb_load_bar)

		if self.filePath is not None:
			totalSize = os.path.getsize(self.filePath)
			
			# Send the firmware size to the target device
			await self.bleHandler.writeCharacteristic(self.consoleIndex.rx_characteristic.uuid, str(f"{totalSize}").encode())

			# Wait for the target device to be ready, with a timeout
			try:
				await asyncio.wait_for(self.ready_event.wait(), timeout=5)
			except asyncio.TimeoutError:
				print("Timeout waiting for device to be ready. OTA update aborted.")
				self.ota_running = False
				return

			transferred = 0
			MAX_RETRIES = 3

			try:
				with open(self.filePath, 'rb') as file:
					print(f"Sending file: {self.filePath}")

					while self.ota_running:

						dataChunk = file.read(self.chunkSize)
						if not dataChunk:
							print("File is empty, aborting OTA update")
							break

						retries = 0
						while retries < MAX_RETRIES:
							self.ack_event.clear()  # Reset the event for the next chunk
							await self.bleHandler.writeCharacteristic(self.consoleIndex.rx_characteristic.uuid, dataChunk)

							# Wrap coroutines in tasks
							ack_task = asyncio.create_task(self.ack_event.wait())
							stop_task = asyncio.create_task(self.stop_event.wait())

							try:
								done, pending = await asyncio.wait(
									[ack_task, stop_task], 
									timeout=0.5,  # 500ms timeout
									return_when=asyncio.FIRST_COMPLETED
								)

								# Check if stop event was set
								if self.stop_event.is_set():
									if self.success_event.is_set(): # Check if success received
										self.update_info(f"[{self.elapsed_str}] OTA Loading completed")

									elif self.error_event.is_set(): # Check if error received
										self.progressBar.setStyleSheet(dark_theme_qpb_load_bar_fail)
										self.update_info(f"[{self.elapsed_str}] OTA Error received")

									elif self.disconnect_event.is_set():
										self.progressBar.setStyleSheet(dark_theme_qpb_load_bar_fail)
										self.update_info(f"[{self.elapsed_str}] OTA Device disconnected")

									else:
										self.progressBar.setStyleSheet(dark_theme_qpb_load_bar_fail)
										self.update_info(f"[{self.elapsed_str}] OTA Loading aborted")
										
									self.ota_running = False
									break

								# Check if ACK was received
								if self.ack_event.is_set():
									self.ack_event.clear()
									break  # Exit retry loop

							except asyncio.TimeoutError:
								print(f"ACK not received for chunk, retrying ({retries + 1}/{MAX_RETRIES})")
								retries += 1

						if self.ota_running == False:
							break

						if retries == MAX_RETRIES:
							print("Maximum retries reached, stopping OTA")
							self.ota_running = False
							break

						transferred += len(dataChunk)
						progress = int((transferred / totalSize) * 100)
						
						self.progressBar.setValue(progress)
						elapsed_time = datetime.now() - self.start_time
						elapsed_time_seconds = elapsed_time.total_seconds()
						kbytes_per_second = (transferred / elapsed_time_seconds) / 1024
						self.elapsed_str = str(elapsed_time).split('.')[0]  # Convert to HH:MM:SS format
						self.update_info(f"[{self.elapsed_str}] OTA Loading Progress: {progress}% ({transferred}/{totalSize} bytes, {kbytes_per_second:.2f} kb/s)")

			except IOError as e:
				print(f"Error reading file: {e}")
		else:
			print("No file selected.")

	@qasync.asyncSlot()
	async def stop_ota(self):
		self.stop_event.set()

	# Callbacks -----------------------------------------------------------------------------------------------

	# Callback handle input notification
	def callback_handle_notification(self, sender, data):

		# Redirect the data to the printf text box
		if sender == self.consoleIndex.tx_characteristic.uuid:
			pass # No device printf for OTA
		elif sender == self.consoleIndex.txs_characteristic.uuid:
			self.update_info(data) # singlef used for ACKs

	def callback_disconnected(self, client):
		if self.ota_running:
			self.stop_event.set()
			self.disconnect_event.set()

	# Window Functions ------------------------------------------------------------------------------------------

	# Update the main text box (printf)
	def update_data(self, data):
		self.updatePlaceholderVisibility(False)
		self.qte_ota_printf.clear()
		self.qte_ota_printf.moveCursor(QTextCursor.End)
		self.qte_ota_printf.insertPlainText(data)
		self.qte_ota_printf.moveCursor(QTextCursor.End)

	# Update the info text box (singlef)
	def update_info(self, info):

		# ACKs coming from the device
		if "READY" in info:
			self.ready_event.set()
			#print("Device ready")
		elif "ACK" in info:
			self.ack_event.set()
			#print("Device ack")
		elif "ERROR" in info:
			self.error_event.set()
			self.stop_event.set()
			#print("Device error")
		elif "DONE" in info:
			self.success_event.set()
			self.stop_event.set()
			#print("Device done")
		elif "TIMEOUT" in info:
			self.error_event.set()
			self.stop_event.set()
			#print("Device timeout")
		else: # Info coming from the program
			self.qte_ota_singlef.setText(info)

	# Reload the file
	def reload_file(self):
		if self.filePath:
			self.extractFileInfo(self.filePath)
		else:
			self.update_info("No file loaded")

	# Path folder button
	def setPath(self):
		options = QFileDialog.Options()
		filePath, _ = QFileDialog.getOpenFileName(self, "Select a .bin file", "", "Bin Files (*.bin)", options=options)
		if filePath:
			self.filePath = filePath
			self.extractFileInfo(self.filePath)

	# Extract file information and update the text box
	def extractFileInfo(self, filePath):
		fileName = os.path.basename(filePath)
		fileSize = os.path.getsize(filePath)
		fileLocation = os.path.dirname(filePath)
		lastModifiedTime = time.ctime(os.path.getmtime(filePath))
		creationTime = time.ctime(os.path.getctime(filePath))
		fileHash = self.calculateFileHash(filePath)

		# Update the information
		otaInformation = (
			f"OTA Information:\n\n"
			f"- File Name: {fileName}\n"
			f"- File Size: {fileSize} bytes\n"
			f"- Last Modified: {lastModifiedTime}\n\n"
			f"- File Location: {fileLocation}\n"
			f"- Creation Time: {creationTime}\n\n"
			f"- File Hash: {fileHash}\n"
		)

		# Update the text box
		self.update_data(otaInformation)

	# Reset the window to its initial state
	def clear_text(self):
		self.filePath = None
		self.qte_ota_printf.clear()
		self.qte_ota_singlef.clear()
		self.updatePlaceholderVisibility(True)
		self.progressBar.setValue(0)

	# Calculate the hash of a file
	def calculateFileHash(self, filePath, hashType='md5'):
		hashFunc = getattr(hashlib, hashType)()
		with open(filePath, 'rb') as file:
			for chunk in iter(lambda: file.read(4096), b""):
				hashFunc.update(chunk)
		return hashFunc.hexdigest()