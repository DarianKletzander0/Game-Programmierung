# boss.py
# Boss enemy type for Uebung 004.

import math
import pygame
from enemy import Enemy
from settings import SCREEN_WIDTH, SCREEN_HEIGHT


class BossProjectile:
    """Visible projectile used by the boss special attack."""

    def __init__(
        self,
        x: float,
        y: float,
        velocity: pygame.Vector2,
        damage: int,
    ):
        self.pos = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(velocity)
        self.damage = damage
        self.radius = 7
        self.alive = True

    def step(self) -> None:
        self.pos += self.velocity
        margin = 30
        if (
            self.pos.x < -margin
            or self.pos.x > SCREEN_WIDTH + margin
            or self.pos.y < -margin
            or self.pos.y > SCREEN_HEIGHT + margin
        ):
            self.alive = False

    def get_rect(self) -> pygame.Rect:
        diameter = self.radius * 2
        return pygame.Rect(
            self.pos.x - self.radius,
            self.pos.y - self.radius,
            diameter,
            diameter,
        )

    def draw(self, screen: pygame.Surface) -> None:
        center = (round(self.pos.x), round(self.pos.y))
        pygame.draw.circle(screen, (255, 92, 74), center, self.radius)
        pygame.draw.circle(screen, (255, 225, 120), center, self.radius, 2)


class BossEnemy(Enemy):
    """Large enemy with more HP, strafing movement, and hit feedback."""

    def __init__(self):
        super().__init__()
        self.is_boss = True
        self.max_hp = 1
        self.phase = 0
        self.hit_flash_frames = 0
        self.score_value = 500
        self.shots: list[BossProjectile] = []
        self.attack_interval = 90
        self.attack_cooldown = self.attack_interval

    def setup(
        self,
        x: float,
        y: float,
        dx: float,
        dy: float,
        image_prefix: str,
        anim_speed: int,
        hp: int,
        damage: int = 10,
        speed: int = 1,
    ):
        super().setup(x, y, dx, dy, image_prefix, anim_speed, hp, damage, speed)
        self.max_hp = hp
        self.is_boss = True
        self.score_value = 500
        self.shots = []
        self.attack_cooldown = self.attack_interval
        self._scale_images()

    def step(self, target_pos: pygame.Vector2, obstacles: list | None = None):
        if not self.alive:
            return

        self.phase += 1
        if self.pos.y < 130:
            self.pos.y += self.speed
        else:
            self.pos.x += math.sin(self.phase / 24) * max(1, self.speed)
            self.pos.x = max(self.hitbox_w / 2, min(SCREEN_WIDTH - self.hitbox_w / 2, self.pos.x))

        self.attack_cooldown -= 1
        if self.attack_cooldown <= 0:
            self.fire_special_attack(target_pos)
            self.attack_cooldown = self.attack_interval

        for shot in self.shots:
            shot.step()
        self.shots = [shot for shot in self.shots if shot.alive]

        if self.hit_flash_frames > 0:
            self.hit_flash_frames -= 1

    def take_damage(self, amount: int) -> bool:
        self.hp = max(0, self.hp - amount)
        self.hit_flash_frames = 8
        if self.hp <= 0:
            self.alive = False
        return not self.alive

    def draw(self, screen: pygame.Surface):
        for shot in self.shots:
            shot.draw(screen)

        super().draw(screen)

        rect = self.get_rect()
        outline = (255, 240, 90) if self.hit_flash_frames else (220, 70, 70)
        pygame.draw.rect(screen, outline, rect.inflate(8, 8), 2)

        bar_width = max(80, rect.width)
        bar_rect = pygame.Rect(0, 0, bar_width, 8)
        bar_rect.center = (rect.centerx, rect.top - 14)
        pygame.draw.rect(screen, (45, 45, 45), bar_rect)
        fill = int(bar_width * (self.hp / max(1, self.max_hp)))
        pygame.draw.rect(screen, (230, 65, 65), (bar_rect.x, bar_rect.y, fill, bar_rect.height))
        pygame.draw.rect(screen, (255, 255, 255), bar_rect, 1)

    def fire_special_attack(self, target_pos: pygame.Vector2) -> None:
        direction = pygame.Vector2(target_pos) - self.pos
        if direction.length_squared() == 0:
            direction = pygame.Vector2(0, 1)
        base_velocity = direction.normalize() * 4
        projectile_damage = max(5, self.damage // 2)
        for angle in (-18, 0, 18):
            self.shots.append(
                BossProjectile(
                    self.pos.x,
                    self.pos.y + self.hitbox_h / 2,
                    base_velocity.rotate(angle),
                    projectile_damage,
                )
            )

    def _scale_images(self) -> None:
        if not self.images:
            self.hitbox_w = 72
            self.hitbox_h = 72
            return

        scaled_images = []
        for image in self.images:
            width = max(48, image.get_width() * 2)
            height = max(48, image.get_height() * 2)
            scaled_images.append(pygame.transform.smoothscale(image, (width, height)))

        self.images = scaled_images
        rect = self.images[0].get_rect()
        self.hitbox_w = rect.width
        self.hitbox_h = rect.height
