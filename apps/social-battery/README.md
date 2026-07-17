# Social Battery

Social Battery turns the BUSY Bar dial into a simple social-energy meter.
Choose one of seven levels, from **critical** to **full**.

![Social Battery full state](assets/full.png)

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
2. If using Wi-Fi, enable **HTTP API access** on the BUSY Bar.
3. If that access is password-protected, keep the password ready; Social
   Battery will ask for it. USB connections do not need this password.
4. Put the BUSY Bar in **Apps** mode.

USB normally uses `10.0.4.20`. For Wi-Fi, use the IP address shown by your BUSY
Bar.

## 3. Start Social Battery

Open the **Start Here** folder, then choose your computer:

### macOS

Double-click **macOS - Double-click to Start.command**.

The first time, macOS may require you to right-click the file and select
**Open**. Enter the BUSY Bar IP address when asked, or press Return to use the
USB default.

### Windows

Double-click **Windows - Double-click to Start.bat**.

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

### The Wi-Fi access password is rejected

Check the BUSY Bar's HTTP API access settings and enter its password when
prompted. This password is only used for protected access over Wi-Fi.

### The dial does not respond

- Keep the BUSY Bar in **Apps** mode.
- Close any other computer app using the BUSY Bar status stream.
- Stop and restart Social Battery.

### Python is not found

Install Python 3.10 or newer from
[python.org](https://www.python.org/downloads/), then reopen the launcher.

## Files included

- `social_battery.py` — the complete app in one Python file
- `assets` — the seven social-battery PNG images
- `requirements.txt` — Python packages
- `Start Here` — clearly labelled macOS and Windows launchers

No test folders, hacked-firmware JavaScript, unused animation code, development
logs, caches, or unrelated assets are included.

## License

Social Battery and its included artwork are available under the repository's
[MIT License](../../LICENSE).
