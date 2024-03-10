# Desc: UUID patterns for the BLE service and characteristics
# This file is part of ArcticStream Library.

import re

# Bluetooth UUIDs
uuid_ble_backend_ats = "4fafc201-1fb5-459e-1000-c5c9c3319f00"
uuid_ble_backend_tx = "4fafc201-1fb5-459e-1000-c5c9c3319a00"
uuid_ble_backend_rx = "4fafc201-1fb5-459e-1000-c5c9c3319b00"
uuid_ble_ota_ats = "4fafc201-1fb5-459e-2000-c5c9c3319f00"
uuid_ble_ota_tx = "4fafc201-1fb5-459e-2000-c5c9c3319a00"
uuid_ble_ota_rx = "4fafc201-1fb5-459e-2000-c5c9c3319b00"
uuid_ble_console_ats = re.compile(r"4fafc201-1fb5-459e-30[0-9a-fA-F]{2}-c5c9c3319f[0-9a-fA-F]{2}")
uuid_ble_console_tx = re.compile(r"4fafc201-1fb5-459e-30[0-9a-fA-F]{2}-c5c9c3319a[0-9a-fA-F]{2}")
uuid_ble_console_txs = re.compile(r"4fafc201-1fb5-459e-30[0-9a-fA-F]{2}-c5c9c3319b[0-9a-fA-F]{2}")
uuid_ble_console_rx = re.compile(r"4fafc201-1fb5-459e-30[0-9a-fA-F]{2}-c5c9c3319c[0-9a-fA-F]{2}")

# UART UUIDs
uuid_uart_backend_ats = "UB-ATS"
uuid_uart_backend_tx = "UB-TXM"
uuid_uart_backend_rx = "UB-RXM"
uuid_uart_ota_ats = "UO-ATS"
uuid_uart_ota_tx = "UO-TXM"
uuid_uart_ota_rx = "UO-RXM"
uuid_uart_console_ats = re.compile(r"UC-ATS[0-9a-fA-F]{2}")
uuid_uart_console_tx = re.compile(r"UC-TXM[0-9a-fA-F]{2}")
uuid_uart_console_txs = re.compile(r"UC-TXS[0-9a-fA-F]{2}")
uuid_uart_console_rx = re.compile(r"UC-RXM[0-9a-fA-F]{2}")

# WiFi UUIDs
uuid_wifi_backend_ats = "WB-ATS"
uuid_wifi_backend_tx = "WB-TXM"
uuid_wifi_backend_rx = "WB-RXM"
uuid_wifi_ota_ats = "WO-ATS"
uuid_wifi_ota_tx = "WO-TXM"
uuid_wifi_ota_rx = "WO-RXM"
uuid_wifi_console_ats = re.compile(r"WC-ATS[0-9a-fA-F]{2}")
uuid_wifi_console_tx = re.compile(r"WC-TXM[0-9a-fA-F]{2}")
uuid_wifi_console_txs = re.compile(r"WC-TXS[0-9a-fA-F]{2}")
uuid_wifi_console_rx = re.compile(r"WC-RXM[0-9a-fA-F]{2}")