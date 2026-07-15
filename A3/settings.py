# settings.py
# Game constants and configuration.

import os

# Screen dimensions
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 800
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Asset path (relative to main.py)
ASSET_DIR = os.path.join(os.path.dirname(__file__), "assets")
