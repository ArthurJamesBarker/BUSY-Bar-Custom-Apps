# Spotify

Spotify shows what’s playing on your Spotify account on the BUSY Bar, with
simple play/pause and skip controls from the bar’s buttons and dial.

The app runs on your computer. It talks to Spotify over the internet, and to
your BUSY Bar over USB or Wi‑Fi using official release firmware.

## What you need

- BUSY Bar with current release firmware
- Windows, macOS, or Linux computer
- Python 3.10 or newer
- A free [Spotify Developer](https://developer.spotify.com/dashboard) app
- Spotify playing on a phone, computer, or speaker linked to your account

## 1. Download the app

1. Open this repository on GitHub:
   [BUSY-Bar-Custom-Apps](https://github.com/ArthurJamesBarker/BUSY-Bar-Custom-Apps).
2. Select **Code**, then **Download ZIP**.
3. Unzip the download.
4. Open `apps`, then `spotify`.

## 2. Create your Spotify credentials

Anyone who runs this app needs **their own** Spotify app credentials. Do not
share your client secret.

1. Open [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Log in and click **Create app**
3. Give it any name (for example `BUSY Bar Spotify`)
4. Open the app → **Settings**
5. Add Redirect URI: `http://127.0.0.1:8888/callback`
6. Save, then copy the **Client ID** and **Client Secret**

In the `spotify` folder, copy the example env file:

```bash
cp .env.example .env
```

Edit `.env` and paste your values:

```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

`.env` stays on your computer only (it is gitignored).

## 3. Prepare the BUSY Bar

1. Connect the BUSY Bar by USB, or put it on the same Wi‑Fi as your computer.
2. If using Wi‑Fi, enable **HTTP API access** and keep the password ready.
3. USB normally uses `10.0.4.20`.

## 4. Start Spotify

Open the **Start Here** folder, then choose your computer, **or** run:

```bash
python3 -m pip install -r requirements.txt
python3 spotify.py
```

For Wi‑Fi:

```bash
python3 spotify.py 192.168.1.123
```

With the Wi‑Fi HTTP password:

```bash
python3 spotify.py 192.168.1.123 YOUR_PASSWORD
```

The first Spotify login opens a browser window so you can approve access. After
that, a local `.cache` file remembers the login (also gitignored).

## Controls

- **Scroll wheel**: volume up / down
- **OK** once: play / pause
- **OK** twice quickly: next track
- **OK** three times quickly: previous track
- **Start**: play / pause
- **Back** or `Ctrl+C`: stop the app

## Optional: cloud display

If your bar is linked to a BUSY cloud account, you can push the display through
the cloud (controls still work best on the same Wi‑Fi):

```bash
python3 spotify.py cloud YOUR_CLOUD_API_TOKEN
```

Create that token at [cloud.busy.app](https://cloud.busy.app) (API tokens).
This is **not** the same as the local Wi‑Fi HTTP password.

## Troubleshooting

### Spotify credentials missing

Create a Spotify developer app and fill in `.env` from `.env.example`.

### Nothing shows / “not playing”

Start playback in the Spotify app on any device signed into the same account.

### BUSY Bar password rejected

Use the Wi‑Fi HTTP access password from the bar’s web UI, not a cloud API token.

### Browser keeps asking to log in

Delete `.cache` in this folder and run the app again to re-authorize.

## Files included

- `spotify.py` — main app
- `busybar_ws_input.py` — BUSY Bar button/dial listener
- `assets/` — logos and control icons
- `.env.example` — Spotify credential template
- `requirements.txt` — Python packages
- `Start Here` — macOS / Windows launchers

## License

Released under the repository [MIT License](../../LICENSE).
