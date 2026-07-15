"""Score, combo, currency, and between-sector upgrade rules."""

from dataclasses import dataclass
import random

from .model import RunStats


class ScoreSystem:
    def __init__(self, run: RunStats, combo_window: float = 2.4):
        self.run = run
        self.combo_window = combo_window
        self.last_kill_time: float | None = None
        self.combo_expires_at = 0.0

    def record_kill(
        self,
        now: float,
        points: int = 100,
        currency: int = 1,
    ) -> int:
        if self.last_kill_time is not None and now - self.last_kill_time <= self.combo_window:
            self.run.combo += 1
        else:
            self.run.combo = 1

        multiplier_bonus = (self.run.combo - 1) * 50
        awarded = max(0, points) + multiplier_bonus
        self.run.score += awarded
        self.run.currency += max(0, currency)
        self.run.best_combo = max(self.run.best_combo, self.run.combo)
        self.last_kill_time = now
        self.combo_expires_at = now + self.combo_window
        return awarded

    def update(self, now: float) -> None:
        if self.run.combo and now > self.combo_expires_at:
            self.run.combo = 0

    def on_player_hit(self) -> None:
        self.run.combo = 0
        self.last_kill_time = None
        self.combo_expires_at = 0.0

    def start_sector(self) -> None:
        self.on_player_hit()


@dataclass(frozen=True, slots=True)
class UpgradeEffect:
    stat: str
    operation: str
    value: float
    minimum: float | None = None
    maximum: float | None = None


@dataclass(frozen=True, slots=True)
class Upgrade:
    label: str
    base_cost: int
    max_level: int
    description: str
    effects: tuple[UpgradeEffect, ...]
    weight: int = 10
    rarity: str = "common"


UPGRADES: dict[str, Upgrade] = {
    "damage": Upgrade(
        "Schaden",
        3,
        4,
        "+1 Projektilschaden",
        (UpgradeEffect("damage", "add", 1),),
        weight=14,
    ),
    "fire_rate": Upgrade(
        "Feuerrate",
        3,
        4,
        "12 % kuerzere Ladezeit",
        (UpgradeEffect("fire_cooldown", "multiply", 0.88, minimum=0.09),),
        weight=12,
    ),
    "max_hp": Upgrade(
        "Integritaet",
        2,
        4,
        "+25 maximale HP und Heilung",
        (UpgradeEffect("max_hp", "add", 25), UpgradeEffect("hp", "add", 25)),
        weight=13,
    ),
    "shot_speed": Upgrade(
        "Projektiltempo",
        2,
        4,
        "+90 Projektiltempo",
        (UpgradeEffect("shot_speed", "add", 90.0),),
        weight=10,
    ),
    "shot_range": Upgrade(
        "Reichweite",
        2,
        3,
        "+140 Projektilreichweite",
        (UpgradeEffect("shot_range", "add", 140.0),),
        weight=10,
    ),
    "spread": Upgrade(
        "Streufeuer",
        5,
        3,
        "+1 zusaetzlicher Schuss",
        (UpgradeEffect("spread_shots", "add", 1, maximum=5),),
        weight=5,
        rarity="rare",
    ),
    "impulse_radius": Upgrade(
        "Impulsfeld",
        3,
        3,
        "+35 Impulsradius",
        (UpgradeEffect("impulse_radius", "add", 35.0),),
        weight=8,
    ),
}


class UpgradeSystem:
    def __init__(
        self,
        run: RunStats,
        rng: random.Random | None = None,
    ):
        self.run = run
        self.levels = {name: 0 for name in UPGRADES}
        self.rng = rng or random.Random()
        self.offer_names: tuple[str, ...] = ()
        self.bought_offer: str | None = None
        self.last_message = "Waehle ein Upgrade oder starte den naechsten Sektor."

    def cost(self, name: str) -> int | None:
        item = self._get(name)
        level = self.levels[name]
        if level >= item.max_level:
            return None
        return item.base_cost * (level + 1)

    def available_names(self) -> list[str]:
        return [
            name
            for name, item in UPGRADES.items()
            if self.levels[name] < item.max_level
        ]

    def draft(self, size: int = 3) -> list[str]:
        pool = self.available_names()
        picks: list[str] = []
        for _ in range(min(max(0, size), len(pool))):
            total_weight = sum(max(1, UPGRADES[name].weight) for name in pool)
            roll = self.rng.uniform(0, total_weight)
            cursor = 0.0
            picked = pool[-1]
            for name in pool:
                cursor += max(1, UPGRADES[name].weight)
                if roll <= cursor:
                    picked = name
                    break
            picks.append(picked)
            pool.remove(picked)
        return picks

    def refresh_offers(self, size: int = 3) -> tuple[str, ...]:
        self.offer_names = tuple(self.draft(size))
        self.bought_offer = None
        if self.offer_names:
            self.last_message = "Waehle eine von drei Upgrade-Karten."
        else:
            self.last_message = "Alle Upgrades sind maximal ausgebaut."
        return self.offer_names

    def clear_offers(self) -> None:
        self.offer_names = ()
        self.bought_offer = None

    def buy(self, name: str) -> bool:
        item = self._get(name)
        if self.offer_names and name not in self.offer_names:
            self.last_message = f"{item.label} ist nicht im aktuellen Angebot"
            return False
        if self.offer_names and self.bought_offer is not None:
            self.last_message = "Pro Shop kann nur eine Karte gewaehlt werden"
            return False
        cost = self.cost(name)
        if cost is None:
            self.last_message = f"{item.label}: Maximalstufe erreicht"
            return False
        if self.run.currency < cost:
            self.last_message = f"Zu wenige Datenfragmente fuer {item.label}"
            return False

        self.run.currency -= cost
        self.levels[name] += 1
        self._apply(name)
        if self.offer_names:
            self.bought_offer = name
        self.last_message = f"{item.label} auf Stufe {self.levels[name]} verbessert"
        return True

    def rows(self) -> list[tuple[str, Upgrade, int, int | None]]:
        names = self.offer_names or tuple(UPGRADES)
        return [
            (name, item, self.levels[name], self.cost(name))
            for name in names
            for item in (UPGRADES[name],)
        ]

    def _apply(self, name: str) -> None:
        player = self.run.player
        for effect in self._get(name).effects:
            current = getattr(player, effect.stat)
            if effect.operation == "add":
                updated = current + effect.value
            elif effect.operation == "multiply":
                updated = current * effect.value
            else:
                raise ValueError(f"Unbekannte Upgrade-Operation: {effect.operation}")

            if effect.minimum is not None:
                updated = max(effect.minimum, updated)
            if effect.maximum is not None:
                updated = min(effect.maximum, updated)
            if isinstance(current, int):
                updated = int(round(updated))
            setattr(player, effect.stat, updated)

        player.hp = max(0, min(player.hp, player.max_hp))

    @staticmethod
    def _get(name: str) -> Upgrade:
        if name not in UPGRADES:
            raise KeyError(f"Unbekanntes Upgrade: {name}")
        return UPGRADES[name]
