# Network

Network shows this computer’s live **download** and **upload** speeds on the
BUSY Bar, next to UP/DOWN label artwork.

The app runs on your computer and talks to a BUSY Bar using its official
release-firmware API. No modified firmware is needed.

**Note:** This measures traffic on a network interface on your computer (what
is moving right now). It is not a separate “speed test to a distant server.”

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
4. Open `apps`, then `network`.

## 2. Prepare the BUSY Bar

1. Connect the BUSY Bar to the computer by USB, or connect both devices to the
   same Wi-Fi network.
2. If using Wi-Fi, enable **HTTP API access** on the BUSY Bar.
3. If that access is password-protected, keep the password ready; Network will
   ask for it. USB connections do not need this password.

USB normally uses `10.0.4.20`. For Wi-Fi, use the IP address shown by your BUSY
Bar. The password is sent directly to the BUSY Bar over the local Wi-Fi
connection and is not saved by Network. Only use a trusted Wi-Fi network.

## 3. Start Network

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
python3 network.py
```

For a Wi-Fi BUSY Bar:

```bash
python3 network.py --host 192.168.1.123
```

Replace `192.168.1.123` with the BUSY Bar's IP address.

Optional Wi-Fi password without a prompt:

```bash
python3 network.py --host 192.168.1.123 --password YOUR_PASSWORD
```

To pick a specific network interface instead of auto:

```bash
python3 network.py --interface en0
```

## What you will see

- Left: UP/DOWN label artwork
- Right: live speeds, for example `48 Mb/s` (down) and `12 Mb/s` (up)

Values refresh several times per second while the app is running.

## Stopping the app

Press `Ctrl+C` in the terminal or close the launcher window. The app clears its
content from the BUSY Bar when it stops.

## Troubleshooting

### The BUSY Bar cannot be reached

- Check the USB cable or Wi-Fi connection.
- Confirm the IP address.
- For Wi-Fi, confirm HTTP API access is enabled.
- Try the USB address `10.0.4.20`.

### The Wi-Fi access password is rejected

Check the BUSY Bar's HTTP API access settings and enter its password when
prompted. This password is only used for protected access over Wi-Fi.

### Speeds stay at 0 Mb/s

That usually means this computer is not sending or receiving much traffic on
the selected interface. Open a download or upload and watch again, or pass
`--interface` with another interface name.

### Python is not found

Install Python 3.10 or newer from
[python.org](https://www.python.org/downloads/), then reopen the launcher.

## Files included

- `network.py` — the complete app in one Python file
- `Speed_down-up.png` — UP/DOWN label artwork for the front display
- `requirements.txt` — Python packages used by the app
- `Start Here` — double-click starters for macOS and Windows
