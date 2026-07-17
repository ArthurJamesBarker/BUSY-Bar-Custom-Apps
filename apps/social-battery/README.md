# Social Battery

Social Battery turns the BUSY Bar dial into a simple social-energy meter.
Choose one of seven levels, from **critical** to **full**.

![Social Battery full state](full.png)

The app runs on your computer and sends the original 72×16 artwork to a BUSY
Bar using its official release-firmware API. No modified firmware is needed.

## What you need

- BUSY Bar with current release firmware
- Windows, macOS, or Linux computer
- Python 3.10 or newer
- USB or Wi-Fi connection to the BUSY Bar

Download Python from [python.org](https://www.python.org/downloads/) if it is
not already installed. On Windows, select **Add Python to PATH** during setup.

## 1. Download the app

1. Open the main
   [BUSY Bar Custom Apps repository](https://github.com/ArthurJamesBarker/BUSY-Bar-Custom-Apps).
2. Select **Code**, then **Download ZIP**.
3. Unzip the download.
4. Open `apps`, then `social-battery`.

## 2. Prepare the BUSY Bar

1. Connect the BUSY Bar to the computer by USB, or connect both devices to the
   same Wi-Fi network.
2. On the BUSY Bar, open **Settings → Developer → HTTP API**.
3. Enable the API. If you choose key-protected access, keep the displayed key
   ready; Social Battery will ask for it.
4. Put the BUSY Bar in **Apps** mode.

USB normally uses `10.0.4.20`. For Wi-Fi, use the IP address shown by your BUSY
Bar.

## 3. Start Social Battery

### macOS

Double-click **Start Social Battery.command**.

The first time, macOS may require you to right-click the file and select
**Open**. Enter the BUSY Bar IP address when asked, or press Return to use the
USB default.

### Windows

Double-click **Start Social Battery.bat**.

Enter the BUSY Bar IP address when asked, or press Enter to use the USB default.

### Linux or manual start

Open a terminal in this folder and run:

```bash
python3 -m pip install -r requirements.txt
python3 social_battery.py
```

For a Wi-Fi BUSY Bar:

```bash
python3 social_battery.py --host 192.168.1.123
```

Replace `192.168.1.123` with the BUSY Bar's IP address.

## Controls

- Turn the dial up or down: move one battery level per registered tick
- Press **OK** or **Start**: move one level higher
- Press **Back**: close Social Battery
- Move away from **Apps** mode: close Social Battery

The state stops at **critical** and **full**; it does not wrap around.

## Stopping the app

Press **Back** on the BUSY Bar, close the launcher window, or press `Ctrl+C` in
the terminal. The app clears its artwork when it closes.

## Troubleshooting

### The BUSY Bar cannot be reached

- Check the USB cable or Wi-Fi connection.
- Confirm the IP address.
- Confirm the HTTP API is enabled.
- Try the USB address `10.0.4.20`.

### The API key is rejected

Open **Settings → Developer → HTTP API** and enter the currently displayed key
when prompted. Do not include spaces.

### The dial does not respond

- Keep the BUSY Bar in **Apps** mode.
- Close any other computer app using the BUSY Bar status stream.
- Stop and restart Social Battery.

### Python is not found

Install Python 3.10 or newer from
[python.org](https://www.python.org/downloads/), then reopen the launcher.

## Files included

- `social_battery.py` — the complete app in one Python file
- seven PNG files — the seven social-battery states
- `requirements.txt` — Python packages
- macOS and Windows launchers

No test folders, hacked-firmware JavaScript, unused animation code, development
logs, caches, or unrelated assets are included.

## License

Social Battery and its included artwork are available under the repository's
[MIT License](../../LICENSE).
