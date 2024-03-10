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

import qasync
from PyQt5.QtCore import QObject, pyqtSignal, QThread, QTimer

# --- Platform-specific imports ---
# For Windows:
import serial.tools.list_ports

# For macOS and Linux:
# import serial.tools.list_ports_posix

from interfaces.com_interface import CommunicationInterface


class UARTHandler(QObject):

    # UART Signals
    devicesDiscovered = pyqtSignal(list)
    connectionCompleted = pyqtSignal(bool)
    deviceDisconnected = pyqtSignal(object)
    dataReceived = pyqtSignal(str)
    writeCompleted = pyqtSignal(bool)

    dataStreamError = pyqtSignal(str)
    dataStreamClosed = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.serial_port = None
        self.baudrate = 230400

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
        self.dataStreamThread = DataStreamThread(device_address, self.baudrate)
        self.dataStreamThread.dataReceived.connect(self.handleDataStream)
        self.dataStreamThread.errorOccurred.connect(self.handleDataStreamError)
        self.dataStreamThread.connectionClosed.connect(
            self.handleDataStreamClosed)
        self.dataStreamThread.start()

        self.serial_port = device_address
        self.connectionCompleted.emit(True)

    def handleDataStream(self, data):
        # Emit the dataReceived signal with appropriate parameters
        # Assuming the data format includes UUID and data separated by ':'
        uuid, data = data.split(':', 1)
        self.dataReceived.emit(uuid, data)

    def handleDataStreamError(self, error_message):
        print(f"Error in data stream: {error_message}")
        self.dataStreamError.emit(error_message)

    def handleDataStreamClosed(self):
        self.dataStreamClosed.emit()

    # --- Data Communication ---

    @qasync.asyncSlot()
    async def send_data(self, uuid, data):
        """Sends data to the connected device."""
        try:
            if self.serial_port and self.serial_port.isOpen():
                self.serial_port.write(
                    uuid.encode() + b':' + data.encode() + b'\n')
                self.writeCompleted.emit(True)
            else:
                self.writeCompleted.emit(False)
        except Exception as e:
            print(f"Write failed: {e}")
            self.writeCompleted.emit(False)

    @qasync.asyncSlot()
    async def send_command(self, command, uuid=""):
        """Sends a command to the connected device."""
        try:
            if self.serial_port and self.serial_port.isOpen():
                self.serial_port.write(
                    uuid.encode() + b':' + command.encode() + b'\n')
                self.writeCompleted.emit(True)
            else:
                self.writeCompleted.emit(False)
        except Exception as e:
            print(f"Write failed: {e}")
            self.writeCompleted.emit(False)

    @qasync.asyncSlot()
    async def get_services(self):
        """Retrieves services information from the connected device."""
        services_response = await self.send_command("ARCTIC_COMMAND_GET_SERVICES")
        print(f"Services response: {services_response}")
        if "Error:" not in services_response:
            return self._parse_services(services_response)
        else:
            print(f"Error in response from {
                  self.serial_port}: {services_response}")
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

    # --- Disconnection ---

    @qasync.asyncSlot()
    async def disconnect(self):
        """Disconnects from the connected device."""
        if self.serial_port and self.serial_port.isOpen():
            self.serial_port.close()
            self.deviceDisconnected.emit(None)


class DataStreamThread(QThread):
    dataReceived = pyqtSignal(str)
    errorOccurred = pyqtSignal(str)
    connectionClosed = pyqtSignal()

    def __init__(self, port, baudrate):  # Adjust baud rate as needed
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.running = True
        self.keepaliveTimer = QTimer()
        self.keepaliveTimer.timeout.connect(self.send_keepalive)
        self.keepaliveTimer.start(400)  # Keepalive interval (ms)

    def run(self):
        try:
            self.serial_port = serial.Serial(self.port, self.baudrate)
            self.errorOccurred.emit("UART connection established")

            while self.running:
                data = self.serial_port.readline().decode()
                if data:
                    print(f"Received: {data.strip()}")
                    # self.dataReceived.emit(data.strip() + "\n")
                else:
                    self.connectionClosed.emit()
                    break

        except serial.SerialException as e:
            self.errorOccurred.emit(f"UART error: {e}")

        finally:
            self.keepaliveTimer.stop()
            if self.serial_port and self.serial_port.isOpen():
                self.serial_port.close()

    def send_keepalive(self):
        if self.serial_port and self.serial_port.isOpen():
            self.serial_port.write(b'\x00')

    def stop(self):
        self.running = False
        self.keepaliveTimer.stop()
        self.quit()  # Ask the thread to quit
        self.wait()  # Wait for the thread to actually finish
