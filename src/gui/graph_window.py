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

import pyqtgraph as pg
from PyQt5.QtWidgets import QVBoxLayout
import pandas as pd
import re
from PyQt5.QtGui import QColor

import qasync
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
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
from resources.indexer import GraphIndex
from helpers.pushbutton_helper import ToggleButton, SimpleButton
import helpers.theme_helper as th
from resources.tooltips import tooltips

pyqtgraph_stylesheet = """
/* Set the plot background color */
PlotWidget {
    background-color: #1e1e1e;
}

/* Set the color for the plot grid */
PlotWidget > QGridLayout {
    color: #555555;
}
"""

class GraphWindow(QWidget):
    data_updated = pyqtSignal(pd.DataFrame)

    def __init__(self, main_window, title="ASG"):
        super().__init__()

        self.mw = main_window  # MainWindow Reference
        self.win_title = title  # Window Title
        self.tooltip_index = tooltips["console_window"]

        self.graphWidget = pg.PlotWidget()  # Create a plot widget
        self.graphWidget.setLabel("left", "Temperature (°C)")
        self.setup_layout()  # Set up the layout
        self.initialize_plot()  # Initialize the plot

        self.setup_graph_style()
        self.setStyleSheet(pyqtgraph_stylesheet)  # Set the stylesheet for the plot widget

    def setup_layout(self):
        layout = QVBoxLayout()  # Create a vertical box layout
        layout.addWidget(self.graphWidget)  # Add the plot widget to the layout
        self.setLayout(layout)  # Set the layout for this widget

    def initialize_plot(self):
        # You can customize your plot here
        self.graphWidget.setBackground("#1e1e1e")  # Set background color
        self.graphWidget.plot([1, 2, 3, 4, 5], [30, 32, 34, 32, 33])  # Sample plot

    def parse_sensor_data(self, data_str):
        pattern = r"\[\s*([^]]+?)\s*\]"
        matches = re.findall(pattern, data_str)
        split_pattern = r"\s*[|,]\s*|\s+"
        df = pd.DataFrame([re.split(split_pattern, m) for m in matches])

        # Return the number of rows in the DataFrame
        return df.shape[1]

    def setup_graph_style(self):
        # Set background color
        self.graphWidget.setBackground('#1e1e1e')

        # Customize plot pen (line color, width)
        pen = pg.mkPen(color='#dcdcdc', width=2)

        # Customize axis color
        axis_color = QColor('#dcdcdc')
        self.graphWidget.getAxis('left').setPen(axis_color)
        self.graphWidget.getAxis('bottom').setPen(axis_color)

        # Customize grid color
        self.graphWidget.showGrid(x=True, y=True, alpha=0.3)

    def update_plot(self, data):
        # Use the customized pen when plotting
        self.graphWidget.plot(data, pen=pen)