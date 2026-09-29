#!/usr/bin/env python3
"""Upload the on-device Social Battery JS app to a BUSY Bar."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from install_js_app import run_package  # noqa: E402

if __name__ == "__main__":
    run_package(
        Path(__file__).resolve().parent / "on-device" / "community.social_battery"
    )
