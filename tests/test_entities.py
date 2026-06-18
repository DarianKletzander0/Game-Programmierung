import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from signal_breach.config import HUD_HEIGHT, PLAYER_RADIUS, SCREEN_HEIGHT, SCREEN_WIDTH
from signal_breach.entities import Boss, Enemy, Player, Projectile
from signal_breach.model import PlayerStats


class PlayerTests(unittest.TestCase):
    def test_movement_is_clamped_to_playfield(self) -> None:
        player = Player(pygame.Vector2(10, 10), PlayerStats())

        player.move(pygame.Vector2(-1, 1), 10.0)

        self.assertEqual(player.pos.x, PLAYER_RADIUS)
        self.assertEqual(player.pos.y, SCREEN_HEIGHT - PLAYER_RADIUS)

        player.move(pygame.Vector2(1, -1), 10.0)
        self.assertEqual(player.pos.x, SCREEN_WIDTH - PLAYER_RADIUS)
        self.assertEqual(player.pos.y, HUD_HEIGHT + PLAYER_RADIUS)

    def test_damage_uses_invulnerability_window(self) -> None:
        player = Player(pygame.Vector2(300, 600), PlayerStats())

        self.assertTrue(player.take_damage(20))
        self.assertFalse(player.take_damage(20))
        player.update(0.81)
        self.assertTrue(player.take_damage(20))

        self.assertEqual(player.hp, 60)

    def test_auto_fire_uses_current_player_stats(self) -> None:
        stats = PlayerStats(damage=3, fire_cooldown=0.1, shot_speed=700, shot_range=900)
        player = Player(pygame.Vector2(300, 600), stats)

        shots = player.update(0.11)

        self.assertEqual(len(shots), 1)
        self.assertEqual(shots[0].damage, 3)
        self.assertEqual(shots[0].velocity.y, -700)
        self.assertEqual(shots[0].max_distance, 900)

    def test_impulse_removes_only_nearby_hostile_projectiles(self) -> None:
        player = Player(pygame.Vector2(300, 600), PlayerStats())
        near = Projectile(pygame.Vector2(320, 600), pygame.Vector2(), 5, True)
        far = Projectile(pygame.Vector2(700, 200), pygame.Vector2(), 5, True)

        removed = player.activate_impulse([near, far])

        self.assertEqual(removed, 1)
        self.assertFalse(near.alive)
        self.assertTrue(far.alive)
        self.assertGreater(player.impulse_cooldown, 0)


class ProjectileTests(unittest.TestCase):
    def test_projectile_expires_after_maximum_range(self) -> None:
        shot = Projectile(
            pygame.Vector2(100, 100),
            pygame.Vector2(0, -100),
            damage=1,
            hostile=False,
            max_distance=50,
        )

        shot.update(0.6)

        self.assertFalse(shot.alive)


class EnemyTests(unittest.TestCase):
    def test_enemy_factory_defines_distinct_movement_profiles(self) -> None:
        drifter = Enemy.create("drifter", pygame.Vector2(200, 100), 1.0)
        weaver = Enemy.create("weaver", pygame.Vector2(200, 100), 1.0)
        charger = Enemy.create("charger", pygame.Vector2(200, 100), 1.0)

        for enemy in (drifter, weaver, charger):
            enemy.update(0.5, pygame.Vector2(500, 600))

        self.assertNotEqual(drifter.pos, weaver.pos)
        self.assertNotEqual(charger.velocity, drifter.velocity)

    def test_splitter_death_creates_two_fragments(self) -> None:
        enemy = Enemy.create("splitter", pygame.Vector2(300, 200), 1.0)

        self.assertTrue(enemy.take_damage(enemy.hp))
        spawned = enemy.on_destroyed()

        self.assertEqual(len(spawned), 2)
        self.assertTrue(all(item.kind == "fragment" for item in spawned))

    def test_boss_has_phases_and_sector_specific_pattern(self) -> None:
        boss = Boss(pygame.Vector2(480, 120), difficulty=1.0, pattern="fan")
        boss.hp = boss.max_hp // 2

        shots, summons = boss.update(2.0, pygame.Vector2(480, 600))

        self.assertGreaterEqual(boss.phase, 2)
        self.assertGreaterEqual(len(shots), 3)
        self.assertEqual(summons, [])

    def test_summon_boss_creates_two_weaver_helpers_in_later_phase(self) -> None:
        boss = Boss(pygame.Vector2(480, 120), difficulty=1.0, pattern="summon")
        boss.hp = boss.max_hp // 2

        shots, summons = boss.update(2.0, pygame.Vector2(480, 600))

        self.assertGreaterEqual(len(shots), 3)
        self.assertEqual([enemy.kind for enemy in summons], ["weaver", "weaver"])

    def test_core_boss_creates_radial_attack_in_later_phase(self) -> None:
        boss = Boss(pygame.Vector2(480, 120), difficulty=1.0, pattern="core")
        boss.hp = 1

        shots, summons = boss.update(2.0, pygame.Vector2(480, 600))

        self.assertGreaterEqual(len(shots), 14)
        self.assertEqual(summons, [])
        self.assertGreater(len({round(shot.velocity.angle_to((0, 1))) for shot in shots}), 10)


if __name__ == "__main__":
    unittest.main()
