# entity.py
# Base class for all game objects.

import pygame
import os
import glob
from settings import ASSET_DIR


class Entity:
    """Base class with position, direction, HP, animation, and hitbox."""

    def __init__(self):
        self.pos = pygame.Vector2(0, 0)       # Position (center of sprite)
        self.dir = pygame.Vector2(0, 0)       # Velocity per frame
        self.hp = 0                           # Hit points

        self.hitbox_w = 0                     # Hitbox width
        self.hitbox_h = 0                     # Hitbox height

        # Animation
        self.images: list[pygame.Surface] = []  # Animation frames
        self.anim_pos = 0                       # Current frame index
        self.anim_speed = 10                    # Frames between animation updates
        self.anim_speed_var = 0                 # Counter for animation timing

    # ------------------------------------------------------------------ #
    #  setup — initialize entity with position, direction, images, etc.  #
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
    ):
        """Initialize the entity. image_prefix loads all matching files
        like 'player_stage001.png', 'player_stage002.png', etc."""
        self.pos = pygame.Vector2(x, y)
        self.dir = pygame.Vector2(dx, dy)
        self.hp = hp
        self.anim_speed = anim_speed
        self.anim_speed_var = anim_speed  # C++ initializes to anim_speed, counts down
        self.anim_pos = 0

        # Load animation frames matching the prefix pattern.
        # The C++ code loads files like <prefix>001.png, <prefix>002.png, ...
        self.images = self._load_images(image_prefix)

        # Set hitbox to first image dimensions (if any images loaded)
        if self.images:
            rect = self.images[0].get_rect()
            self.hitbox_w = rect.width
            self.hitbox_h = rect.height

    # ------------------------------------------------------------------ #
    #  step — advance position by direction vector                       #
    # ------------------------------------------------------------------ #
    def step(self):
        """Move entity by its direction vector. Called once per frame."""
        self.pos += self.dir

    # ------------------------------------------------------------------ #
    #  draw — render current animation frame, advance animation counter  #
    # ------------------------------------------------------------------ #
    def draw(self, screen: pygame.Surface):
        """Draw the current animation frame centered on pos."""
        if not self.images:
            return

        image = self.images[self.anim_pos]
        # Draw centered on pos
        rect = image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        screen.blit(image, rect)

        # Advance animation counter
        self.anim_speed_var += 1
        if self.anim_speed_var >= self.anim_speed:
            self.anim_speed_var = 0
            self.anim_pos = (self.anim_pos + 1) % len(self.images)

    # ------------------------------------------------------------------ #
    #  get_rect — return a pygame.Rect for collision detection           #
    # ------------------------------------------------------------------ #
    def get_rect(self) -> pygame.Rect:
        """Return the hitbox as a Rect centered on pos."""
        return pygame.Rect(
            self.pos.x - self.hitbox_w / 2,
            self.pos.y - self.hitbox_h / 2,
            self.hitbox_w,
            self.hitbox_h,
        )

    # ------------------------------------------------------------------ #
    #  _load_images — find and load numbered animation frames            #
    # ------------------------------------------------------------------ #
    def _load_images(self, prefix: str) -> list[pygame.Surface]:
        """Load all images matching <ASSET_DIR>/<prefix>*.png, sorted."""
        pattern = os.path.join(ASSET_DIR, f"{prefix}*.png")
        files = sorted(glob.glob(pattern))
        surfaces = []
        for f in files:
            try:
                surfaces.append(pygame.image.load(f).convert_alpha())
            except pygame.error:
                print(f"Warning: could not load image {f}")
        return surfaces
