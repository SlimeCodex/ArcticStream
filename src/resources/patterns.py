# Desc: UUID patterns for the BLE service and characteristics
# This file is part of ArcticStream Library.

import re

# Bluetooth UUIDs
UUID_BLE_BACKEND_ATS = "4fafc201-1fb5-459e-1000-c5c9c3319f00"
UUID_BLE_BACKEND_TX = "4fafc201-1fb5-459e-1000-c5c9c3319a00"
UUID_BLE_BACKEND_RX = "4fafc201-1fb5-459e-1000-c5c9c3319b00"
UUID_BLE_OTA_ATS = "4fafc201-1fb5-459e-2000-c5c9c3319f00"
UUID_BLE_OTA_TX = "4fafc201-1fb5-459e-2000-c5c9c3319a00"
UUID_BLE_OTA_RX = "4fafc201-1fb5-459e-2000-c5c9c3319b00"
UUID_BLE_CONSOLE_ATS = re.compile(r"4fafc201-1fb5-459e-30[0-9a-fA-F]{2}-c5c9c3319f[0-9a-fA-F]{2}")
UUID_BLE_CONSOLE_TX = re.compile(r"4fafc201-1fb5-459e-30[0-9a-fA-F]{2}-c5c9c3319a[0-9a-fA-F]{2}")
UUID_BLE_CONSOLE_TXS = re.compile(r"4fafc201-1fb5-459e-30[0-9a-fA-F]{2}-c5c9c3319b[0-9a-fA-F]{2}")
UUID_BLE_CONSOLE_RX = re.compile(r"4fafc201-1fb5-459e-30[0-9a-fA-F]{2}-c5c9c3319c[0-9a-fA-F]{2}")
UUID_BLE_GRAPH_ATS = re.compile(r"4fafc201-1fb5-459e-40[0-9a-fA-F]{2}-c5c9c3319f[0-9a-fA-F]{2}")
UUID_BLE_GRAPH_TX = re.compile(r"4fafc201-1fb5-459e-40[0-9a-fA-F]{2}-c5c9c3319a[0-9a-fA-F]{2}")

# UART UUIDs
UUID_UART_BACKEND_ATS = "UB-ATS"
UUID_UART_BACKEND_TX = "UB-TXM"
UUID_UART_BACKEND_RX = "UB-RXM"
UUID_UART_OTA_ATS = "UO-ATS"
UUID_UART_OTA_TX = "UO-TXM"
UUID_UART_OTA_RX = "UO-RXM"
UUID_UART_CONSOLE_ATS = re.compile(r"UC-ATS[0-9a-fA-F]{2}")
UUID_UART_CONSOLE_TX = re.compile(r"UC-TXM[0-9a-fA-F]{2}")
UUID_UART_CONSOLE_TXS = re.compile(r"UC-TXS[0-9a-fA-F]{2}")
UUID_UART_CONSOLE_RX = re.compile(r"UC-RXM[0-9a-fA-F]{2}")
UUID_UART_GRAPH_ATS = re.compile(r"UG-ATS[0-9a-fA-F]{2}")
UUID_UART_GRAPH_TX = re.compile(r"UG-TXM[0-9a-fA-F]{2}")

# WiFi UUIDs
UUID_WIFI_BACKEND_ATS = "WB-ATS"
UUID_WIFI_BACKEND_TX = "WB-TXM"
UUID_WIFI_BACKEND_RX = "WB-RXM"
UUID_WIFI_OTA_ATS = "WO-ATS"
UUID_WIFI_OTA_TX = "WO-TXM"
UUID_WIFI_OTA_RX = "WO-RXM"
UUID_WIFI_CONSOLE_ATS = re.compile(r"WC-ATS[0-9a-fA-F]{2}")
UUID_WIFI_CONSOLE_TX = re.compile(r"WC-TXM[0-9a-fA-F]{2}")
UUID_WIFI_CONSOLE_TXS = re.compile(r"WC-TXS[0-9a-fA-F]{2}")
UUID_WIFI_CONSOLE_RX = re.compile(r"WC-RXM[0-9a-fA-F]{2}")
UUID_WIFI_GRAPH_ATS = re.compile(r"WG-ATS[0-9a-fA-F]{2}")
UUID_WIFI_GRAPH_TX = re.compile(r"WG-TXM[0-9a-fA-F]{2}")