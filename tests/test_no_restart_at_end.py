#!/usr/bin/env python3
"""Test that pressing forward at the end doesn't restart the algorithm."""

import sys

sys.path.insert(0, "src")

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from app.algos.registry import load_all_algorithms
from app.ui_single.window import SuiteWindow

load_all_algorithms()


def test_no_restart_at_end():
    """Test that we can't restart the algorithm by pressing forward at the end."""
    app = QApplication(sys.argv)
    window = SuiteWindow()
    window.show()

    print("Testing No Restart at End")
    print("=" * 60)

    # Start with a small array
    window.txt_array.setText("3,1,2")
    window.on_generate()

    initial_array = list(window.pane._visualizer._array)
    print(f"Initial array: {initial_array}")

    # Step through to the end
    steps_taken = 0
    max_steps = 1000  # Safety limit

    while steps_taken < max_steps:
        if not window.pane.player_step_forward():
            break
        steps_taken += 1

    print(f"Stepped through {steps_taken} steps to reach the end")
    final_array = list(window.pane._visualizer._array)
    print(f"Final sorted array: {final_array}")
    print(f"Current step index: {window.pane._visualizer._step_idx}")

    # Now try to step forward again multiple times - should not restart
    print("\nAttempting to step past the end...")
    for i in range(10):
        prev_idx = window.pane._visualizer._step_idx

        # Try to step forward
        window._transport_step_forward()

        new_idx = window.pane._visualizer._step_idx
        new_array = list(window.pane._visualizer._array)

        print(f"  Attempt {i+1}: step_idx={new_idx}, array={new_array}")

        # Check if it jumped back to the beginning
        if new_idx < prev_idx:
            print("    ERROR: Step index went backwards!")
            print(f"    Previous: {prev_idx}, New: {new_idx}")

        # Check if array changed to unsorted state
        if new_array != final_array:
            print("    ERROR: Array changed from sorted state!")
            print(f"    Expected: {final_array}")
            print(f"    Got: {new_array}")

    print("\nTest complete. Algorithm should NOT have restarted.")

    # Keep window open briefly
    QTimer.singleShot(2000, app.quit)
    app.exec()


if __name__ == "__main__":
    test_no_restart_at_end()
