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

import os
import time
import qasync
import hashlib
from datetime import datetime

import asyncio
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QLineEdit,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QFileDialog,
    QProgressBar,
)
from PyQt5.QtGui import QTextCursor, QFont

import resources.config as app_config
from interfaces.ble_interface import BLEHandler
from resources.indexer import UpdaterIndex
from helpers.pushbutton_helper import SimpleButton
import helpers.theme_helper as th


class UpdaterWindow(QWidget):
    def __init__(
        self,
        main_window,
        stream_interface: BLEHandler,
        title,
        updater_index: UpdaterIndex,
    ):
        super().__init__()
        self.main_window = main_window  # MainWindow Reference
        self.stream_interface = stream_interface  # BLE Reference
        self.win_title = title  # Original title of the tab
        self.updater_index = updater_index  # Console information

        self.main_window.debug_log("UpdaterWindow: Initializing ...")
        self.main_window.debug_log(f"UpdaterWindow: {self.updater_index.name}")
        self.main_window.debug_log(
            f"UpdaterWindow: {self.updater_index.service.uuid}")
        self.main_window.debug_log(
            f"UpdaterWindow: {self.updater_index.tx_characteristic.uuid}"
        )
        self.main_window.debug_log(
            f"UpdaterWindow: {self.updater_index.rx_characteristic.uuid}"
        )
        self.main_window.debug_log(
            "------------------------------------------")

        # Async BLE Signals
        self.stream_interface.notificationReceived.connect(
            self.callback_handle_notification
        )
        self.stream_interface.deviceDisconnected.connect(
            self.callback_disconnected)
        self.main_window.themeChanged.connect(self.callback_update_theme)

        # Async Events from the device
        self.ready_event = asyncio.Event()
        self.ack_event = asyncio.Event()
        self.error_event = asyncio.Event()
        self.success_event = asyncio.Event()
        self.disconnect_event = asyncio.Event()
        self.stop_event = asyncio.Event()

        # Window usability flags
        self.setAcceptDrops(True)

        # Globals
        self.ota_running = False
        self.firmware_path = None
        self.mtu_size = app_config.globals["updater"]["chunk_size"]
        self.start_time = 0
        self.elapsed_str = "00:00:00"
        self.ota_error_status = False
        self.icons_dir = self.main_window.icon_path()

        self.setup_layout()

    # GUI Functions ------------------------------------------------------------------------------------------

    # Layout and Widgets
    def setup_layout(self):

        # Start and Stop buttons
        start_button = QPushButton("Start", self)
        start_button.clicked.connect(self.start_ota)
        stop_button = QPushButton("Stop", self)
        stop_button.clicked.connect(self.stop_ota)
        clear_button = QPushButton("Clear", self)
        clear_button.clicked.connect(self.clear_text)
        reload_button = QPushButton("Reload", self)
        reload_button.clicked.connect(self.reload_file)

        # Simple folder button
        self.folder_button = SimpleButton(
            self,
            icon=f"{
                self.icons_dir}/drive_folder_upload_FILL0_wght400_GRAD0_opsz24.svg",
            size=app_config["gui"]["default_button_size"],
            style=th.get_style("default_button_style"),
            callback=self.setPath,
        )

        # Main text area for accumulating text
        self.text_edit_printf = QPlainTextEdit(self)
        self.text_edit_printf.setFont(QFont("Inconsolata"))
        self.text_edit_printf.setReadOnly(True)

        # Placeholder text
        self.drag_placeholder = QLineEdit(
            "Drag your firmware here or select your firmware path", self
        )
        self.drag_placeholder.setFont(QFont("Inconsolata"))
        self.drag_placeholder.setGeometry(self.text_edit_printf.geometry())
        self.drag_placeholder.setStyleSheet(
            th.get_style("updater_placeholder_line_edit_style")
        )
        self.drag_placeholder.setReadOnly(True)
        self.drag_placeholder.setAlignment(Qt.AlignCenter)
        self.drag_placeholder.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.show_drag_placeholder(True)
        self.adjust_drag_placeholder()

        # Single line text area for displaying info
        self.line_edit_singlef = QLineEdit(self)
        self.line_edit_singlef.setFont(QFont("Inconsolata"))
        self.line_edit_singlef.setFixedHeight(
            app_config["gui"]["default_line_edit_height"]
        )
        self.line_edit_singlef.setReadOnly(True)

        # Create the progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setFixedHeight(
            app_config["gui"]["default_loading_bar_height"]
        )
        self.progress_bar.setStyleSheet(
            th.get_style("default_loading_bar_style"))
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)

        # Layout for Start and Stop buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(start_button)
        buttons_layout.addWidget(stop_button)
        buttons_layout.addWidget(clear_button)
        buttons_layout.addWidget(reload_button)
        buttons_layout.addWidget(self.folder_button)

        # Update the main layout
        updater_win_layout = QVBoxLayout()
        updater_win_layout.addLayout(buttons_layout)
        updater_win_layout.addWidget(self.text_edit_printf)
        updater_win_layout.addWidget(self.line_edit_singlef)
        updater_win_layout.addWidget(self.progress_bar)
        self.setLayout(updater_win_layout)

    # Window Functions ------------------------------------------------------------------------------------------

    def adjust_drag_placeholder(self):
        self.drag_placeholder.setGeometry(self.text_edit_printf.geometry())

    def show_drag_placeholder(self, visible):
        self.drag_placeholder.setVisible(visible)

    def highlight_drag_box(self, highlight):
        if highlight:
            self.text_edit_printf.setStyleSheet(
                th.get_style("updater_highligh_ptext_edit_style")
            )
        else:
            self.text_edit_printf.setStyleSheet(
                th.get_style("default_text_edit_style"))

    def callback_update_theme(self, theme):
        # Reload stylesheets (background for buttons)
        self.folder_button.setStyleSheet(th.get_style("default_button_style"))
        self.drag_placeholder.setStyleSheet(
            th.get_style("updater_placeholder_line_edit_style")
        )
        self.text_edit_printf.setStyleSheet(
            th.get_style("default_text_edit_style"))

        if self.ota_error_status:  # If in error state
            self.progress_bar.setStyleSheet(
                th.get_style("uploader_loading_bar_fail_style")
            )
        else:
            self.progress_bar.setStyleSheet(
                th.get_style("default_loading_bar_style"))

        # Update special widgets by theme
        if theme == "dark":
            self.folder_button.changeIconColor("#ffffff")
        elif theme == "light":
            self.folder_button.changeIconColor("#000000")

    # Qt Functions ------------------------------------------------------------------------------------------------

    def resizeEvent(self, event):
        self.adjust_drag_placeholder()
        super().resizeEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.highlight_drag_box(True)

    def dragLeaveEvent(self, event):
        self.highlight_drag_box(False)

    def dropEvent(self, event):
        self.highlight_drag_box(False)

        urls = event.mimeData().urls()
        if urls and len(urls) > 0:
            file_path = str(urls[0].toLocalFile())
            if file_path.endswith(".bin"):
                self.firmware_path = file_path
                self.update_info(f"Loaded file: {self.firmware_path}")
                self.extract_file_info(self.firmware_path)
            else:
                self.update_info("Not a .bin file")

    # Async BLE Functions ------------------------------------------------------------------------------------------

    @qasync.asyncSlot()
    async def start_ota(self):

        if self.firmware_path is None:
            self.main_window.debug_log("No file selected.")
            return

        file_hash = self.calculate_hash(self.firmware_path)
        file_size = self.get_file_size(self.firmware_path)
        if file_size == 0:
            self.main_window.debug_log("File is empty, aborting OTA update")
            return

        if self.ota_running:
            self.main_window.debug_log("OTA update is already in progress.")
            return

        self.initialize_ota()  # Initializing OTA-specific variables and settings

        if not await self.wait_for_device_ready(file_size, file_hash):
            return

        await self.transfer_file(file_size)

    def initialize_ota(self):
        self.start_time = datetime.now()
        self.ota_running = True
        self.ota_error_status = False
        self.clear_events()
        self.progress_bar.setStyleSheet(
            th.get_style("default_loading_bar_style"))
        self.progress_bar.setValue(0)

    def clear_events(self):
        events = [
            self.ready_event,
            self.ack_event,
            self.error_event,
            self.success_event,
            self.stop_event,
        ]
        for event in events:
            event.clear()

    def get_file_size(self, file_path):
        return os.path.getsize(file_path)

    async def send_file_info(self, total_size, file_hash):
        await self.stream_interface.writeCharacteristic(
            self.updater_index.rx_characteristic.uuid,
            str(f"ARCTIC_COMMAND_OTA_SETUP -s {
                total_size} -md5 {file_hash}").encode(),
        )

    async def wait_for_device_ready(
        self,
        total_size,
        file_hash,
        max_retries=app_config.globals["updater"]["ack_retries"],
    ):
        retries = 0
        while retries < max_retries:
            try:
                await self.send_file_info(total_size, file_hash)
                await asyncio.wait_for(
                    self.ready_event.wait(),
                    timeout=app_config.globals["updater"]["ack_timeout"],
                )
                self.main_window.debug_log("Device is ready.")
                return True
            except asyncio.TimeoutError:
                self.main_window.debug_log(
                    f"Timeout waiting for device to be ready. Retrying {
                        retries+1}/{max_retries}..."
                )
                retries += 1

        self.main_window.debug_log(
            "Device not ready after maximum retries. OTA update aborted."
        )
        self.ota_running = False
        return False

    async def transfer_file(self, total_size):
        try:
            with open(self.firmware_path, "rb") as file:
                await self.file_transfer_loop(file, total_size)
        except IOError as e:
            self.main_window.debug_log(f"Error reading file: {e}")

    async def file_transfer_loop(self, file, total_size):
        transferred = 0
        while self.ota_running and transferred < total_size:
            # Check if a disconnect event occurred
            if self.disconnect_event.is_set():
                self.main_window.debug_log(
                    "OTA update aborted due to disconnection.")
                self.progress_bar.setStyleSheet(
                    th.get_style("uploader_loading_bar_fail_style")
                )
                self.ota_error_status = True
                self.ota_running = False
                return

            dataChunk = file.read(self.mtu_size)
            if not await self.send_chunk_with_retries(dataChunk):
                break

            transferred += len(dataChunk)
            self.update_progress_bar(transferred, total_size)

        if transferred >= total_size:
            self.update_info(f"OTA Complete. Transferred {transferred} bytes.")
            self.ota_running = False

    def update_progress_bar(self, transferred, total_size):
        progress = int((transferred / total_size) * 100)
        self.progress_bar.setValue(progress)
        elapsed_time = datetime.now() - self.start_time
        self.elapsed_str = str(elapsed_time).split(".")[0]
        kbytes_per_second = (transferred / elapsed_time.total_seconds()) / 1024
        self.update_info(
            f"[{self.elapsed_str}] OTA Loading Progress: {
                progress}% ({transferred}/{total_size} bytes, {kbytes_per_second:.2f} kb/s)"
        )

    async def send_chunk_with_retries(
        self, dataChunk, max_retries=app_config.globals["updater"]["ack_retries"]
    ):
        retries = 0
        while retries < max_retries:
            if self.disconnect_event.is_set():
                self.main_window.debug_log(
                    "OTA update aborted due to disconnection.")
                self.progress_bar.setStyleSheet(
                    th.get_style("uploader_loading_bar_fail_style")
                )
                self.ota_error_status = True
                self.ota_running = False
                return False

            sent = await self.send_chunk_and_wait_for_ack(dataChunk)
            if sent:
                return True
            retries += 1

        self.main_window.debug_log("Maximum retries reached, stopping OTA")
        self.progress_bar.setStyleSheet(
            th.get_style("uploader_loading_bar_fail_style"))
        self.ota_error_status = True
        self.ota_running = False
        return False

    async def send_chunk_and_wait_for_ack(self, dataChunk):
        self.ack_event.clear()
        if app_config.globals["updater"]["enable_output_debug"]:
            self.main_window.debug_log(
                f"Sending chunk of {len(dataChunk)} bytes")
        await self.stream_interface.writeCharacteristic(
            self.updater_index.rx_characteristic.uuid, dataChunk
        )
        return await self.wait_for_ack_or_stop()

    async def wait_for_ack_or_stop(self):
        ack_task = asyncio.create_task(self.ack_event.wait())
        stop_task = asyncio.create_task(self.stop_event.wait())

        done, pending = await asyncio.wait(
            [ack_task, stop_task],
            timeout=app_config.globals["updater"]["ack_timeout"],
            return_when=asyncio.FIRST_COMPLETED,
        )

        if self.stop_event.is_set():
            self.handle_stop_event()
            return False

        if self.ack_event.is_set():
            return True

        if app_config.globals["updater"]["enable_output_debug"]:
            self.main_window.debug_log("ACK not received for chunk, retrying")
        return False

    def handle_stop_event(self):
        if self.success_event.is_set():
            self.update_info(f"[{self.elapsed_str}] OTA Loading completed")
            self.progress_bar.setStyleSheet(
                th.get_style("default_loading_bar_style"))
        elif self.error_event.is_set():
            self.progress_bar.setStyleSheet(
                th.get_style("uploader_loading_bar_fail_style")
            )
            self.update_info(f"[{self.elapsed_str}] OTA Error received")
            self.ota_error_status = True
        elif self.disconnect_event.is_set():
            self.progress_bar.setStyleSheet(
                th.get_style("uploader_loading_bar_fail_style")
            )
            self.update_info(f"[{self.elapsed_str}] OTA Device disconnected")
            self.ota_error_status = True
        else:
            self.progress_bar.setStyleSheet(
                th.get_style("uploader_loading_bar_fail_style")
            )
            self.update_info(f"[{self.elapsed_str}] OTA Loading aborted")
            self.ota_error_status = True

        self.ota_running = False

    @qasync.asyncSlot()
    async def stop_ota(self):
        self.stop_event.set()

    # Callbacks -----------------------------------------------------------------------------------------------

    # Callback handle input notification
    def callback_handle_notification(self, sender, data):

        # Redirect the data to the printf text box
        if sender == self.updater_index.tx_characteristic.uuid:
            self.update_info(data)

    def callback_disconnected(self, client):
        if self.ota_running:
            self.stop_event.set()
            self.disconnect_event.set()

    # Window Functions ------------------------------------------------------------------------------------------

    # Update the main text box (printf)
    def update_data(self, data):
        self.show_drag_placeholder(False)
        self.text_edit_printf.clear()
        self.text_edit_printf.moveCursor(QTextCursor.End)
        self.text_edit_printf.insertPlainText(data)
        self.text_edit_printf.moveCursor(QTextCursor.End)

    # Update the info text box (singlef)
    def update_info(self, info):

        # ACKs coming from the device
        if "READY" in info:
            self.ready_event.set()
            if app_config.globals["updater"]["enable_output_debug"]:
                self.main_window.debug_log("Device ready")
        elif "ACK" in info:
            self.ack_event.set()
            if app_config.globals["updater"]["enable_output_debug"]:
                self.main_window.debug_log("Device ack")
        elif "ERROR" in info:
            self.error_event.set()
            self.stop_event.set()
            if app_config.globals["updater"]["enable_output_debug"]:
                self.main_window.debug_log("Device error")
        elif "DONE" in info:
            self.success_event.set()
            self.stop_event.set()
            if app_config.globals["updater"]["enable_output_debug"]:
                self.main_window.debug_log("Device done")
        elif "TIMEOUT" in info:
            self.error_event.set()
            self.stop_event.set()
            if app_config.globals["updater"]["enable_output_debug"]:
                self.main_window.debug_log("Device timeout")
        else:  # Info coming from the program
            self.line_edit_singlef.setText(info)

    # Reload the file
    def reload_file(self):
        if self.firmware_path:
            self.extract_file_info(self.firmware_path)
        else:
            self.update_info("No file loaded")

    # Path folder button
    def setPath(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select a .bin file", "", "Bin Files (*.bin)", options=options
        )
        if file_path:
            self.firmware_path = file_path
            self.extract_file_info(self.firmware_path)

    # Extract file information and update the text box
    def extract_file_info(self, file_path):
        fileName = os.path.basename(file_path)
        fileSize = os.path.getsize(file_path)
        fileLocation = os.path.dirname(file_path)
        lastModifiedTime = time.ctime(os.path.getmtime(file_path))
        creationTime = time.ctime(os.path.getctime(file_path))
        fileHash = self.calculate_hash(file_path)

        # Update the information
        otaInformation = (
            f"OTA Information:\n\n"
            f"- File Name: {fileName}\n"
            f"- File Size: {fileSize} bytes\n"
            f"- Last Modified: {lastModifiedTime}\n\n"
            f"- File Location: {fileLocation}\n"
            f"- Creation Time: {creationTime}\n\n"
            f"- File Hash: {fileHash}\n"
        )

        # Update the text box
        self.update_data(otaInformation)

    # Reset the window to its initial state
    def clear_text(self):
        self.firmware_path = None
        self.text_edit_printf.clear()
        self.line_edit_singlef.clear()
        self.show_drag_placeholder(True)
        self.progress_bar.setValue(0)

    # Calculate the hash of a file
    def calculate_hash(self, file_path, hashType="md5"):
        hashFunc = getattr(hashlib, hashType)()
        with open(file_path, "rb") as file:
            for chunk in iter(lambda: file.read(4096), b""):
                hashFunc.update(chunk)
        return hashFunc.hexdigest()
