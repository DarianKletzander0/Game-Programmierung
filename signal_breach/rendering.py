"""Procedural rendering for every Signal Breach screen."""

from __future__ import annotations

import math

import pygame

from .config import (
    BACKGROUND,
    BACKGROUND_LIGHT,
    BLUE,
    CYAN,
    GREEN,
    HUD_HEIGHT,
    MAGENTA,
    MUTED,
    ORANGE,
    PANEL,
    RED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WHITE,
    YELLOW,
)
from .entities import Boss, Enemy, Player, Projectile
from .levels import SECTORS
from .model import ScreenState


class Renderer:
    def __init__(self):
        if not pygame.font.get_init():
            pygame.font.init()
        self.title_font = pygame.font.Font(None, 92)
        self.large_font = pygame.font.Font(None, 54)
        self.heading_font = pygame.font.Font(None, 34)
        self.body_font = pygame.font.Font(None, 25)
        self.small_font = pygame.font.Font(None, 20)
        self.tiny_font = pygame.font.Font(None, 16)

    def draw(self, surface: pygame.Surface, game) -> None:
        accent = SECTORS[game.sector_index].accent if game.sector_index < len(SECTORS) else CYAN
        self._draw_background(surface, game.time, accent)
        if game.state is ScreenState.MENU:
            self._draw_menu(surface, game)
            return
        if game.state is ScreenState.SHOP:
            self._draw_shop(surface, game)
            return

        self._draw_world(surface, game)
        self._draw_hud(surface, game)
        if game.state is ScreenState.PAUSED:
            self._draw_overlay(surface, "PAUSE", "P oder ESC zum Fortsetzen", CYAN)
        elif game.state is ScreenState.GAME_OVER:
            self._draw_end_screen(surface, game, won=False)
        elif game.state is ScreenState.WON:
            self._draw_end_screen(surface, game, won=True)
        if game.flash > 0:
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash.fill((*RED, int(100 * min(1.0, game.flash / 0.18))))
            surface.blit(flash, (0, 0))

    def _draw_background(
        self,
        surface: pygame.Surface,
        time: float,
        accent: tuple[int, int, int],
    ) -> None:
        surface.fill(BACKGROUND)
        for y in range(0, SCREEN_HEIGHT, 8):
            ratio = y / SCREEN_HEIGHT
            color = tuple(
                int(BACKGROUND[index] * (1 - ratio) + BACKGROUND_LIGHT[index] * ratio)
                for index in range(3)
            )
            pygame.draw.rect(surface, color, (0, y, SCREEN_WIDTH, 8))

        grid_color = tuple(max(18, value // 7) for value in accent)
        scroll = int(time * 85) % 48
        for y in range(HUD_HEIGHT + scroll, SCREEN_HEIGHT, 48):
            pygame.draw.line(surface, grid_color, (0, y), (SCREEN_WIDTH, y), 1)
        for x in range(0, SCREEN_WIDTH + 1, 80):
            pygame.draw.line(surface, grid_color, (SCREEN_WIDTH // 2, HUD_HEIGHT), (x, SCREEN_HEIGHT), 1)

        for index in range(46):
            x = (index * 157 + 41) % SCREEN_WIDTH
            y = (index * 97 + int(time * (32 + index % 4 * 17))) % (SCREEN_HEIGHT - HUD_HEIGHT) + HUD_HEIGHT
            radius = 1 + (index % 3 == 0)
            pygame.draw.circle(surface, (*accent[:3],), (x, y), radius)

        vignette = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(vignette, (0, 0, 0, 70), vignette.get_rect(), 28, border_radius=24)
        surface.blit(vignette, (0, 0))

    def _draw_menu(self, surface: pygame.Surface, game) -> None:
        center = SCREEN_WIDTH // 2
        self._text(surface, "SIGNAL", self.title_font, WHITE, (center, 150), center=True)
        self._text(surface, "BREACH", self.title_font, CYAN, (center, 222), center=True)
        self._text(
            surface,
            "Stabilisiere drei beschädigte Sektoren des Datennetzes.",
            self.body_font,
            MUTED,
            (center, 286),
            center=True,
        )

        panel = pygame.Rect(190, 330, 580, 230)
        self._panel(surface, panel)
        controls = [
            ("WASD / PFEILE", "Bewegen"),
            ("AUTO-FEUER", "Ziele durch Positionierung"),
            ("LEERTASTE", "Impuls gegen Projektile"),
            ("P / ESC", "Pause"),
            ("F / M", "Vollbild / Ton"),
        ]
        for index, (key, description) in enumerate(controls):
            y = panel.y + 32 + index * 36
            self._text(surface, key, self.small_font, CYAN, (panel.x + 32, y))
            self._text(surface, description, self.small_font, WHITE, (panel.x + 245, y))

        pulse = (math.sin(game.time * 4) + 1) / 2
        button_color = tuple(int(CYAN[i] * (0.75 + pulse * 0.25)) for i in range(3))
        button = pygame.Rect(center - 205, 595, 410, 62)
        pygame.draw.rect(surface, button_color, button, 2, border_radius=10)
        self._text(surface, "ENTER  ·  VERBINDUNG STARTEN", self.heading_font, WHITE, button.center, center=True)
        self._text(
            surface,
            f"HIGHSCORE {game.profile.highscore:06d}   ·   BESTE COMBO x{game.profile.best_combo}",
            self.small_font,
            MUTED,
            (center, 685),
            center=True,
        )

    def _draw_world(self, surface: pygame.Surface, game) -> None:
        for projectile in game.player_projectiles:
            self._draw_projectile(surface, projectile)
        for projectile in game.hostile_projectiles:
            self._draw_projectile(surface, projectile)
        for enemy in game.enemies:
            self._draw_enemy(surface, enemy)
        self._draw_player(surface, game.player)

        if game.pulse_visible > 0:
            progress = 1 - game.pulse_visible / 0.35
            radius = round(35 + progress * 145)
            alpha = round(220 * (1 - progress))
            pulse = pygame.Surface((radius * 2 + 8, radius * 2 + 8), pygame.SRCALPHA)
            pygame.draw.circle(pulse, (*CYAN, alpha), pulse.get_rect().center, radius, 4)
            surface.blit(pulse, pulse.get_rect(center=game.player.pos))

    def _draw_player(self, surface: pygame.Surface, player: Player) -> None:
        x, y = round(player.pos.x), round(player.pos.y)
        if player.invulnerability > 0 and int(player.invulnerability * 12) % 2:
            return
        glow = pygame.Surface((78, 78), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*CYAN, 30), (39, 39), 33)
        surface.blit(glow, glow.get_rect(center=(x, y)))
        points = [(x, y - 24), (x - 18, y + 19), (x, y + 11), (x + 18, y + 19)]
        pygame.draw.polygon(surface, BLUE, points)
        pygame.draw.polygon(surface, CYAN, points, 3)
        pygame.draw.polygon(surface, WHITE, [(x, y - 15), (x - 6, y + 7), (x + 6, y + 7)])
        flame = 12 + round(player.thrust * 9)
        pygame.draw.polygon(surface, ORANGE, [(x - 7, y + 18), (x, y + 18 + flame), (x + 7, y + 18)])

    def _draw_enemy(self, surface: pygame.Surface, enemy: Enemy) -> None:
        x, y = round(enemy.pos.x), round(enemy.pos.y)
        color = WHITE if enemy.hit_flash > 0 else {
            "drifter": MAGENTA,
            "weaver": CYAN,
            "charger": ORANGE,
            "splitter": YELLOW,
            "fragment": GREEN,
            "boss": RED,
        }.get(enemy.kind, MAGENTA)

        if isinstance(enemy, Boss):
            glow = pygame.Surface((140, 140), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*color, 35), (70, 70), 64)
            surface.blit(glow, glow.get_rect(center=(x, y)))
            vertices = [
                (
                    x + math.cos(math.radians(index * 45 + enemy.age * 28)) * enemy.radius,
                    y + math.sin(math.radians(index * 45 + enemy.age * 28)) * enemy.radius,
                )
                for index in range(8)
            ]
            pygame.draw.polygon(surface, PANEL, vertices)
            pygame.draw.polygon(surface, color, vertices, 4)
            pygame.draw.circle(surface, YELLOW if enemy.warning else WHITE, (x, y), 15, 3)
            return

        if enemy.kind == "weaver":
            pygame.draw.polygon(surface, color, [(x, y + 18), (x - 17, y - 12), (x, y - 5), (x + 17, y - 12)])
        elif enemy.kind == "charger":
            pygame.draw.polygon(surface, color, [(x, y + 22), (x - 15, y - 15), (x, y - 8), (x + 15, y - 15)])
        elif enemy.kind == "splitter":
            pygame.draw.rect(surface, color, enemy.rect, 3, border_radius=4)
            pygame.draw.line(surface, color, (x, y - 15), (x, y + 15), 2)
        else:
            pygame.draw.circle(surface, color, (x, y), enemy.radius, 3 if enemy.kind == "fragment" else 0)
            if enemy.kind == "drifter":
                pygame.draw.circle(surface, BACKGROUND, (x, y), max(4, enemy.radius // 2))

    def _draw_projectile(self, surface: pygame.Surface, projectile: Projectile) -> None:
        color = RED if projectile.hostile else CYAN
        end = projectile.pos - projectile.velocity.normalize() * 14 if projectile.velocity else projectile.pos
        pygame.draw.line(surface, color, projectile.pos, end, max(2, projectile.radius))
        pygame.draw.circle(surface, WHITE, projectile.pos, max(2, projectile.radius // 2))

    def _draw_hud(self, surface: pygame.Surface, game) -> None:
        pygame.draw.rect(surface, (5, 14, 30), (0, 0, SCREEN_WIDTH, HUD_HEIGHT))
        pygame.draw.line(surface, SECTORS[game.sector_index].accent, (0, HUD_HEIGHT - 1), (SCREEN_WIDTH, HUD_HEIGHT - 1), 2)
        hp_ratio = game.player.hp / max(1, game.run.player.max_hp)
        self._text(surface, "INTEGRITÄT", self.tiny_font, MUTED, (22, 14))
        bar = pygame.Rect(22, 34, 190, 16)
        pygame.draw.rect(surface, PANEL, bar, border_radius=5)
        pygame.draw.rect(surface, GREEN if hp_ratio > 0.3 else RED, (bar.x, bar.y, round(bar.width * hp_ratio), bar.height), border_radius=5)
        pygame.draw.rect(surface, WHITE, bar, 1, border_radius=5)
        self._text(surface, f"{game.player.hp}/{game.run.player.max_hp}", self.tiny_font, WHITE, (bar.right + 10, bar.y + 1))

        self._text(surface, SECTORS[game.sector_index].name, self.small_font, WHITE, (360, 14), center=True)
        progress = pygame.Rect(285, 39, 150, 8)
        pygame.draw.rect(surface, PANEL, progress, border_radius=4)
        pygame.draw.rect(surface, CYAN, (progress.x, progress.y, round(progress.width * game.sector.progress), progress.height), border_radius=4)

        self._text(surface, f"SCORE {game.run.score:06d}", self.small_font, WHITE, (500, 18))
        self._text(surface, f"DATEN {game.run.currency:02d}", self.small_font, YELLOW, (500, 45))
        combo_color = MAGENTA if game.run.combo > 1 else MUTED
        self._text(surface, f"COMBO x{game.run.combo}", self.small_font, combo_color, (660, 18))

        impulse_ratio = 1 - game.player.impulse_cooldown / 7.0
        self._text(surface, "IMPULS", self.tiny_font, MUTED, (805, 14))
        impulse = pygame.Rect(805, 35, 130, 14)
        pygame.draw.rect(surface, PANEL, impulse, border_radius=4)
        pygame.draw.rect(surface, CYAN, (impulse.x, impulse.y, round(impulse.width * max(0, impulse_ratio)), impulse.height), border_radius=4)

        boss = game.boss
        if boss is not None:
            boss_bar = pygame.Rect(220, 96, 520, 14)
            pygame.draw.rect(surface, PANEL, boss_bar, border_radius=5)
            pygame.draw.rect(surface, RED, (boss_bar.x, boss_bar.y, round(boss_bar.width * boss.hp / boss.max_hp), boss_bar.height), border_radius=5)
            pygame.draw.rect(surface, WHITE, boss_bar, 1, border_radius=5)
            self._text(surface, f"SEKTORWACHE · PHASE {boss.phase}", self.tiny_font, WHITE, (SCREEN_WIDTH // 2, 118), center=True)

        if game.status_timer > 0:
            self._text(surface, game.status_message, self.body_font, WHITE, (SCREEN_WIDTH // 2, 150), center=True)

    def _draw_shop(self, surface: pygame.Surface, game) -> None:
        self._text(surface, "UPGRADE-KNOTEN", self.large_font, WHITE, (SCREEN_WIDTH // 2, 70), center=True)
        self._text(
            surface,
            f"Sektor {game.sector_index + 1} stabilisiert  ·  {game.run.currency} Datenfragmente verfügbar",
            self.body_font,
            YELLOW,
            (SCREEN_WIDTH // 2, 116),
            center=True,
        )

        key_labels = ["1", "2", "3", "4"]
        for index, (name, item, level, cost) in enumerate(game.upgrades.rows()):
            column = index % 2
            row = index // 2
            rect = pygame.Rect(105 + column * 390, 170 + row * 190, 360, 155)
            self._panel(surface, rect)
            affordable = cost is not None and game.run.currency >= cost
            color = CYAN if affordable else MUTED
            pygame.draw.rect(surface, color, rect, 2, border_radius=10)
            self._text(surface, key_labels[index], self.heading_font, color, (rect.x + 28, rect.y + 23))
            self._text(surface, item.label.upper(), self.heading_font, WHITE, (rect.x + 72, rect.y + 22))
            self._text(surface, item.description, self.small_font, MUTED, (rect.x + 28, rect.y + 71))
            price = "MAX" if cost is None else f"KOSTEN {cost}"
            self._text(surface, f"STUFE {level}/{item.max_level}  ·  {price}", self.small_font, color, (rect.x + 28, rect.y + 112))

        self._text(surface, game.upgrades.last_message, self.body_font, WHITE, (SCREEN_WIDTH // 2, 594), center=True)
        self._text(surface, "ENTER  ·  NÄCHSTEN SEKTOR STARTEN", self.heading_font, CYAN, (SCREEN_WIDTH // 2, 655), center=True)

    def _draw_end_screen(self, surface: pygame.Surface, game, won: bool) -> None:
        color = GREEN if won else RED
        title = "NETZWERK STABIL" if won else "VERBINDUNG VERLOREN"
        subtitle = "Alle Sektoren wurden repariert." if won else "Das Reparaturprogramm wurde beendet."
        shade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        shade.fill((2, 8, 20, 220))
        surface.blit(shade, (0, 0))
        self._text(surface, title, self.large_font, color, (SCREEN_WIDTH // 2, 210), center=True)
        self._text(surface, subtitle, self.body_font, WHITE, (SCREEN_WIDTH // 2, 265), center=True)
        panel = pygame.Rect(280, 315, 400, 165)
        self._panel(surface, panel)
        self._text(surface, f"SCORE   {game.run.score:06d}", self.heading_font, WHITE, (panel.centerx, panel.y + 38), center=True)
        self._text(surface, f"BESTE COMBO   x{game.run.best_combo}", self.body_font, MAGENTA, (panel.centerx, panel.y + 83), center=True)
        self._text(surface, f"HIGHSCORE   {game.profile.highscore:06d}", self.body_font, YELLOW, (panel.centerx, panel.y + 122), center=True)
        self._text(surface, "R oder ENTER  ·  ZURÜCK ZUM MENÜ", self.heading_font, CYAN, (SCREEN_WIDTH // 2, 555), center=True)

    def _draw_overlay(
        self,
        surface: pygame.Surface,
        title: str,
        subtitle: str,
        color: tuple[int, int, int],
    ) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((2, 8, 20, 205))
        surface.blit(overlay, (0, 0))
        self._text(surface, title, self.large_font, color, (SCREEN_WIDTH // 2, 310), center=True)
        self._text(surface, subtitle, self.body_font, WHITE, (SCREEN_WIDTH // 2, 370), center=True)

    @staticmethod
    def _panel(surface: pygame.Surface, rect: pygame.Rect) -> None:
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((*PANEL, 225))
        surface.blit(panel, rect)
        pygame.draw.rect(surface, (47, 87, 120), rect, 1, border_radius=10)

    @staticmethod
    def _text(
        surface: pygame.Surface,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        pos: tuple[float, float],
        center: bool = False,
    ) -> None:
        rendered = font.render(text, True, color)
        rect = rendered.get_rect(center=pos) if center else rendered.get_rect(topleft=pos)
        surface.blit(rendered, rect)
