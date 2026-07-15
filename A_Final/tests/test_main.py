from pathlib import Path
import tempfile
import unittest

import pygame

import main


class MainStateTests(unittest.TestCase):
    def test_create_initial_state_bundles_game_values_in_one_dict(self) -> None:
        player_rect = pygame.Rect(80, 260, main.PLAYER_WIDTH, main.PLAYER_HEIGHT)

        state = main.create_initial_state(player_rect, now_ms=1_000)

        self.assertEqual(state["player_rect"], player_rect)
        self.assertEqual(state["player_velocity_y"], 0.0)
        self.assertIs(state["player_moving_left"], False)
        self.assertIs(state["player_moving_right"], False)
        self.assertIs(state["jump_requested"], False)
        self.assertIs(state["on_ground"], False)
        self.assertEqual(state["circle_x"], 520.0)
        self.assertEqual(state["circle_y"], 70.0)
        self.assertEqual(state["collectibles"], [])
        self.assertEqual(state["collected"], 0)
        self.assertEqual(state["status"], "Wheee!")
        self.assertEqual(state["start_time"], 1_000)
        self.assertEqual(state["last_collectible_spawn"], 1_000)
        self.assertIs(state["game_over"], False)

    def test_canvas_rect_preserves_aspect_ratio(self) -> None:
        cases = [
            ((960, 720), (0, 0, 960, 720)),
            ((1920, 1080), (240, 0, 1440, 1080)),
            ((600, 900), (0, 225, 600, 450)),
        ]

        for surface_size, expected_rect in cases:
            with self.subTest(surface_size=surface_size):
                surface = pygame.Surface(surface_size)
                self.assertEqual(tuple(main._canvas_rect(surface)), expected_rect)

    def test_mouse_position_is_mapped_to_virtual_canvas(self) -> None:
        target = pygame.Rect(240, 0, 1440, 1080)
        event = pygame.event.Event(
            pygame.MOUSEMOTION,
            pos=target.center,
            rel=(0, 0),
            buttons=(False, False, False),
        )

        mapped = main._map_mouse_event(event, target)

        self.assertEqual(mapped.pos, (480, 360))


class HighscoreTests(unittest.TestCase):
    def test_load_highscore_returns_zero_when_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            self.assertEqual(main.load_highscore(Path(temp_dir) / "missing.json"), 0)

    def test_save_and_load_highscore_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "highscore.json"

            main.save_highscore(17, path)

            self.assertEqual(main.load_highscore(path), 17)

    def test_update_highscore_only_persists_new_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "highscore.json"
            main.save_highscore(10, path)

            self.assertEqual(main.update_highscore(9, path), 10)
            self.assertEqual(main.load_highscore(path), 10)

            self.assertEqual(main.update_highscore(12, path), 12)
            self.assertEqual(main.load_highscore(path), 12)
