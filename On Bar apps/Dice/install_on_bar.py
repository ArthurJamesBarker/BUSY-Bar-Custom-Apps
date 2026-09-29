#!/usr/bin/env python3
"""Upload the on-device Dice JS app to a BUSY Bar."""

from pathlib import Path
import sys

HELPER = Path(__file__).resolve().parents[1] / "Install helper"
sys.path.insert(0, str(HELPER))

from install_js_app import run_package  # noqa: E402

if __name__ == "__main__":
    run_package(Path(__file__).resolve().parent / "on-device" / "community.dice")
