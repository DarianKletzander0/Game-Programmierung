"""Score, combo, currency, and between-sector upgrade rules."""

from dataclasses import dataclass

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
class Upgrade:
    label: str
    base_cost: int
    max_level: int
    description: str


UPGRADES: dict[str, Upgrade] = {
    "damage": Upgrade("Schaden", 3, 4, "+1 Projektilschaden"),
    "fire_rate": Upgrade("Feuerrate", 3, 4, "12 % kuerzere Ladezeit"),
    "max_hp": Upgrade("Integritaet", 2, 4, "+25 maximale HP und Heilung"),
    "shot_speed": Upgrade("Projektiltempo", 2, 4, "+90 Tempo und +80 Reichweite"),
}


class UpgradeSystem:
    def __init__(self, run: RunStats):
        self.run = run
        self.levels = {name: 0 for name in UPGRADES}
        self.last_message = "Waehle ein Upgrade oder starte den naechsten Sektor."

    def cost(self, name: str) -> int | None:
        item = self._get(name)
        level = self.levels[name]
        if level >= item.max_level:
            return None
        return item.base_cost * (level + 1)

    def buy(self, name: str) -> bool:
        item = self._get(name)
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
        self.last_message = f"{item.label} auf Stufe {self.levels[name]} verbessert"
        return True

    def rows(self) -> list[tuple[str, Upgrade, int, int | None]]:
        return [
            (name, item, self.levels[name], self.cost(name))
            for name, item in UPGRADES.items()
        ]

    def _apply(self, name: str) -> None:
        player = self.run.player
        if name == "damage":
            player.damage += 1
        elif name == "fire_rate":
            player.fire_cooldown = max(0.09, player.fire_cooldown * 0.88)
        elif name == "max_hp":
            player.max_hp += 25
            player.hp = player.max_hp
        elif name == "shot_speed":
            player.shot_speed += 90.0
            player.shot_range += 80.0

    @staticmethod
    def _get(name: str) -> Upgrade:
        if name not in UPGRADES:
            raise KeyError(f"Unbekanntes Upgrade: {name}")
        return UPGRADES[name]
