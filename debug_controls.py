import sys

sys.path.insert(0, "src")

from PyQt6.QtWidgets import QApplication

from app.algos.registry import load_all_algorithms
from app.ui_compare.window import CompareWindow

load_all_algorithms()


class DebugCompareWindow(CompareWindow):
    def keyPressEvent(self, event):
        super().keyPressEvent(event)

        # Debug info
        left_pane = self._view._left.pane
        right_pane = self._view._right.pane

        if left_pane and right_pane:
            print(f"\nDEBUG - Focused: {self._focused_pane}")
            print(f"Left: Step {left_pane.step_index()}, Running: {left_pane.is_running}")
            print(f"Right: Step {right_pane.step_index()}, Running: {right_pane.is_running}")


app = QApplication(sys.argv)
window = DebugCompareWindow()
window.show()

print("\n" + "=" * 60)
print("DEBUG KEYBOARD CONTROLS")
print("=" * 60)
print("\n1. Generate dataset")
print("2. Click left pane and press Right Arrow")
print("3. Check console for debug output")
print("=" * 60)

app.exec()
