import importlib
import importlib.util
import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame


EXERCISE_DIR = Path(__file__).resolve().parents[1]


def load_exercise_modules():
    sys.path.insert(0, str(EXERCISE_DIR))
    try:
        pygame.display.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((1, 1))

        for name in ("settings", "entity", "shot", "player", "enemy", "obstacle", "level"):
            sys.modules.pop(name, None)

        modules = {
            "enemy": importlib.import_module("enemy"),
            "level": importlib.import_module("level"),
            "obstacle": importlib.import_module("obstacle"),
            "player": importlib.import_module("player"),
            "shot": importlib.import_module("shot"),
        }

        main_spec = importlib.util.spec_from_file_location(
            "uebung_003_main",
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


MODULES = load_exercise_modules()
Enemy = MODULES["enemy"].Enemy
Level = MODULES["level"].Level
Obstacle = MODULES["obstacle"].Obstacle
Player = MODULES["player"].Player
Shot = MODULES["shot"].Shot
game_main = MODULES["main"]


class EnemyTests(unittest.TestCase):
    def test_enemy_moves_toward_target_with_configured_speed(self) -> None:
        enemy = Enemy()
        enemy.setup(10, 10, 0, 0, "enemy", 1, hp=3, damage=2, speed=4)

        enemy.step(pygame.Vector2(30, 10))

        self.assertEqual(enemy.pos, pygame.Vector2(14, 10))

    def test_enemy_does_not_cross_obstacle(self) -> None:
        enemy = Enemy()
        enemy.setup(10, 10, 0, 0, "enemy", 1, hp=3, damage=2, speed=10)
        enemy.hitbox_w = 8
        enemy.hitbox_h = 8
        obstacle = Obstacle(track=0, duration_start=0, length=40)
        obstacle.x1 = 15
        obstacle.x2 = 25
        obstacle.y1 = 0
        obstacle.y2 = 40

        enemy.step(pygame.Vector2(100, 10), [obstacle])

        self.assertEqual(enemy.pos, pygame.Vector2(10, 10))


class LevelTests(unittest.TestCase):
    def test_default_level_can_defeat_default_player_if_enemies_are_not_avoided(self) -> None:
        player = game_main.create_player()
        level = Level()

        level.load("lvl001.rfg")

        self.assertGreaterEqual(sum(enemy.damage for enemy in level.enemies), player.hp)

    def test_level_enemy_lines_create_configured_enemy_instances(self) -> None:
        level = Level()
        level._parse_level_line("L T(2) B(background.png) M(song) D(2000)")

        level._parse_enemy_line("E D(3) S(2) A(enemy) N(2) T(1) P(100)")

        self.assertEqual(len(level.enemies), 2)
        self.assertEqual([enemy.damage for enemy in level.enemies], [3, 3])
        self.assertEqual([enemy.speed for enemy in level.enemies], [2, 2])
        self.assertEqual([enemy.starting_point for enemy in level.enemies], [100, 100])
        self.assertTrue(all(enemy.pos.x == 450 for enemy in level.enemies))

    def test_obstacles_enter_screen_over_time_from_duration_position(self) -> None:
        level = Level()
        level._parse_level_line("L T(2) B(background.png) M(song) D(2000)")

        level._parse_obstacle_line("O T(0) D(100) L(40) C(35,56,90) W(5)")

        obstacle = level.obstacles[0]
        self.assertEqual(obstacle.y1, -100)
        self.assertEqual(obstacle.y2, -60)

        level.step()

        self.assertEqual(obstacle.y1, -99)
        self.assertEqual(obstacle.y2, -59)


class ObstacleTests(unittest.TestCase):
    def test_thin_obstacle_uses_reachable_pickup_area_for_player_collision(self) -> None:
        player = Player()
        player.setup(340, 750, 0, 0, "player_stage", 1, hp=100)
        obstacle = Obstacle(effect="upgrade", width=5)
        obstacle.x1 = 298
        obstacle.x2 = 302
        obstacle.y1 = 700
        obstacle.y2 = 760

        self.assertTrue(obstacle.collides_with(player.get_rect()))

    def test_obstacle_upgrade_improves_player_weapon_once(self) -> None:
        player = Player()
        player.setup(20, 20, 0, 0, "player_stage", 1, hp=100)
        player.set_might(rng=100, dmg=1, cad=50, shotspd=1)
        obstacle = Obstacle(effect="upgrade")

        self.assertTrue(obstacle.apply_to_player(player))
        self.assertEqual((player.rng, player.dmg, player.cad, player.shotspd), (150, 2, 40, 2))

        self.assertFalse(obstacle.apply_to_player(player))
        self.assertEqual((player.rng, player.dmg, player.cad, player.shotspd), (150, 2, 40, 2))

    def test_obstacle_upgrade_gives_visible_feedback(self) -> None:
        player = Player()
        player.setup(20, 20, 0, 0, "player_stage", 1, hp=100)
        obstacle = Obstacle(effect="upgrade")

        obstacle.apply_to_player(player)

        self.assertIn("Upgrade", player.status_message)
        self.assertEqual(obstacle.get_label(), "USED")

    def test_obstacle_downgrade_reduces_player_hp_once(self) -> None:
        player = Player()
        player.setup(20, 20, 0, 0, "player_stage", 1, hp=100)
        obstacle = Obstacle(effect="downgrade")

        self.assertTrue(obstacle.apply_to_player(player))
        self.assertEqual(player.hp, 90)

        self.assertFalse(obstacle.apply_to_player(player))
        self.assertEqual(player.hp, 90)


class CollisionTests(unittest.TestCase):
    def test_player_shot_damages_enemy_and_removes_both_when_enemy_dies(self) -> None:
        player = Player()
        player.setup(100, 300, 0, 0, "player_stage", 1, hp=100)
        shot = Shot()
        shot.setup(100, 80, 0, -1, "Shot", 1, hp=1, rng=100, dmg=2)
        player.shots = [shot]
        enemy = Enemy()
        enemy.setup(100, 80, 0, 0, "enemy", 1, hp=2, damage=5, speed=1)
        level = Level()
        level.enemies = [enemy]

        game_main.handle_collisions(player, level)

        self.assertEqual(level.enemies, [])
        self.assertEqual(player.shots, [])

    def test_player_shot_despawns_enemy_on_any_hit(self) -> None:
        player = Player()
        player.setup(100, 300, 0, 0, "player_stage", 1, hp=100)
        shot = Shot()
        shot.setup(100, 80, 0, -1, "Shot", 1, hp=1, rng=100, dmg=1)
        player.shots = [shot]
        enemy = Enemy()
        enemy.setup(100, 80, 0, 0, "enemy", 1, hp=5, damage=5, speed=1)
        level = Level()
        level.enemies = [enemy]

        game_main.handle_collisions(player, level)

        self.assertEqual(level.enemies, [])
        self.assertEqual(player.shots, [])

    def test_enemy_collision_damages_player_and_despawns_enemy(self) -> None:
        player = Player()
        player.setup(100, 100, 0, 0, "player_stage", 1, hp=100)
        enemy = Enemy()
        enemy.setup(100, 100, 0, 0, "enemy", 1, hp=2, damage=25, speed=1)
        level = Level()
        level.enemies = [enemy]

        game_main.handle_collisions(player, level)

        self.assertEqual(player.hp, 75)
        self.assertEqual(level.enemies, [])

    def test_player_death_switches_to_game_over(self) -> None:
        player = Player()
        player.setup(100, 100, 0, 0, "player_stage", 1, hp=0)

        self.assertEqual(game_main.get_game_state(player), "gameover")


class PlayerControlTests(unittest.TestCase):
    def test_player_x_position_is_clamped_inside_screen(self) -> None:
        player = Player()
        player.setup(100, 100, 0, 0, "player_stage", 1, hp=100)

        player.move_to_x(-100)
        self.assertEqual(player.pos.x, 32)

        player.move_to_x(1_000)
        self.assertEqual(player.pos.x, 568)


class GameLoopTests(unittest.TestCase):
    def test_restart_event_is_only_active_during_game_over(self) -> None:
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r)

        self.assertFalse(game_main.is_restart_event(event, game_main.GAME_PLAYING))
        self.assertTrue(game_main.is_restart_event(event, game_main.GAME_OVER))

    def test_create_game_returns_fresh_playing_state(self) -> None:
        player, level, game_state = game_main.create_game()

        self.assertEqual(player.hp, 100)
        self.assertEqual(game_state, game_main.GAME_PLAYING)
        self.assertGreater(len(level.enemies), 0)

    def test_weapon_status_changes_after_upgrade(self) -> None:
        player = game_main.create_player()
        obstacle = Obstacle(effect="upgrade")
        before = game_main.get_weapon_status(player)

        obstacle.apply_to_player(player)

        self.assertNotEqual(game_main.get_weapon_status(player), before)
