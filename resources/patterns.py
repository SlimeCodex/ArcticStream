# Desc: UUID patterns for the BLE service and characteristics
# This file is part of ArcticTerminal Library.

import re

# UUID Patterns
service_ota_pattern = re.compile(r"4fafc201-1fb5-459e-0000-c5c9c3319000")
service_console_pattern = re.compile(r"4fafc201-1fb5-459e-00[0-9a-fA-F]{2}-c5c9c33190[0-9a-fA-F]{2}")
char_tx_pattern = re.compile(r"4fafc201-1fb5-459e-[0-9a-fA-F]{4}-c5c9c3319a[0-9a-fA-F]{2}")
char_txs_pattern = re.compile(r"4fafc201-1fb5-459e-[0-9a-fA-F]{4}-c5c9c3319b[0-9a-fA-F]{2}")
char_rx_pattern = re.compile(r"4fafc201-1fb5-459e-[0-9a-fA-F]{4}-c5c9c3319c[0-9a-fA-F]{2}")
char_name_pattern = re.compile(r"4fafc201-1fb5-459e-[0-9a-fA-F]{4}-c5c9c3319d[0-9a-fA-F]{2}")