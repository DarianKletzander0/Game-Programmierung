# shot.py
# Projectile fired by the player.

import pygame
from entity import Entity


class Shot(Entity):
    """A projectile with limited lifetime (range) and damage."""

    def __init__(self):
        super().__init__()
        self.life = 0       # Frames remaining before the shot dies
        self.rng = 0        # Range (initial life value)
        self.dmg = 0        # Damage dealt on hit

    # ------------------------------------------------------------------ #
    #  setup — initialize shot with position, direction, range, damage   #
    # ------------------------------------------------------------------ #
    def setup(
        self,
        x: float,
        y: float,
        dx: float,
        dy: float,
        image_prefix: str,
        anim_speed: int,
        hp: int,
        rng: int = 100,
        dmg: int = 1,
    ):
        """Set up the shot. Range determines lifetime in frames."""
        super().setup(x, y, dx, dy, image_prefix, anim_speed, hp)
        self.rng = rng
        self.dmg = dmg
        self.life = rng

        # Set hitbox to image dimensions (matches C++ behavior)
        if self.images:
            rect = self.images[0].get_rect()
            self.hitbox_w = rect.width
            self.hitbox_h = rect.height

    # ------------------------------------------------------------------ #
    #  step — move and decrement lifetime                                #
    # ------------------------------------------------------------------ #
    def step(self):
        """Move the shot and reduce its remaining life."""
        super().step()
        self.life -= 1

    # ------------------------------------------------------------------ #
    #  is_alive — check if shot still has life remaining                 #
    # ------------------------------------------------------------------ #
    def is_alive(self) -> bool:
        """Return True if the shot has life remaining."""
        return self.life > 0
