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


class WiFiConnectionWindow(QWidget):
    signal_closing_complete = pyqtSignal()

    def __init__(self, main_window, stream_interface: CommunicationInterface, title):
        self.connection_event = asyncio.Event()
        self.reconnection_event = asyncio.Event()
        super().__init__()

        self.main_window = main_window  # MainWindow Reference
        self.stream_interface = stream_interface  # Interface Reference
        self.win_title = title  # Original title of the tab

        # Add this tab to the main window
        self.main_window.add_connection_tab(self, self.win_title)
        self.main_window.signal_window_close.connect(self.process_close_task)

        # Async WiFi Signals
        self.stream_interface.devicesDiscovered.connect(
            self.callback_update_scan_list)
        self.stream_interface.connectionCompleted.connect(
            self.callback_connection_complete
        )
        self.stream_interface.deviceDisconnected.connect(
            self.callback_disconnected)
        self.stream_interface.writeCompleted.connect(
            self.callback_handle_write_complete
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
        self.console_services = {}
        self.updater_ref = None  # Updater window reference (for window reuse)
        self.console_ref = {}  # Console windows reference (for window reuse)
        self.last_device_address = None
        self.is_closing = False

        self.setup_layout()

    # GUI Functions ------------------------------------------------------------------------------------------

    # Layout and Widgets
    def setup_layout(self):
        connect_button = QPushButton("Connect")
        connect_button.clicked.connect(self.wifi_connect)

        disconnect_button = QPushButton("Disconnect")
        disconnect_button.clicked.connect(self.wifi_clear_connection)

        self.scan_device_list = QListWidget()
        self.scan_device_list.setFont(QFont("Inconsolata"))
        self.scan_device_list.setSelectionMode(QListWidget.SingleSelection)
        self.scan_device_list.itemDoubleClicked.connect(self.wifi_connect)

        scan_button = QPushButton("Scan Network")
        scan_button.clicked.connect(self.wifi_scan)

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

    # Async WiFi Functions ------------------------------------------------------------------------------------------

    # WiFi Scanning
    @qasync.asyncSlot()
    async def wifi_scan(self):
        self.main_window.debug_info("Scanning for devices ...")
        await self.stream_interface.scan_for_devices()
        self.main_window.debug_info("Scanning complete")

    # WiFi Connection
    @qasync.asyncSlot()
    async def wifi_connect(self, reconnect=False):
        selected_items = self.scan_device_list.selectedItems()
        if not selected_items:
            self.main_window.debug_info("No device selected")
            return

        device_address = selected_items[0].text().split(" - ")[2]
        self.last_device_address = device_address

        if not reconnect:
            self.main_window.debug_info(f"Connecting to {device_address} ...")

        retrieved_services = await self.stream_interface.get_services()

        for service in retrieved_services:
            console_name = service["name"]
            console_uuid_ats = service["ats"]
            console_uuid_tx = service["txm"]
            console_uuid_txs = service["txs"]
            console_uuid_rx = service["rxm"]

            # Register the service
            self.console_services[console_uuid_ats] = ConsoleIndex()
            self.console_services[console_uuid_ats].name = console_name
            self.console_services[console_uuid_ats].service = console_uuid_ats
            self.console_services[console_uuid_ats].tx_characteristic = console_uuid_tx
            self.console_services[console_uuid_ats].txs_characteristic = (
                console_uuid_txs
            )
            self.console_services[console_uuid_ats].rx_characteristic = console_uuid_rx

            # Console window is not open, create a new one
            console = ConsoleWindow(
                self.main_window,
                self.stream_interface,
                console_name,
                self.console_services[console_uuid_ats],
            )
            self.console_ref[console_uuid_ats] = console

            self.main_window.add_console_tab(console, console_name)

        await self.stream_interface.connect_to_device(device_address)

    # Reconnection
    @qasync.asyncSlot()
    async def wifi_reconnect(self):
        max_recon_retries = app_config.globals["wifi"]["reconnection_retries"]
        retries_counter = 1  # Static start value

        while retries_counter <= max_recon_retries:
            self.connection_event.clear()
            self.main_window.debug_info(
                f"Attempting reconnection to {self.last_device_address}. Retry: {retries_counter}/{max_recon_retries}"
            )
            await self.wifi_connect(
                self.last_device_address, reconnect=True
            )  # Will wait 5s before timeout
            if self.connection_event.is_set():
                # Reconnection successful
                break
            else:
                retries_counter += 1

        if retries_counter > max_recon_retries:
            self.main_window.debug_info(
                f"Reconnection to {self.last_device_address} failed"
            )

    # Stop WiFi
    @qasync.asyncSlot()
    async def wifi_stop(self):
        self.main_window.debug_info("Disconnecting ...")
        await self.stream_interface.disconnect()

    # Clear connection
    @qasync.asyncSlot()
    async def wifi_clear_connection(self):
        self.main_window.debug_info("Clearing connection ...")
        self.last_device_address = None
        if not self.is_closing:
            asyncio.ensure_future(self.process_close_task(close_window=False))

    # Callbacks -----------------------------------------------------------------------------------------------

    # Callback update device list
    def callback_update_scan_list(self, devices):
        self.scan_device_list.clear()
        for name, address, ip in devices:
            self.scan_device_list.addItem(f"{name} - {address} - {ip}")

    # Callback connection success
    def callback_connection_complete(self, connected):
        if connected:
            self.connection_event.set()
            self.main_window.debug_info(
                f"Connected to {self.last_device_address}")
        else:
            self.connection_event.clear()

    # Callback device disconnected
    def callback_disconnected(self, address):
        self.main_window.debug_info(f"Device {address} disconnected")

        # Manual disconnect are not handled
        if self.last_device_address:
            self.wifi_reconnect()

    def callback_handle_write_complete(self, success):
        if not success:
            self.main_window.debug_info("Wifi write failed")

    # Window Functions ------------------------------------------------------------------------------------------

    # Initialize a new updater window (OTA)
    def new_updater_window(self, name, uuid):

        # Check if the console window is already open
        if self.updater_ref:
            window = self.updater_ref
        else:
            # Console window is not open, create a new one
            window = UpdaterWindow(
                self.main_window, self.stream_interface, name, self.updater_service
            )
            self.updater_ref = window

            self.main_window.add_updater_tab(window, name)

    # Initialize a new console window
    def new_console_window(self, name, uuid):

        # Check if the console window is already open
        if uuid in self.console_ref:
            console = self.console_ref[uuid]
        else:
            # Console window is not open, create a new one
            console = ConsoleWindow(
                self.main_window,
                self.stream_interface,
                name,
                self.console_services[uuid],
            )
            self.console_ref[uuid] = console

            self.main_window.add_console_tab(console, name)

    # Stop Functions ------------------------------------------------------------------------------------------

    # Stop the remaining consoles
    def stop_consoles(self):
        for uuid, console in self.console_ref.items():
            console.close()

    # Stop the WiFi Handler
    @qasync.asyncSlot()
    async def process_close_task(self, close_window=True):
        self.last_device_address = None  # Clear the last device address
        if not self.is_closing:
            self.is_closing = True
            await self.wifi_stop()
            self.stop_consoles()
            if close_window:
                # Emit the signal after all tasks are completed
                self.signal_closing_complete.emit()

    # Exit triggered from "exit" button
    def exitApplication(self):
        self.main_window.exit_interface()
