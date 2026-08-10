# BUSY Bar core knowledge (paste into any AI)

Use this sheet with any AI assistant (ChatGPT, Claude, Gemini, Copilot, etc.).
Build against **official release firmware** only unless the user asks otherwise.

## Displays

| Display | Size | Kind |
|---------|------|------|
| front | 72×16 | RGB LED matrix |
| back | 160×80 | Greyscale OLED |

Origin is top-left. `x`/`y` are the anchor; `align` sets which part of the
element sits on that point.

## Fonts (current only)

Valid `font` values:

`tiny` · `small` · `normal` · `condensed` · `bold` · `large` · `extra_large` · `global`

Do **not** use outdated names: `medium`, `medium_condensed`, `big`, `tiny5_8`.

Front tips:

- Default: `small` (good for 1–2 lines)
- Two lines: top `y:0` + `top_*`, bottom `y:15` + `bottom_*`, both `small`
- `large` / `extra_large` / `global`: treat as single-line on the front
- Prefer printable ASCII; sanitize text from the web

Colour: `#RRGGBBAA` (example white `#FFFFFFFF`).

## Auth — two different secrets

| | HTTP access password | Cloud API token |
|--|----------------------|-----------------|
| From | Bar web UI at `http://10.0.4.20` → Network → HTTP API | https://cloud.busy.app → API tokens |
| Used for | Bar’s Wi‑Fi LAN IP | `https://api.busy.app/busybar` |
| Header | `X-API-Token: <password>` | `Authorization: Bearer <token>` |
| USB `10.0.4.20` | Usually not needed | Not used |

Never mix them up. They are not interchangeable.

### Client hints

Python busylib (LAN password uses `token=`):

```python
BusyBar("10.0.4.20")
BusyBar("192.168.1.20", token="1234")
```

TypeScript busylib-ts:

```ts
new BusyBar({ addr: '192.168.1.20', HTTPAccessPassword: '1234' })
new BusyBar({ addr: 'https://api.busy.app', token: '<cloud-token>' })
```

## HTTP API basics

Base URLs:

- USB: `http://10.0.4.20`
- Wi‑Fi: `http://<bar-ip>`
- Cloud: `https://api.busy.app/busybar`

Key host-widget flow:

1. Optional upload → `POST /api/assets/upload`
2. Draw → `POST /api/display/draw`
3. Clear / delete assets when done

Use field **`application_name`** (not legacy `app_id`).

Image `path` is the uploaded **filename only** (example: `icon.png`), never a
PC path like `/assets/icon.png`.

Prefer `busylib` / `@busy-app/busy-lib` when writing code.

**Device mode:** Apps mode is **not** required to start host widgets. Off mode
is fine. Do not instruct users to enter Apps mode just to run `display/draw`.
Interactive host apps may still exit when the physical mode switch moves.

Never send Busy Bar API calls to `localhost:11434` (that is local AI, not the bar).

## Minimal draw example

```json
{
  "application_name": "demo",
  "elements": [
    {
      "id": "t1",
      "type": "text",
      "x": 36,
      "y": 8,
      "align": "center",
      "text": "HELLO",
      "font": "small",
      "color": "#FFFFFFFF",
      "display": "front"
    }
  ]
}
```

## Assistant rules

1. Ask USB vs Wi‑Fi vs cloud if auth matters.
2. Follow current fonts and `application_name`.
3. Keep front layouts simple; avoid overlap on 16px height.
4. Give beginners short numbered steps and copy-paste commands.
5. Do not require custom/modified firmware for normal widgets.
6. Do **not** tell users they must enter Apps mode to start a host widget;
   Off mode is fine.
7. Never put passwords or API tokens into git or committed files.

## Official links

- https://docs.busy.app/bar/dev/http-api
- https://docs.busy.app/bar/dev/api-tokens
- https://api.busy.app/busybar/docs
- https://pypi.org/project/busylib/
