# score.py
# Score, combo, currency, and highscore persistence for Uebung 004.

from pathlib import Path


class ScoreManager:
    """Tracks score, combo bonus, earned currency, and persistent highscore."""

    def __init__(self, highscore_path: str | Path | None = None, combo_window: int = 90):
        if highscore_path is None:
            self.highscore_path: Path | None = Path(__file__).resolve().parent / "highscore.txt"
        else:
            self.highscore_path = Path(highscore_path)

        self.combo_window = combo_window
        self.score = 0
        self.currency = 0
        self.combo = 0
        self._last_kill_frame: int | None = None
        self.highscore = self.load_highscore()

    def load_highscore(self) -> int:
        if self.highscore_path is None or not self.highscore_path.exists():
            return 0

        try:
            return max(0, int(self.highscore_path.read_text(encoding="utf-8").strip() or 0))
        except (OSError, ValueError):
            return 0

    def save_highscore(self) -> None:
        if self.highscore_path is None:
            return

        self.highscore = max(self.highscore, self.score)
        self.highscore_path.write_text(str(self.highscore), encoding="utf-8")

    def start_level(self) -> None:
        """Reset only the time-based combo state for a new level."""
        self.combo = 0
        self._last_kill_frame = None

    def record_kill(self, frame: int, enemy_kind: str = "normal") -> int:
        if enemy_kind == "boss":
            points = 500
            currency = 5
            self.combo = 0
        else:
            if (
                self._last_kill_frame is not None
                and frame - self._last_kill_frame <= self.combo_window
            ):
                self.combo += 1
            else:
                self.combo = 0

            points = 100 + self.combo * 50
            currency = 1

        self.score += points
        self.currency += currency
        self._last_kill_frame = frame
        self.highscore = max(self.highscore, self.score)
        return points
