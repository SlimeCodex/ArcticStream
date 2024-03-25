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
import pyqtgraph as pg
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QListWidget,
    QSplitter,
)
from PyQt5.QtGui import QFont, QColor
from datetime import datetime

import resources.config as app_config
from interfaces.base_interface import CommunicationInterface
from resources.indexer import GraphIndex, PlotIndex
from helpers.pushbutton_helper import ToggleButton, SimpleButton
import helpers.theme_helper as th
from resources.tooltips import tooltips


class GraphWindow(QWidget):
    def __init__(
        self,
        main_window,
        interface: CommunicationInterface,
        title,
        index: GraphIndex,
    ):
        super().__init__()

        self.mw = main_window  # MainWindow Reference
        self.interface = interface  # BLE Reference
        self.win_title = title  # Original title of the tab
        self.index = index  # Console information
        self.tooltip_index = tooltips["graph_window"]

        # Async window signals
        self.mw.accumulatorChanged.connect(self.toggle_accumulator)
        self.acumulator_status = False

        # Async BLE Signals
        self.interface.linkReady.connect(self.cb_link_ready)
        self.interface.linkLost.connect(self.cb_link_lost)
        self.interface.dataReceived.connect(self.cb_data_received)
        self.mw.themeChanged.connect(self.cb_update_theme)

        # Globals
        self.icons_dir = self.mw.icon_path()
        self.data_tab_counter = 0
        self.console_paused = False

        self.received_package = ""
        self.total_bytes_received = 0
        self.last_received_timestamp = 0
        self.total_data_counter = 0

        self.plot_data_sets = {}  # Stores data for each plot line by plot name
        self.plot_lines = {}  # Stores the actual plot line objects by plot name
        self.plot_widgets = {}  # Stores PlotWidget for each plot name

        self.colors = [
            (255, 0, 0),  # Red
            (0, 255, 0),  # Green
            (0, 0, 255),  # Blue
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Cyan
        ]

        # Initialize variables for delta time calculation
        self.last_update_time = datetime.now()
        self.package_counter = 0
        self.delta_time = "N/A"
        self.package_frequency = "N/A"

        # Setup the timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_delta_time)
        self.update_timer.start(1000)  # 1000 milliseconds = 1 second

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

        # ToggleButton: Toggle show timestamp
        self.show_var_list_button = ToggleButton(
            self,
            icons=(
                f"{self.icons_dir}/keyboard_double_arrow_left_FILL0_wght400_GRAD0_opsz24.svg",
                f"{self.icons_dir}/keyboard_double_arrow_right_FILL0_wght400_GRAD0_opsz24.svg",
            ),
            size=app_config.globals["gui"]["default_button_size"],
            style=th.get_style("default_button"),
            callback=self.toggle_var_list,
            toggled=True,
        )
        self.show_var_list_button.setToolTip(self.tooltip_index["show_var_list_button"])

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
        self.toggle_status_bar_button.setToolTip(self.tooltip_index["show_metadata"])

        # QLineEdit: Main data meta info
        self.status_overlay = QLineEdit(self)
        self.status_overlay.setFont(QFont("Inconsolata"))
        self.status_overlay.setStyleSheet(th.get_style("console_status_line_edit"))
        self.status_overlay.setReadOnly(True)
        self.status_overlay.setAlignment(Qt.AlignCenter)
        self.status_overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.update_status()

        # QListWidget: Main data console
        self.plot_var_list = QListWidget()
        self.plot_var_list.setToolTip(self.tooltip_index["device_list"])
        self.plot_var_list.setFont(QFont("Inconsolata"))
        self.plot_var_list.setSelectionMode(QListWidget.MultiSelection)
        self.plot_var_list.setVisible(False)
        #self.plot_var_list.itemDoubleClicked.connect(self.uart_connect)

    def draw_layout(self):
        # Layout for buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.show_var_list_button)
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.stop_button)
        buttons_layout.addWidget(self.clear_button)
        buttons_layout.addWidget(self.toggle_status_bar_button)

        # Splitter for graph and var list
        self.main_graph_layout = QSplitter(Qt.Horizontal)
        self.main_graph_layout.addWidget(self.plot_var_list)
        self.main_graph_layout.setCollapsible(0, False)
        self.main_graph_layout.setSizes([120, 480])

        # Main layout
        graph_win_layout = QVBoxLayout()
        graph_win_layout.addLayout(buttons_layout)
        graph_win_layout.addWidget(self.status_overlay)
        graph_win_layout.addWidget(self.main_graph_layout)

        # Set the layout
        self.setLayout(graph_win_layout)

    # Overlay text
    def update_status(self):
        # Format the total bytes received
        readable_bytes = self.format_bytes(self.total_bytes_received)

        status_text = (
            f"Inputs: {self.total_data_counter} | "
            f"Bytes: {readable_bytes} | "
            f"Delta: {self.delta_time} | "
            f"Freq: {self.package_frequency} | "
            f"Last: {self.last_received_timestamp.strftime(
                '%H:%M:%S') if self.last_received_timestamp else 'N/A'}"
        )

        self.status_overlay.setText(status_text)

    def start_console(self):
        self.console_paused = False

    def pause_console(self):
        self.console_paused = True

    # Reset the tab counter
    def reset_tab_counter(self):
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

    # Callbacks

    # Callback connection success
    def cb_link_ready(self, connected):
        if connected:
            pass

    # Callback device disconnected
    def cb_link_lost(self, client):
        pass

    # Callback handle input notification
    def cb_data_received(self, uuid, data):
        if uuid == self.index.txm:
            self.update_data(data, uplink=True)

    # Window Functions

    def update_delta_time(self):
        current_time = datetime.now()
        elapsed_time = (current_time - self.last_update_time).total_seconds()
        if elapsed_time > 0:
            if self.package_counter > 0:
                self.delta_time = f"{1000 * elapsed_time / self.package_counter:.0f} ms"
                self.package_frequency = f"{self.package_counter / elapsed_time:.2f} Hz"
        else:
            self.delta_time = "N/A"

        self.last_update_time = current_time
        self.package_counter = 0

    def format_bytes(self, size):
        # 2**10 = 1024
        power = 1024
        n = 0
        power_labels = {0: "B", 1: "KB", 2: "MB", 3: "GB", 4: "TB"}
        while size > power:
            size /= power
            n += 1
        return f"{size:.2f} {power_labels[n]}"

    # Clear the text from the main text box
    def clear_text(self):
        self.plot_var_list.clear()
        self.graph_widget.clear()

        # Clears status bar
        self.total_bytes_received = 0
        self.last_received_timestamp = 0
        self.total_data_counter = 0
        self.update_status()

    def cb_update_theme(self, theme):
        # Reload stylesheets (background for buttons)
        self.show_var_list_button.setStyleSheet(th.get_style("default_button"))
        self.toggle_status_bar_button.setStyleSheet(th.get_style("default_button"))
        self.status_overlay.setStyleSheet(th.get_style("console_status_line_edit"))

        # Update special widgets by theme
        if theme == "dark":
            self.show_var_list_button.changeIconColor("#ffffff")
            self.toggle_status_bar_button.changeIconColor("#ffffff")
        elif theme == "light":
            self.show_var_list_button.changeIconColor("#000000")
            self.toggle_status_bar_button.changeIconColor("#000000")

    def toggle_accumulator(self, status):
        self.acumulator_status = status
        self.update_tab_title()

    # Qt Functions

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def toggle_var_list(self, status):
        self.plot_var_list.hide() if status else self.plot_var_list.show()

    def toggle_status_bar(self, status):
        self.status_overlay.hide() if status else self.status_overlay.show()

###########################################################################################################

    def parse_sensor_data(self, data_str):
        plot_data = {}
        try:
            # Split the string by colon first to separate different data-label pairs
            parts = data_str.split(':')
            plot_name = parts[0]  # The first part is the plot name

            # Process remaining parts for data-label pairs
            values = []
            for part in parts[1:]:  # Skip the first part (plot name)
                data, label = part.split(',')  # Split each pair by comma
                value = float(data.strip())  # Convert data to float
                label = label.strip()  # Clean up label
                values.append((value, label))

            plot_data[plot_name] = values
        except ValueError as e:
            print("Invalid data format in:", data_str)
            print("Error:", e)
        return plot_data

    def update_data(self, data, uplink=False):
        if self.console_paused or not data:
            return

        # New data received - update metrics
        self.total_bytes_received += len(data.encode("utf-8"))
        if not self.check_tab_focus():
            self.data_tab_counter += 1
            self.update_tab_title()
        self.total_data_counter += 1
        self.package_counter += 1
        self.update_status()
        self.last_received_timestamp = datetime.now()

        # Parse the sensor data
        sensor_data = self.parse_sensor_data(data)
        for plot_name, values in sensor_data.items():
            for i, data_point in enumerate(values):
                self.update_plot(plot_name, data_point)

    def update_plot(self, plot_name, data_point):
        max_points = 100  # Maximum number of data points per pen line
        value, label = data_point  # Unpack the data point

        # Create a new plot if it doesn't exist
        if plot_name not in self.plot_widgets:
            self.create_new_plot(plot_name)

        # Add a legend if not present, this should be called before adding the new data point
        if not hasattr(self.plot_widgets[plot_name], 'legend') or self.plot_widgets[plot_name].legend is None:
            print(f"Adding legend to plot: {plot_name} with name: {label}")
            self.plot_widgets[plot_name].addLegend(offset=(-30, 30))
            self.plot_widgets[plot_name].legend = True

        # Create a new pen line for the label if it doesn't exist
        if label not in self.plot_lines[plot_name]:
            print(f"Creating new plot line for label: {label} with data: {data_point}")
            color_index = len(self.plot_lines[plot_name]) % len(self.colors)
            color = self.colors[color_index]
            pen = pg.mkPen(color=color)

            # Create a new plot line and add it to the plot widget
            plot_line = self.plot_widgets[plot_name].plot(pen=pen, name=label)
            self.plot_lines[plot_name][label] = plot_line
            self.plot_data_sets[plot_name][label] = []

        # Add the new data point
        self.plot_data_sets[plot_name][label].append(value)

        # Ensure we don't exceed the maximum number of points
        if len(self.plot_data_sets[plot_name][label]) > max_points:
            self.plot_data_sets[plot_name][label].pop(0)

        # Update the pen line with the new data set
        self.plot_lines[plot_name][label].setData(self.plot_data_sets[plot_name][label])

    def create_new_plot(self, plot_name):
        # Create a new PlotWidget
        plot_widget = pg.PlotWidget(title=plot_name)  # Set plot title
        plot_widget.setBackground("#1e1e1e")
        plot_widget.showGrid(x=True, y=True, alpha=0.3)

        # Add the PlotWidget to the layout
        self.main_graph_layout.addWidget(plot_widget)

        # Set background color
        plot_widget.setAntialiasing(True)

        # Customize axis color
        axis_color = QColor("#dcdcdc")
        plot_widget.getAxis("left").setPen(axis_color)
        plot_widget.getAxis("bottom").setPen(axis_color)

        # Initialize data sets and pen lines dictionaries for this plot
        self.plot_data_sets[plot_name] = {}
        self.plot_lines[plot_name] = {}
        self.plot_widgets[plot_name] = plot_widget

        # Add the PlotWidget to the layout
        self.main_graph_layout.addWidget(plot_widget)  # Assuming main_graph_layout is accessible here