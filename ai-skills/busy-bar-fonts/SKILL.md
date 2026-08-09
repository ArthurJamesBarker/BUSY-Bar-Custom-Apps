---
name: busy-bar-fonts
description: Current BUSY Bar display sizes and text font names for display/draw. Use when laying out front 72x16 or back 160x80 text, choosing fonts, or migrating old medium/big font names.
---

# BUSY Bar fonts and displays

Works with any AI. Paste this file, or use `BUSY-BAR-CORE.md`.

## Displays

| Name | Pixels | Notes |
|------|--------|-------|
| `front` | 72×16 | RGB LED matrix |
| `back` | 160×80 | Greyscale OLED |

Set `display` on every element. Anchor with `x`, `y`, and `align`.

## Valid `font` values only

`tiny` · `small` · `normal` · `condensed` · `bold` · `large` · `extra_large` · `global`

| Name | Approx. height | Front tip |
|------|----------------|-----------|
| `tiny` | smallest | Dense labels |
| `small` | ~5px | Default for 1–2 lines |
| `normal` | ~7px | Clear single line |
| `condensed` | ~7px narrow | More chars per line |
| `bold` | ~7px bold | Emphasis |
| `large` | ~9px | Single-line on front |
| `extra_large` | ~10px | Hero single-line |
| `global` | ~11px | Tallest; one line on front |

## Forbidden legacy names

Do not emit: `medium`, `medium_condensed`, `big`, `tiny5_8`.

Map old → new: `medium`→`normal`/`condensed`, `big`→`large`/`extra_large`.

## Layout defaults (front)

- Prefer `small` for two-line layouts (`y:0` top_* / `y:15` bottom_*).
- Center one line: `x:36`, `y:8`, `align:"center"`.
- Tall fonts (`large`+): one text element only on the front.
- Long text: shorten or use `width` + `scroll_rate`.
- Prefer printable ASCII; sanitize external strings.

Colour: `#RRGGBBAA`.

## Longer lesson

See `ai-lessons/04-fonts-and-displays.md` in this repository.
