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
from PyQt5.QtCore import pyqtSignal, QTimer
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QPushButton, QListWidget, QHBoxLayout
from PyQt5.QtGui import QFont

import resources.config as app_config
from interfaces.com_interface import CommunicationInterface
from gui.console_window import ConsoleWindow
from gui.updater_window import UpdaterWindow
from resources.indexer import ConsoleIndex, BackendIndex, UpdaterIndex
import resources.patterns as patterns


class BLEConnectionWindow(QWidget):
    closingReady = pyqtSignal()

    def __init__(self, main_window, interface: CommunicationInterface, title):
        super().__init__()

        self.mw = main_window  # MainWindow Reference
        self.interface = interface  # Interface Reference

        # Add this tab to the main window
        self.mw.add_connection_tab(self, title)

        # Window Signals & Flags
        self.mw.windowClose.connect(self.process_close_task)
        self.mw.autoSyncStatus.connect(self.auto_sync_status)
        self.is_closing = False

        # Connection Events
        self.connection_event = asyncio.Event()
        self.reconnection_event = asyncio.Event()
        self.get_name_event = asyncio.Event()

        # Async BLE Signals
        self.interface.scanReady.connect(self.cb_scan_ready)
        self.interface.linkReady.connect(self.cb_link_ready)
        self.interface.linkLost.connect(self.cb_link_lost)
        self.interface.dataReceived.connect(self.cb_data_received)
        self.interface.taskHalted.connect(self.cb_task_halted)

        # Console Handling Variables
        self.device_address = None
        self.updater = None  # Updater Index
        self.console = {}  # Console Index and Instance Storage

        # Reconnection variables
        self.auto_sync_enabled = True
        self.reconnection_attempts = 0
        self.max_reconnection_attempts = app_config.globals["bluetooth"]["con_retries"]
        self.reconnection_timer = QTimer()
        self.reconnection_timer.timeout.connect(self.attempt_reconnection)

        # Draw the layout
        self.setup_layout()

    # --- GUI Functions ---

    # Layout and Widgets
    def setup_layout(self):
        connect_button = QPushButton("Connect")
        connect_button.clicked.connect(self.ble_connect)

        disconnect_button = QPushButton("Disconnect && Clear")
        disconnect_button.clicked.connect(self.manual_disconnect)

        self.scan_device_list = QListWidget()
        self.scan_device_list.setFont(QFont("Inconsolata"))
        self.scan_device_list.setSelectionMode(QListWidget.SingleSelection)
        self.scan_device_list.itemDoubleClicked.connect(self.ble_connect)

        scan_button = QPushButton("Scan Bluetooth")
        scan_button.clicked.connect(self.ble_scan)

        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self.exitApplication)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(connect_button)
        buttons_layout.addWidget(disconnect_button)

        connection_layout = QVBoxLayout()
        connection_layout.addLayout(buttons_layout)
        connection_layout.addWidget(self.scan_device_list)
        connection_layout.addWidget(scan_button)
        connection_layout.addWidget(exit_button)
        self.setLayout(connection_layout)

    # --- Async BLE Functions ---

    # BLE Scanning
    @qasync.asyncSlot()
    async def ble_scan(self):
        self.mw.debug_info("Scanning for Bluetooth devices ...")
        await self.interface.scan_for_devices()
        self.mw.debug_info("Scanning complete")

    # BLE Connection
    @qasync.asyncSlot()
    async def ble_connect(self):
        # In case of first connection, select the device from the list
        if not self.reconnection_event.is_set():
            selected_items = self.scan_device_list.selectedItems()
            if not selected_items:
                self.mw.debug_info("No device selected")
                return

            # Select the BLE MAC from the list [name - MAC]
            device_address = selected_items[0].text().split(" - ")[1]
            self.device_address = device_address

        self.mw.debug_info(f"Connecting to {self.device_address} ...")
        await self.interface.connect_to_device(self.device_address)

    # Retrieve Services names from the connected device
    @qasync.asyncSlot()
    async def get_services_names(self):
        uuid = patterns.UUID_BLE_BACKEND_RX
        await self.interface.send_data(uuid, "ARCTIC_COMMAND_GET_SERVICES_NAME")

    # Services Information
    def register_services(self, retrieved_services):
        """Retrieves services information from the connected device."""

        # Register Backend Services
        self.backend = BackendIndex()
        self.backend.service = patterns.UUID_BLE_BACKEND_ATS
        self.backend.txm = patterns.UUID_BLE_BACKEND_TX
        self.backend.rxm = patterns.UUID_BLE_BACKEND_RX

        # Register OTA Services if not already registered
        if self.updater is None:
            self.updater = UpdaterIndex()
            self.updater.name = "OTA"
            self.updater.service = patterns.UUID_BLE_OTA_ATS
            self.updater.txm = patterns.UUID_BLE_OTA_TX
            self.updater.rxm = patterns.UUID_BLE_OTA_RX

        # Add the updater to the main window
        self.create_updater_window(self.updater.name, self.updater.service)

        # Register each console service in the console index
        for service in retrieved_services:
            service_uuid = service["ats"]
            console_name = service["name"]

            # Save the service information if it's not already in the index
            if self.console.get(service_uuid) is None:
                self.console[service_uuid] = ConsoleIndex()
                self.console[service_uuid].name = console_name
                self.console[service_uuid].service = service_uuid
                self.console[service_uuid].txm = service["txm"]
                self.console[service_uuid].txs = service["txs"]
                self.console[service_uuid].rxm = service["rxm"]

            # Add the console to the main window
            self.create_console_window(console_name, service_uuid)

        # Enable data uplink
        self.enable_device_uplink()

    def format_services(self, response, unformatted_services):
        """Parses services information from the response string."""

        # Process the name
        service_names = response.replace("ARCTIC_COMMAND_GET_SERVICES_NAME:", "")
        service_names = service_names.replace("\n", "")
        service_names = service_names.split(",")

        # Process each service name
        services_info = []
        for service_name in service_names:
            # Initialize UUIDs for each service type
            ats_uuid = txm_uuid = txs_uuid = rxm_uuid = None

            # Find UUIDs for each service type
            for uuid in unformatted_services:
                if patterns.UUID_BLE_CONSOLE_ATS.match(uuid):
                    ats_uuid = uuid
                elif patterns.UUID_BLE_CONSOLE_TX.match(uuid):
                    txm_uuid = uuid
                elif patterns.UUID_BLE_CONSOLE_TXS.match(uuid):
                    txs_uuid = uuid
                elif patterns.UUID_BLE_CONSOLE_RX.match(uuid):
                    rxm_uuid = uuid

                # Once all UUIDs for a service are found, break the loop
                if ats_uuid and txm_uuid and txs_uuid and rxm_uuid:
                    break

            # Remove found UUIDs from the list to avoid duplication
            unformatted_services = [
                uuid
                for uuid in unformatted_services
                if uuid not in [ats_uuid, txm_uuid, txs_uuid, rxm_uuid]
            ]

            # Create service info dictionary
            service_info = {
                "name": service_name,
                "ats": ats_uuid,
                "txm": txm_uuid,
                "txs": txs_uuid,
                "rxm": rxm_uuid,
            }

            # Add the dictionary to the list
            services_info.append(service_info)
        return services_info

    @qasync.asyncSlot()
    async def enable_device_uplink(self):
        uuid = patterns.UUID_BLE_BACKEND_RX
        await self.interface.send_data(uuid, "ARCTIC_COMMAND_ENABLE_UPLINK")

    @qasync.asyncSlot()
    async def disable_device_uplink(self):
        uuid = patterns.UUID_BLE_BACKEND_RX
        await self.interface.send_data(uuid, "ARCTIC_COMMAND_DISABLE_UPLINK")

    # --- Callbacks ---

    # Scan List Update
    def cb_scan_ready(self, devices):
        self.scan_device_list.clear()

        if devices is None:
            self.mw.debug_info("No devices found")
            return

        for name, address in devices:
            self.scan_device_list.addItem(f"{name} - {address}")

    # Connection Complete
    def cb_link_ready(self, connected):
        if connected:
            self.mw.debug_info(
                f"Device {self.device_address} is ready to receive commands"
            )
            self.connection_event.set()
            self.reconnection_attempts = 0

            # Start notifications for each TXM and TXS characteristic
            services = self.interface.get_services()
            for service in services:
                if service == patterns.UUID_BLE_BACKEND_TX:  # Not regex
                    self.interface.start_notifications(service)
                if service == patterns.UUID_BLE_OTA_TX:  # Not regex
                    self.interface.start_notifications(service)
                if patterns.UUID_BLE_CONSOLE_TX.match(service):  # Regex
                    self.interface.start_notifications(service)
                if patterns.UUID_BLE_CONSOLE_TXS.match(service):  # Regex
                    self.interface.start_notifications(service)

            # Get the services names through the backend (notify)
            self.get_services_names()

    # Disconnected
    def cb_link_lost(self, device_address):
        self.mw.debug_info(f"Device on {device_address} stopped responding.")

        # Reset the interface
        self.interface.disconnect()
        self.connection_event.clear()

        # Autosync enabled. Try to reconnect
        if self.device_address and self.auto_sync_enabled:
            self.mw.debug_info("Attempting reconnection ...")
            self.reconnection_timer.start(5000)

    # Data Received to handle backend commands
    def cb_data_received(self, uuid, data):
        if uuid == patterns.UUID_BLE_BACKEND_TX:
            if "ARCTIC_COMMAND_GET_SERVICES_NAME" in data:
                unformatted_services = self.interface.get_services()
                services = self.format_services(data, unformatted_services)
                self.register_services(services)

    # Task Halted
    def cb_task_halted(self):
        self.mw.debug_info("BLE Interface task was halted")

    # --- Window Functions ---

    # Initialize a new updater window (OTA)
    def create_updater_window(self, name, uuid):
        # Check if the console window is already open
        print(self.updater.instance)
        if self.updater.instance:
            window = self.updater.instance
        else:
            # Console window is not open, create a new one
            window = UpdaterWindow(self.mw, self.interface, name, self.updater)
            self.updater.instance = window
            self.mw.add_updater_tab(window, name)

    # Initialize or reinitialize a console window
    def create_console_window(self, name, uuid):
        # Reuse the console window if it's already open
        if self.console[uuid].instance:
            window = self.console[uuid].instance
        else:
            # Console window is not open, create a new one
            window = ConsoleWindow(self.mw, self.interface, name, self.console[uuid])
            self.console[uuid].instance = window
            self.mw.add_console_tab(window, name)

    def auto_sync_status(self, status):
        self.auto_sync_enabled = status

    # --- Reconnection Functions ---

    # Reconnection logic triggered by timeout
    @qasync.asyncSlot()
    async def attempt_reconnection(self):
        if self.connection_event.is_set():
            self.reconnection_timer.stop()
            return

        if self.reconnection_attempts < self.max_reconnection_attempts:
            self.interface.disconnect()
            self.reconnection_event.set()
            self.reconnection_attempts += 1
            self.mw.debug_info(
                f"Attempting reconnection to {self.device_address} "
                f"(attempt {self.reconnection_attempts}/{self.max_reconnection_attempts})"
            )
            await self.ble_connect()
        else:
            self.mw.debug_info("Maximum reconnection attempts reached. Giving up.")
            self.reconnection_attempts = 0
            self.reconnection_timer.stop()

            self.reconnection_event.clear()
            self.connection_event.clear()

    # --- Stop Functions ---

    # Manual Disconnect/Clear from button
    @qasync.asyncSlot()
    async def manual_disconnect(self):
        self.reconnection_attempts = 0
        self.reconnection_timer.stop()

        self.mw.debug_info("Clearing BLE connection ...")

        # 2. Disconnect from the device
        self.interface.disconnect()

        # 1. Stop consoles and clear references
        self.stop_consoles()

        # 3. Clear device port and connection events
        self.device_address = None
        self.connection_event.clear()
        self.reconnection_event.clear()

        # 4. Optionally clear the scan device list (if desired)
        self.scan_device_list.clear()

    # Stop the remaining consoles
    def stop_consoles(self):
        self.console = {}  # Clear console index
        for uuid, console_index in self.console.items():
            if console_index.instance:
                console_index.instance.close()

    # Stop the BLE Handler
    @qasync.asyncSlot()
    async def process_close_task(self, close_window=True):
        self.device_address = None
        if not self.is_closing:
            self.is_closing = True
            self.interface.disconnect()
            self.stop_consoles()
            if close_window:
                self.closingReady.emit()

    # Exit triggered from "exit" button
    def exitApplication(self):
        self.mw.exit_interface()
