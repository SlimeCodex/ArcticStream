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
from PyQt5.QtCore import pyqtSignal, QTimer, Qt
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QPushButton,
    QListWidget,
    QHBoxLayout,
    QLabel,
    QStackedWidget,
)
from PyQt5.QtGui import QFont, QMovie

import resources.config as app_config
from interfaces.com_interface import CommunicationInterface
from gui.console_window import ConsoleWindow
from gui.updater_window import UpdaterWindow
from resources.indexer import ConsoleIndex, BackendIndex, UpdaterIndex
import resources.patterns as patterns


class UARTConnectionWindow(QWidget):
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
        self.mw.themeChanged.connect(self.cb_update_theme)
        self.is_closing = False

        # Connection Events
        self.connection_event = asyncio.Event()
        self.reconnection_event = asyncio.Event()

        # Async UART Signals
        self.interface.scanReady.connect(self.cb_scan_ready)
        self.interface.linkReady.connect(self.cb_link_ready)
        self.interface.linkReadyCOM.connect(self.cb_com_link_ready)
        self.interface.linkLost.connect(self.cb_link_lost)
        self.interface.dataReceived.connect(self.cb_data_received)
        self.interface.taskHalted.connect(self.cb_task_halted)

        # Console Handling Variables
        self.device_port = None
        self.updater = None  # Updater Instance
        self.console = {}  # Console Index and Instance Storage

        # Reconnection variables
        self.auto_sync_enabled = True
        self.reconnection_attempts = 0
        self.max_reconnection_attempts = app_config.globals["uart"]["con_retries"]
        self.reconnection_timer = QTimer()
        self.reconnection_timer.timeout.connect(self.attempt_reconnection)

        # Draw the layout
        self.setup_layout()

    # --- GUI Functions ---

    # Layout and Widgets
    def setup_layout(self):
        scan_button = QPushButton("Scan Bluetooth")
        scan_button.clicked.connect(self.uart_scan)

        connect_button = QPushButton("Connect")
        connect_button.clicked.connect(self.uart_connect)

        self.scan_device_list = QListWidget()
        self.scan_device_list.setFont(QFont("Inconsolata"))
        self.scan_device_list.setSelectionMode(QListWidget.SingleSelection)
        self.scan_device_list.itemDoubleClicked.connect(self.uart_connect)
        
        self.movie_dark = QMovie("src/resources/video/loading_scan_dark.gif")
        self.movie_light = QMovie("src/resources/video/loading_scan_light.gif")

        self.animation_label = QLabel(self)
        self.animation_label.setAlignment(Qt.AlignCenter)
        self.animation_label.setGeometry(0, 0, 120, 120)

        disconnect_button = QPushButton("Disconnect")
        disconnect_button.clicked.connect(self.manual_disconnect)

        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self.exitApplication)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(connect_button)
        buttons_layout.addWidget(disconnect_button)

        self.stacked_widget = QStackedWidget(self)
        self.stacked_widget.addWidget(self.scan_device_list)

        connection_layout = QVBoxLayout()
        connection_layout.addWidget(scan_button)
        connection_layout.addWidget(self.stacked_widget)
        connection_layout.addLayout(buttons_layout)
        connection_layout.addWidget(exit_button)
        self.setLayout(connection_layout)

    # Position the animation label
    def position_animation(self):
        list_geometry = self.scan_device_list.geometry()
        animation_width = self.animation_label.width()
        animation_height = self.animation_label.height()
        x = list_geometry.x() + ((list_geometry.width() - animation_width) // 2)
        y = list_geometry.y() + ((list_geometry.height() - animation_height) // 2) + 45
        self.animation_label.setGeometry(x, y, animation_width, animation_height)
        self.animation_label.raise_()
    
    # Update the theme of the loading animation
    def cb_update_theme(self, theme):
        if theme == "dark":
            self.animation_label.setMovie(self.movie_dark)
        if theme == "light":
            self.animation_label.setMovie(self.movie_light)
    
    # Show or hide the loading animation
    def show_loading_animation(self, status):
        if status:
            self.animation_label.setVisible(True)
            self.movie_dark.start()
            self.movie_light.start()
        else:
            self.animation_label.setVisible(False)
            self.movie_dark.stop()
            self.movie_light.stop()

    # --- Qt Events ---

    # Reimplement the resizeEvent
    def resizeEvent(self, event):
        self.position_animation()
        super().resizeEvent(event)

    # --- Async UART Functions ---

    # UART Scanning
    @qasync.asyncSlot()
    async def uart_scan(self):
        self.scan_device_list.clear()
        self.mw.debug_info("Scanning for UART devices ...")
        self.show_loading_animation(True)
        await asyncio.sleep(1)
        await self.interface.scan_for_devices()
        self.show_loading_animation(False)
        self.mw.debug_info("Scanning complete")

    # UART Connection
    @qasync.asyncSlot()
    async def uart_connect(self):
        # In case of first connection, select the device from the list
        if not self.reconnection_event.is_set():
            selected_items = self.scan_device_list.selectedItems()
            if not selected_items:
                self.mw.debug_info("No device selected")
                return

            # Select the COM port from the list [descriptor - port]
            device_port = selected_items[0].text().split(" - ")[1]
            self.device_port = device_port

        self.mw.debug_info(f"Connecting to {self.device_port} ...")
        await self.interface.connect_to_device(self.device_port)

    # --- Device Interaction ---

    # Retrieve Services from the connected device
    @qasync.asyncSlot()
    async def get_services(self):
        uuid = patterns.UUID_UART_BACKEND_RX
        await self.interface.send_data(uuid, "ARCTIC_COMMAND_GET_SERVICES")

    # Services Information
    def register_services(self, retrieved_services):
        """Retrieves services information from the connected device."""

        # Register Backend Services
        self.backend = BackendIndex()
        self.backend.service = patterns.UUID_UART_BACKEND_ATS
        self.backend.txm = patterns.UUID_UART_BACKEND_TX
        self.backend.rxm = patterns.UUID_UART_BACKEND_RX

        # Register OTA Services
        self.updater = UpdaterIndex()
        self.updater.name = "OTA"
        self.updater.service = patterns.UUID_UART_OTA_ATS
        self.updater.txm = patterns.UUID_UART_OTA_TX
        self.updater.rxm = patterns.UUID_UART_OTA_RX

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

    def parse_services(self, response):
        """Parses services information from the response string."""
        modules = response.replace("ARCTIC_COMMAND_GET_SERVICES:", "")
        modules = response.replace("\n", "")
        modules = modules.split(":")
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

    @qasync.asyncSlot()
    async def enable_device_uplink(self):
        uuid = patterns.UUID_UART_BACKEND_RX
        await self.interface.send_data(uuid, "ARCTIC_COMMAND_ENABLE_UPLINK")

    @qasync.asyncSlot()
    async def disable_device_uplink(self):
        uuid = patterns.UUID_UART_BACKEND_RX
        await self.interface.send_data(uuid, "ARCTIC_COMMAND_DISABLE_UPLINK")

    # --- Callbacks ---

    # Scan List Update
    def cb_scan_ready(self, devices):
        self.scan_device_list.clear()
        for name, address in devices:
            self.scan_device_list.addItem(f"{name} - {address}")

    # Connection Complete
    def cb_link_ready(self, connected):
        if connected:
            self.mw.debug_info(
                f"Device {self.device_port} is ready to receive commands"
            )
            self.connection_event.set()
            self.reconnection_attempts = 0
            self.get_services()

    # Connection Complete (COM)
    def cb_com_link_ready(self, connected):
        if connected:
            self.mw.debug_info("COM Connected. Waiting for device to be ready ...")
        else:
            self.mw.debug_info("COM Disconnected")

    # Disconnected
    def cb_link_lost(self, device_port):
        self.mw.debug_info(f"Device on {device_port} stopped responding.")

        # Reset the interface
        self.interface.disconnect()
        self.connection_event.clear()

        # Autosync enabled. Try to reconnect
        if self.device_port and self.auto_sync_enabled:
            self.mw.debug_info("Attempting reconnection ...")
            self.reconnection_timer.start(5000)

    # Data Received to handle backend commands
    def cb_data_received(self, uuid, data):
        if uuid == patterns.UUID_UART_BACKEND_TX:
            if "ARCTIC_COMMAND_GET_SERVICES" in data:
                services = self.parse_services(data)
                self.register_services(services)

    # Task Halted
    def cb_task_halted(self):
        self.mw.debug_info("UART Interface task was halted")

    # --- Window Functions ---

    # Initialize a new updater window (OTA)
    def create_updater_window(self, name, uuid):
        # Check if the console window is already open
        if self.updater.instance:
            window = self.updater.instance
        else:
            # Console window is not open, create a new one
            window = UpdaterWindow(self.mw, self.interface, name, self.updater)
            self.updater = window
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
                f"Attempting reconnection to {self.device_port} "
                f"(attempt {self.reconnection_attempts}/{self.max_reconnection_attempts})"
            )
            await self.uart_connect()
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
        
        # Check if already disconnected
        if not self.connection_event.is_set():
            self.mw.debug_info("Not connected to any device")
            return
        
        self.reconnection_attempts = 0
        self.reconnection_timer.stop()

        self.mw.debug_info("Clearing UART connection ...")

        # 2. Disconnect from the device
        self.interface.disconnect()

        # 1. Stop consoles and clear references
        self.stop_consoles()

        # 3. Clear device port and connection events
        self.device_port = None
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

    # Stop the UART Handler
    @qasync.asyncSlot()
    async def process_close_task(self, close_window=True):
        self.device_port = None
        if not self.is_closing:
            self.is_closing = True
            self.interface.disconnect()
            self.stop_consoles()
            if close_window:
                self.closingReady.emit()

    # Exit triggered from "exit" button
    def exitApplication(self):
        self.mw.exit_interface()
