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

from bleak import BleakScanner, BleakClient
from PyQt5.QtCore import QObject, pyqtSignal

import qasync
from interfaces.com_handler import CommunicationInterface

class BLEHandler(QObject):

	# BLE Signals
	devicesDiscovered = pyqtSignal(list)
	connectionCompleted = pyqtSignal(bool)
	deviceDisconnected = pyqtSignal(object)
	characteristicRead = pyqtSignal(str, bytes)
	notificationReceived = pyqtSignal(str, str)
	writeCompleted = pyqtSignal(bool)

	def __init__(self):
		super().__init__()
		self.client = None # Internal client reference
		self.disconnect_event = asyncio.Event()

	# Scan for devices
	@qasync.asyncSlot()
	async def scan_for_devices(self):
		"""Scans for available devices on the interface."""
		devices = await BleakScanner.discover()
		formatted_devices = [(device.name, device.address) for device in devices]
		self.devicesDiscovered.emit(formatted_devices)

	# Connect to device
	@qasync.asyncSlot()
	async def connect_to_device(self, device_address):
		"""Connects to a device on the interface."""
		self.client = BleakClient(device_address, disconnected_callback=self.on_disconnect, timeout=5)
		try:
			connected = await self.client.connect()
			if connected:
				self.services = self.client.services # Store services
				self.disconnect_event.clear()
				self.connectionCompleted.emit(True)
			else:
				self.connectionCompleted.emit(False)
		except Exception as e:
			print(f"Connection failed: {e}")
			self.connectionCompleted.emit(False)

	# Setup notifications for characteristic
	@qasync.asyncSlot()
	async def start_notifications(self, characteristic):
		"""Starts notifications for a characteristic."""
		if "notify" in characteristic.properties:
			await self.client.start_notify(characteristic, self.notification_callback)

	# Read data from characteristic
	@qasync.asyncSlot()
	async def read_characteristic(self, characteristic):
		"""Reads data from a characteristic."""
		value = await self.client.read_gatt_char(characteristic)
		self.characteristicRead.emit(str(characteristic.uuid), bytes(value))

	# Write data to characteristic
	@qasync.asyncSlot()
	async def send_data(self, characteristic, data, response=False):
		"""Sends data to the specified characteristic."""
		try:
			if self.disconnect_event.is_set():
				print("Operation aborted: Device disconnected.")
				self.writeCompleted.emit(False)
			else:
				await self.client.write_gatt_char(characteristic, data, response)
				self.writeCompleted.emit(True)
		except Exception as e:
			print(f"Write failed: {e}")
			self.writeCompleted.emit(False)

	# Callback for notifications
	def notification_callback(self, sender, data):
		"""Callback for notifications. Emits a signal with the received data."""
		sender_info = sender.uuid if hasattr(sender, 'uuid') else str(sender)
		decoded_data = data.decode('utf-8', errors='replace') if isinstance(data, (bytearray, bytes)) else str(data)
		self.notificationReceived.emit(sender_info, decoded_data)

	# Callback disconnected
	def on_disconnect(self, client):
		"""Callback for disconnection. Emits a signal with the disconnected client."""
		self.disconnect_event.set()
		self.deviceDisconnected.emit(client)

	# Manual retrieve of services
	def get_services(self):
		"""Retrieves services information from the connected device (if applicable)."""
		return self.services if hasattr(self, 'services') else None

	# Manual disconnect
	@qasync.asyncSlot()
	async def disconnect(self):
		"""Disconnects from the connected device."""
		if self.client and self.client.is_connected:
			self.disconnect_event.set()
			await self.client.disconnect()