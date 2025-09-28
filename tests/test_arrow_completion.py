#!/usr/bin/env python3
"""Test that bars turn green when using arrow keys to complete."""

import sys

sys.path.insert(0, "src")

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from app.algos.registry import load_all_algorithms
from app.ui_single.window import SuiteWindow

load_all_algorithms()


def test_arrow_completion():
    """Test that the finish animation triggers when using arrow keys."""
    app = QApplication(sys.argv)
    window = SuiteWindow()
    window.show()

    print("Testing Arrow Key Completion Animation")
    print("=" * 60)

    # Start with a small array for quick testing
    window.txt_array.setText("3,1,2")
    window.on_generate()

    # Step through using arrow keys
    steps_taken = 0
    while window.pane.player_step_forward():
        steps_taken += 1
        if steps_taken > 100:  # Safety limit
            break

    print(f"Stepped through {steps_taken} steps")
    print("Bars should now be green if fix worked!")

    # Keep window open briefly to see result
    QTimer.singleShot(2000, app.quit)
    app.exec()


if __name__ == "__main__":
    test_arrow_completion()
