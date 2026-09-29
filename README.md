# BUSY Bar Custom Apps

Small apps for the [BUSY Bar](https://busy.bar/).

You do not need to know how to code. You do not need anything called Python
already. The double-click files set that up. If a window says Python is
missing, install the free program from
[python.org](https://www.python.org/downloads/), then double-click the file
again. On Windows, tick **Add python.exe to PATH** while installing.

## Two kinds of apps

**The computer stays connected.** These work on a normal BUSY Bar. Leave the
mode switch on **Off**.

| App | Folder | What it does |
|-----|--------|----------------|
| [Network](Python%20Apps/network/) | `Python Apps/network` | Shows this computer’s download and upload speed |
| [Social Battery](Python%20Apps/social-battery/) | `Python Apps/social-battery` | Dial to show how social you feel |

**The app stays on the bar.** Install once. Then open it from **Apps** on the
bar. The computer can be unplugged after that.

| App | Folder | What it does |
|-----|--------|----------------|
| [Chess Clock](apps/chess-clock/) | `apps/chess-clock` | Two-player timer |
| [Dice](apps/Dice/) | `apps/Dice` | Roll 1 to 4 dice |
| [Social Battery](apps/social-battery/) | `apps/social-battery` | Same idea as above, but it stays on the bar |

These three need a bar that already has a **JavaScript runner**. BUSY’s own
site still says putting your own apps on the bar is coming soon. If the app
never shows up in **Apps**, the bar does not have that yet. Use a computer app
instead. Social Battery is in both lists so you can pick the one that works.

## How to start

1. On this GitHub page, click the green **Code** button, then **Download ZIP**.
2. Unzip the download.
3. Open the folder named in the table above.
4. Open **Start Here**.
5. Mac: double-click the file that says **macOS**. The first time, you may
   need to right-click it and choose **Open**.
6. Windows: double-click the file that says **Windows**.
7. When it asks for the BUSY Bar address, press Return if the bar is plugged
   in with USB. That address is `10.0.4.20`.
8. On Wi-Fi, type the address shown on the bar. If it asks for a password,
   that is the bar’s HTTP API password. It is sent only to the bar and is not
   saved.

For an app that stays on the bar: after the window says it is installed, turn
the mode switch to **Apps**, pick the app, and press **Start**.

## If something goes wrong

- **Python is missing or too old.** Install it from the link at the top, then
  double-click the file again.
- **The bar cannot be reached.** Check the cable or Wi-Fi, and try `10.0.4.20`
  if the bar is plugged in.
- **The password is rejected.** Check HTTP API access on the bar, and type
  that password again.
- **An on-bar app never appears.** The bar does not have the JavaScript runner
  yet.

## Linux

The double-click files are for Mac and Windows. On Linux, open Terminal in the
app folder and run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then run `python3 network.py` or `python3 social_battery.py` for a computer
app, or `python3 install_on_bar.py` for an app that stays on the bar. Add
`--host 10.0.4.20` when the bar is plugged in with USB.

## For people building apps

Notes for an AI assistant are in [ai-skills/BUSY-BAR-CORE.md](ai-skills/BUSY-BAR-CORE.md).
Lessons are in [ai-lessons/](ai-lessons/).

These are community projects, not official BUSY apps. The license is
[MIT](LICENSE).
