from pathlib import Path
from random import randint
from typing import Any
import json
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
HIGHSCORE_PATH = Path(__file__).parent / "highscore.json"

GameState = dict[str, Any]


def player_collides_with(player_rect: pygame.Rect, rect: pygame.Rect) -> bool:
    return player_rect.colliderect(rect)


def spawn_collectible(obstacles: list[pygame.Rect]) -> pygame.Rect:
    x = randint(COLLECTIBLE_RADIUS, SCREEN_WIDTH - COLLECTIBLE_RADIUS)
    collectible = pygame.Rect(0, 0, COLLECTIBLE_RADIUS * 2, COLLECTIBLE_RADIUS * 2)
    collectible.center = (x, -COLLECTIBLE_RADIUS)

    while any(collectible.colliderect(obstacle) for obstacle in obstacles):
        collectible.centerx = randint(COLLECTIBLE_RADIUS, SCREEN_WIDTH - COLLECTIBLE_RADIUS)
    return collectible


def load_highscore(path: Path = HIGHSCORE_PATH) -> int:
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return 0
    return int(data.get("highscore", 0))


def save_highscore(score: int, path: Path = HIGHSCORE_PATH) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump({"highscore": score}, file)


def update_highscore(score: int, path: Path = HIGHSCORE_PATH) -> int:
    highscore = load_highscore(path)
    if score > highscore:
        save_highscore(score, path)
        return score
    return highscore


def create_initial_state(player_rect: pygame.Rect, now_ms: int, highscore: int = 0) -> GameState:
    return {
        "player_rect": player_rect,
        "player_velocity_y": 0.0,
        "player_moving_left": False,
        "player_moving_right": False,
        "jump_requested": False,
        "on_ground": False,
        "circle_x": 520.0,
        "circle_y": 70.0,
        "circle_movement_x": 1.8,
        "circle_movement_y": 0.0,
        "collectibles": [],
        "collected": 0,
        "highscore": highscore,
        "highscore_saved": False,
        "status": "Wheee!",
        "start_time": now_ms,
        "last_collectible_spawn": now_ms,
        "game_over": False,
        "remaining_ms": GAME_TIME_MS,
        "running": True,
    }


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


def handle_event(event: pygame.event.Event, state: GameState) -> None:
    if event.type == pygame.QUIT:
        state["running"] = False
    elif event.type == pygame.KEYDOWN:
        if event.key == pygame.K_a:
            state["player_moving_left"] = True
        elif event.key == pygame.K_d:
            state["player_moving_right"] = True
        elif event.key in (pygame.K_w, pygame.K_SPACE):
            state["jump_requested"] = True
        elif event.key == pygame.K_ESCAPE:
            state["running"] = False
    elif event.type == pygame.KEYUP:
        if event.key == pygame.K_a:
            state["player_moving_left"] = False
        elif event.key == pygame.K_d:
            state["player_moving_right"] = False


def update_state(
    state: GameState,
    now_ms: int,
    obstacles: list[pygame.Rect],
    jump_sound: pygame.mixer.Sound,
    highscore_path: Path = HIGHSCORE_PATH,
) -> None:
    remaining_ms = max(0, GAME_TIME_MS - (now_ms - state["start_time"]))
    state["remaining_ms"] = remaining_ms
    if remaining_ms == 0:
        state["game_over"] = True
        if not state["highscore_saved"]:
            state["highscore"] = update_highscore(state["collected"], highscore_path)
            state["highscore_saved"] = True

    if state["game_over"]:
        return

    player_velocity_x = 0.0
    if state["player_moving_right"]:
        player_velocity_x += PLAYER_SPEED
    if state["player_moving_left"]:
        player_velocity_x -= PLAYER_SPEED

    if state["jump_requested"] and state["on_ground"]:
        state["player_velocity_y"] = JUMP_SPEED
        state["on_ground"] = False
        jump_sound.play()
    state["jump_requested"] = False

    state["player_velocity_y"] += GRAVITY
    player_rect, player_velocity_y, on_ground = move_and_collide(
        state["player_rect"],
        player_velocity_x,
        state["player_velocity_y"],
        obstacles,
    )
    state["player_rect"] = player_rect
    state["player_velocity_y"] = player_velocity_y
    state["on_ground"] = on_ground

    state["circle_movement_y"] += GRAVITY * 0.35
    state["circle_x"] += state["circle_movement_x"]
    state["circle_y"] += state["circle_movement_y"]

    if state["circle_y"] >= SCREEN_HEIGHT - 22 - CIRCLE_RADIUS:
        state["circle_y"] = SCREEN_HEIGHT - 22 - CIRCLE_RADIUS
        state["circle_movement_y"] = -abs(state["circle_movement_y"]) * 0.92
    if state["circle_x"] <= CIRCLE_RADIUS or state["circle_x"] >= SCREEN_WIDTH - CIRCLE_RADIUS:
        state["circle_movement_x"] = -state["circle_movement_x"]

    circle_rect = pygame.Rect(0, 0, CIRCLE_RADIUS * 2, CIRCLE_RADIUS * 2)
    circle_rect.center = (round(state["circle_x"]), round(state["circle_y"]))
    state["status"] = "Ouch!" if state["player_rect"].colliderect(circle_rect) else "Wheee!"

    if now_ms - state["last_collectible_spawn"] >= COLLECTIBLE_SPAWN_MS:
        state["collectibles"].append(spawn_collectible(obstacles))
        state["last_collectible_spawn"] = now_ms

    remaining_collectibles = []
    for collectible in state["collectibles"]:
        collectible.y += round(COLLECTIBLE_FALL_SPEED)
        if state["player_rect"].colliderect(collectible):
            state["collected"] += 1
        elif any(collectible.colliderect(obstacle) for obstacle in obstacles):
            continue
        elif collectible.top <= SCREEN_HEIGHT:
            remaining_collectibles.append(collectible)
    state["collectibles"] = remaining_collectibles


def draw_state(
    screen: pygame.Surface,
    font: pygame.font.Font,
    big_font: pygame.font.Font,
    player_image: pygame.Surface,
    obstacles: list[pygame.Rect],
    state: GameState,
) -> None:
    screen.fill(BACKGROUND_COL)
    for obstacle in obstacles:
        color = GROUND_COL if obstacle.bottom == SCREEN_HEIGHT else PLATFORM_COL
        pygame.draw.rect(screen, color, obstacle)

    pygame.draw.circle(screen, CIRCLE_COL, (round(state["circle_x"]), round(state["circle_y"])), CIRCLE_RADIUS)
    for collectible in state["collectibles"]:
        pygame.draw.circle(screen, COLLECTIBLE_COL, collectible.center, COLLECTIBLE_RADIUS)

    screen.blit(player_image, state["player_rect"])
    screen.blit(font.render(state["status"], True, TEXT_COL), (24, 22))
    screen.blit(font.render(f"Kugeln: {state['collected']}", True, TEXT_COL), (24, 50))
    screen.blit(font.render(f"Highscore: {state['highscore']}", True, TEXT_COL), (24, 78))
    screen.blit(font.render(f"Zeit: {math.ceil(state['remaining_ms'] / 1000)}", True, TEXT_COL), (24, 106))

    if state["game_over"]:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        title = big_font.render("Spielende", True, TEXT_COL)
        score_text = font.render(f"Gesamtpunktzahl: {state['collected']}", True, TEXT_COL)
        highscore_text = font.render(f"Highscore: {state['highscore']}", True, TEXT_COL)
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 48)))
        screen.blit(score_text, score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))
        screen.blit(highscore_text, highscore_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30)))


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

    obstacles = [
        pygame.Rect(0, SCREEN_HEIGHT - 22, SCREEN_WIDTH, 22),
        pygame.Rect(60, 390, 165, 14),
        pygame.Rect(270, 340, 140, 14),
        pygame.Rect(480, 285, 150, 14),
        pygame.Rect(160, 235, 145, 14),
        pygame.Rect(420, 185, 170, 14),
        pygame.Rect(650, 120, 105, 14),
    ]

    start_time = pygame.time.get_ticks()
    state = create_initial_state(
        player_image.get_rect(topleft=(80, 260)),
        start_time,
        load_highscore(),
    )

    while state["running"]:
        for event in pygame.event.get():
            handle_event(event, state)

        update_state(state, pygame.time.get_ticks(), obstacles, jump_sound)
        draw_state(screen, font, big_font, player_image, obstacles, state)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
