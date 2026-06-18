"""State machine and simulation orchestration for Signal Breach."""

from pathlib import Path

import pygame

from .audio import AudioManager
from .config import PROFILE_PATH, SCREEN_HEIGHT, SCREEN_WIDTH
from .entities import Boss, Enemy, Player, Projectile
from .levels import SECTORS, SectorRuntime
from .model import Profile, RunStats, ScreenState
from .persistence import load_profile, save_profile
from .scoring import ScoreSystem, UpgradeSystem


SHOP_KEYS = {
    pygame.K_1: "damage",
    pygame.K_2: "fire_rate",
    pygame.K_3: "max_hp",
    pygame.K_4: "shot_speed",
}


class Game:
    def __init__(self, profile_path: Path = PROFILE_PATH, audio: bool = True):
        self.profile_path = Path(profile_path)
        self.profile = load_profile(self.profile_path)
        self.audio = AudioManager(audio and self.profile.sound_enabled)
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

    @property
    def sector_index(self) -> int:
        return self.run.sector_index

    @sector_index.setter
    def sector_index(self, value: int) -> None:
        self.run.sector_index = max(0, min(len(SECTORS) - 1, int(value)))

    @property
    def boss(self) -> Boss | None:
        return next((enemy for enemy in self.enemies if isinstance(enemy, Boss)), None)

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
        self.movement.update(0, 0)
        self.pulse_visible = 0.0
        self.flash = 0.0
        self.state = ScreenState.PLAYING
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
            self.state = ScreenState.WON
            self._finish_run()
        else:
            self.state = ScreenState.SHOP
            self.player_projectiles = []
            self.hostile_projectiles = []
            self._save_profile()

    def toggle_pause(self) -> None:
        if self.state is ScreenState.PLAYING:
            self.state = ScreenState.PAUSED
        elif self.state is ScreenState.PAUSED:
            self.state = ScreenState.PLAYING

    def restart(self) -> None:
        self.state = ScreenState.MENU
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
        removed = self.player.activate_impulse(self.hostile_projectiles)
        if self.player.impulse_cooldown > 0 and (removed or self.pulse_visible <= 0):
            self.pulse_visible = 0.35
            self.audio.play("impulse")
        return removed

    def buy_upgrade(self, name: str) -> bool:
        if self.state is not ScreenState.SHOP:
            return False
        bought = self.upgrades.buy(name)
        self.set_status(self.upgrades.last_message, 2.0)
        if bought:
            self.audio.play("purchase")
        return bought

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

        key = event.key
        if key == pygame.K_f:
            self.fullscreen_requested = True
            return
        if key == pygame.K_m:
            self.profile.sound_enabled = not self.profile.sound_enabled
            self.audio.set_enabled(self.profile.sound_enabled)
            self._save_profile()
            return
        if self.state is ScreenState.MENU:
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.start_run()
            elif key == pygame.K_ESCAPE:
                self.running = False
            return
        if self.state in (ScreenState.PLAYING, ScreenState.PAUSED) and key in (
            pygame.K_p,
            pygame.K_ESCAPE,
        ):
            self.toggle_pause()
            return
        if self.state is ScreenState.PLAYING and key == pygame.K_SPACE:
            self.activate_impulse()
            return
        if self.state is ScreenState.SHOP:
            if key in SHOP_KEYS:
                self.buy_upgrade(SHOP_KEYS[key])
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                self.start_next_sector()
            elif key == pygame.K_ESCAPE:
                self.running = False
            return
        if self.state in (ScreenState.GAME_OVER, ScreenState.WON):
            if key in (pygame.K_r, pygame.K_RETURN):
                self.restart()
            elif key == pygame.K_ESCAPE:
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
            self.audio.play("shoot")

        self.enemies.extend(self.sector.update(dt))
        for enemy in list(self.enemies):
            if isinstance(enemy, Boss):
                shots, summons = enemy.update(dt, self.player.pos)
                self.hostile_projectiles.extend(shots)
                self.enemies.extend(summons)
                if shots and enemy.warning > 0:
                    self.audio.play("warning")
            else:
                self.hostile_projectiles.extend(enemy.update(dt, self.player.pos))

        for projectile in self.player_projectiles:
            projectile.update(dt)
        for projectile in self.hostile_projectiles:
            projectile.update(dt)

        self._resolve_collisions()
        self._cleanup()

        if not self.player.alive:
            self.state = ScreenState.GAME_OVER
            self._finish_run()
            return

        normal_count = sum(1 for enemy in self.enemies if not isinstance(enemy, Boss))
        if self.sector.should_spawn_boss(normal_count):
            self.enemies.append(self.sector.create_boss())
            self.set_status("WARNUNG: Sektorwache erkannt", 3.0)
            self.audio.play("warning")

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
            self.audio.play("hit")
            if killed:
                spawned.extend(target.on_destroyed())
                self.score.record_kill(self.time, target.points, target.currency)
                self.audio.play("explode")

        self.enemies.extend(spawned)
        for projectile in self.hostile_projectiles:
            if (
                projectile.alive
                and self.player.alive
                and projectile.rect.colliderect(self.player.rect)
            ):
                projectile.alive = False
                if self.player.take_damage(projectile.damage):
                    self.score.on_player_hit()
                    self.flash = 0.18
                    self.audio.play("hit")

        for enemy in self.enemies:
            if enemy.alive and enemy.rect.colliderect(self.player.rect):
                if self.player.take_damage(enemy.damage):
                    self.score.on_player_hit()
                    self.flash = 0.18
                    self.audio.play("hit")
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
