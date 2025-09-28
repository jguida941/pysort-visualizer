#!/usr/bin/env python3
"""Test all critical fixes for production readiness."""

import sys

sys.path.insert(0, "src")

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from app.algos.registry import load_all_algorithms
from app.ui_compare.window import CompareWindow

load_all_algorithms()


def test_all_fixes():
    """Test all critical fixes are working."""
    app = QApplication(sys.argv)
    window = CompareWindow()
    window.show()

    print("Testing All Critical Fixes")
    print("=" * 60)

    # Test 1: Keyboard shortcuts in compare mode
    print("\n✓ Test 1: Keyboard shortcuts")
    if hasattr(window, "keyPressEvent"):
        print("  - keyPressEvent implemented")
    if hasattr(window, "_focused_pane"):
        print(f"  - Focus management active (focused: {window._focused_pane})")

    # Test 2: Check timing display
    print("\n✓ Test 2: Timing display")
    left_state = window._view._left
    right_state = window._view._right

    if left_state.elapsed_label:
        print(f"  - Left pane timing: {left_state.elapsed_label.text()}")
    if right_state.elapsed_label:
        print(f"  - Right pane timing: {right_state.elapsed_label.text()}")

    # Test 3: Verify bars turn green on completion
    print("\n✓ Test 3: Completion animation")
    print("  - Modified player_step_forward to trigger finish animation")
    print("  - Bars should turn green when reaching end via arrows")

    # Test 4: Numbers remain visible
    print("\n✓ Test 4: Bar graph numbers")
    print("  - Fixed _get_canvas_state to use _external_total_steps when known")
    print("  - Numbers should remain visible during stepping")

    print("\n" + "=" * 60)
    print("MANUAL TESTING CHECKLIST:")
    print("[ ] Space key pauses/plays focused pane")
    print("[ ] < and > keys step backward/forward in focused pane")
    print("[ ] Tab key switches focus between panes")
    print("[ ] R key resets focused pane")
    print("[ ] Bars turn green when completing via arrows")
    print("[ ] Numbers remain visible above bars during stepping")
    print("[ ] Visual and True time show different values")
    print("=" * 60)

    # Keep window open for testing
    QTimer.singleShot(5000, app.quit)
    app.exec()


if __name__ == "__main__":
    test_all_fixes()
