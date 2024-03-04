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

# Socket test for wifi connector dev

import platform
import ipaddress
import socket

from PyQt5.QtCore import QObject, pyqtSignal

import asyncio
import qasync

class WiFiHandler(QObject):
	connectionCompleted = pyqtSignal(bool)
	dataReceived = pyqtSignal(str)
	writeCompleted = pyqtSignal(bool)

	# WiFi Signals
	devicesDiscovered = pyqtSignal(list)
	deviceDisconnected = pyqtSignal(object)
	characteristicRead = pyqtSignal(str, bytes)
	notificationReceived = pyqtSignal(str, str)

	def __init__(self):
		super().__init__()
		self.client_sockets = {}
		self.host_ip = "192.168.1.23"
		self.ports = {"char1": 10001, "char2": 10002}

		self.network = "192.168.1.0/24"
		self.port = 56320

	@qasync.asyncSlot()
	async def check_host(self, ip):
		# Ping parameters as per the OS
		param = '-n' if platform.system().lower() == 'windows' else '-c'
		process = await asyncio.create_subprocess_exec('ping', param, '1', ip, 
													stdout=asyncio.subprocess.DEVNULL,
													stderr=asyncio.subprocess.DEVNULL)
		await process.wait()
		if process.returncode == 0:
			try:
				reader, writer = await asyncio.wait_for(asyncio.open_connection(ip, self.port), timeout=1)
				writer.close()
				await writer.wait_closed()
				return ip
			except (asyncio.TimeoutError, OSError):
				pass
		return None

	@qasync.asyncSlot()
	async def network_scan(self):
		ip_net = ipaddress.ip_network(self.network)
		all_hosts = [str(host) for host in ip_net.hosts()]
		tasks = [self.check_host(ip, self.port) for ip in all_hosts]
		results = await asyncio.gather(*tasks)

		# Generate list of discovered devices
		filtered_ips = [ip for ip in results if ip]

		# Initialize a list to store device information
		devices_info = []

		# Acquire device name and MAC address
		for ip in filtered_ips:
			info_response = await self.send_command(ip, "ARCTIC_COMMAND_GET_DEVICE")
			if "Error:" not in info_response:
				parts = info_response.split(", ")
				name = ""
				mac = ""
				for part in parts:
					if part.startswith("Name:"):
						name = part.split("Name:")[1].strip()
					elif part.startswith("MAC:"):
						mac = part.split("MAC:")[1].strip()
				print(f"Response from {ip}: Name - {name}, MAC - {mac}")

				# Append the device information as a tuple
				devices_info.append((name, mac, ip))
			else:
				print(f"Response from {ip}: {info_response}")
				
		# Emit the devicesDiscovered signal with the formatted devices
		self.devicesDiscovered.emit(devices_info)

	@qasync.asyncSlot()
	async def send_command(self, ip, command):
		try:
			reader, writer = await asyncio.wait_for(asyncio.open_connection(ip, self.port), timeout=3)
			writer.write(command.encode() + b'\n')
			await writer.drain()
			response = await asyncio.wait_for(reader.read(1024), timeout=3)
			writer.close()
			await writer.wait_closed()
			return response.decode().strip()
		except asyncio.TimeoutError:
			return "Error: Command response timed out"
		except Exception as e:
			return f"Error: {e}"

	@qasync.asyncSlot()
	async def connectToServer(self):
		try:
			for char, self.port in self.ports.items():
				client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				await asyncio.wait_for(client_socket.connect((self.host_ip, self.port)), timeout=5)
				self.client_sockets[char] = client_socket
			self.connectionCompleted.emit(True)
		except Exception as e:
			print(f"Connection failed: {e}")
			self.connectionCompleted.emit(False)

	@qasync.asyncSlot()
	async def sendData(self, char, data):
		try:
			client_socket = self.client_sockets.get(char)
			if client_socket:
				await asyncio.wait_for(client_socket.send(data), timeout=5)
				self.writeCompleted.emit(True)
			else:
				print(f"No socket for characteristic: {char}")
				self.writeCompleted.emit(False)
		except Exception as e:
			print(f"Send failed: {e}")
			self.writeCompleted.emit(False)

	@qasync.asyncSlot()
	async def receiveData(self, char):
		try:
			client_socket = self.client_sockets.get(char)
			if client_socket:
				data = await asyncio.wait_for(client_socket.recv(1024), timeout=5)
				self.dataReceived.emit(data.decode())
			else:
				print(f"No socket for characteristic: {char}")
		except Exception as e:
			print(f"Receive failed: {e}")

	@qasync.asyncSlot()
	async def disconnect(self):
		for client_socket in self.client_sockets.values():
			client_socket.close()
		self.client_sockets.clear()