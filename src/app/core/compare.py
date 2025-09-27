from __future__ import annotations

import random
import time
from dataclasses import dataclass

from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.algos.registry import INFO, REGISTRY
from app.core.base import AlgorithmVisualizerBase
from app.presets import DEFAULT_PRESET_KEY, generate_dataset, get_presets


@dataclass(slots=True)
class _SideState:
    name: str
    visualizer: AlgorithmVisualizerBase


class CompareView(QWidget):
    """Split-view comparison for two algorithms with linked playback controls."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = QSettings()
        self._current_array: list[int] | None = None
        self._current_seed: int | None = None
        self._current_preset: str = DEFAULT_PRESET_KEY

        algo_names = sorted(INFO.keys())
        left_default = algo_names[0]
        right_default = algo_names[1] if len(algo_names) > 1 else algo_names[0]

        self._left = _SideState(left_default, self._create_visualizer(left_default))
        self._right = _SideState(right_default, self._create_visualizer(right_default))

        self._build_ui(algo_names)
        self._restore_settings()

    # ------------------------------------------------------------------ UI --

    def _build_ui(self, algo_names: list[str]) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        selector_row = QHBoxLayout()
        selector_row.setSpacing(12)
        selector_row.addWidget(QLabel("Left algorithm:"))
        self.left_combo = QComboBox()
        for name in algo_names:
            self.left_combo.addItem(name, name)
        selector_row.addWidget(self.left_combo, 1)

        selector_row.addWidget(QLabel("Right algorithm:"))
        self.right_combo = QComboBox()
        for name in algo_names:
            self.right_combo.addItem(name, name)
        selector_row.addWidget(self.right_combo, 1)

        root.addLayout(selector_row)

        dataset_row = QHBoxLayout()
        dataset_row.setSpacing(8)
        dataset_row.addWidget(QLabel("Array:"))
        self.array_edit = QLineEdit()
        self.array_edit.setPlaceholderText("e.g. 4,1,3,2")
        dataset_row.addWidget(self.array_edit, 2)

        self.preset_combo = QComboBox()
        for preset in get_presets():
            self.preset_combo.addItem(preset.label, preset.key)
        dataset_row.addWidget(self.preset_combo)

        self.seed_edit = QLineEdit()
        self.seed_edit.setPlaceholderText("seed (auto)")
        self.seed_edit.setFixedWidth(120)
        dataset_row.addWidget(self.seed_edit)

        self.random_button = QPushButton("Generate")
        dataset_row.addWidget(self.random_button)

        root.addLayout(dataset_row)

        controls_row = QHBoxLayout()
        controls_row.setSpacing(8)
        self.start_button = QPushButton("Start")
        self.pause_button = QPushButton("Pause/Resume")
        self.reset_button = QPushButton("Reset")
        self.step_back_button = QPushButton("Step ◀")
        self.step_forward_button = QPushButton("Step ▶")
        controls_row.addWidget(self.start_button)
        controls_row.addWidget(self.pause_button)
        controls_row.addWidget(self.reset_button)
        controls_row.addWidget(self.step_back_button)
        controls_row.addWidget(self.step_forward_button)

        controls_row.addWidget(QLabel("FPS:"))
        self.fps_slider = QSlider(Qt.Orientation.Horizontal)
        self.fps_slider.setRange(1, 60)
        self.fps_slider.setValue(24)
        controls_row.addWidget(self.fps_slider, 1)
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 60)
        self.fps_spin.setValue(24)
        self.fps_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.fps_spin.setFixedWidth(60)
        controls_row.addWidget(self.fps_spin)

        self.show_values_check = QCheckBox("Show values")
        controls_row.addWidget(self.show_values_check)

        root.addLayout(controls_row)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._left.visualizer)
        splitter.addWidget(self._right.visualizer)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter, 1)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)
        root.addWidget(divider)

        note = QLabel(
            "Linked controls operate both visualizers. Use Tab to reach buttons, "
            "Space to pause/resume, and Left/Right arrows for single-step playback."
        )
        note.setWordWrap(True)
        root.addWidget(note)

        # Connections
        self.left_combo.currentIndexChanged.connect(self._on_left_algo_changed)
        self.right_combo.currentIndexChanged.connect(self._on_right_algo_changed)
        self.random_button.clicked.connect(self._on_generate_clicked)
        self.start_button.clicked.connect(self._on_start_clicked)
        self.pause_button.clicked.connect(self._on_pause_clicked)
        self.reset_button.clicked.connect(self._on_reset_clicked)
        self.step_forward_button.clicked.connect(self._on_step_forward)
        self.step_back_button.clicked.connect(self._on_step_back)
        self.fps_slider.valueChanged.connect(self._on_fps_changed)
        self.fps_spin.valueChanged.connect(self._on_fps_changed)
        self.show_values_check.toggled.connect(self._on_show_values_toggled)

    # -------------------------------------------------------------- helpers --

    def _create_visualizer(self, algo_name: str) -> AlgorithmVisualizerBase:
        info = INFO[algo_name]
        viz = AlgorithmVisualizerBase(
            algo_info=info,
            algo_func=REGISTRY[algo_name],
            show_controls=False,
        )
        viz.setMinimumWidth(520)
        return viz

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
        self.fps_slider.setValue(fps)
        self.fps_spin.setValue(fps)
        self._sync_fps_to_visualizers(fps)

        show_values = bool(int(self._settings.value("compare/show_values", 0)))
        self.show_values_check.setChecked(show_values)
        self._left.visualizer.chk_labels.setChecked(show_values)
        self._right.visualizer.chk_labels.setChecked(show_values)

    def _set_combo_value(self, combo: QComboBox, value: str | bytes | None) -> None:
        if isinstance(value, bytes):
            value = value.decode()
        if not value:
            return
        idx = combo.findData(value)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def apply_theme(self, theme: str) -> None:
        self._left.visualizer.apply_theme(theme)
        self._right.visualizer.apply_theme(theme)

    # ----------------------------------------------------------- data ops --

    def _parse_input(self) -> list[int] | None:
        text = self.array_edit.text().strip()
        if not text:
            return None
        parts = [p for p in text.replace(" ", "").split(",") if p]
        return [int(p) for p in parts]

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
        self._prime_visualizer(self._left.visualizer, array)
        self._prime_visualizer(self._right.visualizer, array)

    def _prime_visualizer(self, viz: AlgorithmVisualizerBase, array: list[int]) -> None:
        viz._timer.stop()
        viz._step_source = None
        viz._confirm_progress = -1
        viz._set_array(array, persist=False)
        viz._step_source = viz._generate_steps(list(viz._array))
        viz._t0 = time.time()
        viz._update_ui_state("paused")

    def _sync_fps_to_visualizers(self, fps: int) -> None:
        for viz in (self._left.visualizer, self._right.visualizer):
            viz.sld_fps.blockSignals(True)
            viz.spn_fps.blockSignals(True)
            viz.sld_fps.setValue(fps)
            viz.spn_fps.setValue(fps)
            viz.sld_fps.blockSignals(False)
            viz.spn_fps.blockSignals(False)

    # ----------------------------------------------------------- slots --

    def _on_left_algo_changed(self, index: int) -> None:
        algo = self.left_combo.itemData(index)
        if not algo:
            return
        self._replace_visualizer(side="left", algo_name=algo)
        self._settings.setValue("compare/left", algo)

    def _on_right_algo_changed(self, index: int) -> None:
        algo = self.right_combo.itemData(index)
        if not algo:
            return
        self._replace_visualizer(side="right", algo_name=algo)
        self._settings.setValue("compare/right", algo)

    def _replace_visualizer(self, *, side: str, algo_name: str) -> None:
        state = self._left if side == "left" else self._right
        parent = state.visualizer.parent()
        if parent is not None and isinstance(parent, QSplitter):
            index = parent.indexOf(state.visualizer)
            old_widget = parent.widget(index)
            if old_widget is not None:
                old_widget.setParent(None)
            state.visualizer.deleteLater()
            new_viz = self._create_visualizer(algo_name)
            parent.insertWidget(index, new_viz)
        else:
            new_viz = self._create_visualizer(algo_name)
        state.visualizer = new_viz
        state.name = algo_name
        if self._current_array is not None:
            self._prime_visualizer(new_viz, self._current_array)
        show_values = self.show_values_check.isChecked()
        new_viz.chk_labels.setChecked(show_values)
        fps = self.fps_slider.value()
        self._sync_fps_to_visualizers(fps)
        theme = self._settings.value("ui/theme", "dark")
        if isinstance(theme, bytes):
            theme = theme.decode()
        new_viz.apply_theme(theme if isinstance(theme, str) else "dark")

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
        except Exception as exc:
            self._error(str(exc))

    def _prime_if_needed(self) -> bool:
        if self._current_array is None:
            parsed = self._parse_input()
            if parsed:
                self._apply_array(parsed)
            else:
                try:
                    self._on_generate_clicked()
                except Exception as exc:
                    self._error(str(exc))
                    return False
        else:
            self._apply_array(self._current_array)
        return True

    def _on_start_clicked(self) -> None:
        if not self._prime_if_needed():
            return
        interval = int(1000 / max(1, self.fps_slider.value()))
        for viz in (self._left.visualizer, self._right.visualizer):
            viz._timer.start(interval)
            viz._update_ui_state("running")

    def _on_pause_clicked(self) -> None:
        any_active = any(
            viz._timer.isActive() for viz in (self._left.visualizer, self._right.visualizer)
        )
        if any_active:
            for viz in (self._left.visualizer, self._right.visualizer):
                viz._timer.stop()
                viz._update_ui_state("paused")
        else:
            interval = int(1000 / max(1, self.fps_slider.value()))
            for viz in (self._left.visualizer, self._right.visualizer):
                viz._timer.start(interval)
                viz._update_ui_state("running")

    def _on_reset_clicked(self) -> None:
        for viz in (self._left.visualizer, self._right.visualizer):
            viz._timer.stop()
            viz._on_reset()
        if self._current_array is not None:
            self._apply_array(self._current_array)

    def _on_step_forward(self) -> None:
        if not self._prime_if_needed():
            return
        for viz in (self._left.visualizer, self._right.visualizer):
            viz._timer.stop()
            viz._on_step_forward()

    def _on_step_back(self) -> None:
        for viz in (self._left.visualizer, self._right.visualizer):
            viz._timer.stop()
            viz._on_step_back()

    def _on_fps_changed(self, value: int) -> None:
        sender = self.sender()
        for widget in (self.fps_slider, self.fps_spin):
            if widget is not sender:
                widget.blockSignals(True)
                widget.setValue(value)
                widget.blockSignals(False)
        self._settings.setValue("compare/fps", value)
        self._sync_fps_to_visualizers(value)
        if any(viz._timer.isActive() for viz in (self._left.visualizer, self._right.visualizer)):
            interval = int(1000 / max(1, value))
            for viz in (self._left.visualizer, self._right.visualizer):
                viz._timer.start(interval)

    def _on_show_values_toggled(self, checked: bool) -> None:
        self._settings.setValue("compare/show_values", int(checked))
        self._left.visualizer.chk_labels.setChecked(checked)
        self._right.visualizer.chk_labels.setChecked(checked)

    def _error(self, message: str) -> None:
        QMessageBox.critical(self, "Compare Mode", message)
