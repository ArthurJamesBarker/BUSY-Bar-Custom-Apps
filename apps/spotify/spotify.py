"""
Spotify BUSY Bar widget — simple one-page version with slide transitions.

- Title page only (logo + artist + song).
- Scroll right  -> next song    (slides to the album-art view, next symbol blinks once, slides back)
- Scroll left   -> previous song (same, with the prev symbol)
- Start button  -> play/pause. While paused, the pause symbol blinks over the
                   album art until you press Start again.

States slide on/off screen horizontally rather than clearing the display,
so there is no blank flash between views.
"""

import io
import math
import os
import re
import subprocess
import sys
import threading
import time

import requests
import spotipy
from PIL import Image, ImageDraw, ImageEnhance
from spotipy.oauth2 import SpotifyOAuth
from unidecode import unidecode

# Reads scroll/button inputs over the firmware /api/status/ws WebSocket
# (replaces the old telnet CLI). Falls back to telnet automatically.
from busybar_ws_input import (
    ACT_PRESS, BTN_OK, BTN_START, stream_input_events,
)

# --- CONFIG ---
APP_ID = "spotify"
UPDATE_INTERVAL = 2
DEFAULT_DEVICE_IP = "10.0.4.20"
CLOUD_HOST = os.environ.get("BUSYBAR_CLOUD_HOST", "api.busy.app")
APP_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_dotenv() -> None:
    """Load optional key=value pairs from a local .env (no extra dependency)."""
    path = os.path.join(APP_DIR, ".env")
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("'").strip('"')
            os.environ.setdefault(key, value)


_load_dotenv()

# Local Wi-Fi / USB (needs the bar IP):
#   python3 spotify.py
#   python3 spotify.py 192.168.1.20
#   python3 spotify.py 192.168.1.20 YOUR_WIFI_PASSWORD
#
# Optional cloud display (Bearer token from cloud.busy.app):
#   python3 spotify.py cloud YOUR_CLOUD_TOKEN
#
# Env fallbacks: BUSYBAR_IP, BUSYBAR_PASSWORD / BUSYBAR_TOKEN, BUSYBAR_CLOUD,
# BUSYBAR_CLOUD_HOST, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI.
_arg1 = (sys.argv[1].strip() if len(sys.argv) > 1 else "")
DEVICE_TOKEN = (
    sys.argv[2].strip()
    if len(sys.argv) > 2
    else (
        os.environ.get("BUSYBAR_PASSWORD")
        or os.environ.get("BUSYBAR_TOKEN")
        or os.environ.get("BUSYBAR_API_KEY")
        or ""
    ).strip()
)
USE_CLOUD = (_arg1.lower() == "cloud") or os.environ.get("BUSYBAR_CLOUD", "") == "1"

if USE_CLOUD:
    DEVICE_IP = None
    API_BASE  = f"https://{CLOUD_HOST}/busybar"
    WS_URL    = f"wss://{CLOUD_HOST}/busybar/status/ws"
    _AUTH_HEADERS = {"Authorization": f"Bearer {DEVICE_TOKEN}"} if DEVICE_TOKEN else {}
    if not DEVICE_TOKEN:
        print("Cloud mode needs a token:  python3 spotify.py cloud <token>")
    else:
        print(f"Cloud mode via {CLOUD_HOST} (no IP needed)")
        print("Display updates work remotely; scroll/button controls need same-WiFi mode.")
else:
    DEVICE_IP = _arg1 or os.environ.get("BUSYBAR_IP", DEFAULT_DEVICE_IP)
    API_BASE  = f"http://{DEVICE_IP}/api"
    WS_URL    = f"ws://{DEVICE_IP}/api/status/ws"
    # Local key-access mode uses the X-API-Token header (and ws query param).
    _AUTH_HEADERS = {"X-API-Token": DEVICE_TOKEN} if DEVICE_TOKEN else {}
    if DEVICE_TOKEN:
        WS_URL += f"?x-api-token={DEVICE_TOKEN}"

DEVICE_URL = f"{API_BASE}/display/draw"

# A shared session carries the auth header (if any) on every device request.
# Spotify CDN downloads use plain `requests` so the token never leaks off-device.
_dev = requests.Session()
if _AUTH_HEADERS:
    _dev.headers.update(_AUTH_HEADERS)


def _verify_connection():
    """Fail fast with a helpful message if the device/cloud won't accept us."""
    try:
        r = _dev.get(f"{API_BASE}/version", timeout=5)
    except requests.RequestException as e:
        where = CLOUD_HOST if USE_CLOUD else DEVICE_IP
        print(f"Cannot reach {where}: {e}")
        sys.exit(1)
    if r.status_code == 200:
        return
    if USE_CLOUD and r.status_code == 401:
        print("Cloud login failed (401). Check your API token at:")
        print("  https://cloud.busy.app/api-tokens")
        print()
        print("  python3 spotify.py cloud <token>")
        sys.exit(1)
    if USE_CLOUD and r.status_code == 403:
        print("Cloud access denied (403). Your token looks valid but the cloud")
        print("cannot control your bar yet. The usual cause: the bar is not")
        print("linked to your cloud account.")
        print()
        print("  1. On the BUSY Bar: Settings → Account → Link (get a PIN)")
        print("  2. At cloud.busy.app: enter that PIN to link the device")
        print("  3. Retry:  python3 spotify.py cloud <token>")
        print()
        print("  Same WiFi (works now, needs IP):")
        print("    python3 spotify.py <ip> <wifi-password>")
        sys.exit(1)
    print(f"Device API error {r.status_code}: {r.text[:200]}")
    sys.exit(1)


# Telnet CLI hosts for button events (local fallback only; not used in cloud mode).
TELNET_HOSTS = [DEVICE_IP] if DEVICE_IP else []

# Control scheme:
#   Scroll wheel  -> Spotify volume up / down
#   OK  x1        -> play / pause
#   OK  x2        -> next track
#   OK  x3        -> previous track
#   Start         -> play / pause (instant shortcut)
#
# Telnet fallback key names (from `input dump` on the device CLI)
SCROLL_UP_KEY    = "InputKeyUp"     # encoder +1 = volume up
SCROLL_DOWN_KEY  = "InputKeyDown"   # encoder -1 = volume down
OK_KEY           = "InputKeyOk"     # ok = play/pause (x2 next, x3 prev)
START_KEY        = "InputKeyStart"  # start = play/pause

SCROLL_STEPS = 1    # wheel detents per volume step (lower = more sensitive)
VOLUME_STEP  = 5    # percent change per volume step
OK_MULTICLICK_WINDOW = 0.45   # seconds to wait for further OK clicks

# Feedback animation timing
SKIP_FRAME_INTERVAL  = 0.09   # seconds per frame of the arrow chase animation
PAUSE_BLINK_INTERVAL = 0.5    # seconds per frame while paused
SLIDE_FRAMES         = 6      # frames in the label swipe (72px / 6 = 12px per frame)
SLIDE_INTERVAL       = 0.02   # extra delay per swipe frame (HTTP latency adds more)

# --- SPOTIFY ---
# Cache the auth token next to this script (absolute path) so it works no matter
# what directory you launch from — otherwise each API call re-opens the browser.
# Never commit .cache — it contains your personal Spotify tokens.
_CACHE_PATH = os.path.join(APP_DIR, ".cache")
_SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", "").strip()
_SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "").strip()
_SPOTIFY_REDIRECT_URI = os.environ.get(
    "SPOTIFY_REDIRECT_URI",
    "http://127.0.0.1:8888/callback",
).strip()
if not _SPOTIFY_CLIENT_ID or not _SPOTIFY_CLIENT_SECRET:
    print("Spotify credentials are missing.")
    print()
    print("Create a Spotify app at https://developer.spotify.com/dashboard")
    print("then set these in apps/spotify/.env (copy from .env.example):")
    print("  SPOTIFY_CLIENT_ID=...")
    print("  SPOTIFY_CLIENT_SECRET=...")
    print("  SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback")
    print()
    print("Add the same Redirect URI in the Spotify dashboard settings.")
    sys.exit(1)

scope = "user-read-currently-playing user-read-playback-state user-modify-playback-state"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=_SPOTIFY_CLIENT_ID,
    client_secret=_SPOTIFY_CLIENT_SECRET,
    redirect_uri=_SPOTIFY_REDIRECT_URI,
    scope=scope,
    cache_path=_CACHE_PATH,
))

# --- SHARED STATE ---
_lock            = threading.Lock()
_control_lock    = threading.Lock()   # serialises Spotify control calls; drops rapid repeats
_refresh_event   = threading.Event()
_scroll_accum    = 0
feedback         = None    # 'next' | 'prev' — transient blink animation request
is_playing       = False
current_track_id = None
_force_poll      = False
last_artist      = None
last_song        = None

# OK multi-click detection
_ok_clicks       = 0
_ok_timer        = None
_ok_lock         = threading.Lock()

# Volume control (coalesces rapid scrolls into sequential applies)
_vol_target      = None
_vol_active      = False
_vol_lock        = threading.Lock()
_overlay_until   = 0.0     # while now < this, pause the wave anim (volume bar shown)

# --- ASSET REMOTE NAMES ---
ASSETS_DIR    = os.path.join(APP_DIR, "assets")
R_BACKGROUND  = "sp_background.png"
R_LOGO        = "sp_logo.png"
R_ALBUM_BG    = "sp_album_strip.png"   # darkened 72x16 album-art strip
# NOTE: must stay 72x16. The device caches an asset's dimensions by filename on
# first draw and then rejects any smaller image uploaded to that name (until it
# reboots), so never reuse this name for a larger image.
R_WAVE_FMT    = "sp_wave_{}.png"       # animated equalizer frames behind the title page
R_WAVE_BLANK  = "sp_wave_blank.png"    # transparent frame for the 'off' style
R_VOLBAR      = "sp_volbar.png"        # transient 72x16 volume bar overlay
R_PAUSE_SEL   = "sp_pause_sel.png"
R_PAUSE_UNSEL = "sp_pause_unsel.png"
R_ARROW_L_GRN = "sp_arrow_l_green.png"
R_ARROW_L_WHT = "sp_arrow_l_white.png"
R_ARROW_R_GRN = "sp_arrow_r_green.png"
R_ARROW_R_WHT = "sp_arrow_r_white.png"

# --- LAYOUT ---
LOGO_X,  LOGO_Y = 1, 2      # 12x12 logo
TEXT_X          = 15
TEXT_TOP_Y      = 0
TEXT_BOT_Y      = 7

ALBUM_BG_X, ALBUM_BG_Y = 0, 0     # 72x16 centre strip of the album art

# Feedback icons centred on screen
PAUSE_X, PAUSE_Y = 29, 1            # 13x13: (72-13)/2≈29
ARROW_XS = (28, 33, 38)             # three 6x12 arrows, outer two pulled 2px toward centre
ARROW_Y  = 2                        # (16-12)/2


# ---------------------------------------------------------------------------
# Asset upload
# ---------------------------------------------------------------------------

def _upload_bytes(data: bytes, remote_name: str) -> bool:
    try:
        r = _dev.post(
            f"{API_BASE}/assets/upload",
            params={"application_name": APP_ID, "file": remote_name},
            data=data,
            headers={"Content-Type": "application/octet-stream"},
            timeout=5,
        )
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"Upload failed [{remote_name}]: {e}")
        return False


def _upload_file(fname: str, remote_name: str):
    path = os.path.join(ASSETS_DIR, fname)
    if not os.path.exists(path):
        print(f"Missing asset: {path}")
        return
    with open(path, "rb") as f:
        _upload_bytes(f.read(), remote_name)


def upload_static_assets():
    print("Uploading static assets...")
    for fname, remote in [
        ("background.png",           R_BACKGROUND),
        ("spotifyLogo.png",          R_LOGO),
        ("pauseButtonSelected.png",  R_PAUSE_SEL),
        ("pauseButtonUnSelected.png",R_PAUSE_UNSEL),
        ("leftSingleArrowGreen.png", R_ARROW_L_GRN),
        ("leftSingleArrowWhite.png", R_ARROW_L_WHT),
        ("rightSingleArrowGreen.png",R_ARROW_R_GRN),
        ("rightSingleArrowWhite.png",R_ARROW_R_WHT),
    ]:
        _upload_file(fname, remote)

    # Flat placeholder equalizer frames so the title page never references
    # a missing asset before the first live frame is rendered.
    flat = [1] * WAVE_BARS
    _upload_bytes(_render_bar_frame(flat), R_WAVE_FMT.format(0))
    _upload_bytes(_render_bar_frame(flat), R_WAVE_FMT.format(1))

    # Fully transparent frame used when the background style is 'off'
    blank = Image.new("RGBA", (72, 16), (0, 0, 0, 0))
    buf = io.BytesIO()
    blank.save(buf, format="PNG")
    _upload_bytes(buf.getvalue(), R_WAVE_BLANK)


def fetch_and_upload_album_art(image_url: str):
    """Download album art, scale to 72 wide, crop the centre 72x16 strip, darken
    to 20%, upload as background. The firmware rejects images larger than the
    72x16 display, so the art is cropped to the screen rather than offset."""
    try:
        img_bytes = requests.get(image_url, timeout=5).content
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        img72 = img.resize((72, 72), Image.LANCZOS)
        top   = (72 - 16) // 2                 # centre band
        strip = img72.crop((0, top, 72, top + 16))

        buf = io.BytesIO()
        ImageEnhance.Brightness(strip).enhance(0.2).save(buf, format="PNG")
        _upload_bytes(buf.getvalue(), R_ALBUM_BG)
    except Exception as e:
        print(f"Album art update failed: {e}")


# Waveform background settings
WAVE_STYLES        = ("off", "wave", "bars")   # OK button cycles through these
WAVE_STYLE         = "wave"                    # starting style
WAVE_COLOR         = (44, 64, 104)    # dim slate blue (base) — recedes behind the text
WAVE_GREEN         = (26, 84, 52)      # dark green accent
WAVE_RED           = (120, 48, 48)     # dark red accent (used very sparingly)
WAVE_GREEN_MIX     = 0.50              # max amount of dark green blended in (0..1)
WAVE_RED_MIX       = 0.18              # max amount of red blended in (kept tiny)
WAVE_OPACITY       = 255             # 100%


def _blend(c1, c2, f):
    """Linear blend from c1 to c2 by fraction f (0..1)."""
    f = max(0.0, min(1.0, f))
    return tuple(round(a + (b - a) * f) for a, b in zip(c1, c2))


def _accent_color(pos: float):
    """Base slate blue with dark-green patches and a rare, tiny touch of red,
    varying along `pos` so the tints drift across the wave/bars."""
    g = WAVE_GREEN_MIX * (0.5 + 0.5 * math.sin(pos * 0.15))
    col = _blend(WAVE_COLOR, WAVE_GREEN, g)
    # Sparse red: only the narrow positive peaks of a slow sine, sharpened by a power.
    r = WAVE_RED_MIX * max(0.0, math.sin(pos * 0.085 + 1.0)) ** 3
    return _blend(col, WAVE_RED, r)
WAVE_X_START       = 14              # left edge of the wave/bars (clears the logo)
WAVE_BARS          = (72 - WAVE_X_START) // 3   # 2px bar + 1px gap from x start to right edge
WAVE_BAR_MAX_H     = 13              # bars never grow longer than this (px)
WAVE_Y_OFFSET      = 1               # nudge the centred waveform down this many px
WAVE_BOB_HZ        = 1.2             # how fast the bars bob
WAVE_SCROLL_PX_S   = 7               # waveform travel speed (px per second, one direction)
WAVE_TAPER         = 8               # px over which the waveform fades to 0 at each edge
WAVE_ANIM_INTERVAL = 0.25            # seconds per animation frame

# Live wave state (set per track by prepare_wave, read by the animation tick)
wave_cols     = None    # 72 normalised loudness columns across the song
wave_duration = 0.0     # track length in seconds
wave_phases   = []      # per-bar bob phase offsets
wave_xvar     = []      # per-pixel height multipliers (breaks up the uniform wave)
progress_s    = 0.0     # playback position at last poll (seconds)
progress_ts   = 0.0     # wall-clock time of that poll


def _render_bar_frame(heights: list) -> bytes:
    """Render WAVE_BARS top-anchored bars (heights in px) starting at WAVE_X_START."""
    img  = Image.new("RGBA", (72, 16), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    for b, h in enumerate(heights[:WAVE_BARS]):
        x0 = WAVE_X_START + b * 3
        # Dark-green patches and a rare tiny bit of red, varying bar to bar.
        col = _accent_color(b * 4)
        draw.rectangle((x0, 0, x0 + 1, h - 1), fill=(*col, WAVE_OPACITY))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _render_wave_frame(level: float, t: float, offset: float) -> bytes:
    """Render a centred travelling waveform (from WAVE_X_START to the right edge).
    The amplitude tapers to 0 over WAVE_TAPER px at both edges instead of cutting off.
    Two sine harmonics plus a per-pixel jitter give the peaks varied heights."""
    img  = Image.new("RGBA", (72, 16), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    xvar = wave_xvar or [1.0] * 72
    n    = len(xvar)
    amp  = 0.4 + 0.6 * level   # overall loudness scaling, with a tall floor
    # Scroll the (seamless) height profile in one direction so it travels.
    scroll = t * WAVE_SCROLL_PX_S
    for x in range(WAVE_X_START, 72):
        env = min(1.0,
                  (x - WAVE_X_START + 1) / WAVE_TAPER,   # fade in from the left edge
                  (72 - x) / WAVE_TAPER)                 # fade out at the right edge
        # Sample the profile at a moving, fractionally-interpolated position.
        p   = (x + scroll) % n
        i0  = int(p)
        f   = p - i0
        v   = xvar[i0] * (1 - f) + xvar[(i0 + 1) % n] * f
        h   = round(amp * v * 16 * env)
        if h < 1:
            continue
        # Dark-green patches and a rare tiny bit of red that drift with the scroll.
        col = _accent_color(x + scroll)
        top = (16 - h) // 2 + WAVE_Y_OFFSET
        draw.line([(x, top), (x, top + h - 1)], fill=(*col, WAVE_OPACITY))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _pseudo_wave_columns(track_id: str) -> list:
    """Deterministic per-track energy profile for when audio analysis isn't available."""
    import hashlib
    import random
    seed = int(hashlib.md5(track_id.encode()).hexdigest(), 16)
    rnd  = random.Random(seed)
    cols, v = [], rnd.uniform(0.3, 0.7)
    for _ in range(72):
        v = min(1.0, max(0.15, v + rnd.uniform(-0.25, 0.25)))
        cols.append(v)
    return cols


def prepare_wave(track_id: str, duration_ms: int):
    """Store the track's loudness profile for the live equalizer.

    The profile (72 columns across the song) comes from Spotify audio analysis;
    the animation tick looks up the column at the current playback position so
    the bars get taller in loud sections and shorter in quiet ones. Falls back
    to a per-track pseudo profile if the analysis endpoint is unavailable."""
    global wave_cols, wave_duration, wave_phases, wave_xvar
    import hashlib
    import random

    duration = (duration_ms or 0) / 1000.0
    try:
        analysis = sp.audio_analysis(track_id)
        segments = analysis.get("segments", [])
        a_dur    = analysis.get("track", {}).get("duration", 0)
        if a_dur:
            duration = a_dur
        if not segments or not duration:
            raise ValueError("no analysis data")

        buckets = [[] for _ in range(72)]
        for s in segments:
            col = min(71, int(s["start"] / duration * 72))
            # loudness is in dB (~ -60..0); convert to linear amplitude
            buckets[col].append(10 ** (s.get("loudness_max", -60) / 20))
        cols = [sum(b) / len(b) if b else 0.0 for b in buckets]
        peak = max(cols) or 1.0
        cols = [c / peak for c in cols]
    except Exception as e:
        print(f"Wave: audio analysis unavailable ({e}) — using pseudo profile")
        cols = _pseudo_wave_columns(track_id)

    seed = int(hashlib.md5(track_id.encode()).hexdigest(), 16)
    rnd  = random.Random(seed)

    # Smoothed height profile: random control points every few px, linearly
    # interpolated, then normalised so the tallest column reaches 1.0. This gives
    # distinct tall/short "hills" across the width rather than uniform noise.
    # The last control point repeats the first so the profile tiles seamlessly
    # when scrolled (no visible seam at the wrap).
    step = 4
    n_ctrl = 72 // step + 1
    ctrl = [rnd.uniform(0.12, 1.0) for _ in range(n_ctrl)]
    ctrl[-1] = ctrl[0]
    shape = []
    for x in range(72):
        i, f = divmod(x, step)
        i = min(i, n_ctrl - 2)
        shape.append(ctrl[i] * (1 - f / step) + ctrl[i + 1] * (f / step))
    smax = max(shape) or 1.0
    # Normalise, then apply a contrast curve so tall peaks and short troughs differ more.
    shape = [(s / smax) ** 1.6 for s in shape]

    with _lock:
        wave_cols     = cols
        wave_duration = duration or 1.0
        wave_phases   = [rnd.uniform(0, 2 * math.pi) for _ in range(WAVE_BARS)]
        wave_xvar     = shape


def _current_loudness() -> float:
    """Loudness (0..1) at the estimated current playback position."""
    with _lock:
        cols, duration = wave_cols, wave_duration
        pos = progress_s + (time.time() - progress_ts)
    if not cols or not duration:
        return 0.5
    idx = min(71, max(0, int(pos / duration * 72)))
    window = cols[max(0, idx - 1):idx + 2]
    return sum(window) / len(window)


def upload_live_wave_frame(slot: int) -> str:
    """Render and upload the current animation frame; returns the asset name.

    Height = current loudness x movement, so the whole wave rises in loud
    parts of the song and falls in quiet ones."""
    level = 0.2 + 0.8 * _current_loudness()   # keep a visible floor
    now   = time.time()
    with _lock:
        phases = list(wave_phases) or [0.0] * WAVE_BARS

    if WAVE_STYLE == "wave":
        data = _render_wave_frame(level, now, phases[0])
    else:
        heights = []
        for b in range(WAVE_BARS):
            bob = 0.6 + 0.4 * math.sin(2 * math.pi * WAVE_BOB_HZ * now + phases[b])
            heights.append(max(1, round(level * bob * WAVE_BAR_MAX_H)))
        data = _render_bar_frame(heights)

    name = R_WAVE_FMT.format(slot)
    _upload_bytes(data, name)
    return name


# ---------------------------------------------------------------------------
# Display — element builders
# ---------------------------------------------------------------------------

def _post_elements(elements: list):
    try:
        r = _dev.post(DEVICE_URL,
                      json={"application_name": APP_ID, "elements": elements},
                      timeout=2)
        if r.status_code >= 400:
            print("Display error:", r.status_code, r.text)
    except Exception as e:
        print("Display error:", e)


def _img(id_, path, x, y, timeout=0):
    return {"id": id_, "type": "image", "path": path, "x": x, "y": y,
            "align": "top_left", "display": "front", "timeout": timeout}


def _txt(id_, text, x, y, color, width=40, scroll_rate=0, timeout=0):
    return {"id": id_, "type": "text", "text": text, "x": x, "y": y,
            "align": "top_left", "font": "small", "color": color,
            "width": width, "scroll_rate": scroll_rate, "display": "front", "timeout": timeout}


def _sanitize(text: str) -> str:
    if not text:
        return "---"
    text = re.sub(r'[^ -~]', '', unidecode(text))
    return text or "---"


def build_title_base() -> list:
    """The static part of the title page: background, wave, logo (no text labels).
    The wave element respects the current style so it matches after a redraw."""
    wave_name = R_WAVE_BLANK if WAVE_STYLE == "off" else R_WAVE_FMT.format(0)
    return [
        _img("bg",   R_BACKGROUND, 0,      0),
        _img("wave", wave_name,    0,      0),   # animated equalizer (or blank when off)
        _img("logo", R_LOGO,       LOGO_X, LOGO_Y),
    ]


def build_label_elements(artist: str, song: str) -> list:
    """Just the two text labels (artist + song)."""
    artist = _sanitize(artist)
    song   = _sanitize(song)
    text_w = 72 - TEXT_X

    SCROLL_THRESHOLD = 12
    RATE             = 50
    scroll_a = RATE if len(artist) > SCROLL_THRESHOLD else 0
    scroll_s = RATE if len(song)   > SCROLL_THRESHOLD else 0

    return [
        _txt("artist", artist, TEXT_X, TEXT_TOP_Y, "#FFFFFFFF", width=text_w, scroll_rate=scroll_a),
        _txt("song",   song,   TEXT_X, TEXT_BOT_Y, "#AAFF00FF", width=text_w, scroll_rate=scroll_s),
    ]


def build_title_elements(artist: str, song: str) -> list:
    return build_title_base() + build_label_elements(artist, song)


def build_feedback_elements(icon_remote: str, x: int, y: int) -> list:
    return [
        _img("album_bg", R_ALBUM_BG, ALBUM_BG_X, ALBUM_BG_Y),
        _img("fb_icon",  icon_remote, x, y),
    ]


def build_skip_elements(direction: str, green_idx=None) -> list:
    """Row of three arrows over the album art. green_idx (0-2) lights one green."""
    white = R_ARROW_R_WHT if direction == "next" else R_ARROW_L_WHT
    green = R_ARROW_R_GRN if direction == "next" else R_ARROW_L_GRN
    els = [_img("album_bg", R_ALBUM_BG, ALBUM_BG_X, ALBUM_BG_Y)]
    for i, x in enumerate(ARROW_XS):
        els.append(_img(f"arrow{i}", green if i == green_idx else white, x, ARROW_Y))
    return els


def _shift(elements: list, dx: int) -> list:
    """Return a copy of elements with all x positions shifted by dx."""
    out = []
    for e in elements:
        e2 = dict(e)
        e2["x"] = e["x"] + dx
        out.append(e2)
    return out


def transition(old_els: list, new_els: list, direction: int = 1):
    """Instant cut between states with no blank flash.

    One single POST: the old elements are parked off-screen and the new ones
    drawn in place, so the device swaps both in the same frame (no clear, no slide).
    """
    frame = _shift(old_els, -100) + new_els
    _post_elements(frame)


def slide_transition(old_els: list, new_els: list, direction: int = 1):
    """Swipe old elements off one side while new ones slide in from the other.

    direction +1: old exits left, new enters from the right (used for 'next').
    direction -1: old exits right, new enters from the left (used for 'prev').
    """
    for i in range(1, SLIDE_FRAMES + 1):
        dx = round(72 * i / SLIDE_FRAMES)
        frame = _shift(old_els, -dx * direction) + _shift(new_els, (72 - dx) * direction)
        _post_elements(frame)
        time.sleep(SLIDE_INTERVAL)


# Motion-blur label swipe
GHOST_COUNT  = 2          # trailing ghost copies per label
GHOST_GAP    = 4          # px between ghosts
GHOST_ALPHAS = (0x60, 0x30)   # ghost transparencies (nearest, farthest)


def _with_alpha(color_hex: str, alpha: int) -> str:
    """Replace the alpha byte of a #RRGGBBAA colour string."""
    return color_hex[:7] + f"{alpha:02X}"


def _blurred_labels(labels: list, dx: int, motion_sign: int) -> list:
    """Labels offset by dx, plus trailing ghost copies (fake motion blur)."""
    out = []
    for el in labels:
        # Ghosts trail behind the direction of travel, fading with distance.
        for g in range(GHOST_COUNT, 0, -1):
            ge = dict(el)
            ge["id"]    = f"{el['id']}_g{g}"
            ge["x"]     = el["x"] + dx - motion_sign * g * GHOST_GAP
            ge["color"] = _with_alpha(el["color"], GHOST_ALPHAS[g - 1])
            out.append(ge)
        me = dict(el)
        me["x"] = el["x"] + dx
        out.append(me)
    return out


def swipe_labels_out(base: list, labels: list, direction: int):
    """Labels swipe off-screen with motion blur over the static base."""
    motion = -direction   # next(+1) → travel left; prev(-1) → travel right
    for i in range(1, SLIDE_FRAMES + 1):
        dx = motion * round(72 * i / SLIDE_FRAMES)
        _post_elements(base + _blurred_labels(labels, dx, motion))
        time.sleep(SLIDE_INTERVAL)


def swipe_labels_in(base: list, labels: list, direction: int):
    """New labels swipe in from off-screen with motion blur over the static base."""
    motion = -direction
    for i in range(0, SLIDE_FRAMES + 1):
        dx = -motion * round(72 * (SLIDE_FRAMES - i) / SLIDE_FRAMES)
        _post_elements(base + _blurred_labels(labels, dx, motion))
        time.sleep(SLIDE_INTERVAL)


def clear_display():
    try:
        _dev.delete(DEVICE_URL, params={"application_name": APP_ID}, timeout=2)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Spotify controls
# ---------------------------------------------------------------------------

def _pick_device():
    """Return a usable device_id, preferring the active one, else any available."""
    try:
        devices = sp.devices().get("devices", [])
    except Exception:
        return None
    if not devices:
        return None
    for d in devices:
        if d.get("is_active"):
            return d["id"]
    return devices[0]["id"]


def _resume(device_id):
    try:
        sp.start_playback(device_id=device_id)
    except Exception:
        dev = _pick_device()
        if dev:
            sp.transfer_playback(dev, force_play=True)
        else:
            print("Spotify: no available device to resume on — start playback in the app once")


def _current_device():
    pb = sp.current_playback()
    playing   = pb.get("is_playing", False) if pb else False
    device_id = pb.get("device", {}).get("id") if pb else None
    if not device_id:
        device_id = _pick_device()
    return device_id, playing


def _control_with_retry(action):
    """Run action(device_id). Spotify returns 404 "Device not found" when the
    target device has gone stale (paused/handed off). In that case re-resolve to
    an available device, transfer playback to it, and retry once."""
    device_id, _ = _current_device()
    try:
        action(device_id)
    except spotipy.SpotifyException as e:
        if getattr(e, "http_status", None) != 404:
            raise
        dev = _pick_device()
        if not dev:
            print("Spotify: no active device — open Spotify and play a track once")
            return
        try:
            sp.transfer_playback(dev, force_play=True)
            time.sleep(0.3)
        except Exception:
            pass
        action(dev)


def do_next():
    global _force_poll
    if not _control_lock.acquire(blocking=False):
        return
    try:
        _control_with_retry(lambda d: sp.next_track(device_id=d))
        _force_poll = True
    except Exception as e:
        print(f"Spotify control error: {e}")
    finally:
        _control_lock.release()


def do_prev():
    global _force_poll
    if not _control_lock.acquire(blocking=False):
        return
    try:
        _control_with_retry(lambda d: sp.previous_track(device_id=d))
        _force_poll = True
    except Exception as e:
        print(f"Spotify control error: {e}")
    finally:
        _control_lock.release()


# ---------------------------------------------------------------------------
# Volume control (scroll wheel)
# ---------------------------------------------------------------------------

def _seed_volume() -> int:
    """Read the current device volume once so relative steps start correctly."""
    try:
        pb = sp.current_playback()
        dev = (pb or {}).get("device") or {}
        vol = dev.get("volume_percent")
        if vol is not None:
            return int(vol)
    except Exception:
        pass
    return 50


def _render_volbar(percent: int) -> bytes:
    """Render a 72x16 row of vertical bars that step up from short to tall.
    The bars up to the current volume level are lit; the rest are dim.
    Fixed size (72x16) so it's safe to reuse the asset name."""
    img = Image.new("RGB", (72, 16), (0, 0, 0))
    d = ImageDraw.Draw(img)

    pad = 2                      # padding around the edges
    n_bars = 14
    bar_w, gap = 3, 1
    pitch = bar_w + gap
    total = n_bars * pitch - gap
    start_x = (72 - total) // 2

    bottom = 15 - pad            # bars sit this far above the bottom edge
    min_h, max_h = 2, 16 - 2 * pad
    pct = max(0, min(100, percent))
    lit = round(pct / 100 * n_bars)

    lit_col = (30, 215, 96)      # Spotify green
    dim_col = (40, 60, 48)       # dim green-grey

    for i in range(n_bars):
        h = round(min_h + (max_h - min_h) * i / (n_bars - 1))
        x0 = start_x + i * pitch
        y0 = bottom - h + 1
        d.rectangle((x0, y0, x0 + bar_w - 1, bottom),
                    fill=lit_col if i < lit else dim_col)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _show_volume(percent: int):
    """Overlay the volume bar for ~2s using the firmware element timeout."""
    global _overlay_until
    try:
        _upload_bytes(_render_volbar(percent), R_VOLBAR)
        _overlay_until = time.time() + 2.0
        _post_elements([_img("volbar", R_VOLBAR, 0, 0, timeout=2)])
    except Exception as e:
        print(f"Volume overlay error: {e}")


def _vol_worker():
    global _vol_active, _vol_target
    while True:
        with _vol_lock:
            target = _vol_target
        try:
            sp.volume(target, device_id=_pick_device())
            _show_volume(target)
        except Exception as e:
            print(f"Spotify volume error: {e}")
        with _vol_lock:
            if _vol_target == target:      # no newer change queued
                _vol_active = False
                return
            # else a newer target arrived while applying — loop and apply it


def _bump_volume(direction: int):
    """Adjust volume by ``direction`` * VOLUME_STEP, coalescing rapid scrolls."""
    global _vol_target, _vol_active
    seed = None
    with _vol_lock:
        if _vol_target is None:
            seed = True
    if seed:
        base = _seed_volume()
        with _vol_lock:
            if _vol_target is None:
                _vol_target = base
    start_worker = False
    with _vol_lock:
        _vol_target = max(0, min(100, _vol_target + direction * VOLUME_STEP))
        if not _vol_active:
            _vol_active = True
            start_worker = True
    if start_worker:
        threading.Thread(target=_vol_worker, daemon=True).start()


# ---------------------------------------------------------------------------
# Shared input actions (used by both WebSocket and telnet transports)
# ---------------------------------------------------------------------------

def _handle_scroll(delta: int):
    """Encoder movement -> volume (with a small sensitivity threshold)."""
    global _scroll_accum
    move = 0
    with _lock:
        _scroll_accum += delta
        if _scroll_accum >= SCROLL_STEPS:
            move = 1
            _scroll_accum = 0
        elif _scroll_accum <= -SCROLL_STEPS:
            move = -1
            _scroll_accum = 0
    if move:
        _bump_volume(-move)   # scroll direction inverted to match the wheel


def _handle_start():
    """Start button -> instant play/pause."""
    global is_playing
    with _lock:
        is_playing = not is_playing
    threading.Thread(target=do_toggle, daemon=True).start()
    _refresh_event.set()


def _ok_fire():
    """Run the action for the accumulated OK click count, then reset."""
    global _ok_clicks, is_playing, feedback
    with _ok_lock:
        n = _ok_clicks
        _ok_clicks = 0
    if n <= 0:
        return
    if n == 1:                       # play / pause
        with _lock:
            is_playing = not is_playing
        threading.Thread(target=do_toggle, daemon=True).start()
    elif n == 2:                     # next
        with _lock:
            feedback = "next"
        threading.Thread(target=do_next, daemon=True).start()
    else:                            # 3+ -> previous
        with _lock:
            feedback = "prev"
        threading.Thread(target=do_prev, daemon=True).start()
    _refresh_event.set()


def _ok_press():
    """Register one OK press and (re)start the multi-click timer."""
    global _ok_clicks, _ok_timer
    with _ok_lock:
        _ok_clicks += 1
        if _ok_timer is not None:
            _ok_timer.cancel()
        _ok_timer = threading.Timer(OK_MULTICLICK_WINDOW, _ok_fire)
        _ok_timer.daemon = True
        _ok_timer.start()


def do_toggle():
    global is_playing, _force_poll
    if not _control_lock.acquire(blocking=False):
        return
    try:
        device_id, playing = _current_device()
        if playing:
            sp.pause_playback(device_id=device_id)
            with _lock:
                is_playing = False
        else:
            _resume(device_id)
            with _lock:
                is_playing = True
        _force_poll = True
        _refresh_event.set()
    except Exception as e:
        print(f"Spotify control error: {e}")
    finally:
        _control_lock.release()


# ---------------------------------------------------------------------------
# WebSocket input listener (preferred — firmware /api/status/ws)
# ---------------------------------------------------------------------------

def _on_ws_input(ev):
    """Dispatch a decoded WebSocket input event.

    Scroll wheel -> volume; OK x1 = play/pause, x2 = next, x3 = previous;
    Start = instant play/pause. Mirrors the telnet handler below.
    """
    kind = ev[0]
    if kind == "encoder":
        _handle_scroll(ev[1])              # firmware: up=+1 (louder), down=-1
    elif kind == "button" and ev[2] == ACT_PRESS:
        if ev[1] == BTN_OK:
            _ok_press()
        elif ev[1] == BTN_START:
            _handle_start()


def input_listener():
    """Prefer the WebSocket input stream; fall back to the telnet CLI if the
    WebSocket endpoint is unavailable (older firmware) or the lib is missing."""
    result = stream_input_events(WS_URL, _on_ws_input,
                                 headers=_AUTH_HEADERS or None,
                                 abort_on_forbidden=USE_CLOUD)
    if USE_CLOUD:
        return
    if result == "fallback":
        print("[input] Falling back to telnet CLI listener")
        telnet_input_listener()
    elif result is False and DEVICE_IP:
        telnet_input_listener()


# ---------------------------------------------------------------------------
# Telnet input listener (fallback for older firmware)
# ---------------------------------------------------------------------------

def _handle_event(line: str):
    if "key:" not in line or "type:" not in line:
        return
    parts = line.split()
    try:
        key   = parts[parts.index("key:")  + 1]
        etype = parts[parts.index("type:") + 1]
    except (ValueError, IndexError):
        return

    if etype != "InputTypeShort":
        return

    # Same scheme as the WebSocket transport: scroll = volume, OK = multi-click,
    # Start = play/pause.
    if key == SCROLL_UP_KEY:
        _handle_scroll(+1)
    elif key == SCROLL_DOWN_KEY:
        _handle_scroll(-1)
    elif key == OK_KEY:
        _ok_press()
    elif key == START_KEY:
        _handle_start()


def telnet_input_listener():
    host_idx = 0
    failures = 0
    while True:
        host = TELNET_HOSTS[host_idx % len(TELNET_HOSTS)]
        proc = None
        try:
            proc = subprocess.Popen(
                ["telnet", host, "23"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=1,
                text=True,
            )
            time.sleep(1.0)
            if proc.poll() is not None:
                raise ConnectionError(f"CLI not available on {host}")

            try:
                proc.stdin.write("\r\n");           proc.stdin.flush()
                time.sleep(0.15)
                proc.stdin.write("input dump\r\n"); proc.stdin.flush()
            except (BrokenPipeError, OSError):
                raise ConnectionError(f"CLI rejected on {host} (closed by device)")

            print(f"[input] Listening for inputs via {host}")
            failures = 0
            for raw in proc.stdout:
                _handle_event(raw.strip())
            # stdout EOF — connection closed by the device
            raise ConnectionError(f"connection to {host} closed")

        except Exception as e:
            failures += 1
            # Print the first few failures, then go quiet to avoid spam
            if failures <= len(TELNET_HOSTS) or failures % 10 == 0:
                print(f"[input] {e} — trying next host in 3s"
                      + ("  (buttons disabled until a CLI host responds;"
                         " connect USB-C for inputs)" if failures == len(TELNET_HOSTS) else ""))
            host_idx += 1   # rotate to the next candidate host
        finally:
            if proc is not None:
                for stream in (proc.stdin, proc.stdout):
                    try:
                        stream.close()
                    except Exception:
                        pass
                try:
                    proc.kill()
                    proc.wait(timeout=2)
                except Exception:
                    pass

        time.sleep(3)


# ---------------------------------------------------------------------------
# Spotify polling
# ---------------------------------------------------------------------------

def get_current_track():
    """Return (artist, song, track_id, image_url, playing, progress_ms, duration_ms).
    Works while paused too."""
    try:
        current = sp.currently_playing()
        if current and current.get("item"):
            item      = current["item"]
            artist    = ", ".join(a["name"] for a in item["artists"])
            song      = item["name"]
            track_id  = item["id"]
            images    = item["album"]["images"]
            image_url = sorted(images, key=lambda x: x["width"])[0]["url"] if images else None
            return (artist, song, track_id, image_url,
                    current.get("is_playing", False),
                    current.get("progress_ms", 0) or 0,
                    item.get("duration_ms", 0) or 0)
    except Exception as e:
        print(f"Spotify error: {e}")
    return None, None, None, None, False, 0, 0


def poll_spotify() -> bool:
    """Poll the API, update shared state, fetch album art on track change.
    Returns True if the track changed."""
    global is_playing, current_track_id, last_artist, last_song
    global progress_s, progress_ts

    artist, song, track_id, image_url, playing, prog_ms, dur_ms = get_current_track()
    if artist and song:
        last_artist, last_song = artist, song

    with _lock:
        is_playing  = playing
        progress_s  = prog_ms / 1000.0
        progress_ts = time.time()
        changed = bool(track_id and track_id != current_track_id)
        if changed:
            current_track_id = track_id

    if changed:
        if image_url:
            fetch_and_upload_album_art(image_url)
        if track_id:
            prepare_wave(track_id, dur_ms)
    return changed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"Connecting via: {API_BASE}")
    _verify_connection()
    upload_static_assets()
    clear_display()   # clean slate on startup only

    threading.Thread(target=input_listener, daemon=True).start()

    last_sig    = None
    last_poll   = 0.0
    mode        = None     # 'title' | 'pause' | None
    blink_on    = True
    current_els = []       # what's currently on screen (steady state)
    wave_idx    = 0        # current equalizer animation frame
    wave_style_shown = None  # last style actually drawn (detects switch to 'off')

    try:
        while True:
            now = time.time()

            if now - last_poll >= UPDATE_INTERVAL or _force_poll:
                _force_poll = False
                changed = poll_spotify()
                last_poll = now
                if changed and mode == "title":
                    last_sig = None   # update title text in place (no transition)

            with _lock:
                fb      = feedback
                playing = is_playing

            # ── Transient next/prev feedback: arrow chase animation ─────
            if fb in ("next", "prev"):
                # Start with all three arrows white, then each goes green once.
                # Chase direction follows the skip: next → left-to-right, prev → right-to-left.
                order = (0, 1, 2) if fb == "next" else (2, 1, 0)

                # Jump cut to the arrow panel (parks the title elements off-screen
                # so they actually disappear), then play the chase.
                skip_els = build_skip_elements(fb)
                transition(current_els, skip_els)
                for idx in order:
                    time.sleep(SKIP_FRAME_INTERVAL)
                    skip_els = build_skip_elements(fb, green_idx=idx)
                    _post_elements(skip_els)
                # End on all-white (no green) so it doesn't freeze on a green arrow.
                time.sleep(SKIP_FRAME_INTERVAL)
                skip_els = build_skip_elements(fb)
                _post_elements(skip_els)
                time.sleep(SKIP_FRAME_INTERVAL)

                # Pick up the new track, then jump cut back to the title page
                # (parks the arrow/album elements off-screen so they're removed).
                poll_spotify()
                last_poll = time.time()

                title_els = build_title_elements(last_artist or "---", last_song or "---")
                transition(skip_els, title_els)
                current_els = title_els
                mode = "title"
                last_sig = ("np", last_artist, last_song)
                wave_style_shown = None   # re-establish the wave/bars/off state next tick
                with _lock:
                    feedback = None
                continue

            have_track = bool(last_artist and last_song)

            # ── Paused: blink the pause symbol until resumed ────────────
            if have_track and not playing:
                if mode != "pause":
                    pause_els = build_feedback_elements(R_PAUSE_SEL, PAUSE_X, PAUSE_Y)
                    transition(current_els, pause_els, 1)
                    current_els = pause_els
                    mode = "pause"
                    blink_on = False   # next frame shows the unselected variant
                else:
                    icon = R_PAUSE_SEL if blink_on else R_PAUSE_UNSEL
                    current_els = build_feedback_elements(icon, PAUSE_X, PAUSE_Y)
                    _post_elements(current_els)
                    blink_on = not blink_on
                _refresh_event.wait(timeout=PAUSE_BLINK_INTERVAL)
                _refresh_event.clear()
                continue

            # ── Normal title page ───────────────────────────────────────
            if have_track:
                sig = ("np", last_artist, last_song)
                title_els = build_title_elements(last_artist, last_song)
                if mode != "title":
                    transition(current_els, title_els, -1)
                    current_els = title_els
                    mode = "title"
                    last_sig = sig
                elif sig != last_sig:
                    _post_elements(title_els)   # in-place update, no flash
                    current_els = title_els
                    last_sig = sig

                # While the volume bar overlay is up, pause the wave animation so
                # it doesn't draw over the bar (the overlay self-clears via its
                # element timeout).
                if time.time() < _overlay_until:
                    _refresh_event.wait(timeout=0.2)
                    _refresh_event.clear()
                    continue

                # Animate the equalizer live: render a frame for the current
                # playback loudness, upload it, then update only the wave
                # element by id so the text scroll keeps running undisturbed.
                # Two alternating asset slots avoid swapping a file mid-render.
                if WAVE_STYLE == "off":
                    if wave_style_shown != "off":
                        _post_elements([_img("wave", R_WAVE_BLANK, 0, 0)])
                        wave_style_shown = "off"
                    _refresh_event.wait(timeout=UPDATE_INTERVAL)
                else:
                    wave_style_shown = WAVE_STYLE
                    name = upload_live_wave_frame(wave_idx % 2)
                    _post_elements([_img("wave", name, 0, 0)])
                    wave_idx = (wave_idx + 1) % 2
                    _refresh_event.wait(timeout=WAVE_ANIM_INTERVAL)
                _refresh_event.clear()
                continue
            # else: nothing has played yet this session — leave the display as-is

            _refresh_event.wait(timeout=UPDATE_INTERVAL)
            _refresh_event.clear()

    except KeyboardInterrupt:
        print("\nQuitting, clearing display.")
        clear_display()
