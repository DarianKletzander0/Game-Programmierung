"""Validated, atomic JSON persistence for profile statistics and settings."""

import json
from pathlib import Path

from .model import Profile


def load_profile(path: Path) -> Profile:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return Profile()
        return Profile(
            highscore=data.get("highscore", 0),
            best_combo=data.get("best_combo", 0),
            unlocked_sector=data.get("unlocked_sector", 1),
            fullscreen=data.get("fullscreen", False)
            if isinstance(data.get("fullscreen", False), bool)
            else False,
            sound_enabled=data.get("sound_enabled", True)
            if isinstance(data.get("sound_enabled", True), bool)
            else True,
        ).sanitized()
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return Profile()


def save_profile(path: Path, profile: Profile) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    payload = json.dumps(profile.sanitized().to_dict(), indent=2, sort_keys=True)
    temporary.write_text(payload + "\n", encoding="utf-8")
    temporary.replace(path)
