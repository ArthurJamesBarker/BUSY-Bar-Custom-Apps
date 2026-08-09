# 01 — Getting started

## What you need

- A BUSY Bar on **current release firmware**
- A computer (Windows, macOS, or Linux)
- Python 3.10+ if you follow the Python examples (`pip install busylib`)
- USB cable, or the same Wi-Fi network as the bar

## First connection (USB)

1. Plug the BUSY Bar into your computer over USB.
2. It appears as a network device at **`10.0.4.20`**.
3. Open http://10.0.4.20 in a browser — that is the bar’s local web UI.

You do **not** need to put the bar in **Apps** mode to start a host widget or
custom app. Off mode (and other modes) is fine for HTTP `display/draw`.

Quick check with busylib:

```python
from busylib import BusyBar

with BusyBar("10.0.4.20") as bb:
    print(bb.version())
```

USB normally needs **no password** and **no API token**.

## Wi-Fi connection

1. Connect the bar to Wi-Fi from the device UI or web UI.
2. Read its IP under **Settings → Wi-Fi → [network] → View IP Address**.
3. Enable **HTTP API access** in the local web UI (over USB first):
   **Network → HTTP API →** turn on access and set a password.
4. Use that Wi-Fi IP in your script. When access is protected, send the
   **HTTP access password** (see lesson 02).

## Cloud / internet connection

Use `https://api.busy.app/busybar` with a **cloud API token** from
https://cloud.busy.app — not the local Wi-Fi password. See lesson 02.

## Mental model

| Where your code runs | How the bar is driven |
|----------------------|------------------------|
| On your PC (widget / custom app) | HTTP API → `display/draw`, assets, audio, etc. |
| On the device (JerryScript app) | Different model; not covered by these core lessons |

This repo’s published apps (for example Social Battery) are **host apps**: they
run on your computer and talk to official firmware over HTTP.
