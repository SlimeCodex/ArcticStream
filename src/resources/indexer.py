# Desc: Classes for indexing the BLE service and characteristics
# This file is part of ArcticStream Library.


class BackendIndex:
    def __init__(self):
        self.service = None
        self.txm = None
        self.rxm = None


class UpdaterIndex:
    def __init__(self):
        self.name = None
        self.service = None
        self.txm = None
        self.rxm = None
        self.instance = None
        self.tab_index = None


class ConsoleIndex:
    def __init__(self):
        self.name = None
        self.service = None
        self.txm = None
        self.txs = None
        self.rxm = None
        self.instance = None
        self.tab_index = None


class GraphIndex:
    def __init__(self):
        self.name = None
        self.service = None
        self.txm = None
        self.instance = None
        self.tab_index = None


class PlotIndex:
    def __init__(self):
        self.name = None
