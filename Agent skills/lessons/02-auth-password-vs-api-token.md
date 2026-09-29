# 02 — Wi-Fi password vs cloud API token

These are **two different secrets**. Mixing them up is the most common setup
mistake.

## Quick comparison

| | HTTP access password (local Wi-Fi) | Cloud API token |
|--|-----------------------------------|-----------------|
| **What it is** | Password you set on the bar’s web UI when enabling HTTP API over Wi-Fi | Long token from your BUSY account |
| **Where you get it** | Local web UI at `http://10.0.4.20` → Network → HTTP API → set password | https://cloud.busy.app → **API tokens** |
| **Used for** | Requests to the bar’s **LAN IP** over Wi-Fi | Requests through **`https://api.busy.app`** |
| **HTTP header** | `X-API-Token: <password>` | `Authorization: Bearer <api_token>` |
| **USB (`10.0.4.20`)** | Usually not required | Not used |
| **Shown again?** | You set and can change it on the device | Shown **once** when created — store it safely |

They are **not interchangeable**. The Wi-Fi password will not work as a Bearer
token on the cloud proxy, and a cloud API token is not the local HTTP password.

## 1. HTTP access password (local Wi-Fi)

Enable over USB first:

1. Open http://10.0.4.20
2. Go to **Network → HTTP API**
3. Turn on HTTP API access
4. Click **Set password and enable** and choose a password (device treats this
   as a short access key / PIN-style secret)

Then every Wi-Fi HTTP request must include:

```http
X-API-Token: <your-http-access-password>
```

### curl

```bash
curl -X GET "http://192.168.1.20/api/status" \
  -H "Accept: application/json" \
  -H "X-API-Token: 1234"
```

### Python (busylib)

busylib’s `token=` argument on a **local/Wi-Fi** address becomes `X-API-Token`:

```python
from busylib import BusyBar

bb = BusyBar("192.168.1.20", token="1234")
```

### TypeScript (busylib-ts)

Use the dedicated field — do not put the Wi-Fi password in `token`:

```ts
import { BusyBar } from '@busy-app/busy-lib';

const bar = new BusyBar({
  addr: '192.168.1.20',
  HTTPAccessPassword: '1234',
});
```

## 2. Cloud API token (internet)

1. Link the bar to your BUSY account (device / setup flow).
2. Open https://cloud.busy.app
3. **API tokens → + Create token**
4. Choose scope (**BUSY Bar** for device control, or **Account** for account API)
5. Copy the token immediately — it is shown only once

Then every cloud request must include:

```http
Authorization: Bearer <your_api_token>
```

Base URL: `https://api.busy.app/busybar`

### curl

```bash
curl -X GET "https://api.busy.app/busybar/status" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer <your_api_token>"
```

### Python (busylib)

When the client is in cloud mode, `token=` becomes `Authorization: Bearer …`.

### TypeScript (busylib-ts)

```ts
const bar = new BusyBar({
  addr: 'https://api.busy.app',
  token: '<your_api_token>',
});
```

## Decision guide

```
Are you talking to 10.0.4.20 over USB?
  → No secret (usually)

Are you talking to the bar’s Wi-Fi IP on your LAN?
  → HTTP access password in X-API-Token
    (busylib: token=… / busylib-ts: HTTPAccessPassword)

Are you talking to https://api.busy.app …?
  → Cloud API token in Authorization: Bearer …
    (busylib-ts: token=… / busylib cloud client)
```

## Safety

- Prefer USB or a trusted home/office Wi-Fi for the HTTP password.
- Never commit passwords or API tokens to git.
- Community apps in this repo send the Wi-Fi password only to the bar over the
  local network and should not save it unless the user opts in.
- Deleting a cloud API token permanently breaks every client still using it.
