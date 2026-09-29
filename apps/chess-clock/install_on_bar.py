#!/usr/bin/env python3
"""Upload the on-device Chess Clock JS app to a BUSY Bar."""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from pathlib import Path

import requests

APP_ID = "community.chess_clock"
DEFAULT_HOST = "10.0.4.20"
APP_DIR = Path(__file__).resolve().parent
PACKAGE_DIR = APP_DIR / "on-device" / APP_ID
JS_APPS_FLAG = "/ext/apps_data/apps_menu/js_apps_enabled"
JS_APPS_DIR = "/ext/apps_data/apps_menu"


def bar_session(host: str, password: str | None) -> tuple[requests.Session, str]:
    clean = host.strip().replace("http://", "").replace("https://", "").rstrip("/")
    session = requests.Session()
    if password:
        session.headers["X-API-Token"] = password
    api = f"http://{clean}/api"
    return session, api


def prepare_access(session: requests.Session, api: str) -> None:
    transport = session.get(f"{api}/transport", timeout=5)
    transport.raise_for_status()
    if str(transport.json().get("type") or "").lower() != "wifi":
        return
    access = session.get(f"{api}/access", timeout=5)
    access.raise_for_status()
    mode = str(access.json().get("mode") or "").lower()
    if mode == "disabled":
        raise PermissionError(
            "Wi-Fi access to the BUSY Bar HTTP API is disabled. "
            "Enable HTTP API access on the BUSY Bar."
        )
    if mode == "key" and not session.headers.get("X-API-Token"):
        if not sys.stdin.isatty():
            raise PermissionError(
                "This BUSY Bar requires its Wi-Fi access password. "
                "Set BUSYBAR_PASSWORD or run the installer in a terminal."
            )
        password = getpass.getpass("BUSY Bar Wi-Fi access password: ").strip()
        if not password:
            raise PermissionError("The Wi-Fi access password is required.")
        session.headers["X-API-Token"] = password


def package_files() -> list[tuple[Path, str]]:
    if not PACKAGE_DIR.is_dir():
        raise FileNotFoundError(f"Missing on-device package: {PACKAGE_DIR}")
    files: list[tuple[Path, str]] = []
    for path in sorted(PACKAGE_DIR.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        remote = path.relative_to(PACKAGE_DIR).as_posix()
        files.append((path, remote))
    if not any(remote == "appmeta/manifest.json" for _, remote in files):
        raise FileNotFoundError("Package is missing appmeta/manifest.json")
    if not any(remote == "scripts/main.js" for _, remote in files):
        raise FileNotFoundError("Package is missing scripts/main.js")
    return files


def upload_file(session: requests.Session, api: str, path: Path, remote: str) -> None:
    response = session.post(
        f"{api}/assets/upload",
        params={"application_name": APP_ID, "file": remote},
        data=path.read_bytes(),
        headers={"Content-Type": "application/octet-stream"},
        timeout=20,
    )
    response.raise_for_status()


def enable_js_apps(session: requests.Session, api: str) -> None:
    mkdir = session.post(f"{api}/storage/mkdir", params={"path": JS_APPS_DIR}, timeout=10)
    if mkdir.status_code not in (200, 201, 204, 400, 409):
        mkdir.raise_for_status()
    flag = session.post(
        f"{api}/storage/write",
        params={"path": JS_APPS_FLAG},
        data=b"1",
        headers={"Content-Type": "application/octet-stream"},
        timeout=10,
    )
    flag.raise_for_status()


def install(host: str, password: str | None) -> None:
    session, api = bar_session(host, password)
    version = session.get(f"{api}/version", timeout=5)
    version.raise_for_status()
    prepare_access(session, api)

    files = package_files()
    print(f"Connected to BUSY Bar at {host}")
    print(f"Uploading Chess Clock ({len(files)} files)…")

    delete = session.delete(
        f"{api}/assets/upload",
        params={"application_name": APP_ID},
        timeout=15,
    )
    if delete.status_code not in (200, 204, 404):
        delete.raise_for_status()

    for path, remote in files:
        print(f"  {remote}")
        upload_file(session, api, path, remote)

    try:
        enable_js_apps(session, api)
        print("Enabled JS apps in the Apps menu.")
    except requests.RequestException as error:
        print(
            "Uploaded, but could not turn on the JS apps menu flag automatically."
        )
        print(f"({error})")
        print("If Chess Clock does not appear in Apps, the bar firmware may")
        print("not include the JS runner yet.")

    print()
    print("Chess Clock is on the bar.")
    print("1. Turn the mode switch to Apps.")
    print("2. Open Chess Clock.")
    print("3. Press Start on the bar.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install the on-device Chess Clock app onto a BUSY Bar."
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
        help="Optional Wi-Fi access password",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        install(args.host, args.password)
    except FileNotFoundError as error:
        raise SystemExit(f"Cannot install Chess Clock: {error}") from error
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
