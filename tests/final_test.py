import sys

sys.path.insert(0, "src")

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from app.algos.registry import load_all_algorithms
from app.ui_compare.window import CompareWindow

load_all_algorithms()

app = QApplication(sys.argv)
window = CompareWindow()
window.show()


def show_instructions():
    print("\n" + "=" * 60)
    print("COMPARE MODE KEYBOARD SHORTCUTS TEST")
    print("=" * 60)
    print("\nINSTRUCTIONS:")
    print("1. Click 'Generate dataset' to create data")
    print("2. Click on LEFT pane - should show BLUE border")
    print("3. Press SPACE - should play/pause LEFT algorithm only")
    print("4. Press < or > - should step LEFT algorithm only")
    print("5. Press TAB - should switch focus to RIGHT pane")
    print("6. Press SPACE - should play/pause RIGHT algorithm only")
    print("7. Press < or > - should step RIGHT algorithm only")
    print("8. Press R - should reset the focused algorithm")
    print("\nFOCUS INDICATORS:")
    print("- Blue 2px border = Active/Focused pane")
    print("- Transparent border = Inactive pane")
    print("\nISSUES TO CHECK:")
    print("✓ Focus should leave text field when clicking panes")
    print("✓ Each pane controlled independently")
    print("✓ Visual feedback shows which pane is active")
    print("=" * 60)


# Show instructions after window loads
QTimer.singleShot(100, show_instructions)

app.exec()
