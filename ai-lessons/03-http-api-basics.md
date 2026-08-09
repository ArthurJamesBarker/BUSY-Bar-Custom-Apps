# 03 — HTTP API basics

The BUSY Bar runs an HTTP server. Your script, desktop app, or automation is
the client.

Official overview: https://docs.busy.app/bar/dev/http-api  
Interactive reference: https://api.busy.app/busybar/docs  
(Also on-device: `http://10.0.4.20/docs`)

## Base URLs

| Connection | Base URL |
|------------|----------|
| USB | `http://10.0.4.20` (paths under `/api/...`) |
| Wi-Fi LAN | `http://<bar-ip>` |
| Internet (cloud proxy) | `https://api.busy.app/busybar` |

Auth for each path is in [02-auth-password-vs-api-token.md](02-auth-password-vs-api-token.md).

## What the API can do

- Draw text / images / animations / countdowns on **front** and **back** displays
- Upload and delete **assets** per `application_name`
- Play audio, adjust volume
- Read status, firmware version, brightness
- Wi-Fi / BLE / account / Matter / storage / updates (see OpenAPI for your firmware)

## Widget-relevant endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/display/draw` | Draw elements |
| `DELETE` | `/api/display/draw` | Clear (often with `application_name`) |
| `POST` | `/api/assets/upload` | Upload a file for an app |
| `DELETE` | `/api/assets/upload` | Delete that app’s assets |
| `GET` | `/api/version` or status/firmware helpers | Check device / API version |

Exact query names and schemas follow the firmware OpenAPI. Prefer
**`application_name`** (current) — not the old lesson field **`app_id`**.

## Prefer busylib

Hand-writing every request works, but the official clients keep auth and
payloads correct:

```bash
pip install busylib
```

```python
from busylib import BusyBar, types

with BusyBar("10.0.4.20") as bb:
    bb.display_draw(
        types.DisplayElements(
            application_name="hello",
            elements=[
                types.TextElement(
                    id="t1",
                    type="text",
                    x=36,
                    y=8,
                    align="center",
                    text="HELLO",
                    font="small",
                    display=types.DisplayName.FRONT,
                )
            ],
        ),
        clear_before_draw=True,
    )
```

TypeScript: `@busy-app/busy-lib` / https://github.com/busy-app/busylib-ts

## Device mode

Host widgets talk to the bar over HTTP. **Apps mode is not required** to start
or run them. Off mode is fine. Do not tell users they must switch to Apps mode
before launching a host script unless a specific app documents that for its own
controls.

## Do not confuse with local AI URLs

`http://localhost:11434` (Ollama, etc.) is **not** the BUSY Bar. Device calls
must target `10.0.4.20`, the bar’s Wi-Fi IP, or `api.busy.app`.
