from pathlib import Path
import tempfile
import unittest

from signal_breach.model import Profile, RunStats
from signal_breach.persistence import load_profile, save_profile


class ProfilePersistenceTests(unittest.TestCase):
    def test_missing_or_invalid_save_uses_safe_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "profile.json"
            self.assertEqual(load_profile(path), Profile())

            path.write_text("not json", encoding="utf-8")

            self.assertEqual(load_profile(path), Profile())

    def test_profile_roundtrip_clamps_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "profile.json"
            save_profile(
                path,
                Profile(
                    highscore=900,
                    best_combo=7,
                    unlocked_sector=99,
                    fullscreen=True,
                    sound_enabled=False,
                ),
            )

            loaded = load_profile(path)

            self.assertEqual(loaded.highscore, 900)
            self.assertEqual(loaded.best_combo, 7)
            self.assertEqual(loaded.unlocked_sector, 3)
            self.assertTrue(loaded.fullscreen)
            self.assertFalse(loaded.sound_enabled)

    def test_negative_profile_values_are_sanitized(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "profile.json"
            path.write_text(
                '{"highscore": -2, "best_combo": -5, "unlocked_sector": 0}',
                encoding="utf-8",
            )

            loaded = load_profile(path)

            self.assertEqual(loaded.highscore, 0)
            self.assertEqual(loaded.best_combo, 0)
            self.assertEqual(loaded.unlocked_sector, 1)


class RunStatsTests(unittest.TestCase):
    def test_run_starts_with_expected_player_values(self) -> None:
        run = RunStats()

        self.assertEqual(run.player.max_hp, 100)
        self.assertEqual(run.player.hp, 100)
        self.assertEqual(run.player.damage, 1)
        self.assertEqual(run.player.fire_cooldown, 0.24)
        self.assertEqual(run.currency, 0)


if __name__ == "__main__":
    unittest.main()
