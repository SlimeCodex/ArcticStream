# Desc: ConsoleIndex class for storing the console information
# This file is part of ArcticStream Library.

class ConsoleIndex:
	def __init__(self, service):
		self.service = service
		self.tx_characteristic = None
		self.txs_characteristic = None
		self.rx_characteristic = None
		self.name_characteristic = None
		self.name = None