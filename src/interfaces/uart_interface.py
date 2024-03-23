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

# The UART interface is used to communicate with devices using a serial connection
# It is a subclass of the CommunicationInterface class and uses the aioserial library
# to handle the asynchronous serial communication.

# The UART interface uses a keepalive and activity timeout mechanism to ensure the device is
# still connected and responding. It also emits signals to notify the user interface
# of the connection status and data received.

import asyncio
import platform
from abc import ABCMeta
import serial.tools.list_ports

import qasync
import aioserial
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

import resources.config as app_config
from interfaces.base_interface import CommunicationInterface

# PyQt wrapper type
pyqtWrapperType = type(QObject)


# Metaclass for UARTHandler to resolve metaclass conflict
class UARTHandlerMeta(pyqtWrapperType, ABCMeta):
    pass


# Concrete class for handling UART communication
class UARTHandler(QObject, CommunicationInterface, metaclass=UARTHandlerMeta):
    # UART Signals
    scanReady = pyqtSignal(list)  # List of available devices
    linkReady = pyqtSignal(bool)  # Device is ready to receive commands
    linkReadyCOM = pyqtSignal(bool)  # COM port connected
    linkLost = pyqtSignal(str)  # Device is not responding
    writeReady = pyqtSignal(bool)  # Data was sent successfully
    dataReceived = pyqtSignal(str, str)  # Data received from the device
    taskHalted = pyqtSignal()  # Interface task was halted

    # Data stream subprocess signals
    dataStreamError = pyqtSignal(str)  # Data stream error
    dataStreamClosed = pyqtSignal()  # Data stream was closed

    def __init__(self):
        super().__init__()
        self.device_address = None
        self.baudrate = app_config.globals["uart"]["baudrate"]
        self.scape_sequence = app_config.globals["uart"]["scape_sequence"]
        self.keepalive_sequence = app_config.globals["uart"]["keepalive_sequence"]
        self.receive_timeout = app_config.globals["uart"]["receive_timeout"]
        self.uplink_chunk_size = app_config.globals["wifi"]["uplink_chunk_size"]
        self.port_instance = None
        self.running = False

    # Network scanning method
    async def scan_for_devices(self):
        """Scans for available devices on the interface."""

        # Get available ports and format them
        if platform.system() == "Windows":
            ports = serial.tools.list_ports.comports()
        else:
            ports = serial.tools.list_ports_posix.comports()

        formatted_devices = []
        for port, desc, hwid in ports:
            formatted_devices.append((desc, port))

        self.scanReady.emit(formatted_devices)

    # Device connection method
    async def connect_to_device(self, device_port):
        """Connects to a device and starts the data stream."""
        try:
            self.port_instance = aioserial.AioSerial(
                port=device_port,
                baudrate=self.baudrate,
                parity=aioserial.PARITY_NONE,
                stopbits=aioserial.STOPBITS_ONE,
                bytesize=aioserial.EIGHTBITS,
                timeout=self.receive_timeout,
            )
            self.device_address = device_port
            self.running = True

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

            # Start asynchronous data reading task
            asyncio.create_task(self.read_data_stream())
            self.linkReadyCOM.emit(True)

        except Exception as e:
            print(f"UART Interface: Error connecting to device: {e}")
            self.linkReadyCOM.emit(False)

    # Data reading task
    async def read_data_stream(self):
        """Reads data from the serial port asynchronously."""
        data_buffer = b""
        while self.running:
            try:
                data = await self.port_instance.read_async(self.uplink_chunk_size)
                if data:
                    # Reset activity timer
                    self.activity_timer.start()

                    # Remove keepalive sequence
                    if self.keepalive_sequence in data:
                        data = data.replace(self.keepalive_sequence, b"")

                    # Process the data
                    data_buffer += data
                    while self.scape_sequence in data_buffer:
                        packet, _, data_buffer = data_buffer.partition(self.scape_sequence)
                        if packet:
                            decoded_packet = packet.decode()
                            if ":" in decoded_packet:
                                uuid, data = decoded_packet.split(":", 1)
                                self.process_packet(uuid, data)

            except Exception as e:
                self.dataStreamError.emit(f"Data stream error: {e}")
                break

        self.dataStreamClosed.emit()

    # Process received packet as uuid:data
    def process_packet(self, uuid, data):
        """Processes the received packet."""

        # Device is ready to receive commands
        if "ARCTIC_COMMAND_INTERFACE_READY" in data:
            self.linkReady.emit(True)
            return

        self.dataReceived.emit(uuid, data)

    # Send data to the device
    async def send_data(self, uuid, data, encoded=False):
        """Sends data to a device."""
        if self.port_instance is not None:
            try:
                await self.port_instance.write_async(uuid.encode() + b":" + (data.encode() if not encoded else data) + b"\n")
                self.writeReady.emit(True)
            except asyncio.TimeoutError:
                print("Timeout error")
                self.writeReady.emit(False)
            except Exception as e:
                print(f"Error writing command: {e}")
                self.writeReady.emit(False)
        else:
            print("Port not open to send command")
            self.writeReady.emit(False)
    
    # Get the type of the interface
    def get_type(self):
        return "uart"

    # Send simple byte keepalive message to the device
    @qasync.asyncSlot()
    async def send_keepalive(self):
        """Sends a keepalive message to the device."""
        if self.port_instance is not None:
            try:
                await self.port_instance.write_async(b"0")
            except Exception as e:
                print(f"Error sending keepalive: {e}")

    # Timeout handler for activity with the device
    def handle_timeout(self):
        """Handles the activity timeout."""
        self.linkLost.emit(self.device_address)

    # Finalize the connection
    async def disconnect(self):
        """Disconnects from the connected device."""

        # Client already disconnected
        if self.device_address is None:
            return
        
        # Send the disconnect signal
        self.linkLost.emit(self.device_address)

        # Clears connection information
        self.device_address = None
        self.running = False

        # Closes the port
        if self.port_instance and self.port_instance.is_open:
            self.port_instance.close()

        # Stops the timers
        if self.keepalive_timer and self.keepalive_timer.isActive():
            self.keepalive_timer.stop()
        if self.activity_timer and self.activity_timer.isActive():
            self.activity_timer.stop()

        # Emits the link lost signal
        self.taskHalted.emit()
