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

import qasync
from PyQt5.QtCore import QObject, pyqtSignal

# --- Platform-specific imports ---
# For Windows:
import serial.tools.list_ports

# For macOS and Linux:
# import serial.tools.list_ports_posix

from interfaces.com_handler import CommunicationInterface

class UARTHandler(QObject):

	# UART Signals
	devicesDiscovered = pyqtSignal(list)
	connectionCompleted = pyqtSignal(bool)
	deviceDisconnected = pyqtSignal(object)
	dataReceived = pyqtSignal(str)
	writeCompleted = pyqtSignal(bool)

	def __init__(self):
		super().__init__()
		self.serial_port = None

	# --- Device Discovery ---

	@qasync.asyncSlot()
	async def scan_for_devices(self):
		"""Scans for available devices on the interface."""
		# --- Platform-specific device discovery ---
		# Windows:
		ports = serial.tools.list_ports.comports()

		# macOS and Linux:
		# ports = serial.tools.list_ports_posix.comports()

		formatted_devices = []
		for port, desc, hwid in ports:
			formatted_devices.append((desc, port))

		self.devicesDiscovered.emit(formatted_devices)

	# --- Connection ---

	@qasync.asyncSlot()
	async def connect_to_device(self, device_address):
		"""Connects to a device on the interface."""
		try:
			# --- Platform-specific connection logic ---
			# You might need to adjust parameters like baud rate, parity, etc.
			self.serial_port = serial.Serial(device_address, baudrate=115200)

			if self.serial_port.isOpen():
				self.connectionCompleted.emit(True)
				asyncio.create_task(self.receiveData())  # Start receiving data
			else:
				self.connectionCompleted.emit(False)
		except Exception as e:
			print(f"Connection failed: {e}")
			self.connectionCompleted.emit(False)

	# --- Data Communication ---

	@qasync.asyncSlot()
	async def send_data(self, uuid, data, response=False):
		"""Sends data to the connected device."""
		try:
			if self.serial_port and self.serial_port.isOpen():
				self.serial_port.write(data.encode())
				self.writeCompleted.emit(True)
			else:
				self.writeCompleted.emit(False)
		except Exception as e:
			print(f"Write failed: {e}")
			self.writeCompleted.emit(False)

	@qasync.asyncSlot()
	async def send_command(self, command, uuid=""):
		"""Sends a command to the connected device."""
		await self.send_data(uuid, command)

	async def receive_data(self):
		"""Receives data from the connected device."""
		while self.serial_port and self.serial_port.isOpen():
			try:
				data = self.serial_port.readline().decode()
				if data:
					self.dataReceived.emit(data.strip())
			except Exception as e:
				print(f"Read error: {e}")
				break

	# --- Disconnection ---

	@qasync.asyncSlot()
	async def disconnect(self):
		"""Disconnects from the connected device."""
		if self.serial_port and self.serial_port.isOpen():
			self.serial_port.close()
			self.deviceDisconnected.emit(None)