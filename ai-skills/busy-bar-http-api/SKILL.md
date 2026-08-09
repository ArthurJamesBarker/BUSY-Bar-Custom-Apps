---
name: busy-bar-http-api
description: BUSY Bar HTTP API basics — base URLs, key endpoints, application_name, busylib usage. Use when calling display/draw, uploading assets, reading status, or writing host widgets against official firmware.
---

# BUSY Bar HTTP API

Works with any AI. Paste this file, or use `BUSY-BAR-CORE.md`.
More tables: `reference.md` next to this file.

## Base URLs

- USB: `http://10.0.4.20`
- Wi‑Fi: `http://<bar-lan-ip>`
- Cloud: `https://api.busy.app/busybar`

Auth: see skill `busy-bar-auth` (password ≠ API token).

Docs: https://docs.busy.app/bar/dev/http-api  
OpenAPI UI: https://api.busy.app/busybar/docs or `http://10.0.4.20/docs`

## Critical naming

- Use **`application_name`** for draw/assets grouping.
- Do **not** use legacy **`app_id`**.

## Core host-widget flow

1. Optional: upload asset → `POST /api/assets/upload`
2. Draw → `POST /api/display/draw` with `application_name` + `elements`
3. Clear / delete assets when done

Prefer official clients:

```python
from busylib import BusyBar, types
# pip install busylib
```

```ts
import { BusyBar } from '@busy-app/busy-lib';
```

## Rules for the assistant

1. Target the bar address — never `localhost:11434` for device APIs.
2. Image `path` is filename only after upload (no `/assets/` prefix).
3. Do **not** require Apps mode to start host widgets; Off mode is fine.
4. Match firmware OpenAPI for the bar’s version when unsure.
5. For fonts/layout use `busy-bar-fonts`. For auth use `busy-bar-auth`.

## Longer lessons

- `ai-lessons/03-http-api-basics.md`
- `ai-lessons/05-draw-and-assets.md`
