# Desc: UUID patterns for the BLE service and characteristics
# This file is part of ArcticStream Library.

import re

# UUID Patterns for background operation
service_background_uuid = "4fafc201-1fb5-459e-1000-c5c9c3319f00"
char_background_tx_uuid = "4fafc201-1fb5-459e-1000-c5c9c3319a00"
char_background_rx_uuid = "4fafc201-1fb5-459e-1000-c5c9c3319b00"

# UUID Patterns for OTA operation
service_ota_uuid = "4fafc201-1fb5-459e-2000-c5c9c3319f00"
char_ota_tx_uuid = "4fafc201-1fb5-459e-2000-c5c9c3319a00"
char_ota_rx_uuid= "4fafc201-1fb5-459e-2000-c5c9c3319b00"

# UUID Patterns for console operation
service_console_pattern = re.compile(r"4fafc201-1fb5-459e-30[0-9a-fA-F]{2}-c5c9c3319f[0-9a-fA-F]{2}")
char_tx_pattern = re.compile(r"4fafc201-1fb5-459e-30[0-9a-fA-F]{2}-c5c9c3319a[0-9a-fA-F]{2}")
char_txs_pattern = re.compile(r"4fafc201-1fb5-459e-30[0-9a-fA-F]{2}-c5c9c3319b[0-9a-fA-F]{2}")
char_rx_pattern = re.compile(r"4fafc201-1fb5-459e-30[0-9a-fA-F]{2}-c5c9c3319c[0-9a-fA-F]{2}")