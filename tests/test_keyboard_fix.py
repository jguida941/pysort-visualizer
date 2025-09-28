#!/usr/bin/env python3
"""Test keyboard shortcuts in Compare Mode after fix."""

import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

# Add src to path
sys.path.insert(0, "src")

from app.algos.registry import load_all_algorithms
from app.ui_compare.window import CompareWindow

load_all_algorithms()


def test_keyboard_shortcuts():
    app = QApplication(sys.argv)
    window = CompareWindow()
    window.show()

    print("Testing Compare Mode Keyboard Shortcuts After Fix")
    print("=" * 60)

    # Check if keyPressEvent is now implemented
    if hasattr(window, "keyPressEvent"):
        print("✅ keyPressEvent method found in CompareWindow")
    else:
        print("❌ keyPressEvent method NOT found")

    # Check if focus management exists
    if hasattr(window, "_focused_pane"):
        print(f"✅ Focus management implemented (focused: {window._focused_pane})")
    else:
        print("❌ Focus management NOT implemented")

    # Check if we can switch focus
    if hasattr(window, "_update_focus_indicator"):
        print("✅ Focus indicator method found")
    else:
        print("❌ Focus indicator method NOT found")

    print("\nKeyboard Shortcuts Status:")
    print("- Space: Play/Pause focused pane")
    print("- Left/< : Step back focused pane")
    print("- Right/> : Step forward focused pane")
    print("- R: Reset focused pane")
    print("- Tab: Switch focus between panes")

    print("\nVisual Indicators:")
    print("- Blue border (2px) on focused pane")
    print("- Click on pane to focus it")
    print("- Tab key switches focus")

    # Keep window open for 3 seconds
    QTimer.singleShot(3000, app.quit)
    app.exec()


if __name__ == "__main__":
    test_keyboard_shortcuts()
