---
name: busy-bar-js-apps
description: On-device JavaScript apps for BUSY Bar firmware that includes the JS runner. Use when creating, uploading, or launching a JS app from the Apps menu, including Dev mode and the js_apps_enabled flag. Not the same as host Python/TS widgets.
---

# On-device JavaScript apps

Works with any AI. Paste this file after `BUSY-BAR-CORE.md`.

This is a **firmware-in-development** feature. Official public docs still say
the JS SDK is coming soon. Do **not** use this path unless the user has
firmware that includes the JS runner, or they explicitly asked for on-device
JS apps.

Host widgets in this repo still run on the PC. JS apps run **on the bar**.

Worked example:

- Chess Clock: `apps/chess-clock/on-device/community.chess_clock/`

Computer apps live under `Python Apps/` (Network, Social Battery). Each on-bar
app has its own `install_on_bar.py`.

Apps that need a live process on the computer, such as network speeds, stay
computer apps.

## What it is

The firmware stores a folder on the bar, lists it in **Apps**, and runs
`scripts/main.js` with JerryScript.

There is no native draw API. The script `fetch()`es the HTTP API, usually
`POST http://127.0.0.1/api/display/draw`. Loopback skips HTTP auth.

## App folder (must match this)

```
<id>/
├── appmeta/
│   ├── manifest.json          required
│   ├── settings.json          optional
│   ├── icon_front_8x8.png     optional, 8×8 colour PNG
│   └── icon_back_11x11.png    optional, 11×11 greyscale PNG
└── scripts/
    └── main.js                required entry point
```

Extra folders (`images`, `resources`, `animations`, …) are allowed. Full path
max 256 characters. Folder name **must equal** `manifest.id`.

Image and animation `path` in draw JSON is relative to the app folder, for
example `images/background.png` or `animations/d16.anim`. Draw animations
with `"type": "animation"` (same as host widgets). The bar plays the `.anim`
file itself. Current firmware only accepts **bicycle1** files (signature
`bicycle1`). Older `bicycle0` files fail with a silent `AnimFile` error. Convert
with firmware `scripts/seq2anim.py`.

## `manifest.json`

```json
{
  "format_version": 1,
  "id": "community.chess_clock",
  "name": "Chess Clock",
  "version": "0.1.1",
  "description": "Two-player game clock",
  "author": "Community",
  "heap_size_kib": 256,
  "debug": false
}
```

| Field | Required | Notes |
|-------|----------|--------|
| `format_version` | yes | Currently `1` |
| `id` | yes | Same as folder name. Max 32 chars. Use `a-zA-Z0-9._` |
| `name` | yes | Shown in Apps menu |
| `version` | yes | `x.y.z` |
| `description` | no | Default `""` |
| `author` | no | Default `""` |
| `heap_size_kib` | no | Default `128`, range 1–512 |
| `debug` | no | If `true`, hidden unless **Dev mode** is on |

Do **not** put a hyphen in `id`. Manifest file max size: 512 bytes.

For apps people should actually see, ship **`"debug": false`**. Use
`"debug": true` only for WIP / firmware-sample apps.

## Two switches before it shows in Apps

Both are required. Uploading files alone is not enough.

### 1. JS apps enabled

Create this file on the bar:

`/ext/apps_data/apps_menu/js_apps_enabled`

```http
POST /api/storage/mkdir?path=/ext/apps_data/apps_menu
POST /api/storage/write?path=/ext/apps_data/apps_menu/js_apps_enabled
```

Body for write: any small bytes (example: `1`),
`Content-Type: application/octet-stream`.

If this file is missing, uploaded JS apps never appear in Apps.

### 2. Dev mode (only if `debug: true`)

`debug: true` apps are hidden unless developer mode is on.

On the bar:

1. Open **Settings**
2. Open **Debug**
3. Set **Dev mode** to **On**

USB CLI (same flag):

```
sysctl debug 1
sysctl debug 0
```

There is no HTTP endpoint for Dev mode.

Community apps (Chess Clock) use `"debug": false`, so Dev mode is not needed
for those. It **is** needed for the firmware example `app.busy.js_example`.

## Upload (same assets API as host widgets)

Wipe the previous copy, then POST each file:

```http
DELETE /api/assets/upload?application_name=<id>
POST /api/assets/upload?application_name=<id>&file=<relative-path>
```

Body is raw file bytes, `Content-Type: application/octet-stream`.

Examples:

- `file=appmeta/manifest.json`
- `file=scripts/main.js`
- `file=appmeta/icon_front_8x8.png`
- `file=images/background.png`

`application_name` is the same namespace as host-widget assets. Do not reuse
an ID a PC widget already uses (`chess_clock` host vs `community.chess_clock`
on-device).

Python installer in this repo:

```bash
cd apps/chess-clock
python install_on_bar.py --host 10.0.4.20
```

That script uploads the package **and** writes `js_apps_enabled`.

After a code or icon change, run the installer again (or re-POST the changed
files). Then reopen the app from Apps.

## How to launch

1. Turn the mode switch to **Apps**.
2. Pick the app (after built-in apps).
3. On the launcher screen, **Start** runs `scripts/main.js`. **Setup** edits
   `appmeta/settings.json` if present. Saved values are at
   `/ext/apps_data/jsrunner/<id>.settings.json` and can be read with
   `/api/storage/read`.
4. The app’s own UI then runs (Chess Clock opens on the clocks; set the
   time control in **Setup** first).

Apps mode **is** required to pick a JS app. Host widgets can still draw from
Off.

## Menu icons

| File | Screen | Size | Colour |
|------|--------|------|--------|
| `appmeta/icon_front_8x8.png` | Front LED matrix | 8×8 | Colour PNG |
| `appmeta/icon_back_11x11.png` | Back OLED | 11×11 | Greyscale PNG |

Missing files → default unknown-app icon. Match **size**, not the casual
filename the user used.

## JS APIs

| API | Use |
|-----|-----|
| `fetch(url)` / `fetch(request)` | HTTP. Prefer `http://127.0.0.1/...` |
| `new Request(url, { method, body, headers })` | Build POST bodies |
| `Headers`, `URL` | Fetch helpers |
| `response.json()` / `.text()` / `.arrayBuffer()` | Body helpers |
| `console.log` / `console.info` / `console.error` | Device logs |
| `setTimeout` / `setInterval` | Timers; minimum delay 10 ms |
| `clearTimeout` / `clearInterval` | Cancel timers |
| `listen("input", handler)` | Buttons / encoder. Returns `unbind()` |
| `localStorage` | Persist string key/values per app id |

Stubs only: `AbortController`, `DOMException`, `FormData`.

### Input

```js
const unbind = listen("input", (event) => { /* ... */ })
```

Only `"input"`. One handler at a time.

| `event.key` | Extra fields |
|-------------|--------------|
| `"encoder"` | `action`: `"clockwise"` / `"counterclockwise"`; `delta`: `1` / `-1` |
| `"ok"` / `"start"` / `"back"` | `action`: `"press"` or `"release"` |

Unbind on Back from the app’s own menu if the script should exit. Do
**not** `fetch` a display clear after `unbind()`: unbind stops the JS
runner, and a request after that can crash the bar. Clear timers first,
then unbind, then return.

`setInterval` / `setTimeout` may return `0`. Treat timers as present with
`timer !== null`, never `if (timer)`.

### Draw

```js
const request = new Request("http://127.0.0.1/api/display/draw", {
  method: "POST",
  body: JSON.stringify({
    application_name: "community.chess_clock",
    elements: [ /* same JSON as host widgets */ ]
  })
});
fetch(request);
```

Set `application_name` to the app `id`. Same fonts and display sizes as
host widgets.

## Lifetime

Keeps running while top-level code, timers, fetches, or an input listener
are active. Then the launcher returns to Start/Setup.

Only **one** JS context at a time. `main.js` max 250 KiB. Extra `.js` files
can be ES-imported from `scripts/`.

## Settings vs localStorage

`appmeta/settings.json` drives the on-bar **Setup** UI. Saved values live at
`/ext/apps_data/jsrunner/<id>.settings.json` as
`{ "version": 1, "values": { "<field>": ... } }`. There is no native settings
API in JS; read that file with
`GET http://127.0.0.1/api/storage/read?path=...` then `response.json()`.
Integer fields are numbers. Enum fields are the option `value` strings.

Use `localStorage` for script-only state (separate file:
`<id>.localstorage.json`).

## CLI (USB serial)

```
js [-i app_id] [filename]
js -k
sysctl debug 1
```

- no file → REPL (`exit` to leave)
- file → run that script
- `-k` → abort all running JS

## Assistant rules for JS apps

1. Confirm the user has JS-runner firmware (or they asked to build on-device).
2. Package as `on-device/<id>/` with matching `manifest.id`.
3. Ship `"debug": false` unless they asked for a hidden debug app.
4. After writing files, upload with the assets API and enable
   `js_apps_enabled`. Give a copy-paste install command.
5. If a `debug: true` app is missing from Apps, tell them to turn **Dev mode**
   on (Settings → Debug), not to re-flash.
6. If a `debug: false` app is missing, check `js_apps_enabled` first.
7. Do not mix host-widget `application_name` with the JS app id.

## Related

- Lessons: `ai-lessons/06-js-apps-on-device.md`,
  `ai-lessons/07-setup-settings-and-launch.md`
- Example on-device: `apps/chess-clock/`
- Host widgets: `Python Apps/` and `ai-skills/busy-bar-widgets/SKILL.md`
