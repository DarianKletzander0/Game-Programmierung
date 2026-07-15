"""Shared constants for simulation, presentation, and persistence."""

from pathlib import Path


SCREEN_WIDTH = 960
SCREEN_HEIGHT = 720
HUD_HEIGHT = 82
FPS = 60

ROOT_DIR = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT_DIR / "signal_breach_profile.json"

BACKGROUND = (7, 17, 38)
BACKGROUND_LIGHT = (12, 34, 63)
CYAN = (65, 238, 255)
BLUE = (74, 132, 255)
MAGENTA = (255, 75, 194)
ORANGE = (255, 159, 67)
YELLOW = (255, 231, 105)
GREEN = (83, 231, 139)
RED = (255, 83, 105)
WHITE = (236, 247, 255)
MUTED = (139, 167, 190)
PANEL = (10, 27, 52)

PLAYER_SPEED = 390.0
PLAYER_RADIUS = 18
PLAYER_INVULNERABILITY = 0.8
IMPULSE_RADIUS = 150.0
IMPULSE_COOLDOWN = 7.0
