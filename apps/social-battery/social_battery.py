#!/usr/bin/env python3
"""Social Battery for BUSY Bar release firmware."""

from __future__ import annotations

import argparse
import getpass
import os
import sys
import threading
import time
from collections import deque
from collections.abc import Callable, Iterator
from pathlib import Path

import requests
from websocket import WebSocketTimeoutException, create_connection

APP_ID = "social_battery"
DEFAULT_HOST = "10.0.4.20"
APP_DIR = Path(__file__).resolve().parent
ASSET_DIR = APP_DIR / "assets"
API_VERSION_HEADER = "X-Busy-Api-Version"
DRAW_PRIORITY = 100

BTN_OK, BTN_BACK, BTN_START = 0, 1, 2
ACT_RELEASE = 1
SW_APPS = 3

STATES = [
    ("critical.png", "critical.png"),
    ("very low.png", "very_low.png"),
    ("low.png", "low.png"),
    ("medium.png", "medium.png"),
    ("good.png", "good.png"),
    ("high.png", "high.png"),
    ("full.png", "full.png"),
]


class BusyBarClient:
    def __init__(
        self,
        host: str,
        app_id: str,
        password: str | None = None,
    ) -> None:
        clean_host = (
            host.strip()
            .replace("http://", "")
            .replace("https://", "")
            .rstrip("/")
        )
        self.host = clean_host
        self.api = f"http://{clean_host}/api"
        self.app_id = app_id
        self.session = requests.Session()
        if password:
            self.set_password(password)

    def set_password(self, password: str) -> None:
        self.session.headers["X-API-Token"] = password

    @property
    def has_password(self) -> bool:
        return bool(self.session.headers.get("X-API-Token"))

    def connect(self) -> str:
        response = self.session.get(f"{self.api}/version", timeout=5)
        response.raise_for_status()
        version = str(response.json().get("api_semver") or "0.1.0")
        self.session.headers[API_VERSION_HEADER] = version
        return version

    def access_mode(self) -> str:
        response = self.session.get(f"{self.api}/access", timeout=5)
        response.raise_for_status()
        return str(response.json().get("mode") or "").lower()

    def transport_type(self) -> str:
        response = self.session.get(f"{self.api}/transport", timeout=5)
        response.raise_for_status()
        return str(response.json().get("type") or "").lower()

    @property
    def ws_url(self) -> str:
        url = f"ws://{self.host}/api/status/ws"
        password = self.session.headers.get("X-API-Token")
        if password:
            url += f"?x-api-token={password}"
        return url

    def upload_asset(self, path: Path, remote_name: str | None = None) -> None:
        response = self.session.post(
            f"{self.api}/assets/upload",
            params={
                "application_name": self.app_id,
                "file": remote_name or path.name,
            },
            data=path.read_bytes(),
            headers={"Content-Type": "application/octet-stream"},
            timeout=15,
        )
        response.raise_for_status()

    def draw_image(self, filename: str) -> None:
        response = self.session.post(
            f"{self.api}/display/draw",
            json={
                "application_name": self.app_id,
                "priority": DRAW_PRIORITY,
                "elements": [
                    {
                        "id": "social_battery_state",
                        "type": "image",
                        "path": filename,
                        "x": 0,
                        "y": 0,
                        "display": "front",
                        "opacity": 100,
                        "timeout": 0,
                    }
                ],
            },
            timeout=5,
        )
        response.raise_for_status()

    def clear(self) -> None:
        response = self.session.delete(
            f"{self.api}/display/draw",
            params={"application_name": self.app_id},
            timeout=5,
        )
        response.raise_for_status()


def _read_varint(data: bytes, offset: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while offset < len(data):
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, offset
        shift += 7
        if shift > 70:
            break
    raise ValueError("Invalid protobuf varint")


def _fields(data: bytes) -> Iterator[tuple[int, int, int | bytes]]:
    offset = 0
    while offset < len(data):
        key, offset = _read_varint(data, offset)
        number, wire_type = key >> 3, key & 7
        if wire_type == 0:
            value, offset = _read_varint(data, offset)
        elif wire_type == 1:
            value = data[offset : offset + 8]
            offset += 8
        elif wire_type == 2:
            length, offset = _read_varint(data, offset)
            value = data[offset : offset + length]
            offset += length
        elif wire_type == 5:
            value = data[offset : offset + 4]
            offset += 4
        else:
            raise ValueError(f"Unsupported protobuf wire type: {wire_type}")
        yield number, wire_type, value


def _zigzag(value: int) -> int:
    return (value >> 1) ^ -(value & 1)


def _input_event(data: bytes) -> tuple | None:
    for number, wire_type, value in _fields(data):
        if wire_type != 2 or not isinstance(value, bytes):
            continue
        if number == 1:
            button = action = 0
            for field, _, item in _fields(value):
                if field == 1 and isinstance(item, int):
                    button = item
                elif field == 2 and isinstance(item, int):
                    action = item
            return "button", button, action
        if number == 2:
            position = 0
            for field, _, item in _fields(value):
                if field == 1 and isinstance(item, int):
                    position = item
            return "switch", position
        if number == 3:
            delta = 0
            for field, _, item in _fields(value):
                if field == 1 and isinstance(item, int):
                    delta = _zigzag(item)
            return "encoder", delta
    return None


def events_from_state(data: bytes) -> Iterator[tuple]:
    """Yield input tuples from one protobuf BSB_State.State frame."""
    for number, wire_type, update in _fields(data):
        if number != 2 or wire_type != 2 or not isinstance(update, bytes):
            continue
        for field, update_wire_type, value in _fields(update):
            if field == 11 and update_wire_type == 2 and isinstance(value, bytes):
                event = _input_event(value)
                if event:
                    yield event


def stream_input_events(
    ws_url: str,
    on_event: Callable[[tuple], None],
    should_stop: Callable[[], bool],
    on_status: Callable[[str], None] = print,
) -> None:
    """Reconnect as needed and forward physical input until asked to stop."""
    while not should_stop():
        socket = None
        try:
            socket = create_connection(ws_url, timeout=5, enable_multithread=True)
            socket.settimeout(1)
            socket.send('{"enable":true}')
            on_status(f"Listening for controls at {ws_url.split('?')[0]}")
            while not should_stop():
                try:
                    opcode, data = socket.recv_data(control_frame=False)
                except WebSocketTimeoutException:
                    continue
                if opcode != 2 or not data:
                    continue
                for event in events_from_state(data):
                    on_event(event)
        except Exception as error:
            if should_stop():
                return
            message = str(error).split(" -+-+- ", 1)[0]
            on_status(f"Control connection lost: {message}; retrying in 2s")
            time.sleep(2)
        finally:
            if socket is not None:
                try:
                    socket.close()
                except Exception:
                    pass


class SocialBattery:
    def __init__(
        self,
        host: str,
        password: str | None,
        skip_upload: bool = False,
    ) -> None:
        self.bar = BusyBarClient(host, APP_ID, password)
        self.skip_upload = skip_upload
        self.state_index = 3
        self.pending_steps: deque[int] = deque()
        self.stop_event = threading.Event()
        self.condition = threading.Condition()

    def _asset_paths(self) -> list[Path]:
        return [ASSET_DIR / local_name for local_name, _ in STATES]

    def _check_assets(self) -> None:
        missing = [path.name for path in self._asset_paths() if not path.is_file()]
        if missing:
            raise FileNotFoundError(
                "Missing artwork: " + ", ".join(missing)
            )

    def _prepare_access(self) -> None:
        if self.bar.transport_type() != "wifi":
            return

        mode = self.bar.access_mode()
        if mode == "disabled":
            raise PermissionError(
                "Wi-Fi access to the BUSY Bar HTTP API is disabled. "
                "Enable HTTP API access on the BUSY Bar."
            )
        if mode == "key" and not self.bar.has_password:
            if not sys.stdin.isatty():
                raise PermissionError(
                    "This BUSY Bar requires its Wi-Fi access password. "
                    "Set BUSYBAR_PASSWORD "
                    "or run the app in a terminal."
                )
            password = getpass.getpass("BUSY Bar Wi-Fi access password: ").strip()
            if not password:
                raise PermissionError("The Wi-Fi access password is required.")
            self.bar.set_password(password)

    def _upload_assets(self) -> None:
        if self.skip_upload:
            return
        print("Preparing Social Battery artwork…")
        for path, (_, remote_name) in zip(
            self._asset_paths(),
            STATES,
            strict=True,
        ):
            self.bar.upload_asset(path, remote_name)

    def _draw(self, index: int) -> None:
        self.bar.draw_image(STATES[index][1])

    def _queue_step(self, direction: int) -> None:
        with self.condition:
            self.pending_steps.append(-1 if direction < 0 else 1)
            self.condition.notify()

    def on_input(self, event: tuple) -> None:
        kind = event[0]
        if kind == "encoder":
            delta = int(event[1])
            if delta:
                self._queue_step(-delta)
            return

        if kind == "switch":
            if int(event[1]) != SW_APPS:
                print("BUSY Bar left Apps mode. Closing Social Battery.")
                self.stop_event.set()
                with self.condition:
                    self.condition.notify_all()
            return

        if kind != "button":
            return

        button, action = int(event[1]), int(event[2])
        if action != ACT_RELEASE:
            return
        if button == BTN_BACK:
            print("Back pressed. Closing Social Battery.")
            self.stop_event.set()
            with self.condition:
                self.condition.notify_all()
        elif button in (BTN_OK, BTN_START):
            self._queue_step(1)

    def _display_loop(self) -> None:
        while not self.stop_event.is_set():
            with self.condition:
                while not self.pending_steps and not self.stop_event.is_set():
                    self.condition.wait(timeout=0.5)
                if self.stop_event.is_set():
                    return

                direction = self.pending_steps.popleft()
                target = max(
                    0,
                    min(len(STATES) - 1, self.state_index + direction),
                )
                if target == self.state_index:
                    continue

            try:
                self.state_index = target
                self._draw(target)
            except requests.RequestException as error:
                print(f"Display update failed: {error}")
                self.stop_event.set()

    def run(self) -> None:
        self._check_assets()
        version = self.bar.connect()
        self._prepare_access()
        self._upload_assets()
        self._draw(self.state_index)

        print(f"Connected to BUSY Bar at {self.bar.host} (API {version})")
        print("Turn the dial to change level. Press Back to close.")

        worker = threading.Thread(
            target=self._display_loop,
            name="social-battery-display",
            daemon=True,
        )
        worker.start()

        try:
            stream_input_events(
                self.bar.ws_url,
                self.on_input,
                self.stop_event.is_set,
            )
        except KeyboardInterrupt:
            print("\nClosing Social Battery…")
        finally:
            self.stop_event.set()
            with self.condition:
                self.condition.notify_all()
            worker.join(timeout=2)
            try:
                self.bar.clear()
            except requests.RequestException:
                pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Social Battery on a release-firmware BUSY Bar."
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("BUSYBAR_IP", DEFAULT_HOST),
        help=f"BUSY Bar IP address (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--password",
        default=(
            os.environ.get("BUSYBAR_PASSWORD")
            or os.environ.get("BUSYBAR_TOKEN")
            or os.environ.get("BUSYBAR_API_KEY")
        ),
        help="Optional Wi-Fi access password; interactive runs prompt when needed",
    )
    parser.add_argument(
        "--token",
        dest="password",
        default=argparse.SUPPRESS,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--skip-upload",
        action="store_true",
        help="Use artwork already uploaded to the BUSY Bar",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        SocialBattery(args.host, args.password, args.skip_upload).run()
    except FileNotFoundError as error:
        raise SystemExit(f"Cannot start Social Battery: {error}") from error
    except PermissionError as error:
        raise SystemExit(str(error)) from error
    except requests.HTTPError as error:
        if error.response is not None and error.response.status_code in (401, 403):
            raise SystemExit(
                "The BUSY Bar rejected the Wi-Fi access password. "
                "Check the HTTP API settings and try again."
            ) from error
        raise SystemExit(f"BUSY Bar request failed: {error}") from error
    except requests.RequestException as error:
        raise SystemExit(
            f"Could not connect to the BUSY Bar at {args.host}: {error}"
        ) from error


if __name__ == "__main__":
    main()
