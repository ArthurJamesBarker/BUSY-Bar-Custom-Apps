# HTTP API quick reference

## Auth headers

| Path | Header |
|------|--------|
| USB `10.0.4.20` | (usually none) |
| Wi-Fi LAN | `X-API-Token: <http-access-password>` |
| Cloud proxy | `Authorization: Bearer <cloud-api-token>` |

## Useful endpoints for widgets

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/version` (or firmware status routes) | Connectivity check |
| POST | `/api/display/draw` | Body: DisplayElements JSON |
| DELETE | `/api/display/draw` | Clear; filter by `application_name` when supported |
| POST | `/api/assets/upload` | Query includes `application_name` + file name |
| DELETE | `/api/assets/upload` | Wipe app assets |
| POST | `/api/storage/mkdir` | Create a folder under `/ext/...` |
| GET | `/api/storage/read` | Download a file under `/ext/...` |

## Minimal draw body

```json
{
  "application_name": "demo",
  "elements": [
    {
      "id": "t1",
      "type": "text",
      "x": 36,
      "y": 8,
      "align": "center",
      "text": "HI",
      "font": "small",
      "display": "front"
    }
  ]
}
```

## Displays

- front: 72×16 RGB
- back: 160×80 greyscale

## Device mode

Apps mode is **not** required to start host widgets. Off mode is fine.

On-device JS apps **do** launch from Apps. After upload, also write
`/ext/apps_data/apps_menu/js_apps_enabled`. `"debug": true` apps need
**Settings → Debug → Dev mode → On**.

## Libraries

- Python: https://pypi.org/project/busylib/
- TypeScript: https://github.com/busy-app/busylib-ts
