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

import sys
import time
from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QLineEdit,
    QHBoxLayout,
    QPushButton,
)
from PyQt5.QtGui import QFontDatabase, QFont, QIcon

import resources.config as app_config
from interfaces.ble_interface import BLEHandler
from interfaces.wifi_interface import WiFiHandler
from interfaces.uart_interface import UARTHandler
from gui.window_properties import SSCWindowProperties
from gui.ble_connection import BLEConnectionWindow
from gui.wifi_connection import WiFiConnectionWindow
from gui.uart_connection import UARTConnectionWindow
from gui.console_window import ConsoleWindow
from helpers.pushbutton_helper import SimpleButton
import helpers.theme_helper as th


class MainWindow(SSCWindowProperties):
    themeChanged = pyqtSignal(str)
    autoSyncStatus = pyqtSignal(bool)
    accumulatorChanged = pyqtSignal(bool)

    def __init__(self, app_main=None):
        super().__init__(self)

        # Default window properties
        self.title = app_config.globals["app"]["name"]
        self.default_size = app_config.globals["app"]["default_size"]
        self.minimum_size = app_config.globals["app"]["minimum_size"]
        self.app_version = app_config.globals["app"]["version"]

        # Window initialization
        self.setWindowTitle(self.title)
        self.set_custom_title(self.title)
        self.resize(*self.default_size)
        self.setMinimumSize(*self.minimum_size)

        # Set the stylesheet
        app_main.setStyleSheet(th.get_style(list(app_config.globals["style"])))
        self.setWindowIcon(QIcon(f"{self.icon_path()}/main_icon.png"))

        # Load the font file (.ttf or .otf)
        QFontDatabase.addApplicationFont(f"{self.font_path()}/Ubuntu-Regular.ttf")
        QFontDatabase.addApplicationFont(f"{self.font_path()}/Inconsolata-Regular.ttf")
        app_main.setFont(QFont("Ubuntu"))

        # Set the status label
        self.set_status_bar("Disconnected")

        # Globals
        self.auto_sync_status = True
        self.connection_tab = None
        self.debug_show = False
        self.start_time = time.time()
        self.interface = None

        # Draw the layout
        self.setup_layout()

        # Set the default theme
        self.theme_status = app_config.globals["gui"]["theme"]
        # self.toggle_theme()

    # --- GUI Functions ---

    def setup_layout(self):
        self.tab_widget = QTabWidget(self)
        self.tab_widget.currentChanged.connect(self.cb_tab_change)
        self.tab_widget.setVisible(False)

        # Single line text area for displaying debug info
        self.line_edit_debug = QLineEdit(self)
        self.line_edit_debug.setFixedHeight(
            app_config.globals["gui"]["debug_line_edit_height"]
        )
        self.line_edit_debug.setStyleSheet(th.get_style("debug_bar_line_edit"))
        self.line_edit_debug.setReadOnly(True)
        self.line_edit_debug.setVisible(self.debug_show)
        self.line_edit_debug.setText(">")

        # Single line text area for displaying version
        self.line_edit_version = QLineEdit(self)
        self.line_edit_version.setAlignment(Qt.AlignCenter)
        self.line_edit_version.setFixedWidth(80)
        self.line_edit_version.setFixedHeight(
            app_config.globals["gui"]["debug_line_edit_height"]
        )
        self.line_edit_version.setStyleSheet(th.get_style("debug_bar_line_edit"))
        self.line_edit_version.setReadOnly(True)
        self.line_edit_version.setVisible(self.debug_show)
        self.line_edit_version.setText(self.app_version)

        # Connector BLE button
        self.ble_button = SimpleButton(
            self,
            icon=f"{self.icons_dir}/bluetooth_FILL0_wght300_GRAD0_opsz24.svg",
            style=th.get_style("connectors_button"),
            callback=self.connect_ble,
        )
        self.ble_button.setIconSize(
            QSize(*app_config.globals["gui"]["connectors_icon_size"])
        )

        # Connector USB button
        self.usb_button = SimpleButton(
            self,
            icon=f"{self.icons_dir}/usb_FILL0_wght300_GRAD0_opsz24.svg",
            style=th.get_style("connectors_button"),
            callback=self.connect_uart,
        )
        self.usb_button.setIconSize(
            QSize(*app_config.globals["gui"]["connectors_icon_size"])
        )

        # Connector WiFi button
        self.wifi_button = SimpleButton(
            self,
            icon=f"{self.icons_dir}/wifi_FILL0_wght300_GRAD0_opsz24.svg",
            style=th.get_style("connectors_button"),
            callback=self.connect_wifi,
        )
        self.wifi_button.setIconSize(
            QSize(*app_config.globals["gui"]["connectors_icon_size"])
        )

        self.ble_descriptor = QPushButton("Bluetooth", self)
        self.ble_descriptor.setStyleSheet(th.get_style("connectors_desc_button"))
        self.usb_descriptor = QPushButton("USB", self)
        self.usb_descriptor.setStyleSheet(th.get_style("connectors_desc_button"))
        self.wifi_descriptor = QPushButton("WiFi", self)
        self.wifi_descriptor.setStyleSheet(th.get_style("connectors_desc_button"))

        connectors_layout = QHBoxLayout()
        connectors_layout.addWidget(self.ble_button)
        connectors_layout.addWidget(self.usb_button)
        connectors_layout.addWidget(self.wifi_button)

        descriptors_layout = QHBoxLayout()
        descriptors_layout.addWidget(self.ble_descriptor)
        descriptors_layout.addWidget(self.usb_descriptor)
        descriptors_layout.addWidget(self.wifi_descriptor)

        debug_layout = QHBoxLayout()
        debug_layout.addWidget(self.line_edit_debug)
        debug_layout.addWidget(self.line_edit_version)

        # Central widget to hold the layout
        main_window_layout = QVBoxLayout()
        main_window_layout.addWidget(self.tab_widget)
        main_window_layout.addLayout(connectors_layout)
        main_window_layout.addLayout(descriptors_layout)
        main_window_layout.addLayout(debug_layout)

        central_widget = QWidget()
        central_widget.setLayout(main_window_layout)
        self.setCentralWidget(central_widget)

    # Window Functions

    # Update the debug info
    def debug_info(self, text):
        self.line_edit_debug.setText(f"> {text}")

        # Log to console
        self.debug_log(text)

    # Log debug data
    def debug_log(self, text):
        elapsed_time = (time.time() - self.start_time) * 1000
        log_entry = f"[{elapsed_time:.3f}]\t{text}"
        print(log_entry)

    # Add a connection tab dynamically
    def add_connection_tab(self, console_widget, title):
        tabIndex = self.tab_widget.addTab(console_widget, title)
        self.debug_log(f"Adding tab: {title} with index {tabIndex}")
        return tabIndex

    # Add a console tab dynamically
    def add_console_tab(self, console_widget, title):
        tabIndex = self.tab_widget.addTab(console_widget, title)
        self.themeChanged.emit(self.theme_status)  # Update theme for new tab
        self.debug_log(f"Adding tab: {title} with index {tabIndex}")
        return tabIndex

    # Add a updater tab dynamically
    def add_updater_tab(self, console_widget, title):
        tabIndex = self.tab_widget.addTab(console_widget, title)
        self.themeChanged.emit(self.theme_status)  # Update theme for new tab
        self.debug_log(f"Adding tab: {title}")
        return tabIndex
    
    # Remove a tab 
    def remove_tab(self, index):
        self.debug_log(f"Removing tab: {index}")
        self.tab_widget.removeTab(index)

    def update_tab_title(self, console, title):
        index = self.tab_widget.indexOf(console)
        if index != -1:
            self.tab_widget.setTabText(index, title)

    def visibility_tab(self, console, status):
        index = self.tab_widget.indexOf(console)
        if index != -1:
            self.tab_widget.setTabVisible(index, status)

    def set_status_bar(self, mode):
        if mode == "Connected":
            self.set_marging("rgba(0, 100, 0, 128)", 3)
            self.con_status_button.setStyleSheet(
                """
                font-size: 12px;
                color: white;
                background-color: rgba(0, 139, 0, 128);
                border-radius: 10px;
                margin-right: 10px;
                margin-left: 10px;
                """
            )
            self.con_status_button.setText("Connected")
        elif mode == "Disconnected":
            self.set_marging("rgba(255, 255, 255, 128)", 3)
            self.con_status_button.setStyleSheet(
                """
                font-size: 12px;
                color: white;
                background-color: rgba(139, 0, 0, 128);
                border-radius: 10px;
                margin-right: 10px;
                margin-left: 10px;
                """
            )
            self.con_status_button.setText("Disconnected")

    def set_marging(self, color, size):
        self.setStyleSheet(f"MainWindow {{border: {size}px solid {color};}}")
        self.setContentsMargins(size, size, size, size)

    # Get the icon path
    def icon_path(self):
        if getattr(sys, "frozen", False):
            application_path = Path(sys._MEIPASS)
        else:
            application_path = Path(__file__).resolve().parent.parent
        icons_dir = application_path / "resources" / "icons"
        return icons_dir

    # Get the font path
    def font_path(self):
        if getattr(sys, "frozen", False):
            application_path = Path(sys._MEIPASS)
        else:
            application_path = Path(__file__).resolve().parent.parent
        font_dir = application_path / "resources" / "fonts"
        return font_dir

    # --- Callbacks ---

    def cb_tab_change(self, index):
        console = self.tab_widget.widget(index)
        if isinstance(console, ConsoleWindow):
            console.resetCounter()

    # Callback connection success
    def cb_link_ready(self, connected):
        if not connected:
            return
        self.set_status_bar("Connected")

    # Callback device disconnected
    def cb_link_lost(self, client):
        self.set_status_bar("Disconnected")

    # Callback toggle theme
    def toggle_theme(self, status=False):
        if self.theme_status == "dark":
            self.theme_status = "light"
        else:
            self.theme_status = "dark"

        th.toggle_theme()  # Update global theme
        QApplication.instance().setStyleSheet(
            th.get_style(list(app_config.globals["style"]))
        )
        self.ble_button.setStyleSheet(th.get_style("connectors_button"))
        self.usb_button.setStyleSheet(th.get_style("connectors_button"))
        self.wifi_button.setStyleSheet(th.get_style("connectors_button"))

        self.ble_descriptor.setStyleSheet(th.get_style("connectors_desc_button"))
        self.usb_descriptor.setStyleSheet(th.get_style("connectors_desc_button"))
        self.wifi_descriptor.setStyleSheet(th.get_style("connectors_desc_button"))

        self.line_edit_debug.setStyleSheet(th.get_style("debug_bar_line_edit"))
        self.line_edit_version.setStyleSheet(th.get_style("debug_bar_line_edit"))

        # Update special widgets by theme
        if self.theme_status == "dark":
            self.ble_button.changeIconColor("#ffffff")
            self.usb_button.changeIconColor("#ffffff")
            self.wifi_button.changeIconColor("#ffffff")
        elif self.theme_status == "light":
            self.ble_button.changeIconColor("#303030")
            self.usb_button.changeIconColor("#303030")
            self.wifi_button.changeIconColor("#303030")

        # Update children widgets
        self.themeChanged.emit(self.theme_status)

    def toggle_debug(self):
        if self.debug_show:
            self.debug_show = False
            self.line_edit_debug.setVisible(False)
            self.line_edit_version.setVisible(False)
        else:
            self.debug_show = True
            self.line_edit_debug.setVisible(True)
            self.line_edit_version.setVisible(True)
    
    def toggle_accumulator(self, status):
        self.accumulator_status = status
        self.accumulatorChanged.emit(status)

    def toggle_autosync(self, status):
        self.auto_sync_status = status
        self.autoSyncStatus.emit(self.auto_sync_status)

    def connect_ble(self):
        self.debug_info("Interface selected: BLE")
        self.interface = BLEHandler()
        self.connection_tab = BLEConnectionWindow(self, self.interface, "BLE")
        self.connection_tab.closingReady.connect(self.cb_finalize_close)
        self.interface.linkReady.connect(self.cb_link_ready)
        self.interface.linkLost.connect(self.cb_link_lost)
        self.tab_widget.setVisible(True)
        self.hide_interfaces()
        self.autoSyncStatus.emit(self.auto_sync_status)
        self.themeChanged.emit(self.theme_status)

    def connect_wifi(self):
        self.debug_info("Interface selected: WiFi")
        self.interface = WiFiHandler()
        self.connection_tab = WiFiConnectionWindow(self, self.interface, "WiFi")
        self.connection_tab.closingReady.connect(self.cb_finalize_close)
        self.interface.linkReady.connect(self.cb_link_ready)
        self.interface.linkLost.connect(self.cb_link_lost)
        self.tab_widget.setVisible(True)
        self.hide_interfaces()
        self.autoSyncStatus.emit(self.auto_sync_status)
        self.themeChanged.emit(self.theme_status)

    def connect_uart(self):
        self.debug_info("Interface selected: UART")
        self.interface = UARTHandler()
        self.connection_tab = UARTConnectionWindow(self, self.interface, "UART")
        self.connection_tab.closingReady.connect(self.cb_finalize_close)
        self.interface.linkReady.connect(self.cb_link_ready)
        self.interface.linkLost.connect(self.cb_link_lost)
        self.tab_widget.setVisible(True)
        self.hide_interfaces()
        self.autoSyncStatus.emit(self.auto_sync_status)
        self.themeChanged.emit(self.theme_status)

    def exit_interface(self):
        # Close the connection tab
        self.connection_tab.close()
        self.connection_tab = None

        # Clear the current tab
        current_index = self.tab_widget.currentIndex()
        if current_index != -1:
            self.tab_widget.removeTab(current_index)

        self.tab_widget.setVisible(False)
        self.show_interfaces()

    def hide_interfaces(self):
        self.ble_button.setVisible(False)
        self.usb_button.setVisible(False)
        self.wifi_button.setVisible(False)
        self.ble_descriptor.setVisible(False)
        self.usb_descriptor.setVisible(False)
        self.wifi_descriptor.setVisible(False)

    def show_interfaces(self):
        self.ble_button.setVisible(True)
        self.usb_button.setVisible(True)
        self.wifi_button.setVisible(True)
        self.ble_descriptor.setVisible(True)
        self.usb_descriptor.setVisible(True)
        self.wifi_descriptor.setVisible(True)

    # --- Qt Events ---

    # Reimplement the resizeEvent
    def resizeEvent(self, event):
        super(MainWindow, self).resizeEvent(event)

    def closeEvent(self, event):
        if self.connection_tab is not None and not self.connection_tab.is_closing:
            self.windowClose.emit()
            event.ignore()
        else:
            event.accept()

    def cb_finalize_close(self):
        self.close()
