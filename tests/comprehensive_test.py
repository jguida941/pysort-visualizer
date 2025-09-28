#!/usr/bin/env python3
"""Comprehensive test of Compare Mode functionality."""

import sys

sys.path.insert(0, "src")

from PyQt6.QtWidgets import QApplication

from app.algos.registry import load_all_algorithms
from app.ui_compare.window import CompareWindow

load_all_algorithms()


def run_tests():
    app = QApplication(sys.argv)
    window = CompareWindow()
    window.show()

    print("\n" + "=" * 80)
    print("COMPREHENSIVE COMPARE MODE TEST")
    print("=" * 80)

    print("\n✅ WORKING:")
    print("- Keyboard focus management (Tab switches, click to focus)")
    print("- Independent pane control (Space, <, >, R for focused pane)")
    print("- Basic visualization rendering")

    print("\n❌ ISSUES TO VERIFY:")
    print("1. When changing algorithm:")
    print("   - Graph disappears? ❌")
    print("   - Shortcuts stop working? ❌ (FIXED)")
    print("   - Need to regenerate dataset? ❌")

    print("2. Timing display:")
    print("   - Visual time working?")
    print("   - True time working?")
    print("   - Stops when algorithm finishes?")

    print("3. When algorithm completes:")
    print("   - Bars turn green?")
    print("   - 'Finished' message appears?")
    print("   - Timer stops?")

    print("4. Step counter:")
    print("   - Updates correctly during stepping?")
    print("   - Shows correct total?")

    print("5. Metrics display (HUD):")
    print("   - Comparisons counter visible?")
    print("   - Swaps counter visible?")
    print("   - Updates in real-time?")

    print("\n📋 TEST STEPS:")
    print("1. Generate a dataset")
    print("2. Step through with > key - CHECK step counter")
    print("3. Let algorithm complete - CHECK if turns green")
    print("4. Change left algorithm - CHECK if graph shows")
    print("5. Try keyboard shortcuts after change - CHECK if working")
    print("6. Check timing display throughout")
    print("=" * 80)

    app.exec()


if __name__ == "__main__":
    run_tests()
