@echo off

:: Navigate to the project root directory (assuming the script is in the build directory)
cd ..

:: Ensure the build directories exist
if not exist build\standalone mkdir build\standalone
if not exist build\console mkdir build\console

:: Clean up old files
del /q build\standalone\ArcticStream.exe
del /q build\console\ArcticStream.exe
del /q ArcticStream.spec

:: Build the standalone (no console) version
pyinstaller --onefile --noconsole --name=ArcticStream_standalone --add-data "src/resources/icons;resources/icons" --add-data "src/resources/fonts;resources/fonts" --add-data "src/resources/videos;resources/videos" --hidden-import=winrt.windows.foundation.collections --icon=src/resources/icons/main_icon.ico --distpath build\standalone --workpath build\standalone src/main.py
:: Build the console version
pyinstaller --onefile --console --name=ArcticStream_console --add-data "src/resources/icons;resources/icons" --add-data "src/resources/fonts;resources/fonts" --add-data "src/resources/videos;resources/videos" --hidden-import=winrt.windows.foundation.collections --icon=src/resources/icons/main_icon.ico --distpath build\console --workpath build\console src/main.py

:: Move executables to the correct locations and clean up PyInstaller generated directories
move /Y build\standalone\ArcticStream_standalone.exe build\standalone\ArcticStream.exe
move /Y build\console\ArcticStream_console.exe build\console\ArcticStream.exe
rd /s /q build\standalone\ArcticStream_standalone
rd /s /q build\console\ArcticStream_console

:: Clean up temporary files (optional)
del ArcticStream_standalone.spec
del ArcticStream_console.spec

:: Navigate back to the build directory
cd build
