from __future__ import annotations

import sys
from typing import cast

from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QAction, QCloseEvent
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget

from app.algos.registry import INFO, REGISTRY, load_all_algorithms
from app.core.base import AlgorithmVisualizerBase
from app.core.compare import CompareView

_ORG_NAME = "org.pysort"
_APP_NAME = "sorting-visualizer"
_APP_DOMAIN = "sortingviz.dev"

load_all_algorithms()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._settings = QSettings(_ORG_NAME, _APP_NAME)
        self.setWindowTitle("Sorting Algorithm Visualizers")
        self.resize(1200, 850)

        self._tabs = QTabWidget()
        self._compare_view = CompareView()
        self._tabs.addTab(self._compare_view, "Compare")

        for name in sorted(INFO.keys()):
            info = INFO[name]
            algo_func = REGISTRY[name]
            visualizer = AlgorithmVisualizerBase(algo_info=info, algo_func=algo_func)
            self._tabs.addTab(visualizer, name)
        self.setCentralWidget(self._tabs)

        geometry = self._settings.value("main/geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        theme = self._settings.value("ui/theme", "dark")
        if isinstance(theme, bytes):
            theme = theme.decode()
        self.current_theme = theme if theme in {"dark", "high-contrast"} else "dark"
        self._apply_theme(self.current_theme)
        self._build_menu()

    def closeEvent(self, event: QCloseEvent | None) -> None:
        self._settings.setValue("main/geometry", self.saveGeometry())
        super().closeEvent(event)

    def _build_menu(self) -> None:
        menu_bar = self.menuBar()
        if menu_bar is None:
            return
        view_menu = menu_bar.addMenu("&View")
        if view_menu is None:
            return
        self.theme_action = QAction("High Contrast Mode", self)
        self.theme_action.setCheckable(True)
        self.theme_action.setChecked(self.current_theme == "high-contrast")
        self.theme_action.setStatusTip("Toggle a light, high-contrast theme for accessibility")
        self.theme_action.toggled.connect(self._on_theme_toggled)
        view_menu.addAction(self.theme_action)

    def _apply_theme(self, theme: str) -> None:
        self.current_theme = theme if theme in {"dark", "high-contrast"} else "dark"
        self._settings.setValue("ui/theme", self.current_theme)
        app = QApplication.instance()
        if app is not None:
            qapp = cast(QApplication, app)
            if self.current_theme == "high-contrast":
                qapp.setStyleSheet(
                    "QToolTip { color: #111111; background: #f7f7f7; border: 1px solid #0f6fff; }"
                )
            else:
                qapp.setStyleSheet(
                    "QToolTip { color: #e6e6e6; background: #1e2530; border: 1px solid #6aa0ff; }"
                )

        if hasattr(self, "theme_action"):
            self.theme_action.blockSignals(True)
            self.theme_action.setChecked(self.current_theme == "high-contrast")
            self.theme_action.blockSignals(False)

        for index in range(self._tabs.count()):
            widget = self._tabs.widget(index)
            if widget is None:
                continue
            if hasattr(widget, "apply_theme"):
                widget.apply_theme(self.current_theme)

    def _on_theme_toggled(self, checked: bool) -> None:
        theme = "high-contrast" if checked else "dark"
        self._apply_theme(theme)


def main() -> None:
    app = QApplication(sys.argv)
    app.setOrganizationDomain(_APP_DOMAIN)
    app.setOrganizationName(_ORG_NAME)
    app.setApplicationName(_APP_NAME)
    app.setApplicationVersion("0.1.0")
    app.setStyleSheet(
        """
QMainWindow, QTabWidget::pane, QTabWidget {
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
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
