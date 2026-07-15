from pathlib import Path
import random
import tempfile
import unittest

from signal_breach.events import EventBus
from signal_breach.model import Profile, RunStats
from signal_breach.persistence import load_profile, save_profile
from signal_breach.scoring import UPGRADES, ScoreSystem, UpgradeSystem


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
        self.assertEqual(run.player.spread_shots, 1)
        self.assertEqual(run.player.impulse_radius, 150.0)
        self.assertEqual(run.currency, 0)


class EventBusTests(unittest.TestCase):
    def test_publish_calls_subscribers_with_payload(self) -> None:
        bus = EventBus()
        received: list[int] = []
        bus.subscribe("enemy_killed", lambda points: received.append(points))

        bus.publish("enemy_killed", points=250)

        self.assertEqual(received, [250])


class ScoreSystemTests(unittest.TestCase):
    def test_quick_kills_build_combo_and_currency(self) -> None:
        run = RunStats()
        score = ScoreSystem(run, combo_window=2.0)

        first = score.record_kill(now=1.0, points=100, currency=1)
        second = score.record_kill(now=2.0, points=100, currency=1)

        self.assertEqual(first, 100)
        self.assertEqual(second, 150)
        self.assertEqual(run.score, 250)
        self.assertEqual(run.combo, 2)
        self.assertEqual(run.best_combo, 2)
        self.assertEqual(run.currency, 2)

    def test_late_kill_and_player_hit_reset_combo(self) -> None:
        run = RunStats()
        score = ScoreSystem(run, combo_window=1.0)
        score.record_kill(now=1.0)
        score.record_kill(now=1.5)

        points = score.record_kill(now=4.0)
        score.on_player_hit()

        self.assertEqual(points, 100)
        self.assertEqual(run.combo, 0)


class UpgradeSystemTests(unittest.TestCase):
    def test_purchase_spends_currency_and_changes_player_stats(self) -> None:
        run = RunStats(currency=12)
        upgrades = UpgradeSystem(run)

        self.assertTrue(upgrades.buy("damage"))
        self.assertTrue(upgrades.buy("max_hp"))

        self.assertEqual(run.currency, 7)
        self.assertEqual(run.player.damage, 2)
        self.assertEqual(run.player.max_hp, 125)
        self.assertEqual(run.player.hp, 125)

    def test_rejected_purchase_does_not_change_data(self) -> None:
        run = RunStats(currency=0)
        upgrades = UpgradeSystem(run)
        before = run.player.damage

        self.assertFalse(upgrades.buy("damage"))

        self.assertEqual(run.currency, 0)
        self.assertEqual(run.player.damage, before)
        self.assertEqual(upgrades.levels["damage"], 0)

    def test_upgrade_cost_scales_and_maximum_level_is_enforced(self) -> None:
        run = RunStats(currency=1000)
        upgrades = UpgradeSystem(run)

        self.assertEqual(upgrades.cost("shot_speed"), 2)
        for _ in range(4):
            self.assertTrue(upgrades.buy("shot_speed"))

        self.assertEqual(upgrades.levels["shot_speed"], 4)
        self.assertIsNone(upgrades.cost("shot_speed"))
        self.assertFalse(upgrades.buy("shot_speed"))

    def test_draft_returns_three_unique_available_upgrades(self) -> None:
        run = RunStats(currency=100)
        upgrades = UpgradeSystem(run, rng=random.Random(4))

        offers = upgrades.refresh_offers()

        self.assertEqual(len(offers), 3)
        self.assertEqual(len(set(offers)), 3)
        self.assertTrue(set(offers).issubset(UPGRADES))

    def test_active_offer_limits_purchase_to_one_drafted_card(self) -> None:
        run = RunStats(currency=100)
        upgrades = UpgradeSystem(run)
        upgrades.offer_names = ("damage", "spread", "max_hp")

        self.assertFalse(upgrades.buy("shot_speed"))
        self.assertTrue(upgrades.buy("spread"))
        self.assertEqual(run.player.spread_shots, 2)
        self.assertFalse(upgrades.buy("damage"))


if __name__ == "__main__":
    unittest.main()
