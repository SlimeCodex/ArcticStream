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

# The WiFi interface is used to communicate with devices using the WiFi protocol.
# It is a subclass of the CommunicationInterface class and uses the asyncio library
# to handle the asynchronous communication.

# The WiFi interface uses a network socket to communicate with the device
# and emits signals to notify the user interface of the connection status and data received.

import errno
import select
import socket
import platform
import ipaddress
import subprocess
from abc import ABCMeta

import qasync
import asyncio
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

import resources.config as app_config
from interfaces.base_interface import CommunicationInterface
import resources.patterns as patterns

# PyQt wrapper type
pyqtWrapperType = type(QObject)


# Metaclass for WiFiHandler to resolve metaclass conflict
class WiFiHandlerMeta(pyqtWrapperType, ABCMeta):
    pass


class WiFiHandler(QObject, CommunicationInterface, metaclass=WiFiHandlerMeta):
    # WiFi Signals
    scanReady = pyqtSignal(list)  # List of available devices
    linkReady = pyqtSignal(bool)  # Device is ready to receive commands
    linkLost = pyqtSignal(str)  # Device is not responding
    dataReceived = pyqtSignal(str, str)  # Data received from the device
    writeReady = pyqtSignal(bool)  # Data was sent successfully
    taskHalted = pyqtSignal()  # Interface task was halted

    # Data stream subprocess signals
    dataStreamError = pyqtSignal(str)  # Data stream error
    dataStreamClosed = pyqtSignal()  # Data stream was closed

    def __init__(self):
        super().__init__()
        self.device_address = None
        self.socket_instance = None
        self.network = app_config.globals["wifi"]["network"]
        self.port_uplink = app_config.globals["wifi"]["port_uplink"]
        self.port_downlink = app_config.globals["wifi"]["port_downlink"]
        self.scape_sequence = app_config.globals["wifi"]["scape_sequence"]
        self.keepalive_sequence = app_config.globals["wifi"]["keepalive_sequence"]
        self.receive_timeout = app_config.globals["uart"]["receive_timeout"]
        self.uplink_chunk_size = app_config.globals["wifi"]["uplink_chunk_size"]
        self.running = False
        self.activity_timer = None

    # Network scanning method
    async def scan_for_devices(self, network=None):
        """Scans the network for devices and emits the discovered devices."""

        # Update the network if a new one is provided
        if network is not None:
            self.network = network
        
        # Check all potential valid IP addresses in the network
        ip_net = ipaddress.ip_network(self.network)
        all_hosts = [str(host) for host in ip_net.hosts()]
        tasks = [self._check_host(ip) for ip in all_hosts]
        results = await asyncio.gather(*tasks)
        filtered_ips = [ip for ip in results if ip]

        # Get device information from the retrieved IPs
        # Unlike the read data stream, this method is synchronous
        # Scan is replied from the same port is requested
        for ip in filtered_ips:
            self.device_address = ip
            scan_response = await self.send_data(
                patterns.UUID_WIFI_BACKEND_RX, "ARCTIC_COMMAND_GET_DEVICE", scan=True
            )
            devices_info = []
            if scan_response is not None:
                if "Error:" not in scan_response:
                    name, mac = self._parse_device_info(scan_response)
                    devices_info.append((name, mac, ip))
                else:
                    print(f"Response from {ip}: {scan_response}")
            self.scanReady.emit(devices_info)

    # Helper method to check if a host is up and running
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
            creationflags=subprocess.CREATE_NO_WINDOW,
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

    # Device information parsing method
    def _parse_device_info(self, response):
        """Parses device information from the response string."""
        response = response.replace(patterns.UUID_WIFI_BACKEND_TX + ":", "")
        response = response.replace("ARCTIC_COMMAND_GET_DEVICE:", "")
        response = response.split(",")
        if len(response) == 2:
            name = response[0].strip()
            mac = response[1].strip()
        else:
            name = ""
            mac = ""
        return name, mac

    # Connect to device
    async def connect_to_device(self, device_address):
        """Connects to a device and starts the data stream."""
        self.device_address = device_address
        self.running = True

        # Activity timer
        self.activity_timer = QTimer()
        self.activity_timer.timeout.connect(self.handle_timeout)
        activity_timeout = app_config.globals["wifi"]["act_timeout"]
        self.activity_timer.setInterval(activity_timeout)

        # Start asynchronous data reading task
        asyncio.create_task(self.read_data_stream())

    # Data reading task
    async def read_data_stream(self):
        """Reads data from the serial port asynchronously."""
        self.socket_instance = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_instance.setblocking(False)

        try:
            self.socket_instance.connect((self.device_address, self.port_uplink))
        except socket.error as err:
            if err.errno != errno.WSAEWOULDBLOCK:
                print(f"Socket error: {err}")
                self.linkReady.emit(False)
                return

        # Wait for the socket to be ready
        _, ready_to_write, _ = select.select([], [self.socket_instance], [], 5)
        if ready_to_write:
            data_buffer = b""
            while self.running:
                try:
                    data = self.socket_instance.recv(self.uplink_chunk_size)
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
                except socket.error as e:
                    if e.errno != errno.WSAEWOULDBLOCK:
                        print(f"Socket error: {e}")
                        break
                    else:
                        await asyncio.sleep(self.receive_timeout)
                        continue
        self.dataStreamClosed.emit()

    # Process received packet as uuid:data
    def process_packet(self, uuid, data):
        """Processes the received packet."""

        # Device is ready to receive commands
        if "ARCTIC_COMMAND_INTERFACE_READY" in data:
            self.linkReady.emit(True)
            return

        self.dataReceived.emit(uuid, data)

    # --- Communication ---

    async def send_data(self, uuid, data, scan=False, encoded=False):
        """Sends data to a device."""
        try:
            # Unpack reader and writer from open_connection
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.device_address, self.port_downlink),
                timeout=3,
            )
            writer.write(uuid.encode() + b":" + (data.encode() if not encoded else data) + b"\n")
            await writer.drain()
            if scan:  # If scanning, wait for the response
                response = await asyncio.wait_for(reader.read(2048), timeout=3)
            writer.close()
            await writer.wait_closed()
            if scan:  # If scanning, return the response
                return response.decode().strip()
            self.writeReady.emit(True)
        except asyncio.TimeoutError:
            print("Error: Data write timed out")
            self.writeReady.emit(False)
            return None
        except Exception as e:
            print(f"Error: {e}")
            self.writeReady.emit(False)
            return None
        return None
    
    # Get the type of the interface
    def get_type(self):
        return "wifi"

    # Timeout handler for activity with the device
    def handle_timeout(self):
        """Handles the activity timeout."""
        self.linkLost.emit(self.device_address)

    # Finalize the connection
    @qasync.asyncSlot()
    async def disconnect(self):
        """Closes all client sockets and clears the connections."""

        # Client already disconnected
        if self.device_address is None:
            return
        
        # Send the disconnect signal
        self.linkLost.emit(self.device_address)

        # Clears connection information
        self.device_address = None
        self.running = False

        # Closes the socket
        if self.socket_instance and self.socket_instance.fileno() != -1:
            self.socket_instance.close()
            self.socket_instance = None

        # Stops the activity timer
        if self.activity_timer and self.activity_timer.isActive():
            self.activity_timer.stop()

        # Emits the task halted signal
        self.taskHalted.emit()
