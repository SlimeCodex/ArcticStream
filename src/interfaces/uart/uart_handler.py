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

from PyQt5.QtCore import QObject, pyqtSignal

class UARTHandler(QObject):

	# UART Signals
	devicesDiscovered = pyqtSignal(list)
	connectionCompleted = pyqtSignal(bool)
	deviceDisconnected = pyqtSignal(object)
	characteristicRead = pyqtSignal(str, bytes)
	notificationReceived = pyqtSignal(str, str)
	writeCompleted = pyqtSignal(bool)