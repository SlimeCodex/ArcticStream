# ArcticStream

ArcticStream is a Python-based visualizer designed for integration with the [ArcticTerminal](https://github.com/SlimeCodex/ArcticTerminal) library for ESP32. It uses PyQt5 to create a GUI application that allows users to interact with BLE devices, update their firmware, and customize the window properties.

<div style="display: flex; justify-content: space-around;">
    <div>
        <img src=".img/dark.png" alt="Dark Theme" width="400"/>
        <p style="text-align: center;">Dark Theme</p>
    </div>
    <div>
        <img src=".img/light.png" alt="Light Theme" width="400"/>
        <p style="text-align: center;">Light Theme</p>
    </div>
</div>

# Project Overview

This project introduces a comprehensive BLE (Bluetooth Low Energy) application, primarily designed for the ESP32 platform. It's engineered with an eye towards future expansions, potentially encompassing other platforms like NRF, Raspberry Pi, and more. The application is rich in features, tailored for enhanced interaction with microcontroller units (MCUs).

## Key Features

### BLE Capabilities
- **GATT Protocol**: Leverages the Generic Attribute Profile (GATT) for efficient BLE communication.
- **OTA Updates**: Supports Over-The-Air (OTA) firmware updates via BLE, capable of achieving speeds up to 19kb/s under optimal conditions.

### Console Management
- **Dynamic Console Creation**: Facilitates on-demand creation of consoles based on server-side (MCU) requirements.
- **Auto Reconnection**: Automatically re-establishes connection following MCU resets.
- **Multiple Consoles**: Supports up to 15 consoles, allowing extensive monitoring and control (note: not fully tested).
- **Low Latency**: Achieves as low as 2ms latency in ideal scenarios.

### User Interface
- **Theme Customization**: Offers both dark and light color themes, switchable with a single click.
- **Console Features**: Each console includes Start, Stop, Clear, and Copy functions for the entire console buffer.
- **Log Types**: Supports Multiline and Single Line logs, ideal for status information or animations.
- **Independent Text Input**: Each console features an independent text input box for sending data to the device, ensuring command isolation among consoles.

### OTA Specific Features
- **Drag and Drop**: Simplifies the firmware update process with a drag-and-drop interface.
- **Firmware Management**: Allows users to Start, Stop, Clear, and Reload selected local firmware, streamlining the development cycle.

# Python Implementation

### Main Window

Defined in `main_window.py`, the main window initializes with a default title and size, incorporates a custom stylesheet and fonts, and sets up a layout with a tab widget and a line edit for debug information. Key functionalities include handling BLE connections, dynamically adding tabs, updating tab titles, managing the status bar, and handling window resizing and closing events.

### Connection Window

Located in `connection_window.py`, this window facilitates scanning and connecting to BLE devices. It features a list widget for displaying scanned devices and buttons for initiating scans, establishing connections, and exiting. Additional functions cover device discovery, managing connections, and characteristic reading.

### Console Window

The console window, defined in `console_window.py`, acts as an interactive interface with a BLE device. It includes a text area for data display, a line edit for sending data, and buttons for various commands. It handles incoming BLE device notifications, updates tab titles, and processes Enter key presses in the data input field.

### OTA Updater

`ota_updater.py` houses the OTA updater, providing a UI for firmware updates over BLE. It includes a display for update progress, a progress bar, and buttons for firmware selection, update initiation, and exit. The module manages update processes, device disconnection, and characteristic writing.

### Window Properties

`window_properties.py` manages the customization of window properties. It features a custom title bar with various controls and functions for setting this bar, determining resize direction, adjusting cursor, resizing and moving the window, and handling diverse window events.

## Getting Started

## Dependencies

Before running the application, ensure you have the following dependencies installed:

Python ofcourse:

```bash
pip install python
```

Mandatory dependencies:

```bash
pip install pyqt5
pip install bleak
pip install qasync
```

For generating the executables, we use `pyinstaller`:

```bash
pip install pyinstaller
```

## Running the Application

To run the application, execute the following python script located in the `src` folder:

```bash
python main.py
```

## Contributing

Contributions are welcome! For guidelines on how to contribute, please refer to the contributing guide (WIP).

## License

