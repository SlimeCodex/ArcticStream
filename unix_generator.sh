#!/bin/bash
pyinstaller --onefile --noconsole --name=ArcticStream --add-data "src/resources/icons;resources/icons" --hidden-import=bleak --hidden-import=winrt.windows.foundation.collections --icon=./src/resources/icons/main_icon.ico --distpath ./ --workpath ./build ./src/main.py
rm -rf build
rm ArcticStream.spec