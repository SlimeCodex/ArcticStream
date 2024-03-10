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

from abc import ABC, abstractmethod


class CommunicationInterface(ABC):
    @abstractmethod
    async def scan_for_devices(self):
        """Scans for available devices on the interface."""
        pass

    @abstractmethod
    async def connect_to_device(self, device_address):
        """Connects to a device on the interface."""
        pass

    @abstractmethod
    async def send_data(self, uuid, data, response=False):
        """Sends data to the specified characteristic or equivalent on the interface."""
        pass

    @abstractmethod
    async def send_command(self, command, uuid=""):
        """Sends a command to the specified characteristic or equivalent on the interface."""
        pass

    @abstractmethod
    async def receive_data(self):
        """Receives data from the connected device."""
        pass

    @abstractmethod
    def get_services(self):
        """Retrieves services information from the connected device (if applicable)."""
        pass

    @abstractmethod
    async def disconnect(self):
        """Disconnects from the connected device."""
        pass

    # --- Optional methods ---

    async def start_notifications(self, characteristic):
        """Starts notifications for a characteristic (if applicable)."""
        pass

    async def read_characteristic(self, characteristic):
        """Reads data from a characteristic (if applicable)."""
        pass
