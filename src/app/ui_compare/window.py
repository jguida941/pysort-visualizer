from __future__ import annotations

import contextlib
import random
import time
from collections.abc import Callable
from dataclasses import dataclass

from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QSplitter,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.algos.registry import INFO, REGISTRY, load_all_algorithms
from app.core.base import AlgorithmVisualizerBase
from app.presets import DEFAULT_PRESET_KEY, generate_dataset, get_presets
from app.ui_compare.controller import CompareController
from app.ui_shared.constants import APP_NAME, ORG_NAME
from app.ui_shared.pane import Pane
from app.ui_shared.theme import apply_global_tooltip_theme

load_all_algorithms()


@dataclass(slots=True)
class _SideState:
    slot: str
    name: str
    visualizer: AlgorithmVisualizerBase
    pane: Pane | None
    transport: object | None
    details_button: QToolButton
    splitter: QSplitter
    detail_area: QScrollArea
    title_label: QLabel | None = None
    step_label: QLabel | None = None
    elapsed_label: QLabel | None = None
    total_steps_fn: Callable[[], int] | None = None
    start_time: float = 0.0
    end_time: float = 0.0


class CompareView(QWidget):
    """Two-pane compare mode with dedicated controls."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("compare_root")
        self._settings = QSettings(ORG_NAME, APP_NAME)
        self._current_array: list[int] | None = None
        self._current_seed: int | None = None
        self._current_preset: str = DEFAULT_PRESET_KEY
        self._dataset_ready = False
        self._status_prefix = ""

        algo_names = sorted(INFO.keys())
        left_default = algo_names[0]
        right_default = algo_names[1] if len(algo_names) > 1 else algo_names[0]

        self._left = self._make_side("left", left_default)
        self._right = self._make_side("right", right_default)
        assert self._left.pane is not None and self._right.pane is not None
        self._controller = CompareController(self._left.transport, self._right.transport)

        self._build_ui(algo_names)
        self._restore_settings()
        self._apply_theme_to_panes("dark")

    # ------------------------------------------------------------------ side setup --

    @property
    def left_pane(self) -> Pane | None:
        return self._left.pane

    @property
    def right_pane(self) -> Pane | None:
        return self._right.pane

    @property
    def controller(self) -> CompareController:
        return self._controller

    def _make_side(self, slot: str, algo_name: str) -> _SideState:
        info = INFO[algo_name]
        viz = AlgorithmVisualizerBase(
            algo_info=info,
            algo_func=REGISTRY[algo_name],
            show_controls=False,
        )

        detail_widget: QWidget
        if viz.right_panel is not None:
            detail_widget = viz.right_panel
            detail_widget.setParent(None)
            detail_widget.setVisible(True)
        else:
            placeholder = QLabel("No details available")
            placeholder.setWordWrap(True)
            detail_widget = QWidget()
            layout = QVBoxLayout(detail_widget)
            layout.addWidget(placeholder)
            layout.addStretch(1)

        details_btn = QToolButton()
        details_btn.setText("Details")
        details_btn.setCheckable(True)
        details_btn.setChecked(False)
        details_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        details_btn.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
        )

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setVisible(False)
        scroll.setWidget(detail_widget)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(viz)
        splitter.addWidget(scroll)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.setSizes([1_000_000, 0])

        state = _SideState(
            slot=slot,
            name=algo_name,
            visualizer=viz,
            pane=None,
            transport=None,
            details_button=details_btn,
            splitter=splitter,
            detail_area=scroll,
            total_steps_fn=viz.total_steps,
        )

        pane = Pane(
            visualizer=viz,
            step_forward=viz.player_step_forward,
            step_back=viz.player_step_back,
            step_index=viz.player_step_index,
            total_steps=state.total_steps_fn,
            on_finished=lambda st=state: self._on_pane_finished(st),
        )
        state.pane = pane
        state.transport = viz.transport

        pane.stepped.connect(lambda idx, st=state: self._on_pane_step(st, idx))
        pane.elapsed_updated.connect(lambda secs, st=state: self._on_pane_elapsed(st, secs))
        pane.finished.connect(lambda st=state: self._on_pane_finished(st))

        details_btn.toggled.connect(lambda checked, st=state: self._on_toggle_details(st, checked))

        pane.set_hud_visible(True)
        pane.toggle_details(False)
        self._update_transport_capabilities()
        return state

    # ------------------------------------------------------------------ UI build --

    def _build_ui(self, algo_names: list[str]) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        controls_header = QHBoxLayout()
        controls_header.setContentsMargins(0, 0, 0, 0)
        controls_header.setSpacing(8)
        self.controls_toggle = QToolButton()
        self.controls_toggle.setText("Hide controls")
        self.controls_toggle.setCheckable(True)
        self.controls_toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.controls_toggle.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarShadeButton)
        )
        self.controls_toggle.toggled.connect(self._on_controls_toggled)
        controls_header.addWidget(self.controls_toggle)
        controls_header.addStretch(1)
        root.addLayout(controls_header)

        self.dataset_card = self._build_dataset_card(algo_names)
        self.transport_card = self._build_transport_card()
        self.controls_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.controls_splitter.addWidget(self.dataset_card)
        self.controls_splitter.addWidget(self.transport_card)
        self.controls_splitter.setStretchFactor(0, 1)
        self.controls_splitter.setStretchFactor(1, 1)
        root.addWidget(self.controls_splitter)

        self.status_strip = QLabel()
        self.status_strip.setObjectName("compare_status")
        self.status_strip.setAlignment(Qt.AlignmentFlag.AlignLeft)
        root.addWidget(self.status_strip)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._compose_pane(self._left))
        splitter.addWidget(self._compose_pane(self._right))
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter, 1)

        note = QLabel(
            "Shortcuts: Space to pause/resume, Left/Right to step. Click a pane to focus its shortcuts."
        )
        note.setObjectName("compare_hint")
        root.addWidget(note)
        self._refresh_controller()

    def _build_dataset_card(self, algo_names: list[str]) -> QFrame:
        card = self._make_card()
        layout = QGridLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(8)

        lbl_left = QLabel("Left algorithm:")
        lbl_right = QLabel("Right algorithm:")
        self.left_combo = QComboBox()
        self.right_combo = QComboBox()
        for combo in (self.left_combo, self.right_combo):
            for name in algo_names:
                combo.addItem(name, name)

        lbl_array = QLabel("Array values:")
        self.array_edit = QLineEdit()
        self.array_edit.setPlaceholderText("e.g. 4,1,3,2")
        self.array_edit.setMinimumHeight(28)

        lbl_preset = QLabel("Preset:")
        self.preset_combo = QComboBox()
        for preset in get_presets():
            self.preset_combo.addItem(preset.label, preset.key)

        lbl_seed = QLabel("Seed:")
        self.seed_edit = QLineEdit()
        self.seed_edit.setPlaceholderText("auto")
        self.seed_edit.setFixedWidth(120)
        self.seed_edit.setMinimumHeight(28)

        self.generate_button = QPushButton("Generate dataset")
        self.generate_button.setMinimumHeight(32)

        layout.addWidget(lbl_left, 0, 0)
        layout.addWidget(self.left_combo, 0, 1)
        layout.addWidget(lbl_right, 0, 2)
        layout.addWidget(self.right_combo, 0, 3)
        layout.addWidget(lbl_array, 1, 0)
        layout.addWidget(self.array_edit, 1, 1, 1, 3)
        layout.addWidget(lbl_preset, 2, 0)
        layout.addWidget(self.preset_combo, 2, 1)
        layout.addWidget(lbl_seed, 2, 2)
        layout.addWidget(self.seed_edit, 2, 3)
        layout.addWidget(self.generate_button, 3, 0, 1, 4)

        self.left_combo.currentIndexChanged.connect(self._on_left_algo_changed)
        self.right_combo.currentIndexChanged.connect(self._on_right_algo_changed)
        self.generate_button.clicked.connect(self._on_generate_clicked)
        self.array_edit.textChanged.connect(self._mark_dataset_dirty)
        self.preset_combo.currentIndexChanged.connect(self._mark_dataset_dirty)
        self.seed_edit.textChanged.connect(self._mark_dataset_dirty)

        card.setMaximumHeight(140)
        return card

    def _build_transport_card(self) -> QFrame:
        card = self._make_card()
        layout = QGridLayout(card)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(8)

        self.start_button = QPushButton("Start")
        self.pause_button = QPushButton("Pause / Resume")
        self.reset_button = QPushButton("Reset")
        self.step_back_button = QPushButton("Step ◀")
        self.step_forward_button = QPushButton("Step ▶")

        self.fps_slider = QSlider(Qt.Orientation.Horizontal)
        self.fps_slider.setRange(1, 60)
        self.fps_slider.setValue(24)
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 60)
        self.fps_spin.setValue(24)
        self.fps_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.fps_spin.setFixedWidth(60)

        self.show_values_check = QCheckBox("Show values")

        layout.addWidget(self.start_button, 0, 0)
        layout.addWidget(self.pause_button, 0, 1)
        layout.addWidget(self.reset_button, 0, 2)
        layout.addWidget(self.step_back_button, 0, 3)
        layout.addWidget(self.step_forward_button, 0, 4)

        layout.addWidget(QLabel("FPS:"), 1, 0)
        layout.addWidget(self.fps_slider, 1, 1, 1, 3)
        layout.addWidget(self.fps_spin, 1, 4)
        layout.addWidget(self.show_values_check, 2, 0, 1, 5)

        self.start_button.clicked.connect(self._on_start_clicked)
        self.pause_button.clicked.connect(self._on_pause_clicked)
        self.reset_button.clicked.connect(self._on_reset_clicked)
        self.step_forward_button.clicked.connect(self._on_step_forward)
        self.step_back_button.clicked.connect(self._on_step_back)
        self.fps_slider.valueChanged.connect(self._on_fps_changed)
        self.fps_spin.valueChanged.connect(self._on_fps_changed)
        self.show_values_check.toggled.connect(self._on_show_values_toggled)

        card.setMaximumHeight(120)
        self._update_transport_capabilities()
        return card

    def _compose_pane(self, state: _SideState) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header_row = QHBoxLayout()
        title = QLabel(state.name)
        title.setObjectName("compare_pane_title")
        state.title_label = title
        header_row.addWidget(title)
        header_row.addStretch(1)
        header_row.addWidget(state.details_button)
        layout.addLayout(header_row)

        status_row = QHBoxLayout()
        status_row.setContentsMargins(0, 0, 0, 0)
        status_row.setSpacing(6)
        step_label = QLabel("Step 0/?")
        elapsed_label = QLabel("Visual 0.00s · True 0.00s")
        state.step_label = step_label
        state.elapsed_label = elapsed_label
        status_row.addWidget(step_label)
        status_row.addStretch(1)
        status_row.addWidget(elapsed_label)
        layout.addLayout(status_row)

        layout.addWidget(state.splitter, 1)

        canvas = getattr(state.visualizer, "canvas", None)
        if canvas is not None:
            canvas.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            old_mouse = canvas.mousePressEvent

            def _focus_then_forward(event):  # type: ignore
                canvas.setFocus()
                if callable(old_mouse):
                    old_mouse(event)

            canvas.mousePressEvent = _focus_then_forward  # type: ignore

        return container

    def _make_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("compare_card")
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setFrameShadow(QFrame.Shadow.Raised)
        return card

    # ------------------------------------------------------------------ state restoration --

    def _restore_settings(self) -> None:
        preset_key = self._settings.value("compare/preset", DEFAULT_PRESET_KEY)
        if isinstance(preset_key, bytes):
            preset_key = preset_key.decode()
        idx = self.preset_combo.findData(preset_key)
        if idx >= 0:
            self.preset_combo.setCurrentIndex(idx)
            self._current_preset = str(preset_key)

        seed = self._settings.value("compare/seed", "")
        if seed not in (None, ""):
            self.seed_edit.setText(str(seed))

        left_algo = self._settings.value("compare/left", self._left.name)
        right_algo = self._settings.value("compare/right", self._right.name)
        self._set_combo_value(self.left_combo, left_algo)
        self._set_combo_value(self.right_combo, right_algo)

        fps = int(self._settings.value("compare/fps", 24))
        self._sync_fps(fps)

        show_values = bool(int(self._settings.value("compare/show_values", 0)))
        self.show_values_check.setChecked(show_values)
        for state in (self._left, self._right):
            if state.pane is not None:
                state.pane.set_show_values(show_values)
            else:
                state.visualizer.set_show_values(show_values)

        left_hud = bool(int(self._settings.value("compare/left/hud_visible", 1)))
        right_hud = bool(int(self._settings.value("compare/right/hud_visible", 1)))

        for state, hud_visible in ((self._left, left_hud), (self._right, right_hud)):
            state.details_button.blockSignals(True)
            state.details_button.setChecked(not hud_visible)
            state.details_button.blockSignals(False)
            self._set_detail_state(state, not hud_visible, persist=False)

        self._update_status()

    # ------------------------------------------------------------------ helpers --

    def _set_combo_value(self, combo: QComboBox, value: str | None) -> None:
        if isinstance(value, bytes):
            value = value.decode()
        if not value:
            return
        idx = combo.findData(value)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def _sync_fps(self, fps: int) -> None:
        for widget in (self.fps_slider, self.fps_spin):
            widget.blockSignals(True)
            widget.setValue(fps)
            widget.blockSignals(False)
        self._left.visualizer.set_fps(fps)
        self._right.visualizer.set_fps(fps)

    def _refresh_controller(self) -> None:
        if self._left.transport is not None:
            self._controller.left = self._left.transport
        if self._right.transport is not None:
            self._controller.right = self._right.transport

    def _update_transport_capabilities(self) -> None:
        if not hasattr(self, "step_back_button"):
            return
        can_step_back = all(
            state.transport is not None and state.transport.capabilities().get("step_back", False)
            for state in (self._left, self._right)
        )
        self.step_back_button.setEnabled(can_step_back)

    def _apply_theme_to_panes(self, theme: str) -> None:
        for viz in (self._left.visualizer, self._right.visualizer):
            viz.apply_theme(theme)

    def _update_status(self) -> None:
        left = self._left.name
        right = self._right.name
        if self._current_array is None:
            text = f"{left} vs {right} — no dataset loaded"
        else:
            preset_label = "Custom"
            if self._current_preset and self._current_preset != DEFAULT_PRESET_KEY:
                preset_label = self.preset_combo.currentText()
            n = len(self._current_array)
            seed_text = "auto" if self._current_seed is None else str(self._current_seed)
            text = f"{left} vs {right} • Preset: {preset_label} • n={n} • seed={seed_text}"
        self._status_prefix = text
        self.status_strip.setText(text)

    # ------------------------------------------------------------------ detail toggles --

    def _set_detail_state(
        self, state: _SideState, show_details: bool, *, persist: bool = True
    ) -> None:
        state.detail_area.setVisible(show_details)
        if state.pane is not None:
            state.pane.toggle_details(show_details)
            state.pane.set_hud_visible(not show_details)
        if show_details:
            state.splitter.setSizes([3_000_000, 1_000_000])
        else:
            state.splitter.setSizes([1_000_000, 0])
        if persist:
            self._settings.setValue(f"compare/{state.slot}/hud_visible", int(not show_details))

    def _on_toggle_details(self, state: _SideState, checked: bool) -> None:
        self._set_detail_state(state, checked, persist=True)

    def _on_controls_toggled(self, hidden: bool) -> None:
        self.controls_splitter.setVisible(not hidden)
        icon = (
            self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarUnshadeButton)
            if hidden
            else self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarShadeButton)
        )
        self.controls_toggle.setIcon(icon)
        self.controls_toggle.setText("Show controls" if hidden else "Hide controls")

    def _mark_dataset_dirty(self) -> None:
        self._dataset_ready = False
        self._current_array = None

    # ------------------------------------------------------------------ slots --

    def _on_pane_step(self, state: _SideState, index: int) -> None:
        if state.step_label is not None:
            total = state.total_steps_fn() if state.total_steps_fn else 0
            total_txt = str(total) if total else "?"
            state.step_label.setText(f"Step {index}/{total_txt}")

    def _on_pane_elapsed(self, state: _SideState, seconds: float) -> None:
        if state.elapsed_label is None or state.pane is None:
            return
        visual_time = state.pane.elapsed_seconds()  # Wall clock time
        logical_time = state.pane.logical_seconds()  # Algorithm logical time
        caps = state.transport.capabilities() if state.transport is not None else {}
        if caps.get("true_total", True):
            state.elapsed_label.setText(f"Visual {visual_time:.2f}s · True {logical_time:.2f}s")
        else:
            state.elapsed_label.setText(f"Visual {visual_time:.2f}s · True ??.??s (estimating)")

    def _on_pane_finished(self, state: _SideState) -> None:
        if state.pane is not None and state.transport is not None:
            state.transport.set_capability("true_total", state.visualizer.total_steps_known())
        if state.elapsed_label is not None and state.pane is not None:
            visual_time = state.pane.elapsed_seconds()  # Wall clock time
            logical_time = state.pane.logical_seconds()  # Algorithm logical time
            caps = state.transport.capabilities() if state.transport is not None else {}
            suffix = "" if caps.get("true_total", True) else " (estimate)"
            state.elapsed_label.setText(
                f"Visual {visual_time:.2f}s · True {logical_time:.2f}s (Finished{suffix})"
            )
        self._post_toast(f"{state.name} finished.")

    def _post_toast(self, message: str) -> None:
        if self._status_prefix:
            self.status_strip.setText(f"{self._status_prefix} • {message}")
        else:
            self.status_strip.setText(message)

    def _on_left_algo_changed(self, index: int) -> None:
        algo = self.left_combo.itemData(index)
        if not algo:
            return
        self._replace_visualizer(self._left, str(algo))
        self._settings.setValue("compare/left", algo)

    def _on_right_algo_changed(self, index: int) -> None:
        algo = self.right_combo.itemData(index)
        if not algo:
            return
        self._replace_visualizer(self._right, str(algo))
        self._settings.setValue("compare/right", algo)

    def _replace_visualizer(self, state: _SideState, algo_name: str) -> None:
        old_viz = state.visualizer
        splitter = state.splitter
        top_widget = splitter.widget(0)
        if top_widget is not None:
            top_widget.setParent(None)
        old_viz.deleteLater()
        info = INFO[algo_name]
        viz = AlgorithmVisualizerBase(
            algo_info=info,
            algo_func=REGISTRY[algo_name],
            show_controls=False,
        )
        detail_widget: QWidget
        if viz.right_panel is not None:
            detail_widget = viz.right_panel
            detail_widget.setParent(None)
            detail_widget.setVisible(True)
        else:
            detail_widget = QWidget()
            layout = QVBoxLayout(detail_widget)
            notice = QLabel("Details unavailable for this algorithm.")
            notice.setWordWrap(True)
            layout.addWidget(notice)
            layout.addStretch(1)
        state.detail_area.takeWidget()
        state.detail_area.setWidget(detail_widget)
        state.detail_area.setVisible(state.details_button.isChecked())
        splitter.insertWidget(0, viz)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        if state.detail_area.isVisible():
            splitter.setSizes([3_000_000, 1_000_000])
        else:
            splitter.setSizes([1_000_000, 0])

        state.visualizer = viz
        state.name = algo_name
        state.total_steps_fn = viz.total_steps

        # Re-establish focus management for the new visualizer
        viz.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # Store the old mouse press event handler
        old_mouse_press = viz.mousePressEvent

        def handle_mouse_press(event):
            # Find the parent CompareWindow
            parent = self.parent()
            while parent and not isinstance(parent, CompareWindow):
                parent = parent.parent()
            if parent and hasattr(parent, "_on_pane_clicked"):
                parent._on_pane_clicked(state.slot, event)
            # Call original handler
            if callable(old_mouse_press):
                old_mouse_press(event)

        viz.mousePressEvent = handle_mouse_press

        pane = Pane(
            visualizer=viz,
            step_forward=viz.player_step_forward,
            step_back=viz.player_step_back,
            step_index=viz.player_step_index,
            total_steps=state.total_steps_fn,
            on_finished=lambda st=state: self._on_pane_finished(st),
        )
        state.pane = pane
        state.transport = viz.transport
        pane.stepped.connect(lambda idx, st=state: self._on_pane_step(st, idx))
        pane.elapsed_updated.connect(lambda secs, st=state: self._on_pane_elapsed(st, secs))
        pane.finished.connect(lambda st=state: self._on_pane_finished(st))
        if state.transport is not None:
            state.transport.set_capability("true_total", False)

        if state.title_label is not None:
            state.title_label.setText(algo_name)
        with contextlib.suppress(TypeError):
            state.details_button.toggled.disconnect()
        state.details_button.toggled.connect(
            lambda checked, st=state: self._on_toggle_details(st, checked)
        )

        if not state.details_button.isChecked():
            splitter.setSizes([1_000_000, 0])
            pane.set_hud_visible(True)
            pane.toggle_details(False)
        else:
            pane.set_hud_visible(False)
            pane.toggle_details(True)

        if self._current_array is not None:
            viz.prime_external_run(self._current_array)
            pane.reset()
            pane.set_hud_visible(not state.details_button.isChecked())
            pane.toggle_details(state.details_button.isChecked())
            state.transport.set_capability("true_total", state.visualizer.total_steps_known())
            self._dataset_ready = True
        else:
            self._dataset_ready = False
            if state.transport is not None:
                state.transport.set_capability("true_total", False)
        pane.set_show_values(self.show_values_check.isChecked())
        viz.set_fps(self.fps_slider.value())
        theme = self._settings.value("ui/theme", "dark")
        if isinstance(theme, bytes):
            theme = theme.decode()
        viz.apply_theme(theme if isinstance(theme, str) else "dark")
        self._update_transport_capabilities()
        self._refresh_controller()

    def _on_generate_clicked(self) -> None:
        try:
            preset_key = self.preset_combo.currentData()
            if not isinstance(preset_key, str):
                preset_key = DEFAULT_PRESET_KEY
            self._current_preset = preset_key
            self._settings.setValue("compare/preset", preset_key)
            seed = self._resolve_seed()
            rng = random.Random(seed)
            cfg = self._left.visualizer.cfg
            array = generate_dataset(
                preset_key,
                cfg.default_n,
                cfg.min_val,
                cfg.max_val,
                rng,
            )
            self._apply_array(array)
            self._dataset_ready = True
        except Exception as exc:
            self._error(str(exc))

    def _resolve_seed(self) -> int:
        seed_text = self.seed_edit.text().strip()
        if seed_text:
            try:
                seed = int(seed_text)
            except ValueError as exc:
                raise ValueError("Seed must be an integer") from exc
        else:
            seed = random.SystemRandom().randint(0, 2**32 - 1)
            self.seed_edit.setText(str(seed))
        self._current_seed = seed
        self._settings.setValue("compare/seed", seed)
        return seed

    def _apply_array(self, array: list[int]) -> None:
        self._current_array = list(array)
        joined = ",".join(str(x) for x in array)
        self.array_edit.setText(joined)
        start_time = time.perf_counter()
        for state in (self._left, self._right):
            state.start_time = start_time
            state.visualizer.prime_external_run(array)
            if state.pane is not None:
                state.pane.reset()
                state.pane.set_hud_visible(not state.details_button.isChecked())
                state.pane.toggle_details(state.details_button.isChecked())
                state.pane.set_show_values(self.show_values_check.isChecked())
                if state.transport is not None:
                    state.transport.set_capability(
                        "true_total", state.visualizer.total_steps_known()
                    )
            else:
                state.visualizer.set_show_hud(not state.details_button.isChecked())
                state.visualizer.set_show_values(self.show_values_check.isChecked())
            if state.step_label is not None:
                state.step_label.setText("Step 0/?")
            if state.elapsed_label is not None:
                state.elapsed_label.setText("Visual 0.00s · True 0.00s")
        self._update_status()
        self._update_transport_capabilities()
        self._dataset_ready = True

    # Public helper for tests/automation --------------------------------

    def prepare_dataset(self, array: list[int]) -> None:
        self._apply_array(array)

    def toggle_details_for_side(self, side: str, on: bool) -> None:
        state = self._left if side.lower() == "left" else self._right
        state.details_button.setChecked(on)

    def _parse_array_input(self) -> list[int] | None:
        text = self.array_edit.text().strip()
        if not text:
            return None
        parts = [p for p in text.replace(" ", "").split(",") if p]
        return [int(p) for p in parts]

    def _ensure_dataset(self) -> bool:
        if self._dataset_ready:
            return True
        if self._current_array is None:
            parsed = self._parse_array_input()
            if parsed:
                self._apply_array(parsed)
            else:
                try:
                    self._on_generate_clicked()
                except Exception:
                    return False
        else:
            self._apply_array(self._current_array)
        self._dataset_ready = True
        return True

    def _on_start_clicked(self) -> None:
        if not self._ensure_dataset():
            return
        self._controller.play()
        self._update_status()

    def _on_pause_clicked(self) -> None:
        self._controller.toggle_pause()

    def _on_reset_clicked(self) -> None:
        self._controller.reset()
        if self._current_array is not None:
            for state in (self._left, self._right):
                state.visualizer.prime_external_run(self._current_array)
                if state.pane is not None:
                    state.pane.reset()
                    state.pane.set_hud_visible(not state.details_button.isChecked())
                    state.pane.toggle_details(state.details_button.isChecked())
                    state.pane.set_show_values(self.show_values_check.isChecked())
                    if state.transport is not None:
                        state.transport.set_capability(
                            "true_total", state.visualizer.total_steps_known()
                        )
                else:
                    state.visualizer.set_show_hud(not state.details_button.isChecked())
                    state.visualizer.set_show_values(self.show_values_check.isChecked())
            self._dataset_ready = True
        else:
            self._dataset_ready = False
            for state in (self._left, self._right):
                if state.pane is not None and state.transport is not None:
                    state.transport.set_capability("true_total", False)
        self._update_status()

    def _on_step_forward(self) -> None:
        if not self._ensure_dataset():
            return
        self._controller.step_forward()

    def _on_step_back(self) -> None:
        if not self._ensure_dataset():
            return
        self._controller.step_back()

    def _on_fps_changed(self, value: int) -> None:
        sender = self.sender()
        for widget in (self.fps_slider, self.fps_spin):
            if widget is not sender:
                widget.blockSignals(True)
                widget.setValue(value)
                widget.blockSignals(False)
        self._settings.setValue("compare/fps", value)
        self._left.visualizer.set_fps(value)
        self._right.visualizer.set_fps(value)

    def _on_show_values_toggled(self, checked: bool) -> None:
        self._settings.setValue("compare/show_values", int(checked))
        for state in (self._left, self._right):
            if state.pane is not None:
                state.pane.set_show_values(checked)
            else:
                state.visualizer.set_show_values(checked)

    def apply_theme(self, theme: str) -> None:
        self._apply_theme_to_panes(theme)
        if theme == "high-contrast":
            style = """
QWidget#compare_root {
  background: #f0f2f8;
}
#compare_card {
  background: #ffffff;
  border: 1px solid rgba(15,111,255,0.45);
  border-radius: 10px;
}
QLabel { color: #0b1e44; }
QLabel#compare_hint { color: #0b1e44; font-size: 12px; }
QLabel#compare_status { color: #0b1e44; font-weight: 600; }
QLabel#compare_pane_title { font-weight: 600; font-size: 14px; }
QLineEdit, QComboBox, QSpinBox {
  background: #ffffff;
  border: 1px solid #0f6fff;
  border-radius: 6px;
  color: #0b1e44;
  padding: 4px 6px;
}
QPushButton, QToolButton {
  background: #ffffff;
  border: 1px solid #0f6fff;
  border-radius: 8px;
  color: #0b1e44;
  padding: 6px 10px;
}
QPushButton:hover, QToolButton:hover {
  background: #eaf2ff;
}
"""
        else:
            style = """
QWidget#compare_root {
  background: #11151d;
}
#compare_card {
  background: #1a2230;
  border: 1px solid rgba(106,160,255,0.35);
  border-radius: 10px;
}
QLabel { color: #cfd6e6; }
QLabel#compare_hint { color: #8fa3c7; font-size: 12px; }
QLabel#compare_status { color: #ffffff; font-weight: 600; }
QLabel#compare_pane_title { font-weight: 600; font-size: 14px; color: #ffffff; }
QLineEdit, QComboBox, QSpinBox {
  background: #111822;
  border: 1px solid rgba(106,160,255,0.45);
  border-radius: 6px;
  color: #e6efff;
  padding: 4px 6px;
}
QPushButton, QToolButton {
  background: #1f2734;
  border: 1px solid rgba(106,160,255,0.55);
  border-radius: 8px;
  color: #e6e6e6;
  padding: 6px 10px;
}
QPushButton:hover, QToolButton:hover {
  background: #273246;
}
"""
        self.setStyleSheet(style)

    def _error(self, message: str) -> None:
        QMessageBox.critical(self, "Compare Mode", message)


class CompareWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._settings = QSettings(ORG_NAME, APP_NAME)
        self.setWindowTitle("Compare Algorithms")
        self.resize(1280, 860)
        self._view = CompareView()
        self.setCentralWidget(self._view)

        # Initialize focus tracking
        self._focused_pane = "left"  # Default to left pane
        self._setup_focus_management()

        theme = self._settings.value("ui/theme", "dark")
        if isinstance(theme, bytes):
            theme = theme.decode()
        self.current_theme = theme if theme in {"dark", "high-contrast"} else "dark"
        self.apply_theme(self.current_theme)
        self._build_menu()

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

    def apply_theme(self, theme: str) -> None:
        self.current_theme = theme if theme in {"dark", "high-contrast"} else "dark"
        self._settings.setValue("ui/theme", self.current_theme)
        apply_global_tooltip_theme(self.current_theme)
        self._view.apply_theme(self.current_theme)

        if hasattr(self, "theme_action"):
            self.theme_action.blockSignals(True)
            self.theme_action.setChecked(self.current_theme == "high-contrast")
            self.theme_action.blockSignals(False)

    def _on_theme_toggled(self, checked: bool) -> None:
        theme = "high-contrast" if checked else "dark"
        self.apply_theme(theme)

    def _setup_focus_management(self) -> None:
        """Setup mouse click handlers for focus management."""
        if hasattr(self._view, "_left") and hasattr(self._view, "_right"):
            # Make visualizers focusable
            self._view._left.visualizer.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self._view._right.visualizer.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

            # Connect mouse press events to focus handlers
            self._view._left.visualizer.mousePressEvent = lambda e: self._on_pane_clicked("left", e)
            self._view._right.visualizer.mousePressEvent = lambda e: self._on_pane_clicked(
                "right", e
            )
            # Set initial focus indicator
            self._update_focus_indicator()

    def _on_pane_clicked(self, pane_side: str, event) -> None:
        """Handle pane click to change focus."""
        self._focused_pane = pane_side
        self._update_focus_indicator()

        # Clear focus from any text input fields
        if hasattr(self._view, "array_edit"):
            self._view.array_edit.clearFocus()

        # Set focus to the clicked visualizer
        if pane_side == "left":
            self._view._left.visualizer.setFocus(Qt.FocusReason.MouseFocusReason)
            super(type(self._view._left.visualizer), self._view._left.visualizer).mousePressEvent(
                event
            )
        else:
            self._view._right.visualizer.setFocus(Qt.FocusReason.MouseFocusReason)
            super(type(self._view._right.visualizer), self._view._right.visualizer).mousePressEvent(
                event
            )

    def _update_focus_indicator(self) -> None:
        """Update visual indicators for focused pane."""
        if not hasattr(self._view, "_left") or not hasattr(self._view, "_right"):
            return

        # Add visual border to focused pane
        if self._focused_pane == "left":
            self._view._left.visualizer.setStyleSheet("border: 2px solid #0084ff;")
            self._view._right.visualizer.setStyleSheet("border: 1px solid transparent;")
        else:
            self._view._left.visualizer.setStyleSheet("border: 1px solid transparent;")
            self._view._right.visualizer.setStyleSheet("border: 2px solid #0084ff;")

    def keyPressEvent(self, event) -> None:
        """Handle keyboard shortcuts for the focused pane."""
        if not hasattr(self._view, "_left") or not hasattr(self._view, "_right"):
            super().keyPressEvent(event)
            return

        # Make sure dataset is ready before allowing playback commands
        if (
            not self._view._dataset_ready
            and event.key() != Qt.Key.Key_Tab
            and event.key()
            in (
                Qt.Key.Key_Space,
                Qt.Key.Key_Left,
                Qt.Key.Key_Right,
                Qt.Key.Key_Comma,
                Qt.Key.Key_Period,
                Qt.Key.Key_Less,
                Qt.Key.Key_Greater,
            )
            and not self._view._ensure_dataset()
        ):
            return

        # Get the focused pane
        focused_state = self._view._left if self._focused_pane == "left" else self._view._right

        # Handle keyboard shortcuts
        if event.key() == Qt.Key.Key_Space:
            # Toggle play/pause for focused pane only
            if focused_state.pane is not None:
                if focused_state.pane.is_running:
                    focused_state.pane.pause()
                else:
                    # Ensure dataset before playing
                    if self._view._ensure_dataset():
                        focused_state.pane.play()

        elif event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Comma, Qt.Key.Key_Less):
            # Step backward for focused pane (<, Left arrow, comma)
            if focused_state.pane is not None and focused_state.pane.player.capabilities.get(
                "step_back", False
            ):
                focused_state.pane.step_back()

        elif event.key() in (Qt.Key.Key_Right, Qt.Key.Key_Period, Qt.Key.Key_Greater):
            # Step forward for focused pane (>, Right arrow, period)
            if (
                focused_state.pane is not None
                and self._view._ensure_dataset()
                and (
                    focused_state.pane.step_index() < focused_state.visualizer.total_steps()
                    or focused_state.visualizer.total_steps() == 0
                )
            ):
                focused_state.pane.step_forward()

        elif event.key() == Qt.Key.Key_R:
            # Reset focused pane
            if focused_state.pane is not None:
                focused_state.pane.reset()
                # Also need to re-prime the visualization
                if self._view._current_array is not None:
                    focused_state.visualizer.prime_external_run(self._view._current_array)

        elif event.key() == Qt.Key.Key_Tab:
            # Tab to switch focus between panes
            self._focused_pane = "right" if self._focused_pane == "left" else "left"
            self._update_focus_indicator()
            # Clear focus from text fields and set to visualizer
            if hasattr(self._view, "array_edit"):
                self._view.array_edit.clearFocus()
            focused_viz = (
                self._view._left.visualizer
                if self._focused_pane == "left"
                else self._view._right.visualizer
            )
            focused_viz.setFocus(Qt.FocusReason.TabFocusReason)
            event.accept()
            return

        else:
            # Pass unhandled events to parent
            super().keyPressEvent(event)
