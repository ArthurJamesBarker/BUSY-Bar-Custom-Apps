---
name: busy-bar-auth
description: Explains BUSY Bar authentication — local Wi-Fi HTTP access password (X-API-Token) versus cloud API token (Authorization Bearer). Use when connecting over USB, Wi-Fi, or api.busy.app, fixing 403 errors, or configuring busylib / busylib-ts auth.
---

# BUSY Bar auth

Works with any AI. Paste this file, or use `BUSY-BAR-CORE.md`.

## Never mix these secrets

| Secret | Where created | When used | Header |
|--------|---------------|-----------|--------|
| **HTTP access password** | Device web UI `http://10.0.4.20` → Network → HTTP API | LAN Wi-Fi IP | `X-API-Token: <password>` |
| **Cloud API token** | https://cloud.busy.app → API tokens | `https://api.busy.app/...` | `Authorization: Bearer <token>` |

USB to `10.0.4.20` usually needs **neither**.

## Client mapping

**busylib (Python)** — on a local/Wi‑Fi address, `token=` becomes `X-API-Token`:

```python
BusyBar("10.0.4.20")                      # USB, no auth
BusyBar("192.168.1.20", token="1234")     # Wi-Fi password
```

**busylib-ts** — separate fields:

```ts
new BusyBar({ addr: '192.168.1.20', HTTPAccessPassword: '1234' })
new BusyBar({ addr: 'https://api.busy.app', token: '<cloud-token>' })
```

Do **not** pass the Wi‑Fi password as a cloud Bearer token, and do **not** use
a cloud API token as `X-API-Token` on the LAN.

## Rules for the assistant

1. Ask which path the user uses: USB, Wi‑Fi LAN, or cloud.
2. For Wi‑Fi `403`, enable HTTP API access on the bar and send the **password**.
3. For cloud, require a token from cloud.busy.app (shown once).
4. Never commit secrets; prefer env vars or prompts.
5. LAN WebSocket/state streams often need the password too (`x-api-token`).

## Longer lesson

See `ai-lessons/02-auth-password-vs-api-token.md` in this repository.
