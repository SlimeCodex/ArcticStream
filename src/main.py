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

from PyQt5.QtWidgets import QApplication

from gui.main_window import MainWindow
from resources.styles import *

import sys
import asyncio
import qasync

# Main Function with event loop
if __name__ == "__main__":
	app = QApplication(sys.argv)
	app.setStyleSheet(dark_theme_app + dark_theme_tab + dark_theme_scroll)
	loop = qasync.QEventLoop(app)
	asyncio.set_event_loop(loop)
	mainWin = MainWindow()
	mainWin.show()
	with loop:
		sys.exit(loop.run_forever())