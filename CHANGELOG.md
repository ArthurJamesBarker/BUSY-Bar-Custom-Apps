# Changelog

## 2026-09-29

- Separated computer apps (`Python Apps/`) from on-bar apps (`apps/`).
  Network and Social Battery moved into `Python Apps/` and still use normal
  BUSY Bar firmware.
- Added on-bar Chess Clock. It needs firmware with the JavaScript runner.
  Official BUSY docs still say installing your own apps on the bar is coming
  soon.
- Updated the AI notes so they explain both kinds of apps.

## 2026-08-10

- Social Battery can start in Off mode, and closes only when the physical mode
  switch moves to a different position (not merely because the bar is not in
  Apps).

## 2026-08-09

- Kept `apps/spotify/` local-only (gitignored) until it is ready for community
  release.
- Added `apps/network/`: host app with UP/DOWN label artwork, live interface
  speeds, right-aligned values, Wi‑Fi password support, and Start Here
  launchers.
- Added `ai-lessons/` and `ai-skills/` (including pasteable `BUSY-BAR-CORE.md`)
  covering getting started, Wi‑Fi password vs cloud API token, HTTP API, fonts,
  and draw/assets for any AI assistant.
- Clarified that Apps mode is not required to start host widgets (Off mode is
  fine), including Social Battery setup docs.
