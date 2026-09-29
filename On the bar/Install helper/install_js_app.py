#!/usr/bin/env python3
"""Upload an on-device JS app package to a BUSY Bar."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
from pathlib import Path

import requests

DEFAULT_HOST = "10.0.4.20"
JS_APPS_FLAG = "/ext/apps_data/apps_menu/js_apps_enabled"
JS_APPS_DIR = "/ext/apps_data/apps_menu"


def bar_session(host: str, password: str | None) -> tuple[requests.Session, str]:
    clean = host.strip().replace("http://", "").replace("https://", "").rstrip("/")
    session = requests.Session()
    if password:
        session.headers["X-API-Token"] = password
    return session, f"http://{clean}/api"


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


def read_manifest(package_dir: Path) -> dict:
    manifest_path = package_dir / "appmeta" / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Package is missing appmeta/manifest.json: {package_dir}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def package_files(package_dir: Path) -> list[tuple[Path, str]]:
    if not package_dir.is_dir():
        raise FileNotFoundError(f"Missing on-device package: {package_dir}")
    files: list[tuple[Path, str]] = []
    for path in sorted(package_dir.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        files.append((path, path.relative_to(package_dir).as_posix()))
    if not any(remote == "scripts/main.js" for _, remote in files):
        raise FileNotFoundError(f"Package is missing scripts/main.js: {package_dir}")
    return files


def upload_file(
    session: requests.Session, api: str, app_id: str, path: Path, remote: str
) -> None:
    response = session.post(
        f"{api}/assets/upload",
        params={"application_name": app_id, "file": remote},
        data=path.read_bytes(),
        headers={"Content-Type": "application/octet-stream"},
        timeout=30,
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


def install_package(
    session: requests.Session, api: str, package_dir: Path
) -> tuple[str, str]:
    manifest = read_manifest(package_dir)
    app_id = str(manifest.get("id") or "").strip()
    title = str(manifest.get("name") or app_id).strip()
    if not app_id:
        raise FileNotFoundError(f"manifest.json is missing id: {package_dir}")
    if package_dir.name != app_id:
        raise FileNotFoundError(
            f"Folder name {package_dir.name!r} must match manifest id {app_id!r}"
        )

    files = package_files(package_dir)
    print(f"Uploading {title} ({len(files)} files)…")

    delete = session.delete(
        f"{api}/assets/upload",
        params={"application_name": app_id},
        timeout=20,
    )
    if delete.status_code not in (200, 204, 404):
        delete.raise_for_status()

    for path, remote in files:
        print(f"  {remote}")
        upload_file(session, api, app_id, path, remote)

    print(f"{title} is on the bar.")
    return app_id, title


def install(host: str, password: str | None, package_dirs: list[Path]) -> None:
    session, api = bar_session(host, password)
    version = session.get(f"{api}/version", timeout=5)
    version.raise_for_status()
    prepare_access(session, api)

    print(f"Connected to BUSY Bar at {host}")
    titles: list[str] = []
    for package_dir in package_dirs:
        _app_id, title = install_package(session, api, package_dir)
        titles.append(title)
        print()

    try:
        enable_js_apps(session, api)
        print("Enabled JS apps in the Apps menu.")
    except requests.RequestException as error:
        print("Uploaded, but could not turn on the JS apps menu flag automatically.")
        print(f"({error})")
        print("If the app does not appear in Apps, the bar firmware may")
        print("not include the JS runner yet.")

    print()
    for title in titles:
        print(f"{title} is on the bar.")
    print("1. Turn the mode switch to Apps.")
    print("2. Open the app.")
    print("3. Use Setup if the app has settings, then press Start.")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install an on-device JS app onto a BUSY Bar."
    )
    parser.add_argument(
        "packages",
        nargs="+",
        type=Path,
        help="Path to an on-device package folder (must match manifest id)",
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
    return parser.parse_args(argv)


def run_cli(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    try:
        install(args.host, args.password, [path.resolve() for path in args.packages])
    except FileNotFoundError as error:
        raise SystemExit(f"Cannot install JS app: {error}") from error
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


def run_package(package_dir: Path) -> None:
    run_cli([str(package_dir), *sys.argv[1:]])


if __name__ == "__main__":
    run_cli()
