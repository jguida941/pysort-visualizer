import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from app.algos.registry import load_all_algorithms
from app.ui_compare.window import CompareWindow
from app.ui_single.window import SuiteWindow

load_all_algorithms()


def test_single_window():
    app = QApplication(sys.argv)
    window = SuiteWindow()
    window.show()

    # Check if window opens
    assert window.isVisible()
    print("✅ Single window opens successfully")

    # Check tabs exist
    assert window._tab_widget.count() > 0
    print(f"✅ Single window has {window._tab_widget.count()} tabs")

    QTimer.singleShot(100, app.quit)
    app.exec()


def test_compare_window():
    app = QApplication(sys.argv)
    window = CompareWindow()
    window.show()

    # Check if window opens
    assert window.isVisible()
    print("✅ Compare window opens successfully")

    # Check if panels exist
    assert hasattr(window, "_left_panel")
    assert hasattr(window, "_right_panel")
    print("✅ Compare window has both panels")

    QTimer.singleShot(100, app.quit)
    app.exec()


print("Testing UI Components...")
print("=" * 60)

try:
    test_single_window()
except Exception as e:
    print(f"❌ Single window failed: {e}")

try:
    test_compare_window()
except Exception as e:
    print(f"❌ Compare window failed: {e}")

print("=" * 60)
