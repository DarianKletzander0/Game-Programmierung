# enemy.py
# Enemy class with movement, damage, and collision-ready hitbox.

import pygame
from entity import Entity


class Enemy(Entity):
    """Enemy entity that moves toward the player and deals contact damage."""

    def __init__(self):
        super().__init__()
        self.damage = 0
        self.speed = 1
        self.starting_point = 0
        self.ready = False
        self.alive = True

    def setup(
        self,
        x: float,
        y: float,
        dx: float,
        dy: float,
        image_prefix: str,
        anim_speed: int,
        hp: int,
        damage: int = 1,
        speed: int = 1,
    ):
        """Initialize enemy with position, images, damage, and speed."""
        super().setup(x, y, dx, dy, image_prefix, anim_speed, hp)
        self.damage = damage
        self.speed = speed
        self.ready = False
        self.alive = True

    def step(self, target_pos: pygame.Vector2, obstacles: list | None = None):
        """Move toward target_pos and stop if the new hitbox hits an obstacle."""
        if not self.alive:
            return

        direction = target_pos - self.pos
        if direction.length_squared() == 0:
            self.dir = pygame.Vector2(0, 0)
            return

        old_pos = self.pos.copy()
        self.dir = direction.normalize() * self.speed
        self.pos += self.dir

        if obstacles and any(self.get_rect().colliderect(obstacle.get_rect()) for obstacle in obstacles):
            self.pos = old_pos
            self.dir = pygame.Vector2(0, 0)

    def is_alive(self) -> bool:
        """Return True while the enemy has HP and was not despawned."""
        if self.hp <= 0:
            self.alive = False
        return self.alive
