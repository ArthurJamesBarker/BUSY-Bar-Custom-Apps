#!/usr/bin/env python3
"""Network for BUSY Bar release firmware.

Uploads a static UP/DOWN label image, then shows this computer's live
download/upload speeds next to it. Official release firmware only.
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys
import time
from pathlib import Path

import psutil
import requests

APP_NAME = "network"
DEFAULT_HOST = "10.0.4.20"
DEFAULT_REFRESH = 0.25
MEASURE_SECONDS = 0.1
API_VERSION_HEADER = "X-Busy-Api-Version"
DRAW_PRIORITY = 50
APP_DIR = Path(__file__).resolve().parent
LABELS_PNG = APP_DIR / "Speed_down-up.png"
DEVICE_LABEL_NAME = "speed_labels.png"


class BusyBarClient:
    def __init__(self, host: str, password: str | None = None) -> None:
        clean_host = (
            host.strip()
            .replace("http://", "")
            .replace("https://", "")
            .rstrip("/")
        )
        self.host = clean_host
        self.api = f"http://{clean_host}/api"
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

    def upload_asset(self, path: Path, remote_name: str) -> None:
        response = self.session.post(
            f"{self.api}/assets/upload",
            params={
                "application_name": APP_NAME,
                "file": remote_name,
            },
            data=path.read_bytes(),
            headers={"Content-Type": "application/octet-stream"},
            timeout=15,
        )
        response.raise_for_status()

    def draw_labels(self, remote_name: str) -> None:
        response = self.session.post(
            f"{self.api}/display/draw",
            json={
                "application_name": APP_NAME,
                "priority": DRAW_PRIORITY,
                "elements": [
                    {
                        "id": "labels_img",
                        "type": "image",
                        "path": remote_name,
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

    def draw_speeds(self, down_mbps: int, up_mbps: int, display_timeout: int) -> None:
        response = self.session.post(
            f"{self.api}/display/draw",
            json={
                "application_name": APP_NAME,
                "priority": DRAW_PRIORITY,
                "elements": [
                    {
                        "id": "down_speed",
                        "type": "text",
                        "text": f"{down_mbps} Mb/s",
                        "x": 71,
                        "y": -1,
                        "align": "top_right",
                        "font": "small",
                        "color": "#FFFFFFFF",
                        "display": "front",
                        "timeout": display_timeout,
                    },
                    {
                        "id": "up_speed",
                        "type": "text",
                        "text": f"{up_mbps} Mb/s",
                        "x": 71,
                        "y": 7,
                        "align": "top_right",
                        "font": "small",
                        "color": "#FFFFFFFF",
                        "display": "front",
                        "timeout": display_timeout,
                    },
                ],
            },
            timeout=5,
        )
        response.raise_for_status()

    def clear(self) -> None:
        response = self.session.delete(
            f"{self.api}/display/draw",
            params={"application_name": APP_NAME},
            timeout=5,
        )
        response.raise_for_status()


def list_interfaces() -> list[str]:
    try:
        return list(psutil.net_io_counters(pernic=True).keys())
    except Exception:
        return []


def is_usable_interface(name: str) -> bool:
    lowered = name.lower()
    if lowered.startswith("lo"):
        return False
    blocked = ("loopback", "awdl", "llw", "utun", "bridge", "veth", "docker")
    return not any(part in lowered for part in blocked)


def pick_interface(preferred: str | None) -> str:
    counters = psutil.net_io_counters(pernic=True)
    if preferred and preferred != "auto":
        if preferred not in counters:
            available = ", ".join(list_interfaces()) or "(none)"
            raise SystemExit(
                f"Network interface '{preferred}' was not found.\n"
                f"Available interfaces: {available}"
            )
        return preferred

    candidates = [name for name in counters if is_usable_interface(name)]
    if not candidates:
        raise SystemExit("No usable network interface was found.")

    # Prefer the interface that has already moved the most traffic.
    ranked = sorted(
        candidates,
        key=lambda name: counters[name].bytes_recv + counters[name].bytes_sent,
        reverse=True,
    )
    return ranked[0]


def measure_speeds(interface: str, interval: float) -> tuple[int, int]:
    first = psutil.net_io_counters(pernic=True)[interface]
    time.sleep(interval)
    second = psutil.net_io_counters(pernic=True)[interface]

    down_mbps = (second.bytes_recv - first.bytes_recv) * 8 / 1_000_000 / interval
    up_mbps = (second.bytes_sent - first.bytes_sent) * 8 / 1_000_000 / interval
    return max(int(down_mbps), 0), max(int(up_mbps), 0)


def prepare_access(bar: BusyBarClient) -> None:
    if bar.transport_type() != "wifi":
        return

    mode = bar.access_mode()
    if mode == "disabled":
        raise PermissionError(
            "Wi-Fi access to the BUSY Bar HTTP API is disabled. "
            "Enable HTTP API access on the BUSY Bar."
        )
    if mode == "key" and not bar.has_password:
        if not sys.stdin.isatty():
            raise PermissionError(
                "This BUSY Bar requires its Wi-Fi access password. "
                "Set BUSYBAR_PASSWORD or run the app in a terminal."
            )
        password = getpass.getpass("BUSY Bar Wi-Fi access password: ").strip()
        if not password:
            raise PermissionError("The Wi-Fi access password is required.")
        bar.set_password(password)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Show live network speeds on a BUSY Bar with UP/DOWN labels."
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
        "--interface",
        default="auto",
        help="Network interface to monitor (default: auto)",
    )
    parser.add_argument(
        "--refresh-interval",
        type=float,
        default=DEFAULT_REFRESH,
        help=f"Seconds between display updates (default: {DEFAULT_REFRESH})",
    )
    parser.add_argument(
        "--display-timeout",
        type=int,
        default=1,
        help="How long speed text stays on screen before refresh (default: 1)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.refresh_interval <= 0:
        raise SystemExit("--refresh-interval must be greater than 0")
    if not LABELS_PNG.is_file():
        raise SystemExit(f"Label image not found: {LABELS_PNG}")

    interface = pick_interface(args.interface)
    bar = BusyBarClient(args.host, args.password)

    try:
        version = bar.connect()
        prepare_access(bar)
        print("Uploading label artwork…")
        bar.upload_asset(LABELS_PNG, DEVICE_LABEL_NAME)
        bar.draw_labels(DEVICE_LABEL_NAME)
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

    print(f"Connected to BUSY Bar at {bar.host} (API {version})")
    print(f"Monitoring interface '{interface}'.")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            down_mbps, up_mbps = measure_speeds(interface, MEASURE_SECONDS)
            print(
                f"DOWN {down_mbps} Mb/s  |  UP {up_mbps} Mb/s    ",
                end="\r",
                flush=True,
            )
            try:
                bar.draw_speeds(down_mbps, up_mbps, args.display_timeout)
            except requests.HTTPError as error:
                if error.response is not None and error.response.status_code in (
                    401,
                    403,
                ):
                    raise SystemExit(
                        "The BUSY Bar rejected the Wi-Fi access password. "
                        "Check the HTTP API settings and try again."
                    ) from error
                print(f"\nDisplay update failed: {error}")
                break
            except requests.RequestException as error:
                print(f"\nDisplay update failed: {error}")
                break
            time.sleep(args.refresh_interval)
    except KeyboardInterrupt:
        print("\nStopping Network…")
    finally:
        try:
            bar.clear()
        except requests.RequestException:
            pass
        print("Cleared display.")


if __name__ == "__main__":
    main()
