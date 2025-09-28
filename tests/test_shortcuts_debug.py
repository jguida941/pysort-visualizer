#!/usr/bin/env python3
import sys

sys.path.insert(0, "src")

from PyQt6.QtWidgets import QApplication, QLabel

from app.algos.registry import load_all_algorithms
from app.ui_compare.window import CompareWindow

load_all_algorithms()


class DebugWindow(CompareWindow):
    def __init__(self):
        super().__init__()
        self.debug_label = QLabel("Keyboard events will show here")
        self.debug_label.setStyleSheet("color: red; font-size: 16px; padding: 10px;")

        # Add debug label to status bar
        if hasattr(self, "statusBar"):
            self.statusBar().addWidget(self.debug_label)

    def keyPressEvent(self, event):
        key_name = event.text() or f"Key_{event.key()}"
        print(f"Key pressed: {key_name} (code: {event.key()})")
        self.debug_label.setText(f"Last key: {key_name} (code: {event.key()})")

        # Call parent implementation
        super().keyPressEvent(event)


app = QApplication(sys.argv)
window = DebugWindow()
window.show()

print("\n" + "=" * 60)
print("KEYBOARD TEST - Try pressing keys:")
print("- Space (code 32)")
print("- Left Arrow (code 16777234)")
print("- Right Arrow (code 16777236)")
print("- < comma (code 44)")
print("- > period (code 46)")
print("- R (code 82)")
print("- Tab (code 16777217)")
print("=" * 60 + "\n")

app.exec()
