from __future__ import annotations

import sys

from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.algos.registry import load_all_algorithms
from app.ui_compare.window import CompareWindow
from app.ui_shared.constants import APP_DOMAIN, APP_NAME, ORG_NAME
from app.ui_shared.theme import apply_global_tooltip_theme
from app.ui_single.window import SuiteWindow

load_all_algorithms()


class LauncherWindow(QMainWindow):
    """Landing window that lets the user choose Single or Compare mode."""

    def __init__(self) -> None:
        super().__init__()
        self._settings = QSettings(ORG_NAME, APP_NAME)
        self.setWindowTitle("Sorting Visualizer")
        self.resize(640, 360)

        self._child_window: QMainWindow | None = None

        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(48, 40, 48, 32)
        layout.setSpacing(24)

        headline = QLabel("Choose a mode to launch")
        headline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        headline.setObjectName("launcher_headline")
        layout.addWidget(headline)

        description = QLabel(
            "Single Visualizer opens one algorithm per tab.\n"
            "Compare Mode opens the dual-pane comparison workspace."
        )
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setWordWrap(True)
        description.setObjectName("launcher_description")
        layout.addWidget(description)

        buttons = QHBoxLayout()
        buttons.setSpacing(16)

        self.single_button = QPushButton("Single Visualizer")
        self.single_button.setMinimumHeight(56)
        self.single_button.clicked.connect(self._launch_single)

        self.compare_button = QPushButton("Compare Mode")
        self.compare_button.setMinimumHeight(56)
        self.compare_button.clicked.connect(self._launch_compare)

        buttons.addWidget(self.single_button)
        buttons.addWidget(self.compare_button)
        layout.addLayout(buttons)
        layout.addStretch(1)

        self.setCentralWidget(central)
        self._apply_theme_from_settings()

    def _apply_theme_from_settings(self) -> None:
        theme = self._settings.value("ui/theme", "dark")
        if isinstance(theme, bytes):
            theme = theme.decode()
        self._current_theme = theme if theme in {"dark", "high-contrast"} else "dark"
        apply_global_tooltip_theme(self._current_theme)
        if self._current_theme == "high-contrast":
            self.setStyleSheet(
                """
QMainWindow { background: #f0f2f8; }
#launcher_headline { color: #0b1e44; font-size: 20px; font-weight: 600; }
#launcher_description { color: #0b1e44; font-size: 13px; }
QPushButton {
  background: #ffffff;
  border: 1px solid #0f6fff;
  border-radius: 10px;
  color: #0b1e44;
  font-size: 15px;
  font-weight: 600;
}
QPushButton:hover { background: #eaf2ff; }
"""
            )
        else:
            self.setStyleSheet(
                """
QMainWindow { background: #11151d; }
#launcher_headline { color: #ffffff; font-size: 20px; font-weight: 600; }
#launcher_description { color: #cfd6e6; font-size: 13px; }
QPushButton {
  background: #1f2734;
  border: 1px solid rgba(106,160,255,0.65);
  border-radius: 10px;
  color: #cfd6e6;
  font-size: 15px;
  font-weight: 600;
}
QPushButton:hover { background: #273246; }
"""
            )

    def _launch_single(self) -> None:
        self._open_child(SuiteWindow)

    def _launch_compare(self) -> None:
        self._open_child(CompareWindow)

    def _open_child(self, window_cls: type[QMainWindow]) -> None:
        if self._child_window is not None:
            self._child_window.close()
        self._child_window = window_cls()
        self._child_window.show()
        self.close()


def main() -> None:
    app = QApplication(sys.argv)
    app.setOrganizationDomain(APP_DOMAIN)
    app.setOrganizationName(ORG_NAME)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion("0.1.0")
    app.setStyleSheet(
        """
QTabWidget::pane, QTabWidget {
  background: #0f1115;
}
QTabBar::tab {
  background: #1a1f27;
  color: #cfd6e6;
  padding: 6px 10px;
  border-radius: 6px;
}
QTabBar::tab:selected { background: #2a2f3a; color: #ffffff; }
QTabBar::tab:hover    { background: #202634; }
"""
    )
    window = LauncherWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
