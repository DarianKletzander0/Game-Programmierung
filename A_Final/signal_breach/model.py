"""Serializable model values independent from pygame rendering."""

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class ScreenState(StrEnum):
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    SHOP = "shop"
    GAME_OVER = "game_over"
    WON = "won"


@dataclass(slots=True)
class Profile:
    highscore: int = 0
    best_combo: int = 0
    unlocked_sector: int = 1
    fullscreen: bool = False
    sound_enabled: bool = True

    def sanitized(self) -> "Profile":
        return Profile(
            highscore=max(0, _safe_int(self.highscore)),
            best_combo=max(0, _safe_int(self.best_combo)),
            unlocked_sector=max(1, min(3, _safe_int(self.unlocked_sector, 1))),
            fullscreen=bool(self.fullscreen),
            sound_enabled=bool(self.sound_enabled),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self.sanitized())


@dataclass(slots=True)
class PlayerStats:
    max_hp: int = 100
    hp: int = 100
    damage: int = 1
    fire_cooldown: float = 0.24
    shot_speed: float = 620.0
    shot_range: float = 760.0
    spread_shots: int = 1
    impulse_radius: float = 150.0


@dataclass(slots=True)
class RunStats:
    score: int = 0
    currency: int = 0
    combo: int = 0
    best_combo: int = 0
    sector_index: int = 0
    player: PlayerStats = field(default_factory=PlayerStats)


def _safe_int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return default
