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

# The BLE interface is used to handle communication with Bluetooth Low Energy devices.
# It uses the Bleak library to handle the communication with the devices.

# The BLE interface uses the bleak callbacks to handle notifications and disconnections.

import asyncio
from abc import ABCMeta

import qasync
from bleak import BleakScanner, BleakClient
from PyQt5.QtCore import QObject, pyqtSignal

import resources.config as app_config
from interfaces.com_interface import CommunicationInterface

# PyQt wrapper type
pyqtWrapperType = type(QObject)


# Metaclass for BLEHandler to resolve metaclass conflict
class BLEHandlerMeta(pyqtWrapperType, ABCMeta):
    pass


# Concrete class for handling BLE communication
class BLEHandler(QObject, CommunicationInterface, metaclass=BLEHandlerMeta):
    # BLE Signals
    scanReady = pyqtSignal(list)  # List of available devices
    linkReady = pyqtSignal(bool)  # Device is ready to receive commands
    linkLost = pyqtSignal(object)  # Device has been disconnected
    characteristicRead = pyqtSignal(str, bytes)  # Read characteristic data
    dataReceived = pyqtSignal(str, str)  # Received data from notifications
    writeReady = pyqtSignal(bool)  # Write operation status
    taskHalted = pyqtSignal()  # Interface task was halted

    def __init__(self):
        super().__init__()
        self.ble_client = None  # Internal client reference
        self.disconnect_event = asyncio.Event()
        self.services = None

    # Scan for devices
    @qasync.asyncSlot()
    async def scan_for_devices(self):
        """Scans for available devices on the interface."""
        devices = await BleakScanner.discover()
        formatted_devices = [(device.name, device.address) for device in devices]
        self.scanReady.emit(formatted_devices)

    # Connect to device
    @qasync.asyncSlot()
    async def connect_to_device(self, device_address):
        """Connects to a device on the interface."""
        self.ble_client = BleakClient(
            device_address,
            disconnected_callback=self.cb_disconnect,
            timeout=app_config.globals["bluetooth"]["connection_timeout"],
        )

        # Retreive services list right after connection
        try:
            connected = await self.ble_client.connect()
            if connected:
                self.services = self.ble_client.services
                self.disconnect_event.clear()
                self.linkReady.emit(True)
            else:
                self.linkReady.emit(False)
        except Exception as e:
            print(f"Connection failed: {e}")
            self.linkReady.emit(False)

    # Read data from characteristic (manual reading)
    @qasync.asyncSlot()
    async def read_characteristic(self, characteristic):
        """Reads data from a characteristic."""
        value = await self.ble_client.read_gatt_char(characteristic)
        self.characteristicRead.emit(str(characteristic.uuid), bytes(value))

    # Write data to characteristic (downlinks)
    @qasync.asyncSlot()
    async def send_data(self, uuid, data, response=False, encoded=False):
        """Sends data to the specified characteristic."""
        try:
            if self.disconnect_event.is_set():
                print("Operation aborted: Device disconnected.")
                self.writeReady.emit(False)
            else:
                characteristic = self.get_char_from_uuid(uuid)
                if characteristic is None:
                    self.writeReady.emit(False)
                else:
                    await self.ble_client.write_gatt_char(
                        characteristic, data.encode() if not encoded else data, response
                    )
                    self.writeReady.emit(True)
        except Exception as e:
            print(f"Write failed: {e}")
            self.writeReady.emit(False)

    # Setup notifications for uplink characteristic
    @qasync.asyncSlot()
    async def start_notifications(self, uuid):
        """Starts notifications for a characteristic."""

        # Find the characteristic from the uuid
        characteristic = self.get_char_from_uuid(uuid)
        if characteristic is None:
            print(f"Characteristic {uuid} not found.")
            return

        if "notify" in characteristic.properties:
            await self.ble_client.start_notify(
                characteristic, self.notification_callback
            )

    # Callback for notifications
    def notification_callback(self, sender, data):
        """Callback for notifications. Emits a signal with the received data."""
        sender_uuid = sender.uuid if hasattr(sender, "uuid") else str(sender)
        decoded_data = (
            data.decode("utf-8", errors="replace")
            if isinstance(data, (bytearray, bytes))
            else str(data)
        )
        self.dataReceived.emit(sender_uuid, decoded_data)

    # Callback disconnected
    def cb_disconnect(self, client):
        """Callback for disconnection. Emits a signal with the disconnected client."""
        self.disconnect_event.set()
        self.linkLost.emit(client)

    # Retreive list of services acquired from the connected device
    def get_services(self):
        """Retrieves services information from the connected device and formats it as a list."""
        services_list = []
        if hasattr(self, "services"):
            for service in self.services:
                services_list.append(service.uuid)  # Add the service UUID
                for characteristic in service.characteristics:
                    services_list.append(
                        characteristic.uuid
                    )  # Add each characteristic UUID
        return services_list

    # Find characteristic by UUID
    def get_char_from_uuid(self, uuid):
        """Finds a characteristic by its UUID."""
        for service in self.services:
            for characteristic in service.characteristics:
                if characteristic.uuid == uuid:
                    return characteristic
        return None

    # Manual disconnect
    @qasync.asyncSlot()
    async def disconnect(self):
        """Disconnects from the connected device."""

        # Client already disconnected
        if self.ble_client is None:
            return

        # Disconnects the client
        if self.ble_client and self.ble_client.is_connected:
            self.disconnect_event.set()
            await self.ble_client.disconnect()

        # Clears connection information
        self.ble_client = None

        # Emits the link lost signal
        self.taskHalted.emit()
