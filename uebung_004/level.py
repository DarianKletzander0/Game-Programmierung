# level.py
# Level loader and manager. Parses .rfg level files, holds enemies and
# obstacles, draws background, and updates spawned enemies.

import os
import re
import pygame
from entity import Entity
from enemy import Enemy, ZigZagEnemy
from boss import BossEnemy
from obstacle import Obstacle
from settings import ASSET_DIR, SCREEN_WIDTH, SCREEN_HEIGHT


class Level(Entity):
    """Loads and manages a level from a .rfg file."""

    def __init__(self):
        super().__init__()
        self.enemies: list[Enemy] = []
        self.obstacles: list[Obstacle] = []
        self.background_image: pygame.Surface | None = None
        self.background_tiles: list[pygame.Surface] = []
        self.background_tile_names: list[str] = []
        self.screen_width = SCREEN_WIDTH
        self.screen_height = SCREEN_HEIGHT

        self.num_tracks = 0
        self.duration = 0
        self.frame = 0
        self.music_name = ""

        self.level_data: list[list[int]] = []

    def load(self, filename: str):
        """Parse a .rfg level file and populate enemies and obstacles."""
        filepath = os.path.join(ASSET_DIR, filename)

        self.pos = pygame.Vector2(0, 0)
        self.dir = pygame.Vector2(0, 1)
        self.frame = 0
        self.enemies = []
        self.obstacles = []
        self.background_tiles = []
        self.background_tile_names = []

        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                if line.startswith("L "):
                    self._parse_level_line(line)
                elif line.startswith("E "):
                    self._parse_enemy_line(line)
                elif line.startswith("BOSS ") or line.startswith("B "):
                    self._parse_boss_line(line)
                elif line.startswith("O "):
                    self._parse_obstacle_line(line)

    def step(self, target_pos: pygame.Vector2 | None = None):
        """Scroll the level, activate enemies, and update ready enemies."""
        self.frame += 1
        if self.background_tiles:
            self.pos.y += self.dir.y
        elif self.background_image and self.pos.y < 0:
            self.pos.y = min(0, self.pos.y + self.dir.y)

        for enemy in self.enemies:
            if self.frame >= enemy.starting_point:
                enemy.ready = True
            if enemy.ready and target_pos is not None:
                enemy.step(target_pos, self.obstacles)

        for obstacle in self.obstacles:
            obstacle.step()

        self.enemies = [enemy for enemy in self.enemies if enemy.is_alive()]

    def draw(self, screen: pygame.Surface):
        """Draw background, obstacles, and active enemies."""
        if self.background_tiles:
            for x, y, tile in self.get_background_tile_positions():
                screen.blit(tile, (x, y))
        elif self.background_image:
            screen.blit(self.background_image, (int(self.pos.x), int(self.pos.y)))

        font = pygame.font.Font(None, 18) if pygame.font.get_init() else None
        for obstacle in self.obstacles:
            obstacle.draw(screen, font)

        for enemy in self.enemies:
            if enemy.ready:
                enemy.draw(screen)

    def get_background_tile_positions(self) -> list[tuple[int, int, pygame.Surface]]:
        """Return repeated background tile positions that cover the screen."""
        if not self.background_tiles:
            return []

        total_height = sum(tile.get_height() for tile in self.background_tiles)
        if total_height <= 0:
            return []

        y = int(self.pos.y) % total_height - total_height
        while y + total_height <= 0:
            y += total_height
        while y > 0:
            y -= total_height

        positions: list[tuple[int, int, pygame.Surface]] = []
        while y < self.screen_height:
            for tile in self.background_tiles:
                positions.append((0, y, tile))
                y += tile.get_height()
                if y >= self.screen_height:
                    break

        return positions

    def _parse_param(self, text: str, key: str) -> str | None:
        """Extract value from a parameter like T(2) or B(background.png)."""
        match = re.search(rf"(?:^|\s){re.escape(key)}\(([^)]*)\)", text)
        return match.group(1) if match else None

    def _parse_level_line(self, line: str):
        """Parse: L T(2) B(background.png) M(Backgnd001music) D(2000)."""
        val = self._parse_param(line, "T")
        if val:
            self.num_tracks = int(val)

        val = self._parse_param(line, "B")
        if val:
            self._load_background_tiles(val)

        val = self._parse_param(line, "M")
        if val:
            self.music_name = val

        val = self._parse_param(line, "D")
        if val:
            self.duration = int(val)

        if self.num_tracks > 0 and self.duration > 0:
            self.level_data = [
                [0] * self.duration for _ in range(self.num_tracks)
            ]

        if self.background_image:
            self.pos.y = -self.background_image.get_height() + SCREEN_HEIGHT
        if self.background_tiles:
            self.pos.y = 0

    def _parse_enemy_line(self, line: str):
        """Create Enemy instances from an enemy line."""
        damage = int(self._parse_param(line, "D") or 1)
        speed = int(self._parse_param(line, "S") or 1)
        anim_prefix = self._parse_param(line, "A") or "enemy"
        variant = (self._parse_param(line, "V") or "normal").lower()
        count = int(self._parse_param(line, "N") or 1)
        track = int(self._parse_param(line, "T") or 0)
        position = int(self._parse_param(line, "P") or 0)

        track_count = max(1, self.num_tracks)
        track_width = SCREEN_WIDTH // track_count
        x = track_width * track + track_width // 2

        for index in range(count):
            enemy = ZigZagEnemy() if variant == "zigzag" else Enemy()
            enemy.setup(
                x=x,
                y=-30 - index * 32,
                dx=0,
                dy=0,
                image_prefix=anim_prefix,
                anim_speed=8,
                hp=2,
                damage=damage,
                speed=speed,
            )
            enemy.starting_point = position
            enemy.ready = position <= 0
            enemy.is_boss = False
            enemy.score_value = 100
            enemy.enemy_type = variant
            self.enemies.append(enemy)

    def _parse_boss_line(self, line: str):
        """Create a BossEnemy from a boss line."""
        damage = int(self._parse_param(line, "D") or 15)
        speed = int(self._parse_param(line, "S") or 1)
        hp = int(self._parse_param(line, "HP") or 8)
        anim_prefix = self._parse_param(line, "A") or "enemy"
        track = int(self._parse_param(line, "T") or max(0, self.num_tracks // 2))
        position = int(self._parse_param(line, "P") or max(0, self.duration - 250))

        track_count = max(1, self.num_tracks)
        track_width = SCREEN_WIDTH // track_count
        x = track_width * track + track_width // 2

        boss = BossEnemy()
        boss.setup(
            x=x,
            y=-80,
            dx=0,
            dy=0,
            image_prefix=anim_prefix,
            anim_speed=8,
            hp=hp,
            damage=damage,
            speed=speed,
        )
        boss.starting_point = position
        boss.ready = position <= 0
        self.enemies.append(boss)

    def _parse_obstacle_line(self, line: str):
        """Create Obstacle objects from an obstacle line."""
        track = int(self._parse_param(line, "T") or 0)
        duration_start = int(self._parse_param(line, "D") or 0)
        length = int(self._parse_param(line, "L") or 0)
        width = int(self._parse_param(line, "W") or 5)

        color_str = self._parse_param(line, "C") or "255,255,255"
        color_parts = color_str.split(",")
        color = (
            int(color_parts[0]),
            int(color_parts[1]),
            int(color_parts[2]),
        )

        obstacle = Obstacle(
            track=track,
            duration_start=duration_start,
            length=length,
            color=color,
            width=width,
            effect="upgrade" if track % 2 == 0 else "downgrade",
        )

        if self.num_tracks > 0:
            track_width = SCREEN_WIDTH // self.num_tracks
            obstacle_x = track_width * (track + 1)
            obstacle.x1 = obstacle_x - width // 2
            obstacle.x2 = obstacle_x + width // 2
            obstacle.y1 = -duration_start
            obstacle.y2 = -duration_start + length

        self.obstacles.append(obstacle)

    def _load_background_tiles(self, value: str):
        """Load one or more background images and turn them into repeatable tiles."""
        names = [name.strip() for name in value.split(",") if name.strip()]
        loaded: list[pygame.Surface] = []
        loaded_names: list[str] = []

        for bg_name in names:
            if not os.path.splitext(bg_name)[1]:
                bg_name += ".png"
            bg_path = os.path.join(ASSET_DIR, bg_name)
            try:
                loaded.append(pygame.image.load(bg_path).convert())
                loaded_names.append(bg_name)
            except pygame.error:
                print(f"Warning: could not load background {bg_path}")

        if not loaded:
            return

        self.background_image = loaded[0]
        self.background_tile_names = loaded_names
        self.background_tiles = []
        for image in loaded:
            self.background_tiles.extend(self._split_background_into_tiles(image))

    def _split_background_into_tiles(self, image: pygame.Surface) -> list[pygame.Surface]:
        tile_height = min(max(120, SCREEN_HEIGHT // 2), image.get_height())
        tiles: list[pygame.Surface] = []
        for y in range(0, image.get_height(), tile_height):
            height = min(tile_height, image.get_height() - y)
            tile = pygame.Surface((SCREEN_WIDTH, height)).convert()
            tile.blit(image, (0, 0), pygame.Rect(0, y, SCREEN_WIDTH, height))
            tiles.append(tile)
        return tiles
