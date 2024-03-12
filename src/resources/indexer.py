# Desc: Classes for indexing the BLE service and characteristics
# This file is part of ArcticStream Library.


class BackendIndex:
    def __init__(self, service):
        self.service = service
        self.txm = None
        self.rxm = None


class UpdaterIndex:
    def __init__(self, service):
        self.name = None
        self.service = service
        self.txm = None
        self.rxm = None


class ConsoleIndex:
    def __init__(self):
        self.name = None
        self.service = None
        self.txm = None
        self.txs = None
        self.rxm = None
