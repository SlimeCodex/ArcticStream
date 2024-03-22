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

import qasync
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QLineEdit,
    QPushButton,
    QPlainTextEdit,
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QFileDialog,
    QSplitter,
)
from PyQt5.QtGui import QTextCursor, QFont, QTextCharFormat
from datetime import datetime

import resources.config as app_config
from interfaces.base_interface import CommunicationInterface
from resources.indexer import ConsoleIndex
from helpers.pushbutton_helper import ToggleButton, SimpleButton
import helpers.theme_helper as th
from resources.tooltips import tooltips


class ConsoleWindow(QWidget):
    def __init__(
        self,
        main_window,
        interface: CommunicationInterface,
        title,
        index: ConsoleIndex,
    ):
        super().__init__()

        self.mw = main_window  # MainWindow Reference
        self.interface = interface  # BLE Reference
        self.win_title = title  # Original title of the tab
        self.index = index  # Console information
        self.tooltip_index = tooltips["console_window"]

        if False:
            self.mw.debug_log("ConsoleWindow: Initializing ...")
            self.mw.debug_log(f"ConsoleWindow: {self.index.name}")
            self.mw.debug_log(f"ConsoleWindow: {self.index.service}")
            self.mw.debug_log(f"ConsoleWindow: {self.index.txm}")
            self.mw.debug_log(f"ConsoleWindow: {self.index.txs}")
            self.mw.debug_log(f"ConsoleWindow: {self.index.rxm}")
            self.mw.debug_log("--------------------------------")

        # Async window signals
        self.mw.accumulatorChanged.connect(self.toggle_accumulator)

        # Async BLE Signals
        self.interface.linkReady.connect(self.cb_link_ready)
        self.interface.linkLost.connect(self.cb_link_lost)
        self.interface.dataReceived.connect(self.cb_data_received)
        self.mw.themeChanged.connect(self.cb_update_theme)

        # Globals
        self.icons_dir = self.mw.icon_path()
        self.data_tab_counter = 0
        self.scroll_locked = True
        self.console_paused = False
        self.logging_enabled = False
        self.user_log_path = None

        self.total_lines = 0
        self.total_bytes_received = 0
        self.last_received_timestamp = 0
        self.total_data_counter = 0

        self.acumulator_status = False

        # Configure and generate the layout
        self.setup_layout()
        self.draw_layout()

    # GUI Functions

    # Layout and Widgets
    def setup_layout(self):

        # QPushButton: Start, Stop, Clear, Copy, Log
        self.start_button = QPushButton("Start", self)
        self.start_button.setToolTip(self.tooltip_index["start_button"])
        self.start_button.clicked.connect(self.start_console)
        self.stop_button = QPushButton("Stop", self)
        self.stop_button.setToolTip(self.tooltip_index["stop_button"])
        self.stop_button.clicked.connect(self.pause_console)
        self.clear_button = QPushButton("Clear", self)
        self.clear_button.setToolTip(self.tooltip_index["clear_button"])
        self.clear_button.clicked.connect(self.clear_text)
        self.copy_button = QPushButton("Copy", self)
        self.copy_button.setToolTip(self.tooltip_index["copy_button"])
        self.copy_button.clicked.connect(self.copy_text)
        self.log_button = QPushButton("Log", self)
        self.log_button.setToolTip(self.tooltip_index["log_button"])
        self.log_button.clicked.connect(self.log_text)

        # SimpleButton: Send button
        self.send_button = SimpleButton(
            self,
            icon=f"{self.icons_dir}/play_arrow_FILL0_wght400_GRAD0_opsz24.svg",
            size=app_config.globals["gui"]["default_button_size"],
            style=th.get_style("default_button"),
            callback=self.send_data,
        )
        self.send_button.setToolTip(self.tooltip_index["send_button"])

        # ToggleButton: Toggle show timestamp
        self.show_timestamp = ToggleButton(
            self,
            icons=(
                f"{self.icons_dir}/keyboard_double_arrow_left_FILL0_wght400_GRAD0_opsz24.svg",
                f"{self.icons_dir}/keyboard_double_arrow_right_FILL0_wght400_GRAD0_opsz24.svg",
            ),
            size=app_config.globals["gui"]["default_button_size"],
            style=th.get_style("default_button"),
            callback=self.toggle_timestamp,
            toggled=True,
        )
        self.show_timestamp.setToolTip(self.tooltip_index["show_timestamp"])

        # ToggleButton: Toggle text wrap
        self.wrap_button = ToggleButton(
            self,
            icons=(
                f"{self.icons_dir}/format_text_clip_FILL0_wght400_GRAD0_opsz24.svg",
                f"{self.icons_dir}/format_text_wrap_FILL0_wght400_GRAD0_opsz24.svg",
            ),
            size=app_config.globals["gui"]["default_button_size"],
            style=th.get_style("default_button"),
            callback=self.toggle_wrap,
            toggled=True,
        )
        self.wrap_button.setToolTip(self.tooltip_index["wrap_button"])

        # ToggleButton: Toggle lock button
        self.lock_button = ToggleButton(
            self,
            icons=(
                f"{self.icons_dir}/lock_open_right_FILL0_wght400_GRAD0_opsz24.svg",
                f"{self.icons_dir}/lock_FILL0_wght400_GRAD0_opsz24.svg",
            ),
            size=app_config.globals["gui"]["default_button_size"],
            style=th.get_style("default_button"),
            callback=self.toggle_lock,
            toggled=True,
        )
        self.lock_button.setToolTip(self.tooltip_index["lock_button"])

        # ToggleButton: Toggle status bar
        self.toggle_status_bar_button = ToggleButton(
            self,
            icons=(
                f"{self.icons_dir}/keyboard_double_arrow_up_FILL0_wght400_GRAD0_opsz24.svg",
                f"{self.icons_dir}/keyboard_double_arrow_down_FILL0_wght400_GRAD0_opsz24.svg",
            ),
            size=app_config.globals["gui"]["default_button_size"],
            style=th.get_style("default_button"),
            callback=self.toggle_status_bar,
            toggled=False,
        )
        self.toggle_status_bar_button.setToolTip(
            self.tooltip_index["show_metadata"])

        # QPlainTextEdit: Plain text area for timestamp
        self.text_edit_timestamp = QPlainTextEdit(self)
        self.text_edit_timestamp.setStyleSheet(
            th.get_style("timestamp_ptext_edit"))
        self.text_edit_timestamp.setFont(QFont("Inconsolata"))
        self.text_edit_timestamp.setReadOnly(True)
        self.text_edit_timestamp.setMaximumBlockCount(
            app_config.globals["console"]["line_limit"]
        )
        self.text_edit_timestamp.verticalScrollBar().setVisible(False)
        self.text_edit_timestamp.verticalScrollBar().setStyleSheet(
            th.get_style("scroll_bar_hide")
        )
        self.text_edit_timestamp.horizontalScrollBar().setVisible(False)
        self.text_edit_timestamp.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.text_edit_timestamp.setVisible(False)
        self.text_edit_timestamp.verticalScrollBar().valueChanged.connect(
            self.sync_scroll
        )

        # QPlainTextEdit: Main text area for accumulating text (printf)
        self.text_edit_printf = QPlainTextEdit(self)
        self.text_edit_printf.setFont(QFont("Inconsolata"))
        self.text_edit_printf.setReadOnly(True)
        self.text_edit_printf.setMaximumBlockCount(
            app_config.globals["console"]["line_limit"]
        )
        self.text_edit_printf.verticalScrollBar().valueChanged.connect(self.sync_scroll)

        # QLineEdit: Main data meta info
        self.status_overlay = QLineEdit(self)
        self.status_overlay.setFont(QFont("Inconsolata"))
        self.status_overlay.setStyleSheet(
            th.get_style("console_status_line_edit"))
        self.status_overlay.setReadOnly(True)
        self.status_overlay.setAlignment(Qt.AlignCenter)
        self.status_overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.update_status()

        # QLineEdit: Single line text area for displaying info (singlef)
        self.line_edit_singlef = QLineEdit(self)
        self.line_edit_singlef.setFont(QFont("Inconsolata"))
        self.line_edit_singlef.setFixedHeight(
            app_config.globals["gui"]["default_line_edit_height"]
        )
        self.line_edit_singlef.setReadOnly(True)

        # QLineEdit: Input text box for sending data
        self.line_edit_send = QLineEdit(self)
        self.line_edit_send.setFont(QFont("Inconsolata"))
        self.line_edit_send.setFixedHeight(
            app_config.globals["gui"]["default_line_edit_height"]
        )
        self.line_edit_send.setStyleSheet(
            th.get_style("console_send_line_edit"))
        self.line_edit_send.setPlaceholderText("Insert data to send ...")

    def draw_layout(self):

        # Layout for buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.show_timestamp)
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.stop_button)
        buttons_layout.addWidget(self.clear_button)
        buttons_layout.addWidget(self.copy_button)
        buttons_layout.addWidget(self.log_button)
        buttons_layout.addWidget(self.wrap_button)
        buttons_layout.addWidget(self.toggle_status_bar_button)

        # Splitter for the text boxes
        main_text_layout = QSplitter(Qt.Horizontal)
        main_text_layout.addWidget(self.text_edit_timestamp)
        main_text_layout.addWidget(self.text_edit_printf)
        main_text_layout.setCollapsible(0, False)
        main_text_layout.setSizes([120, 480])

        # Layout for info data and lock button
        info_data_layout = QHBoxLayout()
        info_data_layout.addWidget(self.line_edit_singlef)
        info_data_layout.addWidget(self.lock_button)

        # Layout for send data
        send_data_layout = QHBoxLayout()
        send_data_layout.addWidget(self.line_edit_send)
        send_data_layout.addWidget(self.send_button)

        # Main layout
        console_win_layout = QVBoxLayout()
        console_win_layout.addLayout(buttons_layout)
        console_win_layout.addWidget(self.status_overlay)
        console_win_layout.addWidget(main_text_layout)
        console_win_layout.addLayout(info_data_layout)
        console_win_layout.addLayout(send_data_layout)

        # Set the layout
        self.setLayout(console_win_layout)

    def start_console(self):
        self.console_paused = False

    def pause_console(self):
        self.console_paused = True

    def toggle_timestamp(self, status):
        self.text_edit_timestamp.hide() if status else self.text_edit_timestamp.show()

    def toggle_status_bar(self, status):
        self.status_overlay.hide() if status else self.status_overlay.show()

    # Toggle text wrap
    def toggle_wrap(self, status):
        self.text_edit_printf.setLineWrapMode(
            QPlainTextEdit.WidgetWidth if status else QPlainTextEdit.NoWrap
        )

    # Lock and unlock the scrollbar
    def toggle_lock(self, status):
        self.scroll_locked = status

    # Reset the tab counter
    def resetCounter(self):
        self.data_tab_counter = 0
        self.update_tab_title()

    # Update the tab title
    def update_tab_title(self):
        if self.acumulator_status:
            new_title = (
                f"{self.win_title} ({self.data_tab_counter})"
                if self.data_tab_counter > 0
                else self.win_title
            )
            self.mw.update_tab_title(self, new_title)
        else:
            self.mw.update_tab_title(self, self.win_title)

    def check_tab_focus(self):
        current_widget = self.mw.tab_widget.currentWidget()
        return current_widget == self

    # Async BLE Functions

    @qasync.asyncSlot()
    async def send_data(self):
        data = self.line_edit_send.text()
        if data:
            await self.interface.send_data(self.index.rxm, data)
            self.line_edit_send.clear()

    # Callbacks

    # Callback connection success
    def cb_link_ready(self, connected):
        if connected:
            self.update_data(f"[ {self.mw.title}: Remote device connected ]\n")

    # Callback device disconnected
    def cb_link_lost(self, client):
        self.update_data(f"[ {self.mw.title}: Remote device disconnected ]\n")

    # Callback handle input notification
    def cb_data_received(self, uuid, data):
        # Redirect the data to the printf text box
        if uuid == self.index.txm:
            self.update_data(data)
        elif uuid == self.index.txs:
            self.update_info(data)

    # Window Functions

    # Overlay text
    def update_status(self):
        current_time = datetime.now()

        # Calculate latency in milliseconds
        if self.last_received_timestamp:
            latency = int(
                (current_time - self.last_received_timestamp).total_seconds() * 1000
            )
            latency_text = f"{latency:3.0f} ms"
        else:
            latency_text = "N/A"

        status_text = (
            f"Lines: {self.total_lines} | "
            f"Inputs: {self.total_data_counter} | "
            f"Bytes: {self.total_bytes_received} B | "
            f"Delta: {latency_text} | "
            f"Last: {self.last_received_timestamp.strftime(
                '%H:%M:%S') if self.last_received_timestamp else 'N/A'}"
        )

        self.status_overlay.setText(status_text)

    def sync_scroll(self, value):
        # Set the value of the other scrollbar to the value of the sender scrollbar
        sender = self.sender()
        if sender == self.text_edit_printf.verticalScrollBar():
            self.text_edit_timestamp.verticalScrollBar().setValue(value)
        elif sender == self.text_edit_timestamp.verticalScrollBar():
            self.text_edit_printf.verticalScrollBar().setValue(value)

    def update_data(self, data):
        if self.console_paused or not data:
            return

        # Update the total lines
        self.total_lines += len(data.split("\n"))-1

        # New data received - update metrics
        self.total_bytes_received += len(data.encode("utf-8"))

        # Save the current position of the scrollbar
        scrollbar = self.text_edit_printf.verticalScrollBar()
        current_pos = scrollbar.value()

        # Save the current position of the horizontal scrollbar
        horizontal_scroll = self.text_edit_printf.horizontalScrollBar()
        current_horizontal_pos = horizontal_scroll.value()

        # Reset the text format to default before inserting new data
        cursor = self.text_edit_printf.textCursor()
        cursor.movePosition(QTextCursor.End)
        reset_format = QTextCharFormat()
        cursor.setCharFormat(reset_format)

        # Insert the new data
        self.text_edit_printf.setTextCursor(cursor)
        self.text_edit_printf.insertPlainText(data)

        # Fix the timestamp cursor
        cursor_ts = self.text_edit_timestamp.textCursor()
        cursor_ts.movePosition(QTextCursor.End)
        reset_format = QTextCharFormat()
        cursor_ts.setCharFormat(reset_format)

        # Update the timestamp window show milliseconds and linecount
        self.text_edit_timestamp.setTextCursor(cursor_ts)
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.text_edit_timestamp.insertPlainText(
            f"{timestamp} | {str(self.total_data_counter)}\n"
        )

        # Log the data if logging is enabled
        if self.logging_enabled and self.user_log_path:
            try:
                with open(self.user_log_path, "a") as log_file:
                    log_file.write(data)
            except Exception as e:
                self.mw.debug_log(f"Error writing to log file: {e}")

        # Scroll to the bottom if the lock button is pressed
        if self.scroll_locked:
            scrollbar.setValue(scrollbar.maximum())
            self.text_edit_timestamp.verticalScrollBar().setValue(scrollbar.maximum())
        else:
            scrollbar.setValue(current_pos)
            self.text_edit_timestamp.verticalScrollBar().setValue(current_pos)

        # Maintain the horizontal scroll position
        horizontal_scroll.setValue(current_horizontal_pos)

        # Increment the tab counter
        if not self.check_tab_focus():
            self.data_tab_counter += 1
            self.update_tab_title()

        # Update the total lines
        self.total_data_counter += 1

        # Update stats bar
        self.update_status()
        self.last_received_timestamp = datetime.now()

    # Update the info text box (singlef)
    def update_info(self, info):
        if "ARCTIC_COMMAND_SHOW" in info:
            self.mw.visibility_tab(self, True)
            return
        if "ARCTIC_COMMAND_HIDE" in info:
            self.mw.visibility_tab(self, False)
            return
        if "ARCTIC_COMMAND_REQ_NAME" in info:
            return
        self.line_edit_singlef.setText(info)

    # Copy the text from the main text box
    def copy_text(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_edit_printf.toPlainText())

    # Clear the text from the main text box
    def clear_text(self):
        self.text_edit_printf.clear()
        self.line_edit_singlef.clear()
        self.text_edit_timestamp.clear()

        # Clears status bar
        self.total_lines = 0
        self.total_bytes_received = 0
        self.last_received_timestamp = 0
        self.total_data_counter = 0
        self.update_status()

    # Save the text from the main text box
    def log_text(self):
        if not self.logging_enabled:
            if self.select_log_file():
                self.logging_enabled = True
                self.log_button.setStyleSheet(
                    "color: #ffffff; background-color: rgba(0, 100, 0, 128)"
                )
        else:
            self.logging_enabled = False
            self.log_button.setStyleSheet(th.get_style("default_button"))

    def select_log_file(self):
        # Use the native file dialog
        fileName, _ = QFileDialog.getSaveFileName(
            self, "Select Log File", self.win_title, "Text Files (*.txt)"
        )
        if fileName:
            self.user_log_path = fileName
            return True
        return False

    def cb_update_theme(self, theme):
        # Reload stylesheets (background for buttons)
        self.line_edit_send.setStyleSheet(
            th.get_style("console_send_line_edit"))
        if not self.logging_enabled:
            self.log_button.setStyleSheet(th.get_style("default_button"))
        self.show_timestamp.setStyleSheet(th.get_style("default_button"))
        self.wrap_button.setStyleSheet(th.get_style("default_button"))
        self.lock_button.setStyleSheet(th.get_style("default_button"))
        self.toggle_status_bar_button.setStyleSheet(
            th.get_style("default_button"))
        self.send_button.setStyleSheet(th.get_style("default_button"))
        self.status_overlay.setStyleSheet(
            th.get_style("console_status_line_edit"))
        self.text_edit_timestamp.setStyleSheet(
            th.get_style("timestamp_ptext_edit"))

        # Update special widgets by theme
        if theme == "dark":
            self.show_timestamp.changeIconColor("#ffffff")
            self.wrap_button.changeIconColor("#ffffff")
            self.lock_button.changeIconColor("#ffffff")
            self.toggle_status_bar_button.changeIconColor("#ffffff")
            self.send_button.changeIconColor("#ffffff")
        elif theme == "light":
            self.show_timestamp.changeIconColor("#000000")
            self.wrap_button.changeIconColor("#000000")
            self.lock_button.changeIconColor("#000000")
            self.toggle_status_bar_button.changeIconColor("#000000")
            self.send_button.changeIconColor("#000000")

    def toggle_accumulator(self, status):
        self.acumulator_status = status
        self.update_tab_title()

    # Qt Functions

    def resizeEvent(self, event):
        super().resizeEvent(event)

    # Reimplement the keyPressEvent
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if self.line_edit_send.hasFocus():
                self.send_data()
