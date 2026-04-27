from pathlib import Path
from random import randint
import math

import pygame


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 500
FPS = 60

BACKGROUND_COL = (24, 112, 172)
GROUND_COL = (84, 68, 39)
PLATFORM_COL = (108, 88, 48)
PLAYER_COL = (30, 210, 76)
CIRCLE_COL = (220, 225, 255)
COLLECTIBLE_COL = (220, 46, 46)
TEXT_COL = (255, 255, 255)

PLAYER_WIDTH = 32
PLAYER_HEIGHT = 42
PLAYER_SPEED = 4.0
JUMP_SPEED = -10.5
GRAVITY = 0.35

CIRCLE_RADIUS = 12
COLLECTIBLE_RADIUS = 9
COLLECTIBLE_FALL_SPEED = 1.2
COLLECTIBLE_SPAWN_MS = 900
GAME_TIME_MS = 45_000

ASSETS_DIR = Path(__file__).parent / "assets"
PLAYER_IMAGE_PATH = ASSETS_DIR / "player.png"
JUMP_SOUND_PATH = ASSETS_DIR / "jump.wav"


def player_collides_with(player_rect: pygame.Rect, rect: pygame.Rect) -> bool:
    return player_rect.colliderect(rect)


def spawn_collectible(obstacles: list[pygame.Rect]) -> pygame.Rect:
    x = randint(COLLECTIBLE_RADIUS, SCREEN_WIDTH - COLLECTIBLE_RADIUS)
    collectible = pygame.Rect(0, 0, COLLECTIBLE_RADIUS * 2, COLLECTIBLE_RADIUS * 2)
    collectible.center = (x, -COLLECTIBLE_RADIUS)

    while any(collectible.colliderect(obstacle) for obstacle in obstacles):
        collectible.centerx = randint(COLLECTIBLE_RADIUS, SCREEN_WIDTH - COLLECTIBLE_RADIUS)
    return collectible


def move_and_collide(
    player_rect: pygame.Rect,
    velocity_x: float,
    velocity_y: float,
    obstacles: list[pygame.Rect],
) -> tuple[pygame.Rect, float, bool]:
    on_ground = False

    player_rect.x += round(velocity_x)
    for obstacle in obstacles:
        if player_collides_with(player_rect, obstacle):
            if velocity_x > 0:
                player_rect.right = obstacle.left
            elif velocity_x < 0:
                player_rect.left = obstacle.right

    player_rect.y += round(velocity_y)
    for obstacle in obstacles:
        if player_collides_with(player_rect, obstacle):
            if velocity_y > 0:
                player_rect.bottom = obstacle.top
                velocity_y = 0
                on_ground = True
            elif velocity_y < 0:
                player_rect.top = obstacle.bottom
                velocity_y = 0

    player_rect.left = max(player_rect.left, 0)
    player_rect.right = min(player_rect.right, SCREEN_WIDTH)
    if player_rect.bottom >= SCREEN_HEIGHT:
        player_rect.bottom = SCREEN_HEIGHT
        velocity_y = 0
        on_ground = True
    return player_rect, velocity_y, on_ground


def main() -> None:
    pygame.mixer.pre_init(44_100, -16, 1, 512)
    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Jump & Run")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 26)
    big_font = pygame.font.SysFont(None, 52)

    player_image = pygame.image.load(PLAYER_IMAGE_PATH).convert_alpha()
    jump_sound = pygame.mixer.Sound(JUMP_SOUND_PATH)

    player_rect = player_image.get_rect(topleft=(80, 260))
    player_velocity_y = 0.0
    player_moving_left = False
    player_moving_right = False
    jump_requested = False
    on_ground = False

    circle_x = 520.0
    circle_y = 70.0
    circle_movement_x = 1.8
    circle_movement_y = 0.0

    obstacles = [
        pygame.Rect(0, SCREEN_HEIGHT - 22, SCREEN_WIDTH, 22),
        pygame.Rect(60, 390, 165, 14),
        pygame.Rect(270, 340, 140, 14),
        pygame.Rect(480, 285, 150, 14),
        pygame.Rect(160, 235, 145, 14),
        pygame.Rect(420, 185, 170, 14),
        pygame.Rect(650, 120, 105, 14),
    ]

    collectibles: list[pygame.Rect] = []
    collected = 0
    status = "Wheee!"
    start_time = pygame.time.get_ticks()
    last_collectible_spawn = start_time
    game_over = False
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    player_moving_left = True
                elif event.key == pygame.K_d:
                    player_moving_right = True
                elif event.key in (pygame.K_w, pygame.K_SPACE):
                    jump_requested = True
                elif event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_a:
                    player_moving_left = False
                elif event.key == pygame.K_d:
                    player_moving_right = False

        now = pygame.time.get_ticks()
        remaining_ms = max(0, GAME_TIME_MS - (now - start_time))
        if remaining_ms == 0:
            game_over = True

        if not game_over:
            player_velocity_x = 0.0
            if player_moving_right:
                player_velocity_x += PLAYER_SPEED
            if player_moving_left:
                player_velocity_x -= PLAYER_SPEED

            if jump_requested and on_ground:
                player_velocity_y = JUMP_SPEED
                on_ground = False
                jump_sound.play()
            jump_requested = False

            player_velocity_y += GRAVITY
            player_rect, player_velocity_y, on_ground = move_and_collide(
                player_rect,
                player_velocity_x,
                player_velocity_y,
                obstacles,
            )

            circle_movement_y += GRAVITY * 0.35
            circle_x += circle_movement_x
            circle_y += circle_movement_y

            if circle_y >= SCREEN_HEIGHT - 22 - CIRCLE_RADIUS:
                circle_y = SCREEN_HEIGHT - 22 - CIRCLE_RADIUS
                circle_movement_y = -abs(circle_movement_y) * 0.92
            if circle_x <= CIRCLE_RADIUS or circle_x >= SCREEN_WIDTH - CIRCLE_RADIUS:
                circle_movement_x = -circle_movement_x

            circle_rect = pygame.Rect(0, 0, CIRCLE_RADIUS * 2, CIRCLE_RADIUS * 2)
            circle_rect.center = (round(circle_x), round(circle_y))
            status = "Ouch!" if player_rect.colliderect(circle_rect) else "Wheee!"

            if now - last_collectible_spawn >= COLLECTIBLE_SPAWN_MS:
                collectibles.append(spawn_collectible(obstacles))
                last_collectible_spawn = now

            remaining_collectibles = []
            for collectible in collectibles:
                collectible.y += round(COLLECTIBLE_FALL_SPEED)
                if player_rect.colliderect(collectible):
                    collected += 1
                elif any(collectible.colliderect(obstacle) for obstacle in obstacles):
                    continue
                elif collectible.top <= SCREEN_HEIGHT:
                    remaining_collectibles.append(collectible)
            collectibles = remaining_collectibles

        screen.fill(BACKGROUND_COL)
        for obstacle in obstacles:
            color = GROUND_COL if obstacle.bottom == SCREEN_HEIGHT else PLATFORM_COL
            pygame.draw.rect(screen, color, obstacle)

        pygame.draw.circle(screen, CIRCLE_COL, (round(circle_x), round(circle_y)), CIRCLE_RADIUS)
        for collectible in collectibles:
            pygame.draw.circle(screen, COLLECTIBLE_COL, collectible.center, COLLECTIBLE_RADIUS)

        screen.blit(player_image, player_rect)
        screen.blit(font.render(status, True, TEXT_COL), (24, 22))
        screen.blit(font.render(f"Kugeln: {collected}", True, TEXT_COL), (24, 50))
        screen.blit(font.render(f"Zeit: {math.ceil(remaining_ms / 1000)}", True, TEXT_COL), (24, 78))

        if game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            title = big_font.render("Spielende", True, TEXT_COL)
            score_text = font.render(f"Gesamtpunktzahl: {collected}", True, TEXT_COL)
            screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30)))
            screen.blit(score_text, score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 18)))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
