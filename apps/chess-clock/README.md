# Chess Clock

Two-player game clock on the BUSY Bar. White is on the left. Black is on the
right.

Install this once onto the bar. Then open it from **Apps**. Your computer does
not need to stay connected while you play.

Set **Minutes** and **Increment** in **Setup**, then press **Start**. The
clocks open paused.

**Firmware:** this needs a BUSY Bar that already includes the JavaScript
runner. Official BUSY docs still say installing your own apps on the bar is
coming soon. If Chess Clock does not appear in Apps after install, the bar
does not have that firmware yet.

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
4. Open `apps`, then `chess-clock`.

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

Or, in a terminal:

```bash
cd apps/chess-clock
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python install_on_bar.py --host 10.0.4.20
```

On Windows, run `.venv\Scripts\activate` instead of `source .venv/bin/activate`.

## 4. Play

1. Turn the mode switch to **Apps**.
2. Open **Chess Clock**.
3. In **Setup**, set **Minutes** and **Increment**.
4. Press **Start**.

| Control | What it does |
|---------|----------------|
| **Setup → Minutes / Increment** | Time control before you start |
| **Start** | Begin White, then hand over after each move. After a flag, starts a new game |
| **OK** | Pause or resume. After a flag, does nothing |
| **Back** | Leave |

Under thirty seconds a clock turns red. At zero that clock flashes `00:00`,
the status light blinks red, and the back shows who won. **Start** begins a
new game and turns the light off.
