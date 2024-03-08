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

import asyncio
import traceback

import qasync
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QPushButton, QListWidget, QHBoxLayout
from PyQt5.QtGui import QFont

from interfaces.com_handler import CommunicationInterface
from interfaces.ble_handler import BLEHandler # DELETE
from interfaces.wifi_handler import WiFiHandler # DELETE
from interfaces.uart_handler import UARTHandler
from gui.console_window import ConsoleWindow
from gui.updater_window import UpdaterWindow
from resources.indexer import ConsoleIndex, BackgroundIndex, OTAIndex
from resources.patterns import *
		
class UARTConnectionWindow(QWidget):
	signal_closing_complete = pyqtSignal()

	def __init__(self, main_window, stream_interface: CommunicationInterface, title):
		super().__init__()

		self.main_window = main_window  # MainWindow Reference
		self.stream_interface = stream_interface  # UART Handler Reference
		self.win_title = title  # Original title of the tab

		# Add this tab to the main window
		self.main_window.add_connection_tab(self, self.win_title)
		self.main_window.signal_window_close.connect(self.process_close_task)

		# Async UART Signals
		self.stream_interface.devicesDiscovered.connect(self.callback_update_scan_list)
		self.stream_interface.connectionCompleted.connect(self.callback_connection_complete)
		self.stream_interface.deviceDisconnected.connect(self.callback_disconnected)
		self.stream_interface.dataReceived.connect(self.callback_handle_data_received)
		self.stream_interface.writeCompleted.connect(self.callback_handle_write_complete)

		# Async Events from the device
		self.get_name_event = asyncio.Event()  # May not be needed for UART

		# Globals
		self.console_ref = {}  # Console windows reference (for window reuse)
		self.last_device_address = None
		self.is_closing = False

		self.setup_layout()

	# GUI Functions ------------------------------------------------------------------------------------------
		
	# Layout and Widgets
	def setup_layout(self):
		connect_button = QPushButton("Connect")
		connect_button.clicked.connect(self.uart_connect) # Use uart_connect

		disconnect_button = QPushButton("Disconnect")
		disconnect_button.clicked.connect(self.uart_clear_connection)

		self.scan_device_list = QListWidget()
		self.scan_device_list.setFont(QFont("Inconsolata"))
		self.scan_device_list.setSelectionMode(QListWidget.SingleSelection)
		self.scan_device_list.itemDoubleClicked.connect(self.uart_connect) # Use uart_connect

		scan_button = QPushButton("Scan UART Devices") # Adjust label
		scan_button.clicked.connect(self.uart_scan) # Use uart_scan

		exit_button = QPushButton("Exit")
		exit_button.clicked.connect(self.exitApplication)

		# Layout for buttons
		buttons_layout = QHBoxLayout()
		buttons_layout.addWidget(connect_button)
		buttons_layout.addWidget(disconnect_button)

		connection_layout = QVBoxLayout()
		connection_layout.addLayout(buttons_layout)
		connection_layout.addWidget(self.scan_device_list)
		connection_layout.addWidget(scan_button)
		connection_layout.addWidget(exit_button)
		self.setLayout(connection_layout)

	# Async UART Functions ------------------------------------------------------------------------------------------


	@qasync.asyncSlot()
	async def uart_scan(self):
		self.main_window.debug_info("Scanning for UART devices ...")
		await self.stream_interface.scan_for_devices()
		self.main_window.debug_info("Scanning complete")

	@qasync.asyncSlot()
	async def uart_connect(self, reconnect=False):
		selected_items = self.scan_device_list.selectedItems()
		if not selected_items:
			self.main_window.debug_info("No device selected")
			return

		device_port = selected_items[0].text().split(" - ")[1]
		self.last_device_address = device_port  # Adjust for UART

		if not reconnect:
			self.main_window.debug_info(f"Connecting to {device_port} ...")

		await self.stream_interface.connect_to_device(device_port)

	# --- Reconnection ---

	@qasync.asyncSlot()
	async def uart_reconnect(self):  # Renamed for clarity
		max_recon_retries = 5
		retries_counter = 1

		while retries_counter <= max_recon_retries:
			self.connection_event.clear()
			self.main_window.debug_info(
				f"Attempting reconnection to {self.last_device_address}. Retry: {retries_counter}/{max_recon_retries}"
			)
			await self.uart_connect(
				self.last_device_address, reconnect=True
			)  # Use uart_connect
			if self.connection_event.is_set():
				# Reconnection successful
				break
			else:
				retries_counter += 1

		if retries_counter > max_recon_retries:
			self.main_window.debug_info(
				f"Reconnection to {self.last_device_address} failed"
			)

	# --- Stop UART ---

	@qasync.asyncSlot()
	async def uart_stop(self):  # Renamed for clarity
		self.main_window.debug_info("Disconnecting UART device ...")
		await self.stream_interface.disconnect()

	# --- Clear connection ---

	@qasync.asyncSlot()
	async def uart_clear_connection(self): # Keep the name for consistency
		self.main_window.debug_info("Clearing UART connection ...")
		self.last_device_address = None
		if not self.is_closing:
			asyncio.ensure_future(self.process_close_task(close_window=False))

	# Callbacks -----------------------------------------------------------------------------------------------

	def callback_update_scan_list(self, devices):
		self.scan_device_list.clear()
		for name, address in devices:
			self.scan_device_list.addItem(f"{name} - {address}")

	def callback_connection_complete(self, connected):
		if connected:
			self.connection_event.set()
			self.main_window.debug_info(f"Connected to {self.last_device_address}")
			# You might not need to register services for UART
		else:
			self.connection_event.clear()

	def callback_handle_char_read(self, uuid, value):  # May not be needed for UART
		pass

	def callback_disconnected(self, client):
		self.main_window.debug_info(f"UART device {client.address} disconnected")

		# Manual disconnect are not handled
		if self.last_device_address:
			self.uart_reconnect()  # Use uart_reconnect

	def callback_handle_data_received(self, data):
		# Create a new console window if needed
		if not self.console_ref:
			self.new_console_window("UART Console", None)  # Adjust UUID if needed

		# Redirect data to the console window
		self.console_ref[None].update_data(data)  # Adjust UUID if needed

	def callback_handle_write_complete(self, success):
		if not success:
			self.main_window.debug_info("UART write failed")
		
	# Window Functions ------------------------------------------------------------------------------------------

	# Initialize a new updater window (OTA)
	def new_updater_window(self, name, uuid):
		pass

	# --- Initialize a new console window ---
	def new_console_window(self, name, uuid):
		# Check if the console window is already open
		if uuid in self.console_ref:
			console = self.console_ref[uuid]
		else:
			# Console window is not open, create a new one
			console = ConsoleWindow(self.main_window, self.stream_interface, name, None)  # Adjust UUID if needed
			self.console_ref[uuid] = console

			self.main_window.add_console_tab(console, name)

	# --- Stop Functions ---

	def stop_consoles(self):
		for uuid, console in self.console_ref.items():
			console.close()

	@qasync.asyncSlot()
	async def process_close_task(self, close_window=True):
		self.last_device_address = None  # Clear the last device address
		if not self.is_closing:
			self.is_closing = True
			await self.uart_stop()  # Use uart_stop
			self.stop_consoles()
			if close_window:
				self.signal_closing_complete.emit()  # Emit the signal after all tasks are completed

	# --- Exit triggered from "exit" button ---

	def exitApplication(self):
		self.main_window.exit_ble()