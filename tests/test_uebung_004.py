import importlib
import importlib.util
import inspect
import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame


EXERCISE_DIR = Path(__file__).resolve().parents[1] / "uebung_004"


def load_exercise_modules():
    sys.path.insert(0, str(EXERCISE_DIR))
    try:
        pygame.display.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((1, 1))

        for name in (
            "settings",
            "entity",
            "shot",
            "player",
            "enemy",
            "boss",
            "obstacle",
            "level",
            "score",
            "shop",
        ):
            sys.modules.pop(name, None)

        modules = {
            "enemy": importlib.import_module("enemy"),
            "level": importlib.import_module("level"),
            "player": importlib.import_module("player"),
            "shot": importlib.import_module("shot"),
        }

        main_spec = importlib.util.spec_from_file_location(
            "uebung_004_main",
            EXERCISE_DIR / "main.py",
        )
        assert main_spec is not None
        assert main_spec.loader is not None
        main_module = importlib.util.module_from_spec(main_spec)
        main_spec.loader.exec_module(main_module)
        modules["main"] = main_module
        return modules
    finally:
        sys.path.remove(str(EXERCISE_DIR))


def import_exercise_module(name: str):
    sys.path.insert(0, str(EXERCISE_DIR))
    try:
        spec = importlib.util.find_spec(name)
        if spec is None:
            raise AssertionError(f"{name}.py fehlt fuer Uebung 004")
        return importlib.import_module(name)
    finally:
        sys.path.remove(str(EXERCISE_DIR))


MODULES = load_exercise_modules()
Enemy = MODULES["enemy"].Enemy
Level = MODULES["level"].Level
Player = MODULES["player"].Player
Shot = MODULES["shot"].Shot
game_main = MODULES["main"]


class TileBackgroundTests(unittest.TestCase):
    def test_level_repeats_smaller_background_tiles_over_visible_screen(self) -> None:
        level = Level()

        level.load("lvl001.rfg")

        self.assertTrue(hasattr(level, "background_tiles"))
        self.assertTrue(hasattr(level, "background_tile_names"))
        self.assertTrue(hasattr(level, "screen_height"))
        self.assertTrue(hasattr(level, "get_background_tile_positions"))
        self.assertGreaterEqual(len(level.background_tile_names), 2)
        self.assertGreaterEqual(len(level.background_tiles), 2)
        self.assertTrue(
            all(tile.get_height() < level.screen_height for tile in level.background_tiles)
        )
        self.assertTrue(
            all((EXERCISE_DIR / "assets" / name).is_file() for name in level.background_tile_names)
        )

        level.pos.y = -123
        positions = level.get_background_tile_positions()
        self.assertGreaterEqual(len(positions), 2)

        visible_top = min(y for _, y, _ in positions)
        visible_bottom = max(y + tile.get_height() for _, y, tile in positions)
        self.assertLessEqual(visible_top, 0)
        self.assertGreaterEqual(visible_bottom, level.screen_height)


class ScoreAndHighscoreTests(unittest.TestCase):
    def test_score_manager_awards_combo_points_currency_and_persists_highscore(self) -> None:
        score_module = import_exercise_module("score")

        with tempfile.TemporaryDirectory() as tmpdir:
            highscore_path = Path(tmpdir) / "highscore.txt"
            score = score_module.ScoreManager(highscore_path=highscore_path, combo_window=30)

            first = score.record_kill(frame=10)
            second = score.record_kill(frame=25)
            score.save_highscore()
            loaded = score_module.ScoreManager(highscore_path=highscore_path)

        self.assertEqual(first, 100)
        self.assertGreater(second, first)
        self.assertEqual(score.score, first + second)
        self.assertEqual(score.currency, 2)
        self.assertEqual(loaded.highscore, score.score)

    def test_combo_resets_when_next_level_starts(self) -> None:
        score_module = import_exercise_module("score")
        score = score_module.ScoreManager(highscore_path=None, combo_window=90)
        score.record_kill(frame=1900)

        player = game_main.create_player()
        game_main.create_game(level_index=1, score_manager=score, player=player)
        next_level_points = score.record_kill(frame=100)

        self.assertEqual(next_level_points, 100)
        self.assertEqual(score.combo, 0)

    def test_shot_kill_increments_score_and_currency(self) -> None:
        score_module = import_exercise_module("score")
        signature = inspect.signature(game_main.handle_collisions)
        self.assertIn("score_manager", signature.parameters)

        player = Player()
        player.setup(100, 300, 0, 0, "player_stage", 1, hp=100)
        shot = Shot()
        shot.setup(100, 80, 0, -1, "Shot", 1, hp=1, rng=100, dmg=3)
        player.shots = [shot]
        enemy = Enemy()
        enemy.setup(100, 80, 0, 0, "enemy", 1, hp=2, damage=5, speed=1)
        enemy.ready = True
        level = Level()
        level.enemies = [enemy]
        score = score_module.ScoreManager(highscore_path=None)

        game_main.handle_collisions(player, level, score_manager=score)

        self.assertEqual(level.enemies, [])
        self.assertEqual(player.shots, [])
        self.assertEqual(score.score, 100)
        self.assertEqual(score.currency, 1)

    def test_shot_does_not_kill_enemy_before_spawn_frame(self) -> None:
        score_module = import_exercise_module("score")
        player = Player()
        player.setup(100, 300, 0, 0, "player_stage", 1, hp=100)
        shot = Shot()
        shot.setup(100, 80, 0, -1, "Shot", 1, hp=1, rng=100, dmg=3)
        player.shots = [shot]
        enemy = Enemy()
        enemy.setup(100, 80, 0, 0, "enemy", 1, hp=2, damage=5, speed=1)
        enemy.ready = False
        enemy.starting_point = 500
        level = Level()
        level.enemies = [enemy]
        level.frame = 100
        score = score_module.ScoreManager(highscore_path=None)

        game_main.handle_collisions(player, level, score_manager=score)

        self.assertEqual(level.enemies, [enemy])
        self.assertEqual(player.shots, [shot])
        self.assertEqual(score.score, 0)


class UpgradeShopTests(unittest.TestCase):
    def test_upgrade_shop_spends_currency_and_improves_player_between_levels(self) -> None:
        score_module = import_exercise_module("score")
        shop_module = import_exercise_module("shop")
        score = score_module.ScoreManager(highscore_path=None)
        player = game_main.create_player()
        shop = shop_module.UpgradeShop()
        score.currency = shop.get_cost("damage")

        bought = shop.buy("damage", player, score)

        self.assertTrue(bought)
        self.assertEqual(score.currency, 0)
        self.assertGreater(player.dmg, 1)
        self.assertEqual(shop.levels["damage"], 1)

    def test_upgrade_shop_rejects_purchase_without_currency(self) -> None:
        score_module = import_exercise_module("score")
        shop_module = import_exercise_module("shop")
        score = score_module.ScoreManager(highscore_path=None)
        player = game_main.create_player()
        shop = shop_module.UpgradeShop()

        bought = shop.buy("hp", player, score)

        self.assertFalse(bought)
        self.assertEqual(player.hp, 100)
        self.assertEqual(shop.levels["hp"], 0)


class LevelProgressionTests(unittest.TestCase):
    def test_game_defines_three_levels_with_increasing_difficulty(self) -> None:
        self.assertTrue(hasattr(game_main, "LEVEL_FILES"))
        self.assertGreaterEqual(len(game_main.LEVEL_FILES), 3)

        levels = []
        for filename in game_main.LEVEL_FILES[:3]:
            level = Level()
            level.load(filename)
            levels.append(level)

        enemy_counts = [len(level.enemies) for level in levels]
        max_speeds = [max(enemy.speed for enemy in level.enemies) for level in levels]

        self.assertGreater(enemy_counts[1], enemy_counts[0])
        self.assertGreater(enemy_counts[2], enemy_counts[1])
        self.assertGreater(max_speeds[2], max_speeds[0])

    def test_later_levels_include_a_non_boss_special_enemy_type(self) -> None:
        enemy_module = import_exercise_module("enemy")
        self.assertTrue(hasattr(enemy_module, "ZigZagEnemy"))

        for filename in game_main.LEVEL_FILES[1:3]:
            with self.subTest(filename=filename):
                level = Level()
                level.load(filename)
                special_enemies = [
                    enemy
                    for enemy in level.enemies
                    if isinstance(enemy, enemy_module.ZigZagEnemy)
                    and not getattr(enemy, "is_boss", False)
                ]

                self.assertGreater(len(special_enemies), 0)

    def test_zigzag_enemy_has_distinct_movement_pattern(self) -> None:
        enemy_module = import_exercise_module("enemy")
        self.assertTrue(hasattr(enemy_module, "ZigZagEnemy"))
        enemy = enemy_module.ZigZagEnemy()
        enemy.setup(100, 20, 0, 0, "enemy", 1, hp=2, damage=5, speed=2)
        enemy.ready = True

        enemy.step(pygame.Vector2(100, 100))

        self.assertNotEqual(enemy.pos.x, 100)
        self.assertGreater(enemy.pos.y, 20)

    def test_create_game_tracks_level_index_score_and_shop_state(self) -> None:
        created = game_main.create_game()
        self.assertEqual(len(created), 5)
        player, level, game_state, level_index, score = created

        self.assertEqual(game_state, game_main.GAME_PLAYING)
        self.assertEqual(level_index, 0)
        self.assertEqual(score.score, 0)

        level.enemies = []
        level.frame = level.duration + 1
        self.assertEqual(game_main.get_game_state(player, level), game_main.GAME_SHOP)

    def test_final_level_completion_transitions_to_won(self) -> None:
        self.assertTrue(hasattr(game_main, "get_progress_state"))
        player, level, _, level_index, _ = game_main.create_game(
            level_index=len(game_main.LEVEL_FILES) - 1
        )
        level.enemies = []

        state = game_main.get_progress_state(player, level, level_index)

        self.assertEqual(state, game_main.GAME_WON)


class BossBattleTests(unittest.TestCase):
    def test_boss_fires_three_projectile_special_attack(self) -> None:
        boss_module = import_exercise_module("boss")
        boss = boss_module.BossEnemy()
        boss.setup(300, 130, 0, 0, "enemy", 1, hp=8, damage=18, speed=2)
        boss.ready = True

        self.assertTrue(hasattr(boss, "shots"))
        self.assertTrue(hasattr(boss, "attack_cooldown"))
        boss.attack_cooldown = 1
        boss.step(pygame.Vector2(300, 750))

        self.assertEqual(len(boss.shots), 3)
        self.assertEqual(len({round(shot.velocity.x, 2) for shot in boss.shots}), 3)
        self.assertTrue(all(shot.velocity.y > 0 for shot in boss.shots))

    def test_boss_projectile_damages_player_and_is_removed(self) -> None:
        boss_module = import_exercise_module("boss")
        player = game_main.create_player()
        boss = boss_module.BossEnemy()
        boss.setup(300, 130, 0, 0, "enemy", 1, hp=8, damage=18, speed=2)
        boss.ready = True
        boss.fire_special_attack(player.pos)
        projectile = boss.shots[1]
        projectile.pos = player.pos.copy()
        boss.shots = [projectile]
        level = Level()
        level.enemies = [boss]
        hp_before = player.hp

        game_main.handle_collisions(player, level)

        self.assertEqual(player.hp, hp_before - projectile.damage)
        self.assertEqual(boss.shots, [])

    def test_each_level_spawns_a_boss_near_the_end(self) -> None:
        boss_module = import_exercise_module("boss")

        for filename in game_main.LEVEL_FILES[:3]:
            with self.subTest(filename=filename):
                level = Level()
                level.load(filename)
                bosses = [
                    enemy for enemy in level.enemies if isinstance(enemy, boss_module.BossEnemy)
                ]

                self.assertEqual(len(bosses), 1)
                self.assertTrue(bosses[0].is_boss)
                self.assertGreater(bosses[0].hp, 2)
                self.assertGreaterEqual(bosses[0].starting_point, level.duration - 300)

    def test_boss_takes_multiple_hits_and_awards_boss_score_on_death(self) -> None:
        boss_module = import_exercise_module("boss")
        score_module = import_exercise_module("score")
        signature = inspect.signature(game_main.handle_collisions)
        self.assertIn("score_manager", signature.parameters)

        player = Player()
        player.setup(100, 300, 0, 0, "player_stage", 1, hp=100)
        boss = boss_module.BossEnemy()
        boss.setup(100, 80, 0, 0, "enemy", 1, hp=5, damage=15, speed=1)
        boss.ready = True
        level = Level()
        level.enemies = [boss]
        score = score_module.ScoreManager(highscore_path=None)

        weak_shot = Shot()
        weak_shot.setup(100, 80, 0, -1, "Shot", 1, hp=1, rng=100, dmg=2)
        player.shots = [weak_shot]
        game_main.handle_collisions(player, level, score_manager=score)

        self.assertEqual(level.enemies, [boss])
        self.assertEqual(boss.hp, 3)
        self.assertEqual(score.score, 0)

        finishing_shot = Shot()
        finishing_shot.setup(100, 80, 0, -1, "Shot", 1, hp=1, rng=100, dmg=3)
        player.shots = [finishing_shot]
        game_main.handle_collisions(player, level, score_manager=score)

        self.assertEqual(level.enemies, [])
        self.assertEqual(score.score, 500)
        self.assertEqual(score.currency, 5)


if __name__ == "__main__":
    unittest.main()
