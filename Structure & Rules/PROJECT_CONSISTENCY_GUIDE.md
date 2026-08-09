# Project consistency guide

## Purpose

This repo ships **community host apps** for official BUSY Bar firmware, plus
teaching materials so humans and AI assistants use the **current** API.

## Layout

| Path | Role |
|------|------|
| `apps/<app-name>/` | One runnable app per folder (README + code + assets) |
| `ai-skills/` | AI skills + paste pack (`BUSY-BAR-CORE.md`) |
| `ai-lessons/` | Longer human-readable lessons |
| `Structure & Rules/` | Repo conventions for contributors and assistants |

## Rules

1. Prefer fixing behaviour in an app or lesson docs before changing any global
   tooling outside this repo.
2. Lessons and skills must stay aligned with official Busy docs / busylib /
   release firmware — especially **fonts** and **auth**.
3. Never document legacy font names (`medium`, `big`, …) as valid.
4. Always distinguish **Wi-Fi HTTP access password** (`X-API-Token`) from
   **cloud API token** (`Authorization: Bearer`).
5. Use `application_name` (not legacy `app_id`) in draw/asset examples.
6. Do **not** say users must enter Apps mode to start host widgets; Off mode is
   fine for HTTP draws.
7. Keep AI materials tool-agnostic (plain Markdown only).
8. Update only the root `CHANGELOG.md` when apps, lessons, or skills change.
   Never add per-folder changelogs (see `.cursor/rules/single-changelog.mdc`).
