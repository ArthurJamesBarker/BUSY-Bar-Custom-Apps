#!/usr/bin/env python3
"""Social Battery for BUSY Bar release firmware."""

from __future__ import annotations

import argparse
import getpass
import os
import sys
import threading
from collections import deque
from pathlib import Path

import requests

from busybar_api import BusyBarClient
from busybar_ws_input import (
    ACT_RELEASE,
    BTN_BACK,
    BTN_OK,
    BTN_START,
    SW_APPS,
    stream_input_events,
)

APP_ID = "social_battery"
DEFAULT_HOST = "10.0.4.20"
APP_DIR = Path(__file__).resolve().parent

STATES = [
    ("critical.png", "critical.png"),
    ("very low.png", "very_low.png"),
    ("low.png", "low.png"),
    ("medium.png", "medium.png"),
    ("good.png", "good.png"),
    ("high.png", "high.png"),
    ("full.png", "full.png"),
]


class SocialBattery:
    def __init__(self, host: str, token: str | None, skip_upload: bool = False) -> None:
        self.bar = BusyBarClient(host, APP_ID, token)
        self.skip_upload = skip_upload
        self.state_index = 3
        self.pending_steps: deque[int] = deque()
        self.stop_event = threading.Event()
        self.condition = threading.Condition()

    def _asset_paths(self) -> list[Path]:
        return [APP_DIR / local_name for local_name, _ in STATES]

    def _check_assets(self) -> None:
        missing = [path.name for path in self._asset_paths() if not path.is_file()]
        if missing:
            raise FileNotFoundError(
                "Missing artwork: " + ", ".join(missing)
            )

    def _prepare_access(self) -> None:
        mode = self.bar.access_mode()
        if mode == "disabled":
            raise PermissionError(
                "The BUSY Bar HTTP API is disabled. Enable it under "
                "Settings → Developer → HTTP API."
            )
        if mode == "key" and not self.bar.has_token:
            if not sys.stdin.isatty():
                raise PermissionError(
                    "This BUSY Bar requires an API key. Set BUSYBAR_TOKEN "
                    "or run the app in a terminal."
                )
            token = getpass.getpass("BUSY Bar API key: ").strip()
            if not token:
                raise PermissionError("An API key is required.")
            self.bar.set_token(token)

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
        "--token",
        default=(
            os.environ.get("BUSYBAR_TOKEN")
            or os.environ.get("BUSYBAR_API_KEY")
        ),
        help="Optional API key; interactive runs prompt when needed",
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
        SocialBattery(args.host, args.token, args.skip_upload).run()
    except FileNotFoundError as error:
        raise SystemExit(f"Cannot start Social Battery: {error}") from error
    except PermissionError as error:
        raise SystemExit(str(error)) from error
    except requests.HTTPError as error:
        if error.response is not None and error.response.status_code in (401, 403):
            raise SystemExit(
                "The BUSY Bar rejected the API key. Check "
                "Settings → Developer → HTTP API and try again."
            ) from error
        raise SystemExit(f"BUSY Bar request failed: {error}") from error
    except requests.RequestException as error:
        raise SystemExit(
            f"Could not connect to the BUSY Bar at {args.host}: {error}"
        ) from error


if __name__ == "__main__":
    main()
