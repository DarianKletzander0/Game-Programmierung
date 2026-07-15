import os
from pathlib import Path
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from signal_breach.audio import tone
from signal_breach.entities import Enemy, Projectile
from signal_breach.game import Game
from signal_breach.levels import SECTORS, SectorRuntime
from signal_breach.model import Profile, ScreenState
from signal_breach.persistence import load_profile, save_profile
from signal_breach.rendering import Renderer


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


class GameStateTests(unittest.TestCase):
    def test_menu_pause_shop_win_and_restart_flow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            game = Game(profile_path=Path(temp_dir) / "profile.json", audio=False)

            self.assertIs(game.state, ScreenState.MENU)
            game.start_run()
            self.assertIs(game.state, ScreenState.PLAYING)

            game.toggle_pause()
            self.assertIs(game.state, ScreenState.PAUSED)
            game.toggle_pause()
            self.assertIs(game.state, ScreenState.PLAYING)

            game.complete_sector()
            self.assertIs(game.state, ScreenState.SHOP)
            game.sector_index = 2
            game.complete_sector()
            self.assertIs(game.state, ScreenState.WON)

            game.restart()
            self.assertIs(game.state, ScreenState.MENU)

    def test_illegal_state_transition_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            game = Game(profile_path=Path(temp_dir) / "profile.json", audio=False)

            with self.assertRaises(AssertionError):
                game.change_state(ScreenState.SHOP)

    def test_paused_update_does_not_advance_simulation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            game = Game(profile_path=Path(temp_dir) / "profile.json", audio=False)
            game.start_run()
            game.toggle_pause()
            elapsed = game.sector.elapsed

            game.update(2.0)

            self.assertEqual(game.sector.elapsed, elapsed)

    def test_combat_hit_removes_enemy_and_awards_score(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            game = Game(profile_path=Path(temp_dir) / "profile.json", audio=False)
            game.start_run()
            enemy = Enemy.create("drifter", pygame.Vector2(300, 250), 1.0)
            enemy.hp = 1
            game.enemies = [enemy]
            game.player_projectiles = [
                Projectile(
                    pygame.Vector2(300, 250),
                    pygame.Vector2(),
                    damage=1,
                    hostile=False,
                )
            ]

            game.update(1 / 60)

            self.assertEqual(game.enemies, [])
            self.assertEqual(game.run.score, enemy.points)
            self.assertEqual(game.run.currency, enemy.currency)

    def test_game_over_persists_highscore_and_best_combo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "profile.json"
            game = Game(profile_path=path, audio=False)
            game.start_run()
            game.run.score = 1234
            game.run.best_combo = 8
            game.player.hp = 0

            game.update(1 / 60)
            profile = load_profile(path)

            self.assertIs(game.state, ScreenState.GAME_OVER)
            self.assertEqual(profile.highscore, 1234)
            self.assertEqual(profile.best_combo, 8)

    def test_keyboard_events_control_start_pause_shop_and_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            game = Game(profile_path=Path(temp_dir) / "profile.json", audio=False)
            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
            self.assertIs(game.state, ScreenState.PLAYING)

            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_p))
            self.assertIs(game.state, ScreenState.PAUSED)

            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_p))
            game.complete_sector()
            game.run.currency = 99
            first_offer = game.upgrades.offer_names[0]
            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1))
            self.assertEqual(game.upgrades.levels[first_offer], 1)
            self.assertEqual(game.upgrades.bought_offer, first_offer)

            game.sector_index = 2
            game.complete_sector()
            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r))
            self.assertIs(game.state, ScreenState.MENU)

    def test_impulse_during_cooldown_does_not_restart_visual_effect(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            game = Game(profile_path=Path(temp_dir) / "profile.json", audio=False)
            game.start_run()
            game.activate_impulse()
            for _ in range(13):
                game.update(1 / 30)
            self.assertEqual(game.pulse_visible, 0.0)
            self.assertGreater(game.player.impulse_cooldown, 0.0)

            game.activate_impulse()

            self.assertEqual(game.pulse_visible, 0.0)

    def test_sound_can_be_enabled_when_profile_started_muted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "profile.json"
            save_profile(path, Profile(sound_enabled=False))
            game = Game(profile_path=path, audio=True)
            self.assertFalse(game.audio.enabled)

            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m))

            self.assertTrue(game.audio.enabled)
            self.assertTrue(game.audio.available)

    def test_complete_simulation_spawns_all_bosses_and_reaches_win(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            game = Game(profile_path=Path(temp_dir) / "profile.json", audio=False)
            game.start_run()
            boss_sectors: set[int] = set()

            for frame in range(12_000):
                game.run.player.max_hp = 100_000
                game.player.hp = 100_000
                if frame % 20 == 0:
                    game.player_projectiles.extend(
                        Projectile(enemy.pos.copy(), pygame.Vector2(), 99_999, False)
                        for enemy in game.enemies
                    )
                game.update(1 / 60)
                if game.boss is not None:
                    boss_sectors.add(game.sector_index)
                if game.state is ScreenState.SHOP:
                    game.start_next_sector()
                if game.state is ScreenState.WON:
                    break

            self.assertIs(game.state, ScreenState.WON)
            self.assertEqual(boss_sectors, {0, 1, 2})
            self.assertEqual(game.profile.unlocked_sector, 3)


class AudioGenerationTests(unittest.TestCase):
    def test_tone_returns_signed_16_bit_mono_samples(self) -> None:
        samples = tone(440.0, 0.1)

        self.assertEqual(len(samples), 4410 * 2)
        self.assertNotEqual(samples, bytes(len(samples)))


class RenderingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        pygame.display.set_mode((1, 1))

    def test_all_game_states_render_to_a_single_surface(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            game = Game(profile_path=Path(temp_dir) / "profile.json", audio=False)
            renderer = Renderer()
            surface = pygame.Surface((960, 720))

            states = [ScreenState.MENU]
            game.start_run()
            states.extend(
                [
                    ScreenState.PLAYING,
                    ScreenState.PAUSED,
                    ScreenState.SHOP,
                    ScreenState.GAME_OVER,
                    ScreenState.WON,
                ]
            )
            for state in states:
                with self.subTest(state=state):
                    game.state = state
                    renderer.draw(surface, game)
                    colors = {
                        surface.get_at((x, y))[:3]
                        for x in range(0, surface.get_width(), 40)
                        for y in range(0, surface.get_height(), 40)
                    }
                    self.assertGreater(len(colors), 5)


if __name__ == "__main__":
    unittest.main()
