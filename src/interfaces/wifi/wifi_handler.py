# Socket test for wifi connector dev

import socket

from PyQt5.QtCore import QObject, pyqtSignal

import asyncio
import qasync

class WiFiHandler(QObject):
	connectionCompleted = pyqtSignal(bool)
	dataReceived = pyqtSignal(str)
	writeCompleted = pyqtSignal(bool)

	def __init__(self):
		super().__init__()
		self.client_sockets = {}
		self.host_ip = "192.168.1.23"
		self.ports = {"char1": 10001, "char2": 10002}

	@qasync.asyncSlot()
	async def connectToServer(self):
		try:
			for char, port in self.ports.items():
				client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				await asyncio.wait_for(client_socket.connect((self.host_ip, port)), timeout=5)
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