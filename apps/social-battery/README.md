# Social Battery (on the bar)

Show your social-energy level on the BUSY Bar, from **critical** to **full**.

Install this once onto the bar. Then open it from **Apps**. Your computer does
not need to stay connected after that.

If your bar does not have the JavaScript runner, use the computer version
instead: [Social Battery on your computer](../../Python%20Apps/social-battery/).
That one works with normal BUSY Bar firmware.

**Firmware:** this on-bar version needs a BUSY Bar that already includes the
JavaScript runner. Official BUSY docs still say installing your own apps on
the bar is coming soon. If it does not appear in Apps after install, use the
computer version.

## What you need

- BUSY Bar with JavaScript-runner firmware
- Windows, macOS, or Linux computer (only for the install)
- Python 3.10 or newer
- USB or Wi-Fi connection to the BUSY Bar

Download Python from [python.org](https://www.python.org/downloads/) if it is
not already installed. On Windows, select **Add Python to PATH** during setup.

## 1. Download the app

1. Open this repository on GitHub:
   [BUSY-Bar-Custom-Apps](https://github.com/ArthurJamesBarker/BUSY-Bar-Custom-Apps).
2. Select **Code**, then **Download ZIP**.
3. Unzip the download.
4. Open `apps`, then `social-battery`.

## 2. Prepare the BUSY Bar

1. Connect the BUSY Bar to the computer by USB, or connect both devices to the
   same Wi-Fi network.
2. If using Wi-Fi, enable **HTTP API access** on the BUSY Bar.
3. If that access is password-protected, keep the password ready. The installer
   will ask for it. USB connections do not need this password.

USB normally uses `10.0.4.20`. For Wi-Fi, use the IP address shown by your BUSY
Bar. The password is sent directly to the BUSY Bar and is not saved.

## 3. Install

Open **Start Here**, then:

- macOS: **macOS - Double-click to Install on Bar.command**
- Windows: **Windows - Double-click to Install on Bar.bat**

The first time on macOS, you may need to right-click the file and select
**Open**.

Or, in a terminal opened at the downloaded repository:

```bash
cd apps/social-battery
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python install_on_bar.py --host 10.0.4.20
```

On Windows, run `.venv\Scripts\activate` instead of `source .venv/bin/activate`.

## 4. Use

1. Turn the mode switch to **Apps**.
2. Open **Social Battery**.
3. Press **Start**.

**Dial** moves one level. **OK** or **Start** moves up. **Back** leaves.

The ends do not wrap. The bar remembers the last level.
