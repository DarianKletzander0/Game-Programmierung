# obstacle.py
# Obstacles block enemies and can apply one-time player effects.

import pygame

MIN_PICKUP_WIDTH = 96
MIN_PICKUP_HEIGHT = 48


class Obstacle:
    """Obstacle parsed from .rfg level files."""

    def __init__(
        self,
        track: int = 0,
        duration_start: int = 0,
        length: int = 0,
        color: tuple[int, int, int] = (255, 255, 255),
        width: int = 5,
        effect: str = "upgrade",
    ):
        self.track = track
        self.duration_start = duration_start
        self.length = length
        self.color = color
        self.width = width
        self.effect = effect
        self.applied = False

        self.x1 = 0
        self.x2 = 0
        self.y1 = 0
        self.y2 = 0
        self.speed_y = 1

    def get_rect(self) -> pygame.Rect:
        raw_rect = pygame.Rect(self.x1, self.y1, self.x2 - self.x1, self.y2 - self.y1)
        width = max(raw_rect.width, MIN_PICKUP_WIDTH)
        height = max(raw_rect.height, MIN_PICKUP_HEIGHT)
        rect = pygame.Rect(0, 0, width, height)
        rect.center = raw_rect.center
        return rect

    def step(self) -> None:
        self.y1 += self.speed_y
        self.y2 += self.speed_y

    def collides_with(self, rect: pygame.Rect) -> bool:
        return self.get_rect().colliderect(rect)

    def apply_to_player(self, player) -> bool:
        """Apply this obstacle's effect once. Returns True when applied."""
        if self.applied:
            return False

        if self.effect == "upgrade":
            player.set_might(
                rng=player.rng + 50,
                dmg=player.dmg + 1,
                cad=max(10, player.cad - 10),
                shotspd=player.shotspd + 1,
            )
            player.status_message = "Upgrade collected: weapon improved"
        elif self.effect == "downgrade":
            player.hp = max(0, player.hp - 10)
            player.status_message = "Downgrade hit: -10 HP"
        else:
            return False

        self.applied = True
        return True

    def get_label(self) -> str:
        if self.applied:
            return "USED"
        return "UP" if self.effect == "upgrade" else "DOWN"

    def draw(self, screen: pygame.Surface, font: pygame.font.Font | None = None):
        rect = self.get_rect()
        color = (80, 80, 80) if self.applied else self.color
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, (255, 255, 255), rect, 2)

        if font is None:
            return

        text = font.render(self.get_label(), True, (255, 255, 255))
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)
