#!/usr/bin/env python3
"""Build Dice .anim files (bicycle1) from the original 60fps PNG sequences."""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANIM_DIR = ROOT / "Animation files"
ON_DEVICE_DIR = ROOT / "on-device" / "community.dice" / "animations"
FPS = 60
FRAMES_PER_ROLL = 180
# Original clips hold the starting face for 63 frames (~1.05s) before the tumble,
# then rest on the result from frame 120. Keep one rest frame so the last face
# is on screen; the bar holds that frame after playback.
SKIP_START_FRAMES = 63
KEEP_UNTIL_FRAME = 121
# Source frames are 72×16; the die only occupies the middle ~20px. Crop to
# 18×16 so several dice can sit side by side on the front matrix.
CROP_BOX = (27, 0, 45, 16)
DIE_WIDTH = CROP_BOX[2] - CROP_BOX[0]
DIE_HEIGHT = CROP_BOX[3] - CROP_BOX[1]
# Source frames are RGB on black. Treat near-black as transparent so the wash
# shows through around (and inside) every die.
BLACK_MAX = 20


def firmware_scripts() -> Path:
    env = os.environ.get("BUSY_FIRMWARE")
    candidates = []
    if env:
        candidates.append(Path(env) / "scripts")
    repo_parent = Path(__file__).resolve().parents[2].parent
    candidates.append(repo_parent / "BSB-Firmware-Library-SDK" / "busybar-firmware" / "scripts")
    for candidate in candidates:
        if (candidate / "seq2anim.py").is_file():
            return candidate
    raise FileNotFoundError(
        "Need firmware scripts/seq2anim.py. Set BUSY_FIRMWARE to the firmware repo, "
        "or keep it next to this repo at BSB-Firmware-Library-SDK/busybar-firmware."
    )


def png_root() -> Path:
    env = os.environ.get("DICE_PNG_SEQUENCES")
    if not env:
        raise FileNotFoundError(
            "Set DICE_PNG_SEQUENCES to the folder of original dice PNG sequences."
        )
    path = Path(env)
    if not path.is_dir():
        raise FileNotFoundError(f"PNG sequence folder not found: {path}")
    return path


def sequence_dir(root: Path, first: int, second: int) -> Path:
    return root / f"{first} -" / f"{first} - {second}"


def sequence_pngs(folder: Path) -> list[Path]:
    files = [path for path in folder.glob("*.png") if not path.name.startswith(".")]
    files.sort(key=lambda path: int(path.stem[-3:]))
    if len(files) != FRAMES_PER_ROLL:
        raise ValueError(f"{folder}: expected {FRAMES_PER_ROLL} PNGs, found {len(files)}")
    return files


def punch_black(frame):
    rgba = frame.convert("RGBA").crop(CROP_BOX)
    pixels = rgba.load()
    width, height = rgba.size
    for y in range(height):
        for x in range(width):
            red, green, blue, _alpha = pixels[x, y]
            if max(red, green, blue) <= BLACK_MAX:
                pixels[x, y] = (red, green, blue, 0)
    return rgba


def encode_sequence(pngs: list[Path], output: Path) -> None:
    from PIL import Image
    from seq2anim import BSBAnimConverter

    with tempfile.TemporaryDirectory(prefix="dice-anim-") as raw_dir:
        raw = Path(raw_dir)
        for index, src in enumerate(pngs):
            with Image.open(src) as frame:
                cropped = punch_black(frame)
                if cropped.size != (DIE_WIDTH, DIE_HEIGHT):
                    raise ValueError(
                        f"{src}: crop produced {cropped.size}, "
                        f"expected {(DIE_WIDTH, DIE_HEIGHT)}"
                    )
                cropped.save(raw / f"{index}.png")
        (raw / "meta.json").write_text(
            json.dumps({"fps": FPS, "color_mode": "argb8888", "sections": []}),
            encoding="utf-8",
        )
        BSBAnimConverter().convert_dir(raw, output)


def main() -> int:
    sys.path.insert(0, str(firmware_scripts()))
    source = png_root()
    ANIM_DIR.mkdir(parents=True, exist_ok=True)
    ON_DEVICE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Source: {source}")
    print(f"FPS: {FPS}")
    print(f"Crop: {DIE_WIDTH}x{DIE_HEIGHT} from {CROP_BOX}")
    print("Color: argb8888 (black punched to alpha)")
    print(f"Skip opening hold: {SKIP_START_FRAMES} frames")
    print(f"Keep through frame: {KEEP_UNTIL_FRAME} (drop trailing rest)")
    for first in range(1, 7):
        for second in range(1, 7):
            folder = sequence_dir(source, first, second)
            pngs = sequence_pngs(folder)[SKIP_START_FRAMES:KEEP_UNTIL_FRAME]
            named = ANIM_DIR / f"{first} - {second}.anim"
            on_device = ON_DEVICE_DIR / f"d{first}{second}.anim"
            encode_sequence(pngs, named)
            shutil.copy2(named, on_device)
            print(f"{named.name}: {len(pngs)} frames -> {named.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
