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

import time
import errno
import select
import socket
import platform
import ipaddress
from abc import ABCMeta

import qasync
import asyncio
from PyQt5.QtCore import QObject, pyqtSignal, QThread

import resources.config as app_config
from interfaces.com_interface import CommunicationInterface

# PyQt wrapper type
pyqtWrapperType = type(QObject)


# Metaclass for WiFiHandler to resolve metaclass conflict
class WiFiHandlerMeta(pyqtWrapperType, ABCMeta):
    pass


class WiFiHandler(QObject, CommunicationInterface, metaclass=WiFiHandlerMeta):
    connectionCompleted = pyqtSignal(bool)
    dataReceived = pyqtSignal(str, str)
    writeCompleted = pyqtSignal(bool)

    # WiFi Signals
    devicesDiscovered = pyqtSignal(list)
    deviceDisconnected = pyqtSignal(object)
    dataStreamError = pyqtSignal(str)
    dataStreamClosed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.device_address = None
        self.network = app_config.globals["wifi"]["network"]
        self.port_uplink = app_config.globals["wifi"]["port_uplink"]
        self.port_downlink = app_config.globals["wifi"]["port_downlink"]

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
            self.device_address = ip
            response = await self.send_command("ARCTIC_COMMAND_GET_DEVICE")
            if "Error:" not in response:
                name, mac = self._parse_device_info(response)
                devices_info.append((name, mac, ip))
            else:
                print(f"Response from {ip}: {response}")

        self.devicesDiscovered.emit(devices_info)

    async def _check_host(self, ip):
        """Checks if a host is up and running."""
        param = "-n" if platform.system().lower() == "windows" else "-c"
        process = await asyncio.create_subprocess_exec(
            "ping",
            param,
            "1",
            ip,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await process.wait()
        if process.returncode == 0:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(ip, self.port_uplink), timeout=1
                )
                writer.close()
                await writer.wait_closed()
                return ip
            except (asyncio.TimeoutError, OSError):
                pass
        return None

    def _parse_device_info(self, response):
        """Parses device information from the response string."""
        response = response.replace(
            "ARCTIC_COMMAND_GET_DEVICE:", "").split(",")
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
        self.dataStreamThread = DataStreamThread(
            device_address, self.port_uplink)
        self.dataStreamThread.dataReceived.connect(self.handleDataStream)
        self.dataStreamThread.errorOccurred.connect(self.handleDataStreamError)
        self.dataStreamThread.connectionClosed.connect(
            self.handleDataStreamClosed)
        self.dataStreamThread.start()

        self.device_address = device_address
        self.connectionCompleted.emit(True)

    def handleDataStream(self, data):
        # Emit the dataReceived signal with appropriate parameters
        # Assuming the data format includes UUID and data separated by ':'
        uuid, data = data.split(":", 1)
        self.dataReceived.emit(uuid, data)

    def handleDataStreamError(self, error_message):
        print(f"Error in data stream: {error_message}")
        self.dataStreamError.emit(error_message)

    def handleDataStreamClosed(self):
        self.dataStreamClosed.emit()

    def stopDataStream(self):
        if self.dataStreamThread:
            self.dataStreamThread.stop()  # Properly signal the thread to stop

    # --- Communication ---

    @qasync.asyncSlot()
    async def send_data(self, uuid, data):
        """Sends data to a device."""
        try:
            # Unpack reader and writer from open_connection
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(
                    self.device_address, self.port_downlink),
                timeout=3,
            )
            print(f"Sending data to {self.device_address}: {uuid} - {data}")
            writer.write(uuid.encode() + b":" + data.encode() + b"\n")
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
                asyncio.open_connection(
                    self.device_address, self.port_downlink),
                timeout=3,
            )
            if uuid:
                uuid = ":" + uuid  # Add separator if UUID is provided
            command_output = uuid + command
            writer.write(command_output.encode() + b"\n")
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
        response = await self.send_command("ARCTIC_COMMAND_GET_SERVICES")
        if "Error:" not in response:
            return self._parse_services(response)
        else:
            print(f"Error in response from {self.device_address}: {response}")
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

    # --- Device Management ---

    @qasync.asyncSlot()
    async def disconnect(self):
        """Closes all client sockets and clears the connections."""
        self.deviceDisconnected.emit(self.device_address)
        self.device_address = None
        self.stopDataStream()

    def __del__(self):
        self.stopDataStream()


class DataStreamThread(QThread):
    dataReceived = pyqtSignal(str)
    errorOccurred = pyqtSignal(str)
    connectionClosed = pyqtSignal()

    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.running = True

    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setblocking(False)

        try:
            s.connect((self.host, self.port))
        except socket.error as err:
            if err.errno != errno.WSAEWOULDBLOCK:
                self.errorOccurred.emit(f"Connection failed: {err}")
                return

        # Wait for the socket to be ready
        _, ready_to_write, _ = select.select([], [s], [], 5)

        if ready_to_write:
            self.errorOccurred.emit("Connection established")

            data_buffer = b""
            while self.running:
                try:
                    data = s.recv(2048)
                    if data:
                        data_buffer += data
                        while b"\n" in data_buffer:
                            line, data_buffer = data_buffer.split(b"\n", 1)
                            line = line.strip()
                            if line:
                                self.dataReceived.emit(line.decode() + "\n")
                    else:
                        self.connectionClosed.emit()
                        break
                except socket.error as e:
                    if e.errno != errno.WSAEWOULDBLOCK:
                        self.errorOccurred.emit(f"Socket error: {e}")
                        break
                    else:
                        time.sleep(0.001)
                        continue

    def stop(self):
        self.running = False
        self.quit()  # Ask the thread to quit
        self.wait()  # Wait for the thread to actually finish
