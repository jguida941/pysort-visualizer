#!/usr/bin/env python3
"""Test that stepping past the end doesn't continue."""

import sys

sys.path.insert(0, "src")

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from app.algos.registry import load_all_algorithms
from app.ui_single.window import SuiteWindow

load_all_algorithms()


def test_step_past_end():
    """Test that we can't step past the end."""
    app = QApplication(sys.argv)
    window = SuiteWindow()
    window.show()

    print("Testing Step Past End Prevention")
    print("=" * 60)

    # Start with a tiny array for quick testing
    window.txt_array.setText("2,1")
    window.on_generate()

    # Step through to the end
    steps_taken = 0
    while window.pane.player_step_forward():
        steps_taken += 1
        if steps_taken > 100:  # Safety limit
            print("ERROR: Too many steps!")
            break

    print(f"Stepped through {steps_taken} steps to reach the end")

    # Now try to step forward again - should not advance
    print("Attempting to step past the end...")
    for i in range(5):
        result = window.pane.player_step_forward()
        print(f"  Attempt {i+1}: {'Advanced' if result else 'Blocked'}")

    print("\nTest complete. Bars should remain green.")

    # Keep window open briefly to see result
    QTimer.singleShot(2000, app.quit)
    app.exec()


if __name__ == "__main__":
    test_step_past_end()
