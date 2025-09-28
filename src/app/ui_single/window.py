from __future__ import annotations

from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtGui import QAction, QCloseEvent
from PyQt6.QtWidgets import QDockWidget, QMainWindow, QTabWidget, QWidget

from app.algos.registry import INFO, REGISTRY
from app.core.base import AlgorithmVisualizerBase
from app.ui_shared.constants import APP_NAME, ORG_NAME
from app.ui_shared.debug_panel import DebugPanel
from app.ui_shared.professional_theme import generate_stylesheet
from app.ui_shared.theme import apply_global_tooltip_theme


class SuiteWindow(QMainWindow):
    """Tabbed window hosting individual algorithm visualizers."""

    def __init__(self) -> None:
        super().__init__()
        self._settings = QSettings(ORG_NAME, APP_NAME)
        self.setWindowTitle("PySort Visualizer")
        self.resize(1280, 900)

        self._tabs = QTabWidget()
        self._algo_tabs: dict[str, AlgorithmVisualizerBase] = {}
        self._panes: dict[str, object] = {}
        self._debug_dock: QDockWidget | None = None
        for name in sorted(INFO.keys()):
            info = INFO[name]
            algo_func = REGISTRY[name]
            visualizer = AlgorithmVisualizerBase(algo_info=info, algo_func=algo_func)
            self._tabs.addTab(visualizer, name)
            self._algo_tabs[name] = visualizer
            pane = getattr(visualizer, "pane", None)
            if pane is not None and hasattr(pane, "logical_elapsed_updated"):
                pane.logical_elapsed_updated.connect(lambda _t, viz=visualizer: viz.canvas.update())
            self._panes[name] = pane
        self.setCentralWidget(self._tabs)
        self._tabs.currentChanged.connect(self._refresh_debug_panel)

        # Apply professional theme
        self.setStyleSheet(generate_stylesheet())

        geometry = self._settings.value("main/geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        theme = self._settings.value("ui/theme", "dark")
        if isinstance(theme, bytes):
            theme = theme.decode()
        self.current_theme = theme if theme in {"dark", "high-contrast"} else "dark"
        self.apply_theme(self.current_theme)
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

        self.debug_action = QAction("Show Debug Panel", self)
        self.debug_action.setCheckable(True)
        self.debug_action.toggled.connect(self._toggle_debug_panel)
        view_menu.addAction(self.debug_action)

    def apply_theme(self, theme: str) -> None:
        self.current_theme = theme if theme in {"dark", "high-contrast"} else "dark"
        self._settings.setValue("ui/theme", self.current_theme)
        apply_global_tooltip_theme(self.current_theme)

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

    def pane_for(self, name: str):
        return self._panes.get(name)

    def _ensure_debug_dock(self) -> None:
        if self._debug_dock is not None:
            return
        dock = QDockWidget("Debug", self)
        dock.setObjectName("single_debug_dock")
        dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        dock.hide()
        self._debug_dock = dock
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

    def _toggle_debug_panel(self, show: bool) -> None:
        if show:
            self._ensure_debug_dock()
            if self._debug_dock is not None:
                self._refresh_debug_panel(self._tabs.currentIndex())
                self._debug_dock.show()
        else:
            if self._debug_dock is not None:
                self._debug_dock.hide()

    def _refresh_debug_panel(self, index: int) -> None:
        if self._debug_dock is None or not self._debug_dock.isVisible():
            return
        name = self._tabs.tabText(index)
        pane = self.pane_for(name)
        widget = DebugPanel(pane) if pane is not None else QWidget()
        old = self._debug_dock.widget()
        if old is not None:
            old.deleteLater()
        self._debug_dock.setWidget(widget)

    def _on_theme_toggled(self, checked: bool) -> None:
        theme = "high-contrast" if checked else "dark"
        self.apply_theme(theme)

    def focus_algorithm(self, name: str) -> None:
        widget = self._algo_tabs.get(name)
        if widget is None:
            return
        index = self._tabs.indexOf(widget)
        if index >= 0:
            self._tabs.setCurrentIndex(index)

    def visualizer_for(self, name: str) -> AlgorithmVisualizerBase | None:
        return self._algo_tabs.get(name)
