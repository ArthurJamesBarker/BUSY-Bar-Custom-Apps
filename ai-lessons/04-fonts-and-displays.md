# 04 — Fonts and displays

## Two displays

| Display | Size | Kind |
|---------|------|------|
| **front** | **72 × 16** | RGB LED matrix |
| **back** | **160 × 80** | Greyscale OLED (16 shades) |

Every element must set `display` to `front` or `back`. Content outside the
bounds is accepted but not visible.

Origin is top-left. `x` / `y` are the **anchor**; `align` chooses which corner
or mid-point of the element sits on that anchor.

## Current font names (required)

Use **only** these values in `font` for text elements:

| API name | Firmware face (approx. height) | Front (72×16) tip |
|----------|--------------------------------|-------------------|
| `tiny` | busy_tiny | Densest; good for lots of small labels |
| `small` | busy_regular_5 (~5px) | Best default for 1–2 lines on the front |
| `normal` | busy_regular_7 (~7px) | Clear single line / short labels |
| `condensed` | busy_condensed_7 (~7px) | Narrower glyphs; more characters per line |
| `bold` | busy_bold_7 (~7px) | Emphasis at ~7px |
| `large` | busy_regular_9 (~9px) | Treat as **single-line** on the front |
| `extra_large` | busy_bold_10 (~10px) | Single-line hero text on the front |
| `global` | lana_pixel_regular_11 (~11px) | Tallest; front is effectively one line |

### Outdated names — do not use

These appeared in old AI lessons and are **rejected** by current firmware /
busylib:

- `medium`
- `medium_condensed`
- `big`
- `tiny5_8` (schema leftover from older docs)

Rough migration:

| Old | Prefer now |
|-----|------------|
| `small` | `small` (still valid) |
| `medium` / `medium_condensed` | `normal` or `condensed` |
| `big` | `large` or `extra_large` |

## Front layout recipes (72×16)

- **One line, centered:** `x: 36`, `y: 8`, `align: "center"`, font `small` or `normal`
- **Two lines:** top `y: 0` + `align: "top_mid"`; bottom `y: 15` + `align: "bottom_mid"`; both `small`
- **Avoid 3+ text lines** on the front
- **Tall fonts** (`large`, `extra_large`, `global`): one element only on the front
- Long text: set `width` (often `72`) and `scroll_rate`, or shorten the string
- Safe non-scrolling lengths vary by font; start around ≤12 chars for `small`

## Back layout (160×80)

More room for `large` / `extra_large` / `global` and multi-line layouts. Still
keep icons and text from overlapping; the back is greyscale.

## Text and colour

- Prefer **printable ASCII** for reliable glyphs (bitmap fonts).
- With busylib, `sanitize_text=True` on draw strips unsupported characters.
- Colours use 8-digit hex with alpha: `#RRGGBBAA` (example white `#FFFFFFFF`).

## Example

```json
{
  "application_name": "demo",
  "elements": [
    {
      "id": "title",
      "type": "text",
      "x": 36,
      "y": 8,
      "align": "center",
      "text": "BUSY",
      "font": "small",
      "color": "#FFFFFFFF",
      "display": "front"
    }
  ]
}
```
