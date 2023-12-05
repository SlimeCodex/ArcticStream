# Desc: ToggleButton class for toggling between two states
# This file is part of ArcticStream Library.

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QIcon, QPixmap

class ToggleButton(QPushButton):
	def __init__(self, parent=None, icons=None, size=(25, 25), style=None, callback=None, toggled=False):
		"""
		Initializes a toggle button.

		:param parent: The parent widget.
		:param icons: A tuple containing the icon paths for the toggled and untoggled states.
		:param size: A tuple for the size of the button (width, height).
		:param style: A string containing the CSS style for the button.
		:param callback: The function to call when the button is toggled.
		:param toggled: The initial toggle state.
		"""
		super().__init__(parent)
		self.icons = icons
		self.toggled = toggled
		self.callback = callback
		self.size = size
		
		# Set button size
		self.setFixedSize(*self.size)

		# Setup button appearance
		self.setupButton()

		# Apply custom style if provided
		if style:
			self.setStyleSheet(style)

		# Connect the toggle signal
		self.clicked.connect(self.toggleState)

	def setupButton(self):
		"""
		Setup the button appearance based on the current toggle state.
		"""
		if self.icons:
			iconPath = self.icons[1] if self.toggled else self.icons[0]
			icon = QIcon(iconPath)
			self.setIcon(icon)
			# Set button size, if commented out, Qt will automatically resize it
			#self.setIconSize(QPixmap(iconPath).size())

	def toggleState(self):
		"""
		Toggle the state of the button and update its appearance.
		"""
		self.toggled = not self.toggled
		self.setupButton()

		# Call the callback function if provided
		if self.callback:
			self.callback(self.toggled)

class SimpleButton(QPushButton):
	def __init__(self, parent=None, icon=None, size=(25, 25), style=None, callback=None):
		"""
		Initializes a simple button.

		:param parent: The parent widget.
		:param icon: The path to the icon for the button.
		:param size: A tuple for the size of the button (width, height).
		:param style: A string containing the CSS style for the button.
		:param callback: The function to call when the button is pressed.
		"""
		super().__init__(parent)
		self.iconPath = icon
		self.callback = callback

		# Set button icon
		if self.iconPath:
			self.setIcon(QIcon(self.iconPath))

		# Set button size
		self.setFixedSize(*size)

		# Setup button appearance
		if self.iconPath:
			self.setIcon(QIcon(self.iconPath))
			# Set button size, if commented out, Qt will automatically resize it
			#self.setIconSize(QPixmap(iconPath).size())

		# Apply custom style if provided
		if style:
			self.setStyleSheet(style)

		# Connect the button signal
		self.clicked.connect(self.onButtonPress)

	def onButtonPress(self):
		"""
		Handle the button press event.
		"""
		if self.callback:
			self.callback()