from __future__ import annotations

import contextlib
import random
import time
from collections.abc import Callable
from dataclasses import dataclass

from PyQt6.QtCore import QSettings, Qt, QTimer
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
from app.ui_compare.compare_theme import apply_compare_theme
from app.ui_shared.constants import APP_NAME, ORG_NAME
from app.ui_shared.pane import Pane
from app.ui_shared.theme import apply_global_tooltip_theme
from app.ui_shared.design_system import SPACING, COLORS

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

        # Debounce timer for auto-applying typed input
        self._input_debounce_timer = QTimer(self)
        self._input_debounce_timer.setSingleShot(True)
        self._input_debounce_timer.setInterval(500)  # 500ms delay after typing stops
        self._input_debounce_timer.timeout.connect(self._try_auto_apply_input)

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
        root.setContentsMargins(8, 8, 8, 8)  # Reduced margins for more space
        root.setSpacing(8)  # Reduced spacing for more compactness

        # Keep controls visible by default - no separate hide button needed

        # Create vertical layout for two control panels WITHOUT gap
        self.controls_container = QWidget()
        self.controls_container.setObjectName("controls_container")
        controls_layout = QVBoxLayout(self.controls_container)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(0)  # NO SPACING between panels

        # Build two separate panels
        self.dataset_card = self._build_dataset_card(algo_names)
        self.transport_card = self._build_transport_card()

        controls_layout.addWidget(self.dataset_card)
        controls_layout.addWidget(self.transport_card)

        root.addWidget(self.controls_container)

        # Remove redundant status strip - we can see the algorithms already

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
        """Build dataset control card."""
        card = self._make_card()
        card.setObjectName("dataset_card")

        layout = QHBoxLayout(card)
        layout.setContentsMargins(SPACING["sm"], SPACING["xs"], SPACING["sm"], SPACING["xs"])
        layout.setSpacing(SPACING["sm"])

        # Algorithm selectors
        lbl_left = QLabel("Left:")
        lbl_left.setObjectName("control_label")
        self.left_combo = QComboBox()
        self.left_combo.setObjectName("algo_selector")
        for name in algo_names:
            self.left_combo.addItem(name, name)

        lbl_right = QLabel("Right:")
        lbl_right.setObjectName("control_label")
        self.right_combo = QComboBox()
        self.right_combo.setObjectName("algo_selector")
        for name in algo_names:
            self.right_combo.addItem(name, name)

        # Array input
        lbl_array = QLabel("Array:")
        lbl_array.setObjectName("control_label")
        self.array_edit = QLineEdit()
        self.array_edit.setObjectName("array_input")
        self.array_edit.setPlaceholderText("e.g., 5,2,9,1,5,6")

        # Preset
        lbl_preset = QLabel("Preset:")
        lbl_preset.setObjectName("control_label")
        self.preset_combo = QComboBox()
        self.preset_combo.setObjectName("preset_selector")
        for preset in get_presets():
            self.preset_combo.addItem(preset.label, preset.key)

        # Seed
        lbl_seed = QLabel("Seed:")
        lbl_seed.setObjectName("control_label")
        self.seed_edit = QLineEdit()
        self.seed_edit.setObjectName("seed_input")
        self.seed_edit.setPlaceholderText("auto")
        self.seed_edit.setFixedWidth(100)

        # Generate button
        self.generate_button = QPushButton("Generate")
        self.generate_button.setObjectName("generate_button")

        # Add all to layout
        layout.addWidget(lbl_left)
        layout.addWidget(self.left_combo, 1)
        layout.addWidget(lbl_right)
        layout.addWidget(self.right_combo, 1)
        layout.addWidget(lbl_array)
        layout.addWidget(self.array_edit, 2)
        layout.addWidget(lbl_preset)
        layout.addWidget(self.preset_combo, 1)
        layout.addWidget(lbl_seed)
        layout.addWidget(self.seed_edit)
        layout.addWidget(self.generate_button)

        # Connect signals
        self.left_combo.currentIndexChanged.connect(self._on_left_algo_changed)
        self.right_combo.currentIndexChanged.connect(self._on_right_algo_changed)
        self.generate_button.clicked.connect(self._on_generate_clicked)
        self.array_edit.textChanged.connect(self._mark_dataset_dirty)
        self.preset_combo.currentIndexChanged.connect(self._mark_dataset_dirty)
        self.seed_edit.textChanged.connect(self._mark_dataset_dirty)

        card.setMaximumHeight(50)
        return card

    def _build_transport_card(self) -> QFrame:
        """Build transport control card."""
        card = self._make_card()
        card.setObjectName("transport_card")

        layout = QHBoxLayout(card)
        layout.setContentsMargins(SPACING["sm"], SPACING["xs"], SPACING["sm"], SPACING["xs"])
        layout.setSpacing(SPACING["sm"])

        # Transport buttons
        self.start_button = QPushButton("Start")
        self.start_button.setObjectName("transport_button")
        self.pause_button = QPushButton("Pause")
        self.pause_button.setObjectName("transport_button")
        self.reset_button = QPushButton("Reset")
        self.reset_button.setObjectName("transport_button")
        self.step_back_button = QPushButton("Step")
        self.step_back_button.setObjectName("transport_button")
        self.step_forward_button = QPushButton("Step")
        self.step_forward_button.setObjectName("transport_button")

        # FPS controls
        fps_label = QLabel("FPS:")
        fps_label.setObjectName("control_label")
        self.fps_slider = QSlider(Qt.Orientation.Horizontal)
        self.fps_slider.setRange(1, 60)
        self.fps_slider.setValue(24)
        self.fps_slider.setFixedWidth(200)

        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 60)
        self.fps_spin.setValue(24)
        self.fps_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.fps_spin.setFixedWidth(50)
        self.fps_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Show values
        self.show_values_check = QCheckBox("Show values")
        self.show_values_check.setObjectName("control_checkbox")

        # Collapse button
        self.controls_toggle = QPushButton("▼ Hide")
        self.controls_toggle.setCheckable(True)
        self.controls_toggle.setToolTip("Toggle dataset controls visibility")
        self.controls_toggle.setObjectName("transport_button")
        self.controls_toggle.setFixedWidth(80)
        self.controls_toggle.toggled.connect(self._on_controls_toggled)

        # Add to layout
        layout.addWidget(self.start_button)
        layout.addWidget(self.pause_button)
        layout.addWidget(self.reset_button)
        layout.addWidget(self.step_back_button)
        layout.addWidget(self.step_forward_button)
        layout.addStretch()
        layout.addWidget(fps_label)
        layout.addWidget(self.fps_slider)
        layout.addWidget(self.fps_spin)
        layout.addWidget(self.show_values_check)
        layout.addWidget(self.controls_toggle)

        # Connect signals
        self.start_button.clicked.connect(self._on_start_clicked)
        self.pause_button.clicked.connect(self._on_pause_clicked)
        self.reset_button.clicked.connect(self._on_reset_clicked)
        self.step_forward_button.clicked.connect(self._on_step_forward)
        self.step_back_button.clicked.connect(self._on_step_back)
        self.fps_slider.valueChanged.connect(self._on_fps_changed)
        self.fps_spin.valueChanged.connect(self._on_fps_changed)
        self.show_values_check.toggled.connect(self._on_show_values_toggled)

        card.setMaximumHeight(50)
        self._update_transport_capabilities()
        return card


    def _compose_pane(self, state: _SideState) -> QWidget:
        container = QWidget()
        container.setObjectName("compare_pane_container")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(SPACING["xs"], SPACING["xs"], SPACING["xs"], SPACING["xs"])
        layout.setSpacing(SPACING["xs"])

        # Simple header with just title and details toggle
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(SPACING["xs"])

        title = QLabel(state.name)
        title.setObjectName("compare_pane_title")
        state.title_label = title

        # Style the details button properly
        state.details_button.setObjectName("details_toggle")
        state.details_button.setToolTip("Toggle algorithm details panel")

        header_row.addWidget(title)
        header_row.addStretch(1)
        header_row.addWidget(state.details_button)
        layout.addLayout(header_row)

        # Remove duplicate Step and Time displays - info is in the viz already
        # Set these to None so other code doesn't crash
        state.step_label = None
        state.elapsed_label = None

        # Main visualization area
        layout.addWidget(state.splitter, 1)

        # Setup focus handling for the canvas
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
        # Status info removed - it's redundant
        pass

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
        # Toggle only the dataset card visibility
        self.dataset_card.setVisible(not hidden)
        self.controls_toggle.setText("▲ Show" if hidden else "▼ Hide")
        self.controls_toggle.setToolTip("Show dataset controls" if hidden else "Hide dataset controls")


    def _mark_dataset_dirty(self) -> None:
        """Mark dataset as needing regeneration and start debounce timer for auto-apply."""
        self._dataset_ready = False
        self._current_array = None
        # Restart the debounce timer - will auto-apply after user stops typing
        self._input_debounce_timer.start()

    def _try_auto_apply_input(self) -> None:
        """Attempt to parse and apply the current input text automatically."""
        try:
            parsed = self._parse_array_input()
            if parsed and len(parsed) > 0:
                self._apply_array(parsed)
                self._dataset_ready = True
        except (ValueError, TypeError):
            # Invalid input, do nothing
            pass

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
        # Toast messages removed - status bar is gone
        pass

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
        apply_compare_theme(self, theme)

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
            # Toggle play/pause using controller like buttons do
            if self._view._controller.is_running():
                self._view._controller.toggle_pause()
            else:
                # Ensure dataset before playing
                if self._view._ensure_dataset():
                    self._view._controller.play()

        elif event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Comma, Qt.Key.Key_Less):
            # Step backward - use the same controller as Step button
            if self._view._ensure_dataset():
                self._view._controller.step_back()

        elif event.key() in (Qt.Key.Key_Right, Qt.Key.Key_Period, Qt.Key.Key_Greater):
            # Step forward - use the same controller as Step button
            if self._view._ensure_dataset():
                self._view._controller.step_forward()

        elif event.key() == Qt.Key.Key_R:
            # Reset using controller like Reset button does
            self._view._controller.reset()
            if self._view._current_array is not None:
                for state in (self._view._left, self._view._right):
                    state.visualizer.prime_external_run(self._view._current_array)

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
