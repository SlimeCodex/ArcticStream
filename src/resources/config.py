globals = {
    "app": {
        "name": "ArcticStream",  # Name of the application
        "version": "v1.1.0",  # Version of the application
        "default_size": (800, 420),  # Default size of the application window
        "minimum_size": (620, 350),  # Minimum size of the application window
        "debug_mode": False,  # Indicates if the application is in debug mode
    },
    "gui": {
        "theme": "dark",  # Theme of the GUI
        "custom_bar_height": 30,  # Height of the custom bar in the GUI
        "custom_bar_button_size": (30, 30),  # Size of buttons in the custom bar
        "resize_corner_size": 10,  # Size of the resize corner in the GUI
        "default_button_size": (30, 30),  # Default size of buttons in the GUI
        "default_line_edit_height": 30,  # Default height of line edit fields in the GUI
        "default_loading_bar_height": 30,  # Default height of loading bars in the GUI
        "debug_line_edit_height": 25,  # Height of line edit fields in debug mode
        "default_status_ledit_size": (520, 25),  # Size of the status line edit
        "connectors_icon_size": (150, 150),  # Size of connector icons in the GUI
    },
    "bluetooth": {
        "scan_timeout": 5,  # Timeout for Bluetooth scanning
        "connection_timeout": 5,  # Connection timeout for Bluetooth
        "con_retries": 5,  # Number of retries for Bluetooth reconnection
        "updater_chunk_size": 500,  # Data chunk size for Bluetooth updates
        "updater_ack_timeout": 0.5,  # Timeout for acknowledgements during Bluetooth updates
        "updater_ack_retries": 3,  # Number of retries for acknowledgements during Bluetooth updates
    },
    "uart": {
        "baudrate": 921600,  # Baud rate for UART communication
        "keepalive": 400,  # Keepalive interval for UART
        "con_retries": 5,  # Number of retries for UART reconnection
        "keepalive_com": 0xA5,  # Keepalive command for UART
        "act_timeout": 500,  # Timeout to declare UART connection lost in ms
        "updater_chunk_size": 4096,  # Data chunk size for UART updates
        "updater_ack_timeout": 0.5,  # Timeout for acknowledgements during UART updates
        "updater_ack_retries": 5,  # Number of retries for acknowledgements during UART updates
    },
    "wifi": {
        "network": "192.168.1.0/24",  # Network IP range for WiFi
        "port_uplink": 56320,  # Uplink port number for WiFi
        "port_downlink": 56321,  # Downlink port number for WiFi
        "con_retries": 5,  # Number of retries for WiFi reconnection
        "act_timeout": 2000,  # Timeout to declare WiFi connection lost in ms
        "updater_chunk_size": 4096,  # Data chunk size for WiFi updates
        "updater_ack_timeout": 0.5,  # Timeout for acknowledgements during WiFi updates
        "updater_ack_retries": 5,  # Number of retries for acknowledgements during WiFi updates
    },
    "console": {
        "line_limit": 1000  # Maximum number of lines in the console log
    },
    "updater": {
        "enable_output_debug": False,  # Enable debug output for the updater
    },
    "style": {  # Collection of default styles for the application
        "default_app",  # Default application style
        "default_button",  # Default button style
        "default_line_edit",  # Default line edit style
        "default_text_edit",  # Default text edit style
        "default_ptext_edit",  # Default plaintext edit style
        "default_tab",  # Default tab style
        "default_scroll",  # Default scroll style
        "default_splitter",  # Default splitter style
    },
}
