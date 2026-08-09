# 05 — Draw payloads and assets

## DisplayElements body

Current field name is **`application_name`** (not legacy `app_id`).

```json
{
  "application_name": "my_app",
  "elements": [ /* ... */ ],
  "priority": 6
}
```

`application_name` groups everything your app draws and owns in assets. Use a
stable name like `social_battery` or `my_app`.

Apps mode is **not** required to start drawing over HTTP. Off mode is fine.

## Element types (common)

Every element needs `id`, `type`, and usually `x`, `y`, `display`.

### text

```json
{
  "id": "status",
  "type": "text",
  "x": 2,
  "y": 4,
  "text": "BUILDING",
  "font": "small",
  "display": "front"
}
```

Optional: `align`, `color`, `width`, `scroll_rate`, `scroll_start_delay`,
`scroll_repeat_delay`, `timeout`, `display_until`.

Fonts: see [04-fonts-and-displays.md](04-fonts-and-displays.md).

### image

Upload first, then reference by **filename only**:

```json
{
  "id": "icon",
  "type": "image",
  "x": 0,
  "y": 0,
  "path": "icon.png",
  "display": "front"
}
```

- Do: `"path": "icon.png"`
- Don’t: `"path": "/assets/icon.png"` or a PC filesystem path
- Optional: `stock_path` for device stock art, `opacity` 0–100

Front icons: keep roughly ≤15×15 so text still fits.

### animation

Use only real device `.anim` assets (or stock paths). Type name in current
clients is often `"animation"` (check OpenAPI / busylib). Homemade zip bytes
that are not converted with the official toolchain will 400 at draw time.

### countdown

Needs `timestamp`, `direction` (`time_left` | `time_since`), and `show_hours`.
Usually tall — prefer countdown-only layouts on the front.

## Assets workflow

1. Convert/resize for the target display when needed (`busylib.converter` helps).
2. `POST /api/assets/upload` with `application_name` + filename.
3. `POST /api/display/draw` referencing that filename in `path`.
4. On exit: clear draw + delete assets for your `application_name`.

### busylib sketch

```python
from busylib import BusyBar, converter, types

APP = "my_app"

with BusyBar("10.0.4.20") as bb:
    with open("icon.png", "rb") as f:
        name, data = converter.convert_for_storage("icon.png", f.read())
    bb.assets_upload(APP, name, data)

    bb.display_draw(
        types.DisplayElements(
            application_name=APP,
            elements=[
                types.ImageElement(
                    id="icon",
                    type="image",
                    x=0,
                    y=0,
                    path=name,
                    display=types.DisplayName.FRONT,
                ),
                types.TextElement(
                    id="label",
                    type="text",
                    x=18,
                    y=8,
                    align="mid_left",
                    text="OK",
                    font="small",
                    display=types.DisplayName.FRONT,
                ),
            ],
        ),
        clear_before_draw=True,
    )
```

## Replace vs add

- Default draw **adds** elements for your app.
- Prefer `clear_before_draw=True` (busylib) when refreshing a full frame.
- `display_clear` / `DELETE` clears your app’s content when you are done.

## Working example in this repo

[`apps/social-battery/`](../apps/social-battery/) — host Python app, official
firmware only, Wi-Fi password prompt when needed, seven 72×16 PNG states.
