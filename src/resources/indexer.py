# Desc: Classes for indexing the BLE service and characteristics
# This file is part of ArcticStream Library.


class BackendIndex:
    def __init__(self, service):
        self.service = service
        self.tx_characteristic = None
        self.rx_characteristic = None


class UpdaterIndex:
    def __init__(self, service):
        self.name = None
        self.service = service
        self.tx_characteristic = None
        self.rx_characteristic = None


class ConsoleIndex:
    def __init__(self):
        self.name = None
        self.service = None
        self.tx_characteristic = None
        self.txs_characteristic = None
        self.rx_characteristic = None
