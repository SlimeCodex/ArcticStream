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
from abc import ABCMeta
import serial.tools.list_ports

import qasync
import aioserial
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

import resources.config as app_config
from interfaces.com_interface import CommunicationInterface

# PyQt wrapper type
pyqtWrapperType = type(QObject)


# Metaclass for UARTHandler to resolve metaclass conflict
class UARTHandlerMeta(pyqtWrapperType, ABCMeta):
    pass


# Concrete class for handling UART communication
class UARTHandler(QObject, CommunicationInterface, metaclass=UARTHandlerMeta):
    connectionCompleted = pyqtSignal(bool)
    dataReceived = pyqtSignal(str, str)
    writeCompleted = pyqtSignal(bool)

    # UART Signals
    devicesDiscovered = pyqtSignal(list)
    deviceDisconnected = pyqtSignal(object)
    dataStreamError = pyqtSignal(str)
    dataStreamClosed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.device_address = None
        self.baudrate = app_config.globals["uart"]["baudrate"]
        self.port_instance = None

        self.run_digester = False
        self.running = False

        # Timer for keepalive sent
        self.keepalive_timer = QTimer()
        self.keepalive_timer.timeout.connect(self.send_keepalive)
        self.keepalive_timer.start(400)

    # --- Network Scanning ---

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
    async def connect_to_device(self, device_port):
        """Connects to a device and starts the data stream."""
        try:
            self.port_instance = aioserial.AioSerial(
                port=device_port,
                baudrate=self.baudrate,
                parity=aioserial.PARITY_NONE,
                stopbits=aioserial.STOPBITS_ONE,
                bytesize=aioserial.EIGHTBITS,
                timeout=0.1,
            )
            self.running = True
            self.device_address = device_port
            self.connectionCompleted.emit(True)

            # Start asynchronous data reading task
            asyncio.create_task(self.read_data_stream())
        except Exception as e:
            print(f"Error opening UART port: {e}")

    # --- Data Digester ---

    async def read_data_stream(self):
        """Reads data from the serial port asynchronously."""
        data_buffer = b""
        while self.running:
            if not self.run_digester:
                await asyncio.sleep(0.1)
            try:
                data = await self.port_instance.read_until_async(b'\n')
                if data:
                    data_buffer += data
                    while b"\n" in data_buffer:
                        line, data_buffer = data_buffer.split(b"\n", 1)
                        line = line.strip()
                        if line:
                            data = line.decode()
                            # Check if the data contains a colon before unpacking
                            if ":" in data:
                                uuid, data = data.split(":", 1)
                                self.dataReceived.emit(uuid, data + "\n")
                            else:
                                # Ignore this line or handle it differently
                                print(f"Ignoring malformed data: {data}")
                else:
                    self.running = False
            except Exception as e:
                self.dataStreamError.emit(f"Data stream error: {e}")
                break

        self.dataStreamClosed.emit()

    # --- Data Transmission ---

    @qasync.asyncSlot()
    async def send_data(self, uuid, data):
        """Sends data to a device."""
        if self.port_instance is not None:
            try:
                print(f"Sending data: {uuid}:{data}")
                await self.port_instance.write_async(uuid.encode() + b":" + data.encode() + b"\n")
                self.writeCompleted.emit(True)
            except Exception as e:
                print(f"Error writing data: {e}")
                self.writeCompleted.emit(False)

    # --- Command Transmission ---

    @qasync.asyncSlot()
    async def send_command(self, command, uuid=""):
        """Sends a command to a device and returns the response."""
        if self.port_instance is not None:
            try:
                if uuid:
                    uuid = uuid + ":"
                command_output = uuid + command

                self.disable_data_digester()
                await self.port_instance.write_async(command_output.encode() + b"\n")

                # Wait for the exact response
                expected_response_prefix = f"{command}:"
                response = await self.read_until_prefix(expected_response_prefix)

                self.enable_data_digester()
                return response.decode().strip()

            except asyncio.TimeoutError:
                return "Error: Command response timed out"
            except Exception as e:
                return f"Error: {e}"
        else:
            return "Error: Not connected to a device"

    async def read_until_prefix(self, prefix):
        """Reads data from the serial port until the specified prefix is found."""
        data_buffer = b""
        while self.running:
            try:
                data = await self.port_instance.read_async(2048)
                if data:
                    data_buffer += data
                    if data_buffer.startswith(prefix.encode()):
                        return data_buffer
            except Exception as e:
                print(f"Error reading response: {e}")
                break

    # --- Services ---

    @qasync.asyncSlot()
    async def get_services(self):
        """Retrieves services information from the connected device."""
        response = await self.send_command("ARCTIC_COMMAND_GET_SERVICES")
        if "Error:" not in response:
            return self._parse_services(response)
        else:
            print(f"Error in response from {
                self.device_address}: {response}")
            return []

    def _parse_services(self, response):
        """Parses services information from the response string."""
        modules = response.replace(
            "ARCTIC_COMMAND_GET_SERVICES:", "").split(":")
        parsed_services = []
        for module in modules:
            parts = module.split(",")
            if len(parts) >= 5:
                module_info = {
                    "name": parts[0],
                    "ats": parts[1],
                    "txm": parts[2],
                    "txs": parts[3],
                    "rxm": parts[4],
                }
                parsed_services.append(module_info)
        return parsed_services

    # --- Keepalive ---

    @qasync.asyncSlot()
    async def send_keepalive(self):
        """Sends a keepalive message to the device."""
        if self.port_instance is not None:
            try:
                await self.port_instance.write_async(b"\n")
            except Exception as e:
                print(f"Error sending keepalive: {e}")

    # --- Data Transmission Control ---

    def enable_data_digester(self):
        """Starts the data digester."""
        self.run_digester = True

    def disable_data_digester(self):
        """Stops the data digester."""
        self.run_digester = False

    # --- Disconnection ---

    @qasync.asyncSlot()
    async def disconnect(self):
        """Closes all client sockets and clears the connections."""
        self.deviceDisconnected.emit(self.device_address)
        self.device_address = None
        self.running = False
        if self.port_instance and self.port_instance.is_open:
            self.port_instance.close()

    # --- Destructor ---

    def __del__(self):
        if self.port_instance and self.port_instance.is_open:
            self.port_instance.close()
