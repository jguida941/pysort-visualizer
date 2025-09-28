import sys

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QApplication

from app.algos.registry import load_all_algorithms
from app.ui_compare.window import CompareWindow

load_all_algorithms()

app = QApplication(sys.argv)
window = CompareWindow()
window.show()

# Test keyboard shortcuts
print("Testing keyboard shortcuts in Compare Mode:")
print("=" * 60)


# Check if window handles key events
def test_key(key, name):
    event = QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier)
    result = window.keyPressEvent(event) if hasattr(window, "keyPressEvent") else None
    if result is None:
        print(f"❌ {name} key: No keyPressEvent handler found")
    else:
        print(f"✅ {name} key: Handler exists")


# Common playback shortcuts
test_key(Qt.Key.Key_Space, "Space (play/pause)")
test_key(Qt.Key.Key_Left, "Left arrow (step back)")
test_key(Qt.Key.Key_Right, "Right arrow (step forward)")
test_key(Qt.Key.Key_Comma, "< key (step back)")
test_key(Qt.Key.Key_Period, "> key (step forward)")
test_key(Qt.Key.Key_R, "R (reset)")

# Check for shortcut actions in menus
if hasattr(window, "menuBar"):
    print("\nMenu shortcuts:")
    for action in window.menuBar().actions():
        if action.shortcut():
            print(f"  {action.text()}: {action.shortcut().toString()}")

app.quit()
