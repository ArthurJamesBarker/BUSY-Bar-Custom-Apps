# 06 — On-device JavaScript apps

This is a different kind of app from the Python host widgets.

- **Host widget** (`Python Apps/`): code runs on your computer and talks to
  the bar over HTTP.
- **JS app** (`apps/`): you upload files **onto the bar**. The bar runs the
  JavaScript itself, and the app shows up in the Apps menu.

Official docs still say the JS SDK is coming soon. This is for firmware that
already has a JS runner.

Worked example: Chess Clock under `apps/chess-clock/on-device/`.

## When to use which

Use a **host widget** if you want the current public path, or the computer
must do the work (live network stats, Spotify).

Use an **on-device JS app** if the user has JS-runner firmware and wants the
app to live on the bar after a one-time install.

## Repo layout

```
apps/                         on-bar JS apps
  chess-clock/on-device/community.chess_clock/
Python Apps/                  computer apps (normal firmware)
  network/  social-battery/
```

## Package

Folder name = app id:

```
community.chess_clock/
├── appmeta/manifest.json
├── appmeta/settings.json      optional — drives launcher Setup
├── appmeta/icon_front_8x8.png 8×8 colour, front menu
├── appmeta/icon_back_11x11.png 11×11 greyscale, back menu
├── scripts/main.js
├── images/                    optional
└── animations/                optional .anim files (bicycle1)
```

`manifest.id` must match the folder name. Allowed chars: `a-zA-Z0-9._`
(no hyphens).

`"debug": false` shows in Apps for everyone. `"debug": true` needs **Dev mode**.

## Put it on the bar

### Upload

```
POST /api/assets/upload?application_name=<id>&file=scripts/main.js
DELETE /api/assets/upload?application_name=<id>   # wipe before re-install
```

Body = raw file bytes. Shared helper:

```bash
cd apps/chess-clock
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python install_on_bar.py --host 10.0.4.20
```

Each on-bar app has its own `install_on_bar.py`. It uploads the package and
turns on the Apps listing.

If upload returns **503**, stop the running app first (leave with **Back**, or
CLI `js -k`), clear draws
(`DELETE /api/display/draw` with `application_name`), then install again.
Wiping assets while an animation is playing often fails.

### Enable Apps listing

`/ext/apps_data/apps_menu/js_apps_enabled` must exist. Installers write it.

### Dev mode (only for `debug: true`)

**Settings → Debug → Dev mode → On**, or USB CLI `sysctl debug 1`.

## Launch

1. Mode switch to **Apps**.
2. Open the app.
3. Launcher screen: **Start** runs `scripts/main.js`. **Setup** edits
   `appmeta/settings.json` when present (you cannot rename those two buttons).

Draw with `fetch("http://127.0.0.1/api/display/draw")`. Input with
`listen("input", handler)`.

To leave: call the `unbind()` from `listen`. Do **not** clear the display
after unbind — that can crash the bar.

Ignore the Start press that opened the app (short input grace), or the first
frame may flash and dump you back to the launcher.

## Animations

- Draw with `"type": "animation"` and a path relative to the app folder.
- Current firmware needs **bicycle1** files (`scripts/seq2anim.py`).
  Older `bicycle0` fails with a silent `AnimFile` error (often a magenta X).
- There is **no scale** in draw JSON — only `x`, `y`, `loop`, `opacity`.
  To fit several sprites, crop the source frames so empty canvas does not
  use the whole width.
- Opaque black blocks layers underneath. Punch near-black to alpha
  (`argb8888`) if a wash or background must show through.

## If it does not show up

| Symptom | Check |
|---------|--------|
| Nothing new in Apps | `js_apps_enabled` missing, or no JS runner |
| WIP app missing | `"debug": true` and Dev mode Off |
| Icons wrong | names/sizes `icon_front_8x8.png` / `icon_back_11x11.png` |
| Magenta X / blank | bad `.anim` (not bicycle1), or draw error |
| Old version | re-upload, reopen from Apps |

Next: [07-setup-settings-and-launch.md](07-setup-settings-and-launch.md).

Skill detail: `ai-skills/busy-bar-js-apps/SKILL.md`.
