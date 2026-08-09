"""
Read BUSY Bar physical inputs (scroll encoder + buttons) over the firmware's
``/api/status/ws`` WebSocket.

Firmware publishes input events as protobuf state frames on the status stream.
This module hand-decodes the few fields we need instead of generating protobuf
classes, so the only extra dependency is ``websocket-client``.
"""

import time

try:
    from websocket import create_connection
except Exception:                       # websocket-client not installed
    create_connection = None

try:
    import certifi
except Exception:
    certifi = None


def _ws_sslopt(url: str):
    """SSL options for wss:// — macOS Python often lacks system certs without certifi."""
    if not url.startswith("wss://"):
        return None
    if certifi is not None:
        return {"ca_certs": certifi.where()}
    return {}

# Button enum (input.proto -> enum Button)
BTN_OK, BTN_BACK, BTN_START = 0, 1, 2
# ButtonAction enum
ACT_PRESS, ACT_RELEASE = 0, 1
# SwitchPosition enum
SW_BUSY, SW_CUSTOM, SW_OFF, SW_APPS, SW_SETTINGS = 0, 1, 2, 3, 4

WS_PATH = "/api/status/ws"
ENABLE_FRAME = '{"enable":true}'


# ---------------------------------------------------------------------------
# Minimal protobuf reader
# ---------------------------------------------------------------------------

def _read_varint(buf, i):
    shift = result = 0
    n = len(buf)
    while i < n:
        b = buf[i]; i += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result, i
        shift += 7
    return result, i


def _iter_fields(buf):
    """Yield (field_number, wire_type, value) for one protobuf message.

    value is an int for varints, or a bytes slice for length-delimited fields.
    Fixed 32/64-bit fields are returned as raw bytes; unknown wire types stop
    parsing (the rest of the message is skipped safely)."""
    i, n = 0, len(buf)
    while i < n:
        key, i = _read_varint(buf, i)
        field, wt = key >> 3, key & 7
        if wt == 0:                      # varint
            val, i = _read_varint(buf, i)
            yield field, wt, val
        elif wt == 2:                    # length-delimited
            ln, i = _read_varint(buf, i)
            yield field, wt, buf[i:i + ln]; i += ln
        elif wt == 1:                    # 64-bit
            yield field, wt, buf[i:i + 8]; i += 8
        elif wt == 5:                    # 32-bit
            yield field, wt, buf[i:i + 4]; i += 4
        else:                            # groups / unknown — bail out
            return


def _zigzag(n):
    """Decode a protobuf sint32/sint64 zig-zag varint."""
    return (n >> 1) ^ -(n & 1)


def _parse_input_event(buf):
    """Decode a BSB_Input.InputEvent message into an event tuple, or None."""
    for f, wt, v in _iter_fields(buf):
        if wt != 2:
            continue
        if f == 1:                       # button_event
            button = action = 0
            for bf, _bwt, bv in _iter_fields(v):
                if bf == 1:
                    button = bv
                elif bf == 2:
                    action = bv
            return ("button", button, action)
        if f == 2:                       # switch_event
            pos = 0
            for pf, _pwt, pv in _iter_fields(v):
                if pf == 1:
                    pos = pv
            return ("switch", pos)
        if f == 3:                       # encoder_event
            delta = 0
            for ef, _ewt, ev in _iter_fields(v):
                if ef == 1:
                    delta = _zigzag(ev)
            return ("encoder", delta)
    return None


def _events_from_state(data):
    """Yield input event tuples found in one binary State frame."""
    for f, wt, v in _iter_fields(data):          # State
        if f == 2 and wt == 2:                   # StateUpdate
            for sf, swt, sv in _iter_fields(v):
                if sf == 11 and swt == 2:        # input -> InputEvent
                    ev = _parse_input_event(sv)
                    if ev:
                        yield ev


# ---------------------------------------------------------------------------
# Public listener
# ---------------------------------------------------------------------------

def _short_ws_error(err):
    """Trim noisy websocket-client handshake dumps for console output."""
    text = str(err).split(" -+-+- ", 1)[0].strip()
    if len(text) > 120:
        text = text[:117] + "..."
    return text


def stream_input_events(ws_url, on_event, on_status=print,
                        max_initial_failures=4, headers=None,
                        abort_on_forbidden=False):
    """Blocking loop: connect to the status WebSocket and call ``on_event`` for
    every decoded input event. Reconnects forever once it has connected at least
    once.

    ``ws_url`` is the full WebSocket URL (e.g. ``ws://<ip>/api/status/ws`` for
    local, or ``wss://<host>/busybar/status/ws`` for cloud). ``headers`` is an
    optional dict of extra headers (e.g. ``{"Authorization": "Bearer ..."}``).

    Returns:
        "fallback"  if the WebSocket never connected after ``max_initial_failures``
                    attempts (caller should fall back to the telnet CLI).
        "forbidden" if ``abort_on_forbidden`` and the server rejects the handshake
                    with HTTP 403 (cloud status/ws is not available yet).
        False       if ``websocket-client`` isn't installed.
    """
    if create_connection is None:
        on_status("[input] websocket-client not installed — run: pip3 install websocket-client")
        return False

    hdr = [f"{k}: {v}" for k, v in (headers or {}).items()]
    connected_once = False
    failures = 0
    url = ws_url
    while True:
        ws = None
        try:
            ws = create_connection(url, timeout=5, enable_multithread=True,
                                   header=hdr or None,
                                   sslopt=_ws_sslopt(url))
            ws.send(ENABLE_FRAME)
            connected_once = True
            failures = 0
            on_status(f"[input] Listening via websocket: {url.split('?')[0]}")
            while True:
                opcode, data = ws.recv_data(control_frame=False)
                if opcode != 2 or not data:      # not a binary frame
                    continue
                for ev in _events_from_state(data):
                    on_event(ev)
        except Exception as e:
            failures += 1
            short = _short_ws_error(e)
            if abort_on_forbidden and not connected_once and "403" in short:
                on_status("[input] Cloud WebSocket denied (403) — "
                          "physical controls need same-WiFi mode")
                return "forbidden"
            if not connected_once and failures >= max_initial_failures:
                on_status(f"[input] websocket unavailable ({short})")
                return "fallback"
            on_status(f"[input] websocket error: {short} — reconnecting in 3s")
            time.sleep(3)
        finally:
            if ws is not None:
                try:
                    ws.close()
                except Exception:
                    pass
