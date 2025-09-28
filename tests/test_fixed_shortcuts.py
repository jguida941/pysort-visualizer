import sys

sys.path.insert(0, "src")

from PyQt6.QtWidgets import QApplication

from app.algos.registry import load_all_algorithms
from app.ui_compare.window import CompareWindow

load_all_algorithms()

app = QApplication(sys.argv)
window = CompareWindow()
window.show()

print("\n" + "=" * 60)
print("KEYBOARD SHORTCUTS TEST - AFTER FIX")
print("=" * 60)
print("\n✅ FIXED:")
print("- Base class shortcuts disabled in Compare Mode")
print("- CompareWindow handles its own keyboard events")
print("- Focus management implemented")
print("\n📋 INSTRUCTIONS:")
print("1. Click 'Generate dataset' button")
print("2. Click on LEFT pane - should see BLUE border")
print("3. Test these keys:")
print("   - Space: Play/Pause")
print("   - < or Left Arrow: Step back")
print("   - > or Right Arrow: Step forward")
print("   - R: Reset")
print("   - Tab: Switch to other pane")
print("\nEach pane should respond INDEPENDENTLY to keyboard")
print("=" * 60)

app.exec()
