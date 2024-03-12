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

import qasync
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QPushButton, QListWidget, QHBoxLayout
from PyQt5.QtGui import QFont

import resources.config as app_config
from interfaces.com_interface import CommunicationInterface
from gui.console_window import ConsoleWindow
from gui.updater_window import UpdaterWindow
from resources.indexer import ConsoleIndex, BackendIndex, UpdaterIndex
import resources.patterns as patterns


class BLEConnectionWindow(QWidget):
    signal_closing_complete = pyqtSignal()

    def __init__(self, main_window, interface: CommunicationInterface, title):
        self.connection_event = asyncio.Event()
        self.reconnection_event = asyncio.Event()
        super().__init__()

        self.mw = main_window  # MainWindow Reference
        self.interface = interface  # Interface Reference
        self.win_title = title  # Original title of the tab

        # Add this tab to the main window
        self.mw.add_connection_tab(self, self.win_title)
        self.mw.signal_window_close.connect(self.process_close_task)

        # Async BLE Signals
        self.interface.scanReady.connect(
            self.cb_scan_ready)
        self.interface.linkReady.connect(
            self.cb_link_ready
        )
        self.interface.linkLost.connect(
            self.cb_link_lost)
        self.interface.characteristicRead.connect(
            self.cb_handle_char_read)
        self.interface.dataReceived.connect(
            self.cb_handle_notification
        )

        # Async Events from the device
        self.get_name_event = asyncio.Event()

        # Globals
        self.background_service = (
            None  # Background service reference (for service reuse)
        )
        # Updater service reference (for service reuse)
        self.updater_service = None
        # Console services reference (for service reuse)
        self.console = {}
        self.updater_ref = None  # Updater window reference (for window reuse)
        self.console_ref = {}  # Console windows reference (for window reuse)
        self.device_address = None
        self.is_closing = False

        self.setup_layout()

    # GUI Functions ------------------------------------------------------------------------------------------

    # Layout and Widgets
    def setup_layout(self):
        connect_button = QPushButton("Connect")
        connect_button.clicked.connect(self.ble_connect)

        disconnect_button = QPushButton("Disconnect")
        disconnect_button.clicked.connect(self.ble_clear_connection)

        self.scan_device_list = QListWidget()
        self.scan_device_list.setFont(QFont("Inconsolata"))
        self.scan_device_list.setSelectionMode(QListWidget.SingleSelection)
        self.scan_device_list.itemDoubleClicked.connect(self.ble_connect)

        scan_button = QPushButton("Scan Bluetooth")
        scan_button.clicked.connect(self.ble_scan)

        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self.exitApplication)

        # Layout for buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(connect_button)
        buttons_layout.addWidget(disconnect_button)

        connection_layout = QVBoxLayout()
        connection_layout.addLayout(buttons_layout)
        connection_layout.addWidget(self.scan_device_list)
        connection_layout.addWidget(scan_button)
        connection_layout.addWidget(exit_button)
        self.setLayout(connection_layout)

    # Async BLE Functions ------------------------------------------------------------------------------------------

    # BLE Scanning
    @qasync.asyncSlot()
    async def ble_scan(self):
        self.mw.debug_info("Scanning for devices ...")
        await self.interface.scan_for_devices()
        self.mw.debug_info("Scanning complete")

    # BLE Connection
    @qasync.asyncSlot()
    async def ble_connect(self, reconnect=False):
        selected_items = self.scan_device_list.selectedItems()
        if not selected_items:
            self.mw.debug_info("No device selected")
            return

        device_address = selected_items[0].text().split(" - ")[1]
        self.device_address = device_address

        if not reconnect:
            self.mw.debug_info(f"Connecting to {device_address} ...")

        await self.interface.connect_to_device(device_address)

    # BLE Setting up notifications and retrieving name characteristic
    @qasync.asyncSlot()
    async def setup_consoles(self):
        # Load OTA window
        if self.updater_service:
            self.mw.debug_log("OTA service found")
            if self.updater_service.txm:
                await self.interface.start_notifications(
                    self.updater_service.txm
                )
            self.create_updater_window(
                self.updater_service.name, self.updater_service.service.uuid
            )

        # Load consoles windows
        for service_uuid, indexer in self.console.items():
            # Start notifications
            if indexer.txm:
                await self.interface.start_notifications(
                    indexer.txm
                )
            if indexer.txs:
                await self.interface.start_notifications(
                    indexer.txs
                )

            # Retreive console name from device
            self.get_name_event.clear()
            await self.interface.send_command(  # Request name
                str("ARCTIC_COMMAND_GET_NAME").encode(),
                indexer.rxm.uuid
            )
            await self.get_name_event.wait()  # Wait for the name to be retrieved
            self.create_console_window(indexer.name, service_uuid)

    # Reconnection
    @qasync.asyncSlot()
    async def ble_reconnect(self):
        max_recon_retries = app_config.globals["bluetooth"]["reconnection_retries"]
        retries_counter = 1  # Static start value

        while retries_counter <= max_recon_retries:
            self.connection_event.clear()
            self.mw.debug_info(
                f"Attempting reconnection to {self.device_address}. Retry: {retries_counter}/{max_recon_retries}"
            )
            await self.ble_connect(
                self.device_address, reconnect=True
            )  # Will wait 5s before timeout
            if self.connection_event.is_set():
                # Reconnection successful
                break
            else:
                retries_counter += 1

        if retries_counter > max_recon_retries:
            self.mw.debug_info(
                f"Reconnection to {self.device_address} failed"
            )

    # Stop BLE
    @qasync.asyncSlot()
    async def ble_stop(self):
        self.mw.debug_info("Disconnecting ...")
        await self.interface.disconnect()

    # Clear connection
    @qasync.asyncSlot()
    async def ble_clear_connection(self):
        self.mw.debug_info("Clearing connection ...")
        self.device_address = None
        if not self.is_closing:
            asyncio.ensure_future(self.process_close_task(close_window=False))

    # Callbacks -----------------------------------------------------------------------------------------------

    # Callback update device list
    def cb_scan_ready(self, devices):
        self.scan_device_list.clear()
        for name, address in devices:
            self.scan_device_list.addItem(f"{name} - {address}")

    # Callback connection success
    def cb_link_ready(self, connected):
        if connected:
            self.connection_event.set()
            self.mw.debug_info(
                f"Connected to {self.device_address}")
            self.register_services()
        else:
            self.connection_event.clear()

    # Callback handle name characteristic read
    def cb_handle_char_read(self, uuid, value):
        pass

    # Callback device disconnected
    def cb_link_lost(self, client):
        self.mw.debug_info(f"Device {client.address} disconnected")

        # Manual disconnect are not handled
        if self.device_address:
            self.ble_reconnect()

    # Callback handle notification for retrieving console name
    def cb_handle_notification(self, uuid, value):
        for service_uuid, indexer in self.console.items():
            if indexer.txs.uuid == uuid:
                value = value.replace(
                    "ARCTIC_COMMAND_REQ_NAME:", "")  # Remove command
                self.console[service_uuid].name = value
                self.get_name_event.set()

    # Window Functions ------------------------------------------------------------------------------------------

    # Register services
    def register_services(self):
        registered_services = self.interface.get_services()  # Not async
        for service in registered_services:
            service_uuid = str(service.uuid)
            self.mw.debug_log(f"Service found: {service_uuid}")

            # Register background services
            if service_uuid == patterns.uuid_ble_backend_ats:
                self.mw.debug_log("Background service found")
                temp_indexer = BackendIndex(service)

                # Loop through characteristics
                for characteristic in service.characteristics:
                    char_uuid = str(characteristic.uuid)
                    if char_uuid == patterns.uuid_ble_backend_tx:  # TX
                        temp_indexer.txm = characteristic
                    if char_uuid == patterns.uuid_ble_backend_rx:  # RX
                        temp_indexer.rxm = characteristic

                # Register the temp_indexer
                self.background_service = temp_indexer

            # Register OTA services
            if service_uuid == patterns.uuid_ble_ota_ats:
                self.mw.debug_log("OTA service found")
                temp_indexer = UpdaterIndex(service)

                # Loop through characteristics
                for characteristic in service.characteristics:
                    char_uuid = str(characteristic.uuid)
                    if char_uuid == patterns.uuid_ble_ota_tx:  # TX
                        temp_indexer.txm = characteristic
                    if char_uuid == patterns.uuid_ble_ota_rx:  # RX
                        temp_indexer.rxm = characteristic

                # Register the temp_indexer
                temp_indexer.name = "OTA"
                self.updater_service = temp_indexer

            # Register console services
            if patterns.uuid_ble_console_ats.match(service_uuid):
                self.mw.debug_log("Console service found")

                # Check if the service is already registered and reuse it
                if service_uuid in self.console:
                    temp_indexer = self.console[service_uuid]
                else:
                    temp_indexer = ConsoleIndex()
                    temp_indexer.service = service

                # Loop through characteristics
                for characteristic in service.characteristics:
                    char_uuid = str(characteristic.uuid)

                    # Check and update or set characteristics
                    if patterns.uuid_ble_console_tx.match(char_uuid):
                        temp_indexer.txm = characteristic # TODO: CHECK HANDLER FOR THIS, SHOULD BE ONLY UUID, NOT COMPLETE CHARACTERISTIC
                    elif patterns.uuid_ble_console_txs.match(char_uuid):
                        temp_indexer.txs = characteristic
                    elif patterns.uuid_ble_console_rx.match(char_uuid):
                        temp_indexer.rxm = characteristic

                # Register the temp_indexer
                temp_indexer.name = "<arctic>"
                self.console[service_uuid] = temp_indexer

        # Setup notification and read name characteristic
        self.setup_consoles()

    # Initialize a new updater window (OTA)
    def create_updater_window(self, name, uuid):
        # Check if the console window is already open
        if self.updater_ref:
            window = self.updater_ref
        else:
            # Console window is not open, create a new one
            window = UpdaterWindow(
                self.mw, self.interface, name, self.updater_service
            )
            self.updater_ref = window

            self.mw.add_updater_tab(window, name)

    # Initialize a new console window
    def create_console_window(self, name, uuid):
        # Check if the console window is already open
        if uuid in self.console_ref:
            console = self.console_ref[uuid]
        else:
            # Console window is not open, create a new one
            console = ConsoleWindow(
                self.mw,
                self.interface,
                name,
                self.console[uuid],
            )
            self.console_ref[uuid] = console

            self.mw.add_console_tab(console, name)

    # Stop Functions ------------------------------------------------------------------------------------------

    # Stop the remaining consoles
    def stop_consoles(self):
        for uuid, console in self.console_ref.items():
            console.close()

    # Stop the BLE Handler
    @qasync.asyncSlot()
    async def process_close_task(self, close_window=True):
        self.device_address = None  # Clear the last device address
        if not self.is_closing:
            self.is_closing = True
            await self.ble_stop()
            self.stop_consoles()
            if close_window:
                # Emit the signal after all tasks are completed
                self.signal_closing_complete.emit()

    # Exit triggered from "exit" button
    def exitApplication(self):
        self.mw.exit_interface()
