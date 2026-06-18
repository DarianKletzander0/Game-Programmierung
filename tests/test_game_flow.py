import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from signal_breach.levels import SECTORS, SectorRuntime


class SectorDefinitionTests(unittest.TestCase):
    def test_three_sectors_increase_difficulty_and_use_distinct_bosses(self) -> None:
        self.assertEqual(len(SECTORS), 3)
        self.assertEqual(
            [sector.boss_pattern for sector in SECTORS],
            ["fan", "summon", "core"],
        )
        self.assertLess(SECTORS[0].difficulty, SECTORS[1].difficulty)
        self.assertLess(SECTORS[1].difficulty, SECTORS[2].difficulty)
        self.assertTrue(all(sector.waves for sector in SECTORS))

    def test_later_sectors_combine_more_enemy_types(self) -> None:
        first_types = {wave.kind for wave in SECTORS[0].waves}
        final_types = {wave.kind for wave in SECTORS[2].waves}

        self.assertGreater(len(final_types), len(first_types))
        self.assertIn("charger", final_types)
        self.assertIn("splitter", final_types)


class SectorRuntimeTests(unittest.TestCase):
    def test_spawner_emits_each_wave_once(self) -> None:
        runtime = SectorRuntime(SECTORS[0])
        first_time = SECTORS[0].waves[0].at

        before = runtime.update(first_time - 0.01)
        first = runtime.update(0.02)
        duplicate = runtime.update(0.0)

        self.assertEqual(before, [])
        self.assertEqual(len(first), SECTORS[0].waves[0].count)
        self.assertEqual(duplicate, [])

    def test_formation_spreads_enemies_across_safe_screen_area(self) -> None:
        runtime = SectorRuntime(SECTORS[2])

        enemies = runtime.update(SECTORS[2].waves[0].at + 0.1)

        positions = [enemy.pos.x for enemy in enemies]
        self.assertEqual(len(positions), len(set(positions)))
        self.assertTrue(all(40 <= position <= 920 for position in positions))

    def test_boss_unlocks_only_after_all_waves_and_normal_enemies(self) -> None:
        runtime = SectorRuntime(SECTORS[0])
        runtime.update(SECTORS[0].duration + 1)

        self.assertFalse(runtime.should_spawn_boss(active_normal_enemies=1))
        self.assertTrue(runtime.should_spawn_boss(active_normal_enemies=0))
        self.assertFalse(runtime.should_spawn_boss(active_normal_enemies=0))


if __name__ == "__main__":
    unittest.main()
