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

import platform
import ipaddress
import socket

from PyQt5.QtCore import QObject, pyqtSignal

import asyncio
import qasync
from interfaces.com_handler import CommunicationInterface

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
		self.device_address = None
		self.network = "192.168.1.0/24"
		self.port = 56320

	# --- Network Scanning ---

	@qasync.asyncSlot()
	async def scan_for_devices(self):
		"""Scans the network for devices and emits the discovered devices."""
		ip_net = ipaddress.ip_network(self.network)
		all_hosts = [str(host) for host in ip_net.hosts()]
		tasks = [self._check_host(ip) for ip in all_hosts]
		results = await asyncio.gather(*tasks)
		filtered_ips = [ip for ip in results if ip]

		devices_info = []
		for ip in filtered_ips:
			self.device_address = ip # Set the device address before sending the command
			info_response = await self.send_command("ARCTIC_COMMAND_GET_DEVICE")
			if "Error:" not in info_response:
				name, mac = self._parse_device_info(info_response)
				devices_info.append((name, mac, ip))
			else:
				print(f"Response from {ip}: {info_response}")

		self.devicesDiscovered.emit(devices_info)

	async def _check_host(self, ip):
		"""Checks if a host is up and running."""
		param = '-n' if platform.system().lower() == 'windows' else '-c'
		process = await asyncio.create_subprocess_exec(
			'ping', param, '1', ip,
			stdout=asyncio.subprocess.DEVNULL,
			stderr=asyncio.subprocess.DEVNULL
		)
		await process.wait()
		if process.returncode == 0:
			try:
				reader, writer = await asyncio.wait_for(
					asyncio.open_connection(ip, self.port), timeout=1
				)
				writer.close()
				await writer.wait_closed()
				return ip
			except (asyncio.TimeoutError, OSError):
				pass
		return None

	def _parse_device_info(self, response):
		"""Parses device information from the response string."""
		response = response.replace("ARCTIC_COMMAND_GET_DEVICE:", "").split(',')
		if len(response) == 2:
			name = response[0].strip()
			mac = response[1].strip()
		else:
			name = ""
			mac = ""
		return name, mac
	
	# --- Connection ---
	
	@qasync.asyncSlot()
	async def connect_to_device(self, device_address):
		"""Connects to a device and starts the data stream."""
		self.device_address = device_address
		self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Use TCP socket
		self.client_socket.setblocking(False)
		try:
			await asyncio.wait_for(asyncio.open_connection(sock=self.client_socket), 5)

			# Check if the connection is open
			if self.client_socket.fileno() != -1:
				self.connectionCompleted.emit(True)
				asyncio.create_task(self.data_stream()) # Schedule the data stream task
			else:
				print("Connection failed: Socket not open")
				self.connectionCompleted.emit(False)
		except Exception as e:
			print(f"Connection failed: {e}")
			self.connectionCompleted.emit(False)

	# --- Communication ---
	
	@qasync.asyncSlot()
	async def send_data(self, uuid, data):
		"""Sends data to a device."""
		try:
			writer = await asyncio.wait_for(
				asyncio.open_connection(self.device_address, self.port), timeout=3
			)
			writer.write(uuid.encode() + b',' + data.encode() + b'\n')
			await writer.drain()
			writer.close()
			await writer.wait_closed()
			self.writeCompleted.emit(True)
		except asyncio.TimeoutError:
			print("Error: Data write timed out")
			self.writeCompleted.emit(False)
		except Exception as e:
			print(f"Error: {e}")
			self.writeCompleted.emit(False)

	@qasync.asyncSlot()
	async def send_command(self, command, uuid=""):
		"""Sends a command to a device and returns the response."""
		try:
			reader, writer = await asyncio.wait_for(
				asyncio.open_connection(self.device_address, self.port), timeout=3
			)
			if uuid:
				uuid = ':' + uuid # Add separator if UUID is provided
			command_output = uuid + command
			writer.write(command_output.encode() + b'\n')
			await writer.drain()
			response = await asyncio.wait_for(reader.read(2048), timeout=3)
			writer.close()
			await writer.wait_closed()
			return response.decode().strip()
		except asyncio.TimeoutError:
			return "Error: Command response timed out"
		except Exception as e:
			return f"Error: {e}"

	@qasync.asyncSlot()
	async def get_services(self):
		"""Retrieves services information from the connected device."""
		services_response = await self.send_command("ARCTIC_COMMAND_GET_SERVICES")
		if "Error:" not in services_response:
			return self._parse_services(services_response)
		else:
			print(f"Error in response from {self.device_address}: {services_response}")
			return []

	def _parse_services(self, response):
		"""Parses services information from the response string."""
		modules = response.replace("ARCTIC_COMMAND_GET_SERVICES:", "").split(':')
		parsed_services = []
		for module in modules:
			parts = module.split(',')
			if len(parts) >= 4:
				module_info = {
					"name": parts[0],
					"uuidtx": parts[1],
					"uuidtxs": parts[2],
					"uuidrx": parts[3]
				}
				parsed_services.append(module_info)
		return parsed_services

	# --- Data Stream ---

	@qasync.asyncSlot()
	async def data_stream(self):
		"""Handles data stream from a connected device."""
		try:
			# is this necessary?
			client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			client_socket.setblocking(False)
			await asyncio.wait_for(asyncio.open_connection(sock=client_socket), 5)
			self.connectionCompleted.emit(True)
			# is this necessary?

			data_buffer = b""
			while True:
				try:
					data = await asyncio.wait_for(client_socket.recv(1024), 5)
					if data:
						data_buffer += data
						while b'\n' in data_buffer:
							line, data_buffer = data_buffer.split(b'\n', 1)
							line = line.strip()
							if line:
								self.dataReceived.emit(line.decode())
					else:
						print("Connection closed by the server")
						break
				except asyncio.TimeoutError:
					pass  # Continue receiving data
				except Exception as e:
					print(f"Socket error: {e}")
					break
		except Exception as e:
			print(f"Connection failed: {e}")
			self.connectionCompleted.emit(False)
		finally:
			client_socket.close()

	@qasync.asyncSlot()
	async def disconnect(self):
		"""Closes all client sockets and clears the connections."""
		self.deviceDisconnected.emit(None)
		if self.client_socket:
			self.client_socket.close()
			self.client_socket = None