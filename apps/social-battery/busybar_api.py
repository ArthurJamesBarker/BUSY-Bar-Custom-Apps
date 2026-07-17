"""Release-firmware HTTP client used by Social Battery."""

from __future__ import annotations

from pathlib import Path

import requests

API_VERSION_HEADER = "X-Busy-Api-Version"
DRAW_PRIORITY = 100


class BusyBarClient:
    def __init__(self, host: str, app_id: str, token: str | None = None) -> None:
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
        if token:
            self.set_token(token)

    def set_token(self, token: str) -> None:
        self.session.headers["X-API-Token"] = token

    @property
    def has_token(self) -> bool:
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

    @property
    def ws_url(self) -> str:
        url = f"ws://{self.host}/api/status/ws"
        token = self.session.headers.get("X-API-Token")
        if token:
            url += f"?x-api-token={token}"
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
