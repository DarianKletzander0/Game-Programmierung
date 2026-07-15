"""State machine and simulation orchestration for Signal Breach."""

from enum import StrEnum
from pathlib import Path

import pygame

from .audio import AudioManager
from .config import PROFILE_PATH, SCREEN_HEIGHT, SCREEN_WIDTH
from .entities import Boss, Enemy, Player, Projectile
from .events import EventBus
from .levels import SECTORS, SectorRuntime
from .model import Profile, RunStats, ScreenState
from .persistence import load_profile, save_profile
from .scoring import ScoreSystem, UpgradeSystem


class Action(StrEnum):
    CONFIRM = "confirm"
    PRIMARY = "primary"
    CANCEL = "cancel"
    PAUSE = "pause"
    RESTART = "restart"
    TOGGLE_FULLSCREEN = "toggle_fullscreen"
    TOGGLE_SOUND = "toggle_sound"
    BUY_1 = "buy_1"
    BUY_2 = "buy_2"
    BUY_3 = "buy_3"


KEY_ACTIONS: dict[int, Action] = {
    pygame.K_RETURN: Action.CONFIRM,
    pygame.K_SPACE: Action.PRIMARY,
    pygame.K_ESCAPE: Action.CANCEL,
    pygame.K_p: Action.PAUSE,
    pygame.K_r: Action.RESTART,
    pygame.K_f: Action.TOGGLE_FULLSCREEN,
    pygame.K_m: Action.TOGGLE_SOUND,
    pygame.K_1: Action.BUY_1,
    pygame.K_2: Action.BUY_2,
    pygame.K_3: Action.BUY_3,
}

SHOP_ACTION_INDEX = {
    Action.BUY_1: 0,
    Action.BUY_2: 1,
    Action.BUY_3: 2,
}

ALLOWED_TRANSITIONS: dict[ScreenState, set[ScreenState]] = {
    ScreenState.MENU: {ScreenState.PLAYING},
    ScreenState.PLAYING: {
        ScreenState.PAUSED,
        ScreenState.SHOP,
        ScreenState.GAME_OVER,
        ScreenState.WON,
    },
    ScreenState.PAUSED: {ScreenState.PLAYING},
    ScreenState.SHOP: {ScreenState.PLAYING, ScreenState.WON},
    ScreenState.GAME_OVER: set(),
    ScreenState.WON: set(),
}


class Game:
    def __init__(self, profile_path: Path = PROFILE_PATH, audio: bool = True):
        self.profile_path = Path(profile_path)
        self.profile = load_profile(self.profile_path)
        self.audio = AudioManager(audio)
        self.audio.set_enabled(audio and self.profile.sound_enabled)
        self.events = EventBus()
        self.state = ScreenState.MENU
        self.running = True
        self.fullscreen_requested = False
        self.run = RunStats()
        self.score = ScoreSystem(self.run)
        self.upgrades = UpgradeSystem(self.run)
        self.player = Player(pygame.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 70), self.run.player)
        self.sector = SectorRuntime(SECTORS[0])
        self.enemies: list[Enemy] = []
        self.player_projectiles: list[Projectile] = []
        self.hostile_projectiles: list[Projectile] = []
        self.movement = pygame.Vector2()
        self.time = 0.0
        self.pulse_visible = 0.0
        self.flash = 0.0
        self.status_message = "ENTER: Verbindung starten"
        self.status_timer = 0.0
        self._wire_events()

    @property
    def sector_index(self) -> int:
        return self.run.sector_index

    @sector_index.setter
    def sector_index(self, value: int) -> None:
        self.run.sector_index = max(0, min(len(SECTORS) - 1, int(value)))

    @property
    def boss(self) -> Boss | None:
        return next((enemy for enemy in self.enemies if isinstance(enemy, Boss)), None)

    def change_state(self, next_state: ScreenState) -> None:
        if self.state is next_state:
            return
        if next_state is not ScreenState.MENU:
            allowed = ALLOWED_TRANSITIONS[self.state]
            assert next_state in allowed, f"Illegal state transition: {self.state} -> {next_state}"
        old_state = self.state
        self.state = next_state
        self.events.publish("state_changed", old_state=old_state, new_state=next_state)

    def start_run(self) -> None:
        self.run = RunStats()
        self.score = ScoreSystem(self.run)
        self.upgrades = UpgradeSystem(self.run)
        self._start_sector(0)

    def _start_sector(self, index: int) -> None:
        self.sector_index = index
        self.sector = SectorRuntime(SECTORS[self.sector_index])
        self.player = Player(
            pygame.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 70),
            self.run.player,
        )
        self.player.hp = max(self.player.hp, self.run.player.max_hp // 2)
        self.enemies = []
        self.player_projectiles = []
        self.hostile_projectiles = []
        self.score.start_sector()
        self.upgrades.clear_offers()
        self.movement.update(0, 0)
        self.pulse_visible = 0.0
        self.flash = 0.0
        self.change_state(ScreenState.PLAYING)
        sector = SECTORS[self.sector_index]
        self.set_status(f"{sector.name}: {sector.subtitle}", 3.0)

    def start_next_sector(self) -> None:
        if self.state is not ScreenState.SHOP:
            return
        next_index = self.sector_index + 1
        if next_index >= len(SECTORS):
            self.complete_sector()
            return
        self._start_sector(next_index)

    def complete_sector(self) -> None:
        self.profile.unlocked_sector = max(
            self.profile.unlocked_sector,
            min(3, self.sector_index + 2),
        )
        if self.sector_index >= len(SECTORS) - 1:
            self.change_state(ScreenState.WON)
            self._finish_run()
        else:
            self.change_state(ScreenState.SHOP)
            self.player_projectiles = []
            self.hostile_projectiles = []
            self.upgrades.refresh_offers()
            self._save_profile()

    def toggle_pause(self) -> None:
        if self.state is ScreenState.PLAYING:
            self.change_state(ScreenState.PAUSED)
        elif self.state is ScreenState.PAUSED:
            self.change_state(ScreenState.PLAYING)

    def restart(self) -> None:
        self.change_state(ScreenState.MENU)
        self.enemies = []
        self.player_projectiles = []
        self.hostile_projectiles = []
        self.movement.update(0, 0)
        self.status_message = "ENTER: Verbindung starten"
        self.status_timer = 0.0

    def set_movement(self, x: float, y: float) -> None:
        self.movement.update(x, y)

    def set_status(self, message: str, seconds: float = 2.0) -> None:
        self.status_message = message
        self.status_timer = max(0.0, seconds)

    def activate_impulse(self) -> int:
        if self.state is not ScreenState.PLAYING:
            return 0
        was_ready = self.player.alive and self.player.impulse_cooldown <= 0
        removed = self.player.activate_impulse(self.hostile_projectiles)
        if was_ready:
            self.events.publish("impulse_used", removed=removed)
        return removed

    def buy_upgrade(self, name: str) -> bool:
        if self.state is not ScreenState.SHOP:
            return False
        bought = self.upgrades.buy(name)
        self.set_status(self.upgrades.last_message, 2.0)
        if bought:
            self.events.publish("upgrade_bought", name=name)
        return bought

    def buy_offer(self, index: int) -> bool:
        if index < 0 or index >= len(self.upgrades.offer_names):
            self.set_status("Keine Upgrade-Karte auf diesem Slot", 2.0)
            return False
        return self.buy_upgrade(self.upgrades.offer_names[index])

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
            return
        if event.type == pygame.MOUSEMOTION and self.state is ScreenState.PLAYING:
            x, y = event.pos
            if y >= 82:
                self.player.pos.update(x, y)
                self.player.move(pygame.Vector2(), 0)
            return
        if event.type != pygame.KEYDOWN:
            return

        action = KEY_ACTIONS.get(event.key)
        if action is None:
            return
        if action is Action.TOGGLE_FULLSCREEN:
            self.fullscreen_requested = True
            return
        if action is Action.TOGGLE_SOUND:
            self.profile.sound_enabled = not self.profile.sound_enabled
            self.audio.set_enabled(self.profile.sound_enabled)
            self._save_profile()
            return
        if self.state is ScreenState.MENU:
            if action in (Action.CONFIRM, Action.PRIMARY):
                self.start_run()
            elif action is Action.CANCEL:
                self.running = False
            return
        if self.state in (ScreenState.PLAYING, ScreenState.PAUSED) and action in (
            Action.PAUSE,
            Action.CANCEL,
        ):
            self.toggle_pause()
            return
        if self.state is ScreenState.PLAYING and action is Action.PRIMARY:
            self.activate_impulse()
            return
        if self.state is ScreenState.SHOP:
            if action in SHOP_ACTION_INDEX:
                self.buy_offer(SHOP_ACTION_INDEX[action])
            elif action in (Action.CONFIRM, Action.PRIMARY):
                self.start_next_sector()
            elif action is Action.CANCEL:
                self.running = False
            return
        if self.state in (ScreenState.GAME_OVER, ScreenState.WON):
            if action in (Action.RESTART, Action.CONFIRM):
                self.restart()
            elif action is Action.CANCEL:
                self.running = False

    def update(self, dt: float) -> None:
        if self.state is not ScreenState.PLAYING:
            return
        dt = max(0.0, min(1 / 30, dt))
        self.time += dt
        self.status_timer = max(0.0, self.status_timer - dt)
        self.pulse_visible = max(0.0, self.pulse_visible - dt)
        self.flash = max(0.0, self.flash - dt)
        self.score.update(self.time)
        self.player.move(self.movement, dt)
        new_shots = self.player.update(dt)
        if new_shots:
            self.player_projectiles.extend(new_shots)
            self.events.publish("player_fired", count=len(new_shots))

        self.enemies.extend(self.sector.update(dt))
        for enemy in list(self.enemies):
            if isinstance(enemy, Boss):
                shots, summons = enemy.update(dt, self.player.pos)
                self.hostile_projectiles.extend(shots)
                self.enemies.extend(summons)
                if shots and enemy.warning > 0:
                    self.events.publish("boss_warning", boss=enemy)
            else:
                self.hostile_projectiles.extend(enemy.update(dt, self.player.pos))

        for projectile in self.player_projectiles:
            projectile.update(dt)
        for projectile in self.hostile_projectiles:
            projectile.update(dt)

        self._resolve_collisions()
        self._cleanup()

        if not self.player.alive:
            self.change_state(ScreenState.GAME_OVER)
            self._finish_run()
            return

        normal_count = sum(1 for enemy in self.enemies if not isinstance(enemy, Boss))
        if self.sector.should_spawn_boss(normal_count):
            self.enemies.append(self.sector.create_boss())
            self.set_status("WARNUNG: Sektorwache erkannt", 3.0)
            self.events.publish("boss_warning", boss=self.boss)

        if self.sector.boss_spawned and not self.enemies:
            self.complete_sector()

    def _resolve_collisions(self) -> None:
        spawned: list[Enemy] = []
        for projectile in self.player_projectiles:
            if not projectile.alive:
                continue
            target = next(
                (
                    enemy
                    for enemy in self.enemies
                    if enemy.alive and projectile.rect.colliderect(enemy.rect)
                ),
                None,
            )
            if target is None:
                continue
            projectile.alive = False
            killed = target.take_damage(projectile.damage)
            self.events.publish("enemy_hit", enemy=target)
            if killed:
                spawned.extend(target.on_destroyed())
                self.events.publish("enemy_killed", enemy=target)

        self.enemies.extend(spawned)
        for projectile in self.hostile_projectiles:
            if (
                projectile.alive
                and self.player.alive
                and projectile.rect.colliderect(self.player.rect)
            ):
                projectile.alive = False
                if self.player.take_damage(projectile.damage):
                    self.events.publish("player_hit", damage=projectile.damage)

        for enemy in self.enemies:
            if enemy.alive and enemy.rect.colliderect(self.player.rect):
                if self.player.take_damage(enemy.damage):
                    self.events.publish("player_hit", damage=enemy.damage)
                if not isinstance(enemy, Boss):
                    enemy.alive = False

    def _cleanup(self) -> None:
        self.enemies = [enemy for enemy in self.enemies if enemy.alive]
        self.player_projectiles = [shot for shot in self.player_projectiles if shot.alive]
        self.hostile_projectiles = [shot for shot in self.hostile_projectiles if shot.alive]

    def _finish_run(self) -> None:
        self.profile.highscore = max(self.profile.highscore, self.run.score)
        self.profile.best_combo = max(self.profile.best_combo, self.run.best_combo)
        self._save_profile()

    def _save_profile(self) -> None:
        save_profile(self.profile_path, self.profile)

    def consume_fullscreen_request(self) -> bool:
        requested = self.fullscreen_requested
        self.fullscreen_requested = False
        return requested

    def _wire_events(self) -> None:
        self.events.subscribe("player_fired", lambda **_: self.audio.play("shoot"))
        self.events.subscribe("enemy_hit", lambda **_: self.audio.play("hit"))
        self.events.subscribe("boss_warning", lambda **_: self.audio.play("warning"))
        self.events.subscribe("upgrade_bought", lambda **_: self.audio.play("purchase"))
        self.events.subscribe("impulse_used", self._on_impulse_used)
        self.events.subscribe("enemy_killed", self._on_enemy_killed)
        self.events.subscribe("player_hit", self._on_player_hit)

    def _on_impulse_used(self, **_: object) -> None:
        self.pulse_visible = 0.35
        self.audio.play("impulse")

    def _on_enemy_killed(self, enemy: Enemy, **_: object) -> None:
        self.score.record_kill(self.time, enemy.points, enemy.currency)
        self.audio.play("explode")

    def _on_player_hit(self, **_: object) -> None:
        self.score.on_player_hit()
        self.flash = 0.18
        self.audio.play("hit")
