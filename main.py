"""Signal Breach application entry point.

Run with ``python main.py``. The small compatibility helpers at the top retain
the independently graded state/persistence exercises from the first prototype.
"""

import json
from pathlib import Path
from typing import Any

import pygame

from signal_breach.config import FPS, PROFILE_PATH, SCREEN_HEIGHT, SCREEN_WIDTH
from signal_breach.game import Game
from signal_breach.persistence import save_profile
from signal_breach.rendering import Renderer


# Compatibility API for the earlier root exercise tests.
PLAYER_WIDTH = 32
PLAYER_HEIGHT = 42
GAME_TIME_MS = 45_000
HIGHSCORE_PATH = Path(__file__).parent / "highscore.json"
GameState = dict[str, Any]


def load_highscore(path: Path = HIGHSCORE_PATH) -> int:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return int(data.get("highscore", 0))
    except (FileNotFoundError, OSError, ValueError, TypeError, json.JSONDecodeError):
        return 0


def save_highscore(score: int, path: Path = HIGHSCORE_PATH) -> None:
    path.write_text(json.dumps({"highscore": int(score)}), encoding="utf-8")


def update_highscore(score: int, path: Path = HIGHSCORE_PATH) -> int:
    highscore = load_highscore(path)
    if score > highscore:
        save_highscore(score, path)
        return score
    return highscore


def create_initial_state(
    player_rect: pygame.Rect,
    now_ms: int,
    highscore: int = 0,
) -> GameState:
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


def _create_window(fullscreen: bool) -> pygame.Surface:
    flags = pygame.FULLSCREEN if fullscreen else pygame.RESIZABLE
    size = (0, 0) if fullscreen else (SCREEN_WIDTH, SCREEN_HEIGHT)
    return pygame.display.set_mode(size, flags)


def _canvas_rect(window: pygame.Surface) -> pygame.Rect:
    window_width, window_height = window.get_size()
    scale = min(window_width / SCREEN_WIDTH, window_height / SCREEN_HEIGHT)
    width = max(1, round(SCREEN_WIDTH * scale))
    height = max(1, round(SCREEN_HEIGHT * scale))
    return pygame.Rect(
        (window_width - width) // 2,
        (window_height - height) // 2,
        width,
        height,
    )


def _map_mouse_event(event: pygame.event.Event, target: pygame.Rect) -> pygame.event.Event:
    if event.type != pygame.MOUSEMOTION:
        return event
    x = (event.pos[0] - target.x) * SCREEN_WIDTH / max(1, target.width)
    y = (event.pos[1] - target.y) * SCREEN_HEIGHT / max(1, target.height)
    values = dict(event.dict)
    values["pos"] = (round(x), round(y))
    return pygame.event.Event(event.type, values)


def main() -> None:
    pygame.mixer.pre_init(44_100, -16, 1, 512)
    pygame.init()
    pygame.display.set_caption("Signal Breach")
    game = Game(PROFILE_PATH)
    fullscreen = game.profile.fullscreen
    window = _create_window(fullscreen)
    canvas = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    renderer = Renderer()
    clock = pygame.time.Clock()

    while game.running:
        target = _canvas_rect(window)
        for event in pygame.event.get():
            game.handle_event(_map_mouse_event(event, target))

        if game.consume_fullscreen_request():
            fullscreen = not fullscreen
            game.profile.fullscreen = fullscreen
            save_profile(game.profile_path, game.profile)
            window = _create_window(fullscreen)

        keys = pygame.key.get_pressed()
        horizontal = float(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - float(
            keys[pygame.K_a] or keys[pygame.K_LEFT]
        )
        vertical = float(keys[pygame.K_s] or keys[pygame.K_DOWN]) - float(
            keys[pygame.K_w] or keys[pygame.K_UP]
        )
        game.set_movement(horizontal, vertical)
        game.update(clock.tick(FPS) / 1000.0)
        renderer.draw(canvas, game)

        target = _canvas_rect(window)
        window.fill((0, 0, 0))
        if target.size == canvas.get_size():
            scaled = canvas
        else:
            scaled = pygame.transform.smoothscale(canvas, target.size)
        window.blit(scaled, target)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
