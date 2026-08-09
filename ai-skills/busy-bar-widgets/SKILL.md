---
name: busy-bar-widgets
description: Build host-side BUSY Bar widgets and custom apps against official release firmware using busylib and the HTTP display API. Use when creating or updating Python/TS widgets, Social Battery-style apps, or AI-generated Busy Bar UI.
---

# BUSY Bar widget builder

Works with any AI. Paste this file after `BUSY-BAR-CORE.md` when building an app.

Build **host apps**: code runs on the PC and drives official firmware over HTTP.
Do not invent custom firmware requirements unless the user asks.
Do **not** tell users they must enter Apps mode to start; Off mode is fine.

## Checklist

```
- [ ] Connection path chosen (USB / Wi-Fi / cloud)
- [ ] Correct auth secret applied (see busy-bar-auth)
- [ ] application_name chosen
- [ ] Front 72×16 and/or back 160×80 respected
- [ ] Only current fonts used (see busy-bar-fonts)
- [ ] Assets uploaded before image draw; path = filename only
- [ ] clear on refresh/exit
- [ ] Do not require Apps mode to start (Off mode is fine)
- [ ] Beginner-friendly run steps if the user is non-technical
```

## Default stack

1. Python 3.10+ and `pip install busylib`
2. USB address `10.0.4.20` unless user gives a Wi‑Fi IP
3. `types.DisplayElements` + `display_draw(..., clear_before_draw=True)`
4. Optional `converter.convert_for_storage` before `assets_upload`

## Design rules (front)

- Prefer one composition: icon + short label, or one/two `small` text lines
- Center helpers: `x:36` + `top_mid` / `center` / `bottom_mid`
- No legacy fonts (`medium`, `big`, …)
- Sanitize text from the web/APIs to printable ASCII when needed

## Auth reminder

- Wi‑Fi password → `X-API-Token` / busylib `token=` on LAN / TS `HTTPAccessPassword`
- Cloud token → `Authorization: Bearer` / TS `token` with `api.busy.app`
- Never treat them as the same value

## Related files in this repo

- `ai-skills/BUSY-BAR-CORE.md`
- `ai-skills/busy-bar-auth/SKILL.md`
- `ai-skills/busy-bar-fonts/SKILL.md`
- `ai-skills/busy-bar-http-api/SKILL.md`
- `ai-lessons/README.md`
- Example: `apps/social-battery/`

## Output style for end users

Assume low technical experience unless told otherwise: short numbered steps,
one recommended path, and clear copy-paste commands.
