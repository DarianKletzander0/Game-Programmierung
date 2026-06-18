# shop.py
# Between-level upgrade shop for Uebung 004.


class UpgradeShop:
    """Spends gameplay currency on persistent player upgrades."""

    OPTIONS = {
        "damage": {
            "label": "Damage",
            "base_cost": 3,
            "description": "+1 shot damage",
        },
        "fire_rate": {
            "label": "Fire Rate",
            "base_cost": 2,
            "description": "Faster auto-fire",
        },
        "hp": {
            "label": "HP",
            "base_cost": 2,
            "description": "+25 max HP and heal",
        },
        "shot_speed": {
            "label": "Shot Speed",
            "base_cost": 2,
            "description": "Faster bullets",
        },
    }

    def __init__(self):
        self.levels = {name: 0 for name in self.OPTIONS}
        self.last_message = "Buy upgrades, then press Enter"

    def get_cost(self, upgrade_name: str) -> int:
        self._require_upgrade(upgrade_name)
        option = self.OPTIONS[upgrade_name]
        return option["base_cost"] + self.levels[upgrade_name] * option["base_cost"]

    def buy(self, upgrade_name: str, player, score_manager) -> bool:
        self._require_upgrade(upgrade_name)
        cost = self.get_cost(upgrade_name)
        if score_manager.currency < cost:
            self.last_message = f"Not enough currency for {self.OPTIONS[upgrade_name]['label']}"
            return False

        score_manager.currency -= cost
        self.levels[upgrade_name] += 1
        self._apply(upgrade_name, player)
        self.last_message = f"Bought {self.OPTIONS[upgrade_name]['label']}"
        return True

    def get_rows(self) -> list[tuple[str, str, int, int, str]]:
        rows = []
        for index, (name, option) in enumerate(self.OPTIONS.items(), start=1):
            rows.append(
                (
                    str(index),
                    option["label"],
                    self.get_cost(name),
                    self.levels[name],
                    option["description"],
                )
            )
        return rows

    def _apply(self, upgrade_name: str, player) -> None:
        if upgrade_name == "damage":
            player.dmg += 1
        elif upgrade_name == "fire_rate":
            player.cad = max(10, player.cad - 5)
            player._cad_counter = min(player._cad_counter, player.cad)
        elif upgrade_name == "hp":
            if not hasattr(player, "max_hp"):
                player.max_hp = player.hp
            player.max_hp += 25
            player.hp = player.max_hp
        elif upgrade_name == "shot_speed":
            player.shotspd += 1
            player.rng += 20

    def _require_upgrade(self, upgrade_name: str) -> None:
        if upgrade_name not in self.OPTIONS:
            raise KeyError(f"Unknown upgrade: {upgrade_name}")
