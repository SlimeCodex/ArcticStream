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

    def __init__(self, main_window, interface: CommunicationInterface, title):
        self.connection_event = asyncio.Event()
        self.reconnection_event = asyncio.Event()
        super().__init__()

        self.mw = main_window  # MainWindow Reference
        self.interface = interface  # Interface Reference

        # Add this tab to the main window
        self.mw.add_connection_tab(self, title)

        # Window Signals & Flags
        self.mw.signal_window_close.connect(self.process_close_task)
        self.is_closing = False

        # Async WiFi Signals
        self.interface.scanReady.connect(self.cb_scan_ready)
        self.interface.linkReady.connect(self.cb_link_ready)
        self.interface.linkLost.connect(self.cb_link_lost)
        self.interface.writeReady.connect(self.cb_write_ready)

        # Console Handling Variables
        self.device_address = None
        self.updater_service = None
        self.console = {}
        self.updater_ref = None
        self.console_ref = {}

        # Draw the layout
        self.setup_layout()

    # --- GUI Functions ---

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

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(connect_button)
        buttons_layout.addWidget(disconnect_button)

        connection_layout = QVBoxLayout()
        connection_layout.addLayout(buttons_layout)
        connection_layout.addWidget(self.scan_device_list)
        connection_layout.addWidget(scan_button)
        connection_layout.addWidget(exit_button)
        self.setLayout(connection_layout)

    # --- Async WiFi Functions ---

    # WiFi Scanning
    @qasync.asyncSlot()
    async def wifi_scan(self):
        self.mw.debug_info("Scanning for WiFi devices ...")
        await self.interface.scan_for_devices()
        self.mw.debug_info("Scanning complete")

    # WiFi Connection
    @qasync.asyncSlot()
    async def wifi_connect(self, reconnect=False):
        selected_items = self.scan_device_list.selectedItems()
        if not selected_items:
            self.mw.debug_info("No device selected")
            return

        # Select the IP address from the list [name - mac - ip]
        device_address = selected_items[0].text().split(" - ")[2]
        self.device_address = device_address

        if not reconnect:
            self.mw.debug_info(f"Connecting to {device_address} ...")

        await self.interface.connect_to_device(device_address)

    # WiFi Reconnection
    @qasync.asyncSlot()
    async def wifi_reconnect(self):
        max_recon_retries = app_config.globals["wifi"]["reconnection_retries"]
        retries_counter = 1  # Static start value

        while retries_counter <= max_recon_retries:
            self.connection_event.clear()
            self.mw.debug_info(
                f"Attempting reconnection to {self.device_address}. Retry: {
                    retries_counter}/{max_recon_retries}"
            )
            await self.wifi_connect(self.device_address, reconnect=True)
            if self.connection_event.is_set():
                break
            else:
                retries_counter += 1

        if retries_counter > max_recon_retries:
            self.mw.debug_info(f"Reconnection to {self.device_address} failed")

    # Retrieve Services Information
    @qasync.asyncSlot()
    async def register_services(self):
        """Retrieves services information from the connected device."""
        retrieved_services = await self.interface.get_services()

        for service in retrieved_services:
            service_uuid = service["ats"]
            console_name = service["name"]

            # Register the service
            self.console[service_uuid] = ConsoleIndex()
            self.console[service_uuid].name = console_name
            self.console[service_uuid].service = service_uuid
            self.console[service_uuid].txm = service["txm"]
            self.console[service_uuid].txs = service["txs"]
            self.console[service_uuid].rxm = service["rxm"]

            # Console window is not open, create a new one
            console = ConsoleWindow(
                self.mw,
                self.interface,
                console_name,
                self.console[service_uuid],
            )
            self.console_ref[service_uuid] = console

            # Add the console to the main window
            self.mw.add_console_tab(console, console_name)

    # Stop WiFi Threads and processes
    @qasync.asyncSlot()
    async def wifi_stop(self):
        self.mw.debug_info("Disconnecting WiFi device ...")
        await self.interface.disconnect()

    # Clear connection
    @qasync.asyncSlot()
    async def wifi_clear_connection(self):
        self.mw.debug_info("Clearing connection ...")
        self.device_address = None
        if not self.is_closing:
            asyncio.ensure_future(self.process_close_task(close_window=False))

    # --- Callbacks ---

    # Scan List Update
    def cb_scan_ready(self, devices):
        self.scan_device_list.clear()
        for name, address, ip in devices:
            self.scan_device_list.addItem(f"{name} - {address} - {ip}")

    # Connection Complete
    def cb_link_ready(self, connected):
        if connected:
            self.connection_event.set()
            self.mw.debug_info(f"Connected to {self.device_address}")
            self.register_services()
        else:
            self.connection_event.clear()

    # Disconnected
    def cb_link_lost(self, address):
        self.mw.debug_info(f"Device {address} disconnected")

        # Manual disconnect are not handled
        if self.device_address:
            self.wifi_reconnect()

    # Write Complete
    def cb_write_ready(self, success):
        if not success:
            self.mw.debug_info("Wifi write failed")

    # --- Window Functions ---

    # Initialize a new updater window (OTA)
    def create_updater_window(self, name, uuid):
        
        # Check if the console window is already open
        if self.updater_ref:
            window = self.updater_ref
        else:
            # Console window is not open, create a new one
            window = UpdaterWindow(
                self.mw, self.interface, name, self.updater_service)
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
                self.console[uuid]
            )
            self.console_ref[uuid] = console

            self.mw.add_console_tab(console, name)

    # --- Stop Functions ---

    # Stop the remaining consoles
    def stop_consoles(self):
        for uuid, console in self.console_ref.items():
            console.close()

    # Stop the WiFi Handler
    @qasync.asyncSlot()
    async def process_close_task(self, close_window=True):
        self.device_address = None
        if not self.is_closing:
            self.is_closing = True
            await self.wifi_stop()
            self.stop_consoles()
            if close_window:
                self.signal_closing_complete.emit()

    # Exit triggered from "exit" button
    def exitApplication(self):
        self.mw.exit_interface()
