#
# This file is part of ArcticTerminal Library.
# Copyright (C) 2023 Alejandro Nicolini
# 
# ArcticTerminal is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# ArcticTerminal is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with ArcticTerminal. If not, see <https://www.gnu.org/licenses/>.
#

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QPushButton, QListWidget

from gui.console_window import ConsoleWindow
from gui.updater_window import UpdaterWindow
from bluetooth.ble_handler import BLEHandler
from resources.indexer import ConsoleIndex
from resources.patterns import *
from resources.styles import *

import traceback
import asyncio
import qasync
		
class ConnectionWindow(QWidget):
	closingCompleted = pyqtSignal()
	
	def __init__(self, main_window, ble_handler: BLEHandler, title):
		self.connection_event = asyncio.Event()
		self.reconnection_event = asyncio.Event()

		super().__init__()
		self.mainWindow = main_window # MainWindow Reference
		self.bleHandler = ble_handler # BLE Reference
		self.winTitle = title  # Original title of the tab

		# Add this tab to the main window
		self.mainWindow.add_connection_tab(self, self.winTitle)

		# Connect the mainWindow's windowCloseEvent to a local slot
		self.mainWindow.windowCloseEvent.connect(self.initiateCloseTasks)

		# Async BLE Signals
		self.bleHandler.devicesDiscovered.connect(self.callback_update_scan_list)
		self.bleHandler.connectionCompleted.connect(self.callback_connection_complete)
		self.bleHandler.deviceDisconnected.connect(self.callback_disconnected)
		self.bleHandler.characteristicRead.connect(self.callback_handle_char_read)

		# Globals
		self.console_services = {} # Console services reference (for service reuse)
		self.console_ref = {} # Console windows reference (for window reuse)
		self.last_device_address = None
		self.is_closing = False

		self.setup_layout()

	# GUI Functions ------------------------------------------------------------------------------------------
		
	# Layout and Widgets
	def setup_layout(self):
		self.scanButton = QPushButton("Scan Bluetooth")
		self.scanButton.clicked.connect(self.scanBluetooth)

		self.deviceList = QListWidget()
		self.deviceList.setSelectionMode(QListWidget.SingleSelection)
		self.deviceList.itemDoubleClicked.connect(self.connectDevice)

		self.connectButton = QPushButton("Connect")
		self.connectButton.clicked.connect(self.connectDevice)

		self.exitButton = QPushButton("Exit")
		self.exitButton.clicked.connect(self.exitApplication)

		layout = QVBoxLayout()
		layout.addWidget(self.scanButton)
		layout.addWidget(self.deviceList)
		layout.addWidget(self.connectButton)
		layout.addWidget(self.exitButton)
		self.setLayout(layout)

	# Async BLE Functions ------------------------------------------------------------------------------------------

	# BLE Scanning
	@qasync.asyncSlot()
	async def scanBluetooth(self):
		self.mainWindow.debug_info("Scanning for devices ...")
		await self.bleHandler.scanForDevices()
		self.mainWindow.debug_info("Scanning complete")

	# BLE Connection
	@qasync.asyncSlot()
	async def connectDevice(self, reconnect=False):
		selected_items = self.deviceList.selectedItems()
		if not selected_items:
			self.mainWindow.debug_info("No device selected")
			return
		
		device_address = selected_items[0].text().split(" - ")[1]
		self.last_device_address = device_address

		if not reconnect:
			self.mainWindow.debug_info(f"Connecting to {device_address} ...")
			
		await self.bleHandler.connectToDevice(device_address)

	# BLE Setting up notifications and retrieving name characteristic
	@qasync.asyncSlot()
	async def setup_consoles(self):
		for service_uuid, ble_service in self.console_services.items():
			# Start notifications and read name characteristics asynchronously
			if ble_service.tx_characteristic:
				await self.bleHandler.startNotifications(ble_service.tx_characteristic)
			if ble_service.txs_characteristic:
				await self.bleHandler.startNotifications(ble_service.txs_characteristic)
			if ble_service.name_characteristic:
				await self.bleHandler.readCharacteristic(ble_service.name_characteristic)

	# Reconnection
	@qasync.asyncSlot()
	async def attemptReconnection(self):
		MAX_RETRIES = 5
		reconnection_retries = 1

		while reconnection_retries <= MAX_RETRIES:
			self.connection_event.clear()
			self.mainWindow.debug_info(f"Attempting reconnection to {self.last_device_address}. Retry: {reconnection_retries}/{MAX_RETRIES}")
			await self.connectDevice(self.last_device_address, reconnect=True) # Will wait 5s before timeout
			if self.connection_event.is_set():
				# Reconnection successful
				break
			else:
				reconnection_retries += 1

		if reconnection_retries > MAX_RETRIES:
			self.mainWindow.debug_info(f"Reconnection to {self.last_device_address} failed")

	# Stop BLE
	@qasync.asyncSlot()
	async def stopBluetooth(self):
		self.mainWindow.debug_info("Disconnecting ...")
		await self.bleHandler.disconnect()

	# Callbacks -----------------------------------------------------------------------------------------------

	# Callback update device list
	def callback_update_scan_list(self, devices):
		self.deviceList.clear()
		for name, address in devices:
			self.deviceList.addItem(f"{name} - {address}")

	# Callback connection success
	def callback_connection_complete(self, connected):
		if connected:
			self.connection_event.set()
			
			self.mainWindow.debug_info(f"Connected to {self.last_device_address}")

			registered_services = self.bleHandler.getServices()
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
						self.newUpdaterWindow(name, uuid)
					else:
						self.newConsoleWindow(name, uuid)
					ble_service.name = name
					break

		except Exception as e:
			print(f"Error in handling console window with UUID {uuid}: {e}")
			traceback.print_exc()
	
	# Callback device disconnected
	def callback_disconnected(self, client):
		self.mainWindow.debug_info(f"Device {client.address} disconnected")

		# Manual disconnect are not handled
		if self.last_device_address:
			self.attemptReconnection()

	# Window Functions ------------------------------------------------------------------------------------------

	# Get ConsoleIndex instance from name characteristic UUID
	def find_and_update_console_service(self, uuid, name):
		for service in self.console_services.values():
			if service.name_characteristic and str(service.name_characteristic.uuid) == uuid:
				service.name = name
				return service
		return None
	
	# Initialize a new console window
	def newConsoleWindow(self, name, uuid):
		ble_service = self.find_and_update_console_service(uuid, name)
		if not ble_service:
			print(f"No matching service found for UUID: {uuid}")
			return

		# Check if the console window is already open
		if uuid in self.console_ref:
			console = self.console_ref[uuid]
		else:
			# Console window is not open, create a new one
			console = ConsoleWindow(self.mainWindow, self.bleHandler, name, ble_service)
			self.console_ref[uuid] = console

			self.mainWindow.add_console_tab(console, name)

	# Initialize a new updater window (OTA)
	def newUpdaterWindow(self, name, uuid):
		ble_service = self.find_and_update_console_service(uuid, name)
		if not ble_service:
			print(f"No matching service found for UUID: {uuid}")
			return
		
		# Check if the console window is already open
		if uuid in self.console_ref:
			console = self.console_ref[uuid]
		else:
			# Console window is not open, create a new one
			console = UpdaterWindow(self.mainWindow, self.bleHandler, name, ble_service)
			self.console_ref[uuid] = console

			self.mainWindow.add_updater_tab(console, name)

	# Stop Functions ------------------------------------------------------------------------------------------

	# Stop the remaining consoles
	def stopConsoles(self):
		for uuid, console in self.console_ref.items():
			console.close()
	
	# Stop the BLE Handler
	@qasync.asyncSlot()
	async def initiateCloseTasks(self):
		self.last_device_address = None # Clear the last device address
		if not self.is_closing:
			self.is_closing = True
			await self.stopBluetooth()
			self.stopConsoles()
			self.closingCompleted.emit()  # Emit the signal after all tasks are completed

	# Exit triggered from "exit" button
	def exitApplication(self):
		self.last_device_address = None # Clear the last device address
		if not self.is_closing:
			asyncio.ensure_future(self.initiateCloseTasks())