#!/bin/bash

# Navigate to the project root directory (assuming the script is in the build directory)
cd ..

# Ensure the build directories exist
[ ! -d "build/standalone" ] && mkdir -p build/standalone
[ ! -d "build/console" ] && mkdir -p build/console

# Clean up old files
rm -f build/standalone/ArcticStream
rm -f build/console/ArcticStream
rm -f ArcticStream_standalone.spec
rm -f ArcticStream_console.spec

# Build the standalone (no console) version
pyinstaller --onefile --noconsole --name=ArcticStream_standalone --add-data "src/resources/icons:resources/icons" --icon=src/resources/icons/main_icon.ico --distpath build/standalone --workpath build/standalone src/main.py

# Build the console version
pyinstaller --onefile --console --name=ArcticStream_console --add-data "src/resources/icons:resources/icons" --icon=src/resources/icons/main_icon.ico --distpath build/console --workpath build/console src/main.py

# Move executables to the correct locations and clean up PyInstaller generated directories
mv -f build/standalone/ArcticStream_standalone build/standalone/ArcticStream
mv -f build/console/ArcticStream_console build/console/ArcticStream
rm -rf build/standalone/ArcticStream_standalone
rm -rf build/console/ArcticStream_console

# Clean up temporary files (optional)
rm -f ArcticStream_standalone.spec
rm -f ArcticStream_console.spec
