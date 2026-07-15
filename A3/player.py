# player.py
# Player entity — follows mouse X, auto-fires shots.

import pygame
from entity import Entity
from shot import Shot
from settings import SCREEN_WIDTH


class Player(Entity):
    """The player ship. Follows mouse X position and auto-fires shots."""

    def __init__(self):
        super().__init__()
        self.shots: list[Shot] = []   # Active shots

        # Weapon stats (matching C++ defaults)
        self.rng = 100      # Shot range in frames
        self.dmg = 1        # Damage per shot
        self.cad = 50       # Cadence: frames between shots
        self.shotspd = 1    # Shot speed (pixels per frame, upward)

        self._cad_counter = 0   # Countdown to next shot
        self.status_message = ""

    # ------------------------------------------------------------------ #
    #  setup — place player near bottom of screen                        #
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
        """Initialize the player."""
        super().setup(x, y, dx, dy, image_prefix, anim_speed, hp)
        self._cad_counter = self.cad

    # ------------------------------------------------------------------ #
    #  set_might — configure weapon stats (mirrors C++ setMight)         #
    # ------------------------------------------------------------------ #
    def set_might(self, rng: int, dmg: int, cad: int, shotspd: int):
        """Configure weapon stats. Called from main after setup."""
        self.rng = rng
        self.dmg = dmg
        self.cad = cad
        self.shotspd = shotspd
        self._cad_counter = cad

    def move_to_x(self, x: float, screen_width: int = SCREEN_WIDTH):
        """Move horizontally while keeping the full player sprite visible."""
        half_width = self.hitbox_w / 2
        self.pos.x = max(half_width, min(x, screen_width - half_width))

    # ------------------------------------------------------------------ #
    #  step — move, track mouse X, fire shots, update shots              #
    # ------------------------------------------------------------------ #
    def step(self):
        """Per-frame update: move, fire when cadence allows, update shots."""
        # Move by direction (in case dir is set)
        super().step()

        # Player X follows mouse X position
        mouse_x, _ = pygame.mouse.get_pos()
        self.move_to_x(mouse_x)

        # Cadence countdown — fire a shot when it reaches 0
        self._cad_counter -= 1
        if self._cad_counter <= 0:
            self._cad_counter = self.cad
            self.create_shot()

        # Step all active shots
        for shot in self.shots:
            shot.step()

        # Remove dead shots
        self.shots = [s for s in self.shots if s.is_alive()]

    # ------------------------------------------------------------------ #
    #  create_shot — spawn a new shot above the player                   #
    # ------------------------------------------------------------------ #
    def create_shot(self):
        """Create a shot 10px above the player, moving upward."""
        shot = Shot()
        shot.setup(
            x=self.pos.x,
            y=self.pos.y - 10,      # 10 px above player
            dx=0,
            dy=-self.shotspd,        # Moving upward (negative Y)
            image_prefix="Shot",
            anim_speed=1,
            hp=1,
            rng=self.rng,
            dmg=self.dmg,
        )
        self.shots.append(shot)

    # ------------------------------------------------------------------ #
    #  draw — draw player and all shots                                  #
    # ------------------------------------------------------------------ #
    def draw(self, screen: pygame.Surface):
        """Draw the player and all active shots."""
        # Draw shots first (behind player)
        for shot in self.shots:
            shot.draw(screen)
        # Draw player
        super().draw(screen)
