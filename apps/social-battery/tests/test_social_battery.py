from __future__ import annotations

import sys
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from busybar_ws_input import events_from_state  # noqa: E402
from social_battery import STATES, SocialBattery  # noqa: E402


class SocialBatteryTests(unittest.TestCase):
    def test_release_firmware_encoder_event_decodes(self) -> None:
        frame = bytes.fromhex("12065a041a020802")
        self.assertEqual(list(events_from_state(frame)), [("encoder", 1)])

    def test_each_encoder_event_queues_one_step(self) -> None:
        app = SocialBattery("10.0.4.20", None)
        app.on_input(("encoder", 1))
        app.on_input(("encoder", -1))
        app.on_input(("encoder", 1))
        self.assertEqual(list(app.pending_steps), [-1, 1, -1])

    def test_release_safe_asset_names(self) -> None:
        self.assertEqual(len(STATES), 7)
        remote_names = [remote for _, remote in STATES]
        self.assertEqual(len(remote_names), len(set(remote_names)))
        self.assertNotIn(" ", "".join(remote_names))


if __name__ == "__main__":
    unittest.main()
