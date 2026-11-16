# NexaDesk — PC Control Center

A lightweight Windows desktop dashboard for monitoring your PC. Built with Python + Tkinter.

## Features
- Live CPU and RAM usage with a simple history graph
- System drive usage
- Live network download/upload rate
- Device and operating-system details
- Process viewer sorted by memory use
- Optional process termination with confirmation
- User TEMP folder scan and cleanup with confirmation
- No telemetry, accounts, ads, registry tweaks, or background services

## Screenshots
Run the app to see the interface. (Add screenshots here after your first run.)

## Run from source
1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Run:
   ```bash
   python -m pip install -r requirements.txt
   python nexadesk.py
   ```

## Build Windows EXE
On Windows, double-click `build.bat`. The executable will be created at `dist/NexaDesk.exe`.

Or run:
```bash
python -m pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --clean --onefile --windowed --name NexaDesk nexadesk.py
```

## Safety
Process termination can lose unsaved work. Temporary-file cleanup only targets the current user's TEMP directory and skips files that cannot be removed. Review prompts before either action.

## License
MIT — see [LICENSE](LICENSE).
