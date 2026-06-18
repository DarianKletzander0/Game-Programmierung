"""Runtime-generated sound effects with a silent fallback."""

from math import pi, sin
from struct import pack

import pygame


SAMPLE_RATE = 44_100


def tone(
    frequency: float,
    seconds: float,
    volume: float = 0.18,
    sweep: float = 0.0,
) -> bytes:
    frames = max(1, int(SAMPLE_RATE * max(0.001, seconds)))
    values: list[bytes] = []
    phase = 0.0
    for index in range(frames):
        progress = index / frames
        current_frequency = max(20.0, frequency + sweep * progress)
        phase += 2 * pi * current_frequency / SAMPLE_RATE
        envelope = (1.0 - progress) ** 1.6
        sample = int(32767 * max(0.0, min(1.0, volume)) * envelope * sin(phase))
        values.append(pack("<h", sample))
    return b"".join(values)


class AudioManager:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.available = False
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        if not enabled:
            return
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)
            self.sounds = {
                "shoot": pygame.mixer.Sound(buffer=tone(660, 0.045, 0.06, 220)),
                "hit": pygame.mixer.Sound(buffer=tone(180, 0.08, 0.12, -70)),
                "explode": pygame.mixer.Sound(buffer=tone(105, 0.18, 0.15, -60)),
                "purchase": pygame.mixer.Sound(buffer=tone(520, 0.14, 0.12, 440)),
                "warning": pygame.mixer.Sound(buffer=tone(240, 0.22, 0.12, 0)),
                "impulse": pygame.mixer.Sound(buffer=tone(340, 0.2, 0.14, 500)),
            }
            self.available = True
        except pygame.error:
            self.available = False
            self.sounds = {}

    def play(self, name: str) -> None:
        if self.enabled and self.available and name in self.sounds:
            self.sounds[name].play()

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = bool(enabled)
