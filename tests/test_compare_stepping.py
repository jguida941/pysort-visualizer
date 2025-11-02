"""Unit tests for Compare mode stepping and time synchronization."""

import unittest
from unittest.mock import MagicMock, patch
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication
import sys

# Create QApplication if not exists
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


class TestCompareModeStepping(unittest.TestCase):
    """Test stepping and time synchronization in Compare mode."""

    def setUp(self):
        """Set up test fixtures."""
        from src.app.ui_compare.window import CompareWindow
        self.window = CompareWindow()
        self.view = self.window._view

        # Mock the controller
        self.view._controller = MagicMock()
        self.view._controller.is_running.return_value = False

        # Mock ensure_dataset to always return True
        self.view._ensure_dataset = MagicMock(return_value=True)

        # Mock current array
        self.view._current_array = [5, 2, 9, 1, 5, 6]

    def test_step_buttons_use_controller(self):
        """Test that Step buttons use controller methods."""
        # Test step forward button
        self.view._on_step_forward()
        self.view._controller.step_forward.assert_called_once()

        # Test step back button
        self.view._on_step_back()
        self.view._controller.step_back.assert_called_once()

    def test_arrow_keys_use_controller(self):
        """Test that arrow keys use controller methods like buttons."""
        from PyQt6.QtGui import QKeyEvent

        # Test right arrow key
        event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Right, Qt.KeyboardModifier.NoModifier)
        self.window.keyPressEvent(event)
        self.view._controller.step_forward.assert_called_once()

        # Test left arrow key
        event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Left, Qt.KeyboardModifier.NoModifier)
        self.window.keyPressEvent(event)
        self.view._controller.step_back.assert_called_once()

    def test_spacebar_uses_controller(self):
        """Test that spacebar uses controller for play/pause."""
        from PyQt6.QtGui import QKeyEvent

        # Test play when not running
        self.view._controller.is_running.return_value = False
        event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Space, Qt.KeyboardModifier.NoModifier)
        self.window.keyPressEvent(event)
        self.view._controller.play.assert_called_once()

        # Test pause when running
        self.view._controller.reset_mock()
        self.view._controller.is_running.return_value = True
        event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Space, Qt.KeyboardModifier.NoModifier)
        self.window.keyPressEvent(event)
        self.view._controller.toggle_pause.assert_called_once()

    def test_reset_key_uses_controller(self):
        """Test that R key uses controller reset."""
        from PyQt6.QtGui import QKeyEvent

        # Mock visualizers
        self.view._left = MagicMock()
        self.view._right = MagicMock()

        event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_R, Qt.KeyboardModifier.NoModifier)
        self.window.keyPressEvent(event)
        self.view._controller.reset.assert_called_once()

    def test_play_pause_buttons_use_controller(self):
        """Test that Play/Pause buttons use controller methods."""
        # Test start button
        self.view._on_start_clicked()
        self.view._controller.play.assert_called_once()

        # Test pause button
        self.view._on_pause_clicked()
        self.view._controller.toggle_pause.assert_called_once()

    def test_reset_button_uses_controller(self):
        """Test that Reset button uses controller method."""
        # Mock visualizers
        self.view._left = MagicMock()
        self.view._right = MagicMock()

        self.view._on_reset_clicked()
        self.view._controller.reset.assert_called_once()

    def test_controller_coordinates_both_panes(self):
        """Test that controller coordinates stepping for both panes."""
        from src.app.ui_compare.controller import CompareController

        # Create mock panes
        left_pane = MagicMock()
        right_pane = MagicMock()

        controller = CompareController(left_pane, right_pane)

        # Test step forward
        controller.step_forward()
        left_pane.step_forward.assert_called_once()
        right_pane.step_forward.assert_called_once()

        # Test step back
        controller.step_back()
        left_pane.step_back.assert_called_once()
        right_pane.step_back.assert_called_once()

    def test_time_sync_on_step(self):
        """Test that logical time is properly synced when stepping."""
        from src.app.core.player import Player

        # Create a player with mock callbacks
        step_index = 0

        def mock_step_forward():
            nonlocal step_index
            step_index += 1
            return True

        def mock_step_back():
            nonlocal step_index
            if step_index > 0:
                step_index -= 1
                return True
            return False

        def get_step_index():
            return step_index

        player = Player(
            step_forward_cb=mock_step_forward,
            step_back_cb=mock_step_back,
            step_index_cb=get_step_index,
            total_steps_cb=lambda: 100,
            after_finish_cb=lambda: None
        )

        player.set_visual_fps(60)

        # Step forward a few times
        player.step_forward()
        self.assertEqual(step_index, 1)
        self.assertAlmostEqual(player.logical_seconds(), 1.0/60, places=3)

        player.step_forward()
        self.assertEqual(step_index, 2)
        self.assertAlmostEqual(player.logical_seconds(), 2.0/60, places=3)

        # Step back
        player.step_back()
        self.assertEqual(step_index, 1)
        self.assertAlmostEqual(player.logical_seconds(), 1.0/60, places=3)

        # Step back to beginning
        player.step_back()
        self.assertEqual(step_index, 0)
        self.assertAlmostEqual(player.logical_seconds(), 0.0, places=3)


if __name__ == "__main__":
    unittest.main()