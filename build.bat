@echo off
title Build NexaDesk
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --clean --onefile --windowed --name NexaDesk nexadesk.py
echo.
echo Done! Your EXE is in the dist folder.
pause
