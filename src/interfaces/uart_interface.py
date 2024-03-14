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
import resources.patterns as patterns

# PyQt wrapper type
pyqtWrapperType = type(QObject)


# Metaclass for UARTHandler to resolve metaclass conflict
class UARTHandlerMeta(pyqtWrapperType, ABCMeta):
    pass


# Concrete class for handling UART communication
class UARTHandler(QObject, CommunicationInterface, metaclass=UARTHandlerMeta):
    linkReady = pyqtSignal(bool)
    dataReceived = pyqtSignal(str, str)
    writeReady = pyqtSignal(bool)

    # UART Signals
    scanReady = pyqtSignal(list)
    linkLost = pyqtSignal(object)
    dataStreamError = pyqtSignal(str)
    dataStreamClosed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.device_address = None
        self.baudrate = app_config.globals["uart"]["baudrate"]
        self.port_instance = None
        self.running = False

        # Timer for keepalive
        self.keepalive_timer = QTimer()
        self.keepalive_timer.timeout.connect(self.send_keepalive)
        keepalive_interval = app_config.globals["uart"]["keepalive"]
        self.keepalive_timer.start(keepalive_interval)

        # Activity timer
        self.activity_timer = QTimer()
        self.activity_timer.timeout.connect(self.handle_timeout)
        activity_timeout = app_config.globals["uart"]["act_timeout"]
        self.activity_timer.setInterval(activity_timeout)

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

        self.scanReady.emit(formatted_devices)

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
                dsrdtr=True,  # Prevents MCU Reset when init port
            )
            self.running = True
            self.device_address = device_port

            # Start asynchronous data reading task
            asyncio.create_task(self.read_data_stream())
        except Exception as e:
            print(f"Error opening UART port: {e}")

    # --- Data Digester ---

    async def read_data_stream(self):
        """Reads data from the serial port asynchronously."""
        data_buffer = b""
        while self.running:
            try:
                data = await self.port_instance.read_async(2048)
                if data:
                    # Reset activity timer
                    self.activity_timer.start()

                    # Process the data
                    data_buffer += data
                    while b"\n" in data_buffer:
                        line, data_buffer = data_buffer.split(b"\n", 1)
                        line = line.strip()
                        if line:
                            data = line.decode()
                            if ":" in data:
                                uuid, data = data.split(":", 1)
                                self.process_packet(uuid, data)

            except Exception as e:
                self.dataStreamError.emit(f"Data stream error: {e}")
                break

        self.dataStreamClosed.emit()

    def process_packet(self, uuid, data):
        """Processes the received packet."""

        if "ARCTIC_COMMAND_INTERFACE_READY" in data:
            self.linkReady.emit(True)
            self.activity_timer.start()
            return

        self.dataReceived.emit(uuid, data + "\n")

    # --- Data Transmission ---

    @qasync.asyncSlot()
    async def send_data(self, uuid, data):
        """Sends data to a device."""
        if self.port_instance is not None:
            try:
                print(f"Sending data: {uuid}:{data}")
                data_output = f"{uuid}:{data}\n"
                await self.port_instance.write_async(data_output.encode())
                self.writeReady.emit(True)
            except Exception as e:
                print(f"Error writing data: {e}")
                self.writeReady.emit(False)

    # --- Command Transmission ---

    @qasync.asyncSlot()
    async def send_command(self, command, uuid):
        """Sends a command to a device and returns the response."""
        if self.port_instance is not None:
            try:
                data_output = f"{uuid}:{command}\n"
                print(f"Sending command: {data_output}")
                await self.port_instance.write_async(data_output.encode())
            except asyncio.TimeoutError:
                print("Timeout error")
            except Exception as e:
                print(f"Error writing command: {e}")
        else:
            print("Port not open to send command")

    # --- Keepalive ---

    @qasync.asyncSlot()
    async def send_keepalive(self):
        """Sends a keepalive message to the device."""
        if self.port_instance is not None:
            try:
                await self.port_instance.write_async(b"0")
            except Exception as e:
                print(f"Error sending keepalive: {e}")

    # --- Activity Timeout ---

    def handle_timeout(self):
        """Handles the activity timeout."""
        self.disconnect()

    # --- Disconnection ---

    def disconnect(self):
        """Closes all client sockets and clears the connections."""
        print("Disconnecting UART interface")

        # Clears connection information
        self.device_address = None
        self.running = False
        if self.port_instance and self.port_instance.is_open:
            self.port_instance.close()
        self.keepalive_timer.stop()
        self.activity_timer.stop()

        # Emits the link lost signal
        self.linkLost.emit(self.device_address)

    # --- Destructor ---

    def __del__(self):
        self.disconnect()
