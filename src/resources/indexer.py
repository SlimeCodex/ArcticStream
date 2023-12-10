# Desc: Classes for indexing the BLE service and characteristics
# This file is part of ArcticStream Library.

class BackgroundIndex:
	def __init__(self, service):
		self.service = service
		self.tx_characteristic = None
		self.rx_characteristic = None

class OTAIndex:
	def __init__(self, service):
		self.service = service
		self.tx_characteristic = None
		self.rx_characteristic = None
		self.name = None

class ConsoleIndex:
	def __init__(self, service):
		self.service = service
		self.tx_characteristic = None
		self.txs_characteristic = None
		self.rx_characteristic = None
		self.name = None