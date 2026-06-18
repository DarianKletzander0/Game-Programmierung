"""Data-driven sector definitions and deterministic wave spawning."""

from dataclasses import dataclass

import pygame

from .config import SCREEN_WIDTH
from .entities import Boss, Enemy


@dataclass(frozen=True, slots=True)
class Wave:
    at: float
    kind: str
    count: int
    formation: str = "line"


@dataclass(frozen=True, slots=True)
class SectorDefinition:
    name: str
    subtitle: str
    difficulty: float
    accent: tuple[int, int, int]
    duration: float
    waves: tuple[Wave, ...]
    boss_pattern: str


SECTORS: tuple[SectorDefinition, ...] = (
    SectorDefinition(
        "SEKTOR 01",
        "Handshake-Fehler",
        1.0,
        (65, 238, 255),
        42.0,
        (
            Wave(1.0, "drifter", 4, "line"),
            Wave(7.0, "drifter", 5, "stagger"),
            Wave(13.0, "weaver", 4, "line"),
            Wave(20.0, "drifter", 6, "v"),
            Wave(27.0, "weaver", 5, "stagger"),
            Wave(34.0, "drifter", 7, "line"),
        ),
        "fan",
    ),
    SectorDefinition(
        "SEKTOR 02",
        "Rekursive Schleife",
        1.35,
        (255, 75, 194),
        50.0,
        (
            Wave(1.0, "weaver", 5, "line"),
            Wave(6.5, "drifter", 6, "v"),
            Wave(12.0, "charger", 3, "line"),
            Wave(18.5, "weaver", 6, "stagger"),
            Wave(25.0, "splitter", 3, "line"),
            Wave(32.0, "charger", 4, "v"),
            Wave(39.0, "weaver", 7, "line"),
            Wave(45.0, "drifter", 8, "stagger"),
        ),
        "summon",
    ),
    SectorDefinition(
        "SEKTOR 03",
        "Kernbruch",
        1.7,
        (255, 159, 67),
        58.0,
        (
            Wave(1.0, "drifter", 6, "line"),
            Wave(6.0, "weaver", 6, "v"),
            Wave(11.0, "charger", 4, "stagger"),
            Wave(17.0, "splitter", 4, "line"),
            Wave(23.0, "weaver", 8, "stagger"),
            Wave(29.0, "charger", 5, "v"),
            Wave(35.0, "splitter", 5, "line"),
            Wave(41.0, "drifter", 9, "stagger"),
            Wave(47.0, "weaver", 9, "v"),
            Wave(53.0, "charger", 6, "line"),
        ),
        "core",
    ),
)


class SectorRuntime:
    def __init__(self, definition: SectorDefinition):
        self.definition = definition
        self.elapsed = 0.0
        self.next_wave_index = 0
        self.boss_spawned = False

    @property
    def progress(self) -> float:
        return min(1.0, self.elapsed / max(0.001, self.definition.duration))

    @property
    def remaining_waves(self) -> int:
        return len(self.definition.waves) - self.next_wave_index

    def update(self, dt: float) -> list[Enemy]:
        self.elapsed += max(0.0, dt)
        spawned: list[Enemy] = []
        while self.next_wave_index < len(self.definition.waves):
            wave = self.definition.waves[self.next_wave_index]
            if wave.at > self.elapsed:
                break
            spawned.extend(self._spawn_wave(wave))
            self.next_wave_index += 1
        return spawned

    def should_spawn_boss(self, active_normal_enemies: int) -> bool:
        ready = (
            not self.boss_spawned
            and self.next_wave_index >= len(self.definition.waves)
            and self.elapsed >= self.definition.duration
            and active_normal_enemies == 0
        )
        if ready:
            self.boss_spawned = True
        return ready

    def create_boss(self) -> Boss:
        return Boss(
            pygame.Vector2(SCREEN_WIDTH / 2, -60),
            self.definition.difficulty,
            self.definition.boss_pattern,
        )

    def _spawn_wave(self, wave: Wave) -> list[Enemy]:
        positions = self._formation_positions(wave.count, wave.formation)
        enemies: list[Enemy] = []
        for index, (x, y) in enumerate(positions):
            enemy = Enemy.create(
                wave.kind,
                pygame.Vector2(x, y),
                self.definition.difficulty,
            )
            enemy.fire_timer += index * 0.12
            enemies.append(enemy)
        return enemies

    @staticmethod
    def _formation_positions(count: int, formation: str) -> list[tuple[float, float]]:
        count = max(1, count)
        margin = 70
        if count == 1:
            xs = [SCREEN_WIDTH / 2]
        else:
            spacing = (SCREEN_WIDTH - margin * 2) / (count - 1)
            xs = [margin + index * spacing for index in range(count)]

        if formation == "line":
            return [(x, -30.0) for x in xs]
        if formation == "stagger":
            return [(x, -30.0 - (index % 2) * 55) for index, x in enumerate(xs)]
        if formation == "v":
            middle = (count - 1) / 2
            return [
                (x, -30.0 - abs(index - middle) * 28)
                for index, x in enumerate(xs)
            ]
        raise ValueError(f"Unbekannte Formation: {formation}")
