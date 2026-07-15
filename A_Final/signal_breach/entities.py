"""Simulation entities for Signal Breach.

The classes contain movement and combat rules but deliberately do not draw
themselves. This keeps the rules deterministic and testable without a window.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from .config import (
    HUD_HEIGHT,
    IMPULSE_COOLDOWN,
    PLAYER_INVULNERABILITY,
    PLAYER_RADIUS,
    PLAYER_SPEED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from .model import PlayerStats


@dataclass(slots=True)
class Projectile:
    pos: pygame.Vector2
    velocity: pygame.Vector2
    damage: int
    hostile: bool
    max_distance: float = 1000.0
    radius: int = 5
    alive: bool = True
    distance: float = 0.0

    def __post_init__(self) -> None:
        self.pos = pygame.Vector2(self.pos)
        self.velocity = pygame.Vector2(self.velocity)

    @property
    def rect(self) -> pygame.Rect:
        diameter = self.radius * 2
        return pygame.Rect(
            round(self.pos.x - self.radius),
            round(self.pos.y - self.radius),
            diameter,
            diameter,
        )

    def update(self, dt: float) -> None:
        movement = self.velocity * max(0.0, dt)
        self.pos += movement
        self.distance += movement.length()
        margin = 50
        if (
            self.distance >= self.max_distance
            or self.pos.x < -margin
            or self.pos.x > SCREEN_WIDTH + margin
            or self.pos.y < -margin
            or self.pos.y > SCREEN_HEIGHT + margin
        ):
            self.alive = False


class Player:
    radius = PLAYER_RADIUS

    def __init__(self, pos: pygame.Vector2, stats: PlayerStats):
        self.pos = pygame.Vector2(pos)
        self.stats = stats
        self.invulnerability = 0.0
        self.fire_timer = stats.fire_cooldown
        self.impulse_cooldown = 0.0
        self.alive = stats.hp > 0
        self.thrust = 0.0

    @property
    def hp(self) -> int:
        return self.stats.hp

    @hp.setter
    def hp(self, value: int) -> None:
        self.stats.hp = max(0, min(self.stats.max_hp, int(value)))
        self.alive = self.stats.hp > 0

    @property
    def rect(self) -> pygame.Rect:
        diameter = self.radius * 2
        return pygame.Rect(
            round(self.pos.x - self.radius),
            round(self.pos.y - self.radius),
            diameter,
            diameter,
        )

    def move(self, direction: pygame.Vector2, dt: float) -> None:
        movement = pygame.Vector2(direction)
        if movement.length_squared() > 1:
            movement.normalize_ip()
        self.pos += movement * PLAYER_SPEED * max(0.0, dt)
        self.pos.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.pos.x))
        self.pos.y = max(
            HUD_HEIGHT + self.radius,
            min(SCREEN_HEIGHT - self.radius, self.pos.y),
        )
        self.thrust = min(1.0, movement.length())

    def update(self, dt: float) -> list[Projectile]:
        dt = max(0.0, dt)
        self.invulnerability = max(0.0, self.invulnerability - dt)
        self.impulse_cooldown = max(0.0, self.impulse_cooldown - dt)
        self.fire_timer -= dt
        if self.fire_timer > 0 or not self.alive:
            return []

        self.fire_timer = self.stats.fire_cooldown
        shot_count = max(1, int(self.stats.spread_shots))
        if shot_count == 1:
            angles = [0.0]
        else:
            spread = min(34.0, 9.0 * (shot_count - 1))
            middle = (shot_count - 1) / 2
            angles = [(index - middle) * spread / max(1, shot_count - 1) for index in range(shot_count)]

        return [
            Projectile(
                self.pos + pygame.Vector2(0, -self.radius),
                pygame.Vector2(0, -self.stats.shot_speed).rotate(angle),
                self.stats.damage,
                False,
                self.stats.shot_range,
                radius=4,
            )
            for angle in angles
        ]

    def take_damage(self, amount: int) -> bool:
        if self.invulnerability > 0 or not self.alive:
            return False
        self.hp = self.hp - max(0, amount)
        self.invulnerability = PLAYER_INVULNERABILITY
        return True

    def activate_impulse(self, projectiles: list[Projectile]) -> int:
        if self.impulse_cooldown > 0 or not self.alive:
            return 0
        removed = 0
        for projectile in projectiles:
            if (
                projectile.alive
                and projectile.hostile
                and self.pos.distance_to(projectile.pos) <= self.stats.impulse_radius
            ):
                projectile.alive = False
                removed += 1
        self.impulse_cooldown = IMPULSE_COOLDOWN
        return removed


class Enemy:
    def __init__(
        self,
        kind: str,
        pos: pygame.Vector2,
        speed: float,
        hp: int,
        damage: int,
        radius: int,
        points: int,
        currency: int = 1,
    ):
        self.kind = kind
        self.pos = pygame.Vector2(pos)
        self.spawn_x = float(pos.x)
        self.velocity = pygame.Vector2(0, speed)
        self.speed = speed
        self.hp = hp
        self.max_hp = hp
        self.damage = damage
        self.radius = radius
        self.points = points
        self.currency = currency
        self.alive = True
        self.age = 0.0
        self.fire_timer = 0.8 + (pos.x % 100) / 200
        self.hit_flash = 0.0
        self.charging = False

    @classmethod
    def create(cls, kind: str, pos: pygame.Vector2, difficulty: float) -> "Enemy":
        difficulty = max(0.5, difficulty)
        definitions = {
            "drifter": (90.0, 1, 10, 14, 100),
            "weaver": (105.0, 2, 12, 16, 140),
            "charger": (78.0, 3, 18, 17, 180),
            "splitter": (72.0, 3, 14, 18, 210),
            "fragment": (150.0, 1, 8, 9, 50),
        }
        if kind not in definitions:
            raise ValueError(f"Unbekannter Gegnertyp: {kind}")
        speed, hp, damage, radius, points = definitions[kind]
        scaled_hp = max(1, round(hp * (0.75 + difficulty * 0.25)))
        return cls(
            kind,
            pos,
            speed * (0.85 + difficulty * 0.15),
            scaled_hp,
            round(damage * (0.8 + difficulty * 0.2)),
            radius,
            points,
        )

    @property
    def rect(self) -> pygame.Rect:
        diameter = self.radius * 2
        return pygame.Rect(
            round(self.pos.x - self.radius),
            round(self.pos.y - self.radius),
            diameter,
            diameter,
        )

    def update(self, dt: float, target: pygame.Vector2) -> list[Projectile]:
        if not self.alive:
            return []
        dt = max(0.0, dt)
        self.age += dt
        self.hit_flash = max(0.0, self.hit_flash - dt)

        if self.kind == "weaver":
            self.pos.y += self.speed * dt
            self.pos.x = self.spawn_x + math.sin(self.age * 3.2) * 105
        elif self.kind == "charger":
            if self.age > 1.2 and not self.charging:
                direction = pygame.Vector2(target) - self.pos
                self.velocity = direction.normalize() * self.speed * 3.4 if direction else pygame.Vector2(0, self.speed)
                self.charging = True
            self.pos += self.velocity * dt
        elif self.kind == "fragment":
            horizontal = -1 if int(self.spawn_x) % 2 else 1
            self.pos += pygame.Vector2(horizontal * self.speed * 0.45, self.speed) * dt
        else:
            self.pos.y += self.speed * dt

        shots: list[Projectile] = []
        if self.kind in {"drifter", "weaver", "splitter"} and self.pos.y > HUD_HEIGHT:
            self.fire_timer -= dt
            if self.fire_timer <= 0:
                direction = pygame.Vector2(target) - self.pos
                if direction.length_squared() == 0:
                    direction = pygame.Vector2(0, 1)
                shots.append(
                    Projectile(
                        self.pos.copy(),
                        direction.normalize() * 245,
                        max(5, self.damage // 2),
                        True,
                        900,
                        radius=5,
                    )
                )
                self.fire_timer = 1.9 if self.kind == "drifter" else 2.5

        if self.pos.y > SCREEN_HEIGHT + self.radius * 3:
            self.alive = False
        return shots

    def take_damage(self, amount: int) -> bool:
        self.hp = max(0, self.hp - max(0, amount))
        self.hit_flash = 0.1
        if self.hp == 0:
            self.alive = False
        return not self.alive

    def on_destroyed(self) -> list["Enemy"]:
        if self.kind != "splitter":
            return []
        left = Enemy.create("fragment", self.pos + pygame.Vector2(-12, 0), 1.0)
        right = Enemy.create("fragment", self.pos + pygame.Vector2(12, 0), 1.0)
        left.spawn_x = 201
        right.spawn_x = 200
        return [left, right]


class Boss(Enemy):
    def __init__(self, pos: pygame.Vector2, difficulty: float, pattern: str):
        if pattern not in {"fan", "summon", "core"}:
            raise ValueError(f"Unbekanntes Bossmuster: {pattern}")
        hp = round(28 * difficulty)
        super().__init__("boss", pos, 55 * difficulty, hp, round(22 * difficulty), 48, 1200, 8)
        self.pattern = pattern
        self.phase = 1
        self.attack_timer = 0.0
        self.warning = 0.0

    def update(
        self,
        dt: float,
        target: pygame.Vector2,
    ) -> tuple[list[Projectile], list[Enemy]]:
        if not self.alive:
            return [], []
        dt = max(0.0, dt)
        self.age += dt
        self.hit_flash = max(0.0, self.hit_flash - dt)
        ratio = self.hp / max(1, self.max_hp)
        self.phase = 1 if ratio > 0.66 else 2 if ratio > 0.33 else 3
        self.pos.x = SCREEN_WIDTH / 2 + math.sin(self.age * (0.9 + self.phase * 0.12)) * 250
        self.pos.y = min(150, self.pos.y + self.speed * dt)
        self.attack_timer -= dt
        self.warning = max(0.0, self.warning - dt)
        if self.attack_timer > 0:
            return [], []

        self.attack_timer = max(0.55, 1.8 - self.phase * 0.28)
        self.warning = 0.18
        if self.pattern == "summon" and self.phase >= 2:
            summons = [
                Enemy.create("weaver", self.pos + pygame.Vector2(-90, 20), 1.3),
                Enemy.create("weaver", self.pos + pygame.Vector2(90, 20), 1.3),
            ]
            return self._fan(target, 3), summons
        if self.pattern == "core" and self.phase >= 2:
            count = 8 + self.phase * 2
            return self._radial(count), []
        return self._fan(target, 3 + (self.phase - 1) * 2), []

    def _fan(self, target: pygame.Vector2, count: int) -> list[Projectile]:
        direction = pygame.Vector2(target) - self.pos
        if direction.length_squared() == 0:
            direction = pygame.Vector2(0, 1)
        base = direction.normalize() * (235 + self.phase * 25)
        middle = (count - 1) / 2
        return [
            Projectile(
                self.pos.copy(),
                base.rotate((index - middle) * 13),
                max(7, self.damage // 2),
                True,
                1000,
                radius=7,
            )
            for index in range(count)
        ]

    def _radial(self, count: int) -> list[Projectile]:
        return [
            Projectile(
                self.pos.copy(),
                pygame.Vector2(0, 250 + self.phase * 20).rotate(index * 360 / count),
                max(7, self.damage // 2),
                True,
                1000,
                radius=7,
            )
            for index in range(count)
        ]
