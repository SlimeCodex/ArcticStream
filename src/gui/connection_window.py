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
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QPushButton, QListWidget

from bluetooth.ble_handler import BLEHandler
from gui.console_window import ConsoleWindow
from gui.updater_window import UpdaterWindow
from resources.indexer import ConsoleIndex
from resources.patterns import *
from resources.styles import *
		
class ConnectionWindow(QWidget):
	signal_closing_complete = pyqtSignal()
	
	def __init__(self, main_window, ble_handler: BLEHandler, title):
		self.connection_event = asyncio.Event()
		self.reconnection_event = asyncio.Event()

		super().__init__()
		self.main_window = main_window # MainWindow Reference
		self.ble_handler = ble_handler # BLE Reference
		self.win_title = title  # Original title of the tab

		# Add this tab to the main window
		self.main_window.add_connection_tab(self, self.win_title)

		# Connect the mainWindow's signal_window_close to a local slot
		self.main_window.signal_window_close.connect(self.process_close_task)

		# Async BLE Signals
		self.ble_handler.devicesDiscovered.connect(self.callback_update_scan_list)
		self.ble_handler.connectionCompleted.connect(self.callback_connection_complete)
		self.ble_handler.deviceDisconnected.connect(self.callback_disconnected)
		self.ble_handler.characteristicRead.connect(self.callback_handle_char_read)

		# Globals
		self.console_services = {} # Console services reference (for service reuse)
		self.console_ref = {} # Console windows reference (for window reuse)
		self.last_device_address = None
		self.is_closing = False

		self.setup_layout()

	# GUI Functions ------------------------------------------------------------------------------------------
		
	# Layout and Widgets
	def setup_layout(self):
		scan_button = QPushButton("Scan Bluetooth")
		scan_button.clicked.connect(self.ble_scan)

		self.scan_device_list = QListWidget()
		self.scan_device_list.setSelectionMode(QListWidget.SingleSelection)
		self.scan_device_list.itemDoubleClicked.connect(self.ble_connect)

		connect_button = QPushButton("Connect")
		connect_button.clicked.connect(self.ble_connect)

		exit_button = QPushButton("Exit")
		exit_button.clicked.connect(self.exitApplication)

		connection_layout = QVBoxLayout()
		connection_layout.addWidget(scan_button)
		connection_layout.addWidget(self.scan_device_list)
		connection_layout.addWidget(connect_button)
		connection_layout.addWidget(exit_button)
		self.setLayout(connection_layout)

	# Async BLE Functions ------------------------------------------------------------------------------------------

	# BLE Scanning
	@qasync.asyncSlot()
	async def ble_scan(self):
		self.main_window.debug_info("Scanning for devices ...")
		await self.ble_handler.scanForDevices()
		self.main_window.debug_info("Scanning complete")

	# BLE Connection
	@qasync.asyncSlot()
	async def ble_connect(self, reconnect=False):
		selected_items = self.scan_device_list.selectedItems()
		if not selected_items:
			self.main_window.debug_info("No device selected")
			return
		
		device_address = selected_items[0].text().split(" - ")[1]
		self.last_device_address = device_address

		if not reconnect:
			self.main_window.debug_info(f"Connecting to {device_address} ...")
			
		await self.ble_handler.connectToDevice(device_address)

	# BLE Setting up notifications and retrieving name characteristic
	@qasync.asyncSlot()
	async def setup_consoles(self):
		for service_uuid, ble_service in self.console_services.items():
			# Start notifications and read name characteristics asynchronously
			if ble_service.tx_characteristic:
				await self.ble_handler.startNotifications(ble_service.tx_characteristic)
			if ble_service.txs_characteristic:
				await self.ble_handler.startNotifications(ble_service.txs_characteristic)
			if ble_service.name_characteristic:
				await self.ble_handler.readCharacteristic(ble_service.name_characteristic)

	# Reconnection
	@qasync.asyncSlot()
	async def ble_reconnect(self):
		max_recon_retries = 5
		retries_counter = 1

		while retries_counter <= max_recon_retries:
			self.connection_event.clear()
			self.main_window.debug_info(f"Attempting reconnection to {self.last_device_address}. Retry: {retries_counter}/{max_recon_retries}")
			await self.ble_connect(self.last_device_address, reconnect=True) # Will wait 5s before timeout
			if self.connection_event.is_set():
				# Reconnection successful
				break
			else:
				retries_counter += 1

		if retries_counter > max_recon_retries:
			self.main_window.debug_info(f"Reconnection to {self.last_device_address} failed")

	# Stop BLE
	@qasync.asyncSlot()
	async def ble_stop(self):
		self.main_window.debug_info("Disconnecting ...")
		await self.ble_handler.disconnect()

	# Callbacks -----------------------------------------------------------------------------------------------

	# Callback update device list
	def callback_update_scan_list(self, devices):
		self.scan_device_list.clear()
		for name, address in devices:
			self.scan_device_list.addItem(f"{name} - {address}")

	# Callback connection success
	def callback_connection_complete(self, connected):
		if connected:
			self.connection_event.set()
			
			self.main_window.debug_info(f"Connected to {self.last_device_address}")

			registered_services = self.ble_handler.getServices()
			for service in registered_services:
				service_uuid = str(service.uuid)

				# Ignore services that are not console services
				if not service_console_pattern.match(service_uuid):
					continue
				
				# Check if the service is already registered and reuse it
				if service_uuid in self.console_services:
					ble_service = self.console_services[service_uuid]
				else:
					ble_service = ConsoleIndex(service)
					self.console_services[service_uuid] = ble_service

				# Update or register characteristics
				for characteristic in service.characteristics:
					char_uuid = str(characteristic.uuid)

					# Check and update or set characteristics
					if char_tx_pattern.match(char_uuid):
						ble_service.tx_characteristic = characteristic
					elif char_txs_pattern.match(char_uuid):
						ble_service.txs_characteristic = characteristic
					elif char_rx_pattern.match(char_uuid):
						ble_service.rx_characteristic = characteristic
					elif char_name_pattern.match(char_uuid):
						ble_service.name_characteristic = characteristic

					self.console_services[str(service.uuid)] = ble_service
			
			# Setup notification and read name characteristic
			self.setup_consoles()
		else:
			self.connection_event.clear()
	
	# Callback handle name characteristic read
	def callback_handle_char_read(self, uuid, value):
		try:
			# Register the name characteristic
			name = value.decode("utf-8")
			for service_uuid, ble_service in self.console_services.items():
				if ble_service.name_characteristic and str(ble_service.name_characteristic.uuid) == uuid:
					if (service_ota_pattern.match(service_uuid)):
						self.new_updater_window(name, uuid)
					else:
						self.new_console_window(name, uuid)
					ble_service.name = name
					break

		except Exception as e:
			print(f"Error in handling console window with UUID {uuid}: {e}")
			traceback.print_exc()
	
	# Callback device disconnected
	def callback_disconnected(self, client):
		self.main_window.debug_info(f"Device {client.address} disconnected")

		# Manual disconnect are not handled
		if self.last_device_address:
			self.ble_reconnect()

	# Window Functions ------------------------------------------------------------------------------------------

	# Get ConsoleIndex instance from name characteristic UUID
	def find_and_update_console_service(self, uuid, name):
		for service in self.console_services.values():
			if service.name_characteristic and str(service.name_characteristic.uuid) == uuid:
				service.name = name
				return service
		return None
	
	# Initialize a new console window
	def new_console_window(self, name, uuid):
		ble_service = self.find_and_update_console_service(uuid, name)
		if not ble_service:
			print(f"No matching service found for UUID: {uuid}")
			return

		# Check if the console window is already open
		if uuid in self.console_ref:
			console = self.console_ref[uuid]
		else:
			# Console window is not open, create a new one
			console = ConsoleWindow(self.main_window, self.ble_handler, name, ble_service)
			self.console_ref[uuid] = console

			self.main_window.add_console_tab(console, name)

	# Initialize a new updater window (OTA)
	def new_updater_window(self, name, uuid):
		ble_service = self.find_and_update_console_service(uuid, name)
		if not ble_service:
			print(f"No matching service found for UUID: {uuid}")
			return
		
		# Check if the console window is already open
		if uuid in self.console_ref:
			console = self.console_ref[uuid]
		else:
			# Console window is not open, create a new one
			console = UpdaterWindow(self.main_window, self.ble_handler, name, ble_service)
			self.console_ref[uuid] = console

			self.main_window.add_updater_tab(console, name)

	# Stop Functions ------------------------------------------------------------------------------------------

	# Stop the remaining consoles
	def stop_consoles(self):
		for uuid, console in self.console_ref.items():
			console.close()
	
	# Stop the BLE Handler
	@qasync.asyncSlot()
	async def process_close_task(self):
		self.last_device_address = None # Clear the last device address
		if not self.is_closing:
			self.is_closing = True
			await self.ble_stop()
			self.stop_consoles()
			self.signal_closing_complete.emit()  # Emit the signal after all tasks are completed

	# Exit triggered from "exit" button
	def exitApplication(self):
		self.last_device_address = None # Clear the last device address
		if not self.is_closing:
			asyncio.ensure_future(self.process_close_task())