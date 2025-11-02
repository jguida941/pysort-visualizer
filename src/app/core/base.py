from __future__ import annotations

import csv
import json
import logging
import os
import sys
import time
from collections.abc import Callable, Iterator
from contextlib import suppress
from dataclasses import dataclass, fields
from html import escape
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, get_type_hints

from PIL import Image
from PIL.ImageQt import fromqimage
from PyQt6.QtCore import QRect, QSettings, QSize, Qt, QTimer
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFontDatabase,
    QHideEvent,
    QKeySequence,
    QPainter,
    QPaintEvent,
    QPen,
    QShortcut,
)
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QSplitter,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.algos.registry import INFO, REGISTRY, AlgoInfo
from app.core.step import Step
from app.presets import DEFAULT_PRESET_KEY, generate_dataset, get_preset, get_presets
from app.ui_shared.pane import Pane

try:
    from app.ui_shared.professional_theme import generate_stylesheet
except ImportError:
    generate_stylesheet = None

AlgorithmFunc = Callable[[list[int]], Iterator[Step]]

THEME_PRESETS: dict[str, dict[str, dict[str, str]]] = {
    "dark": {
        "cfg": {
            "bg_color": "#0f1115",
            "bar_color": "#6aa0ff",
            "cmp_color": "#ffe08a",
            "swap_color": "#fa8072",
            "pivot_color": "#90ee90",
            "merge_color": "#a390ee",
            "key_color": "#3cd7d7",
            "shift_color": "#ff9f43",
            "confirm_color": "#62d26f",
            "hud_color": "#e6e6e6",
        },
        "style": {
            "widget_fg": "#e6e6e6",
            "widget_bg": "#0f1115",
            "caption_bg": "rgba(106,160,255,0.06)",
            "caption_border": "#6aa0ff",
            "placeholder_fg": "#b6bfca",
            "legend_fg": "#98a6c7",
            "legend_bg": "rgba(35,45,64,0.45)",
            "legend_border": "rgba(152,166,199,0.25)",
            "input_bg": "rgba(106,160,255,0.06)",
            "input_border": "#6aa0ff",
            "disabled_fg": "#7b8496",
            "list_bg": "rgba(106,160,255,0.04)",
            "list_border": "#6aa0ff",
            "focus_border": "#2f6bff",
            "focus_bg": "rgba(47,107,255,0.14)",
            "slider_focus_border": "#2f6bff",
            "card_bg": "rgba(35,45,64,0.35)",
        },
    },
    "high-contrast": {
        "cfg": {
            "bg_color": "#ffffff",
            "bar_color": "#0f6fff",
            "cmp_color": "#ff6f00",
            "swap_color": "#d32f2f",
            "pivot_color": "#00796b",
            "merge_color": "#5e35b1",
            "key_color": "#1565c0",
            "shift_color": "#c2185b",
            "confirm_color": "#2e7d32",
            "hud_color": "#111111",
        },
        "style": {
            "widget_fg": "#111111",
            "widget_bg": "#ffffff",
            "caption_bg": "rgba(15,111,255,0.12)",
            "caption_border": "#0f6fff",
            "placeholder_fg": "#4a4a4a",
            "legend_fg": "#1b1b1b",
            "legend_bg": "rgba(15,111,255,0.10)",
            "legend_border": "rgba(15,111,255,0.35)",
            "input_bg": "rgba(15,111,255,0.08)",
            "input_border": "#0f6fff",
            "disabled_fg": "#5f5f5f",
            "list_bg": "rgba(15,111,255,0.06)",
            "list_border": "#0f6fff",
            "focus_border": "#0b4bb3",
            "focus_bg": "rgba(11,75,179,0.12)",
            "slider_focus_border": "#0b4bb3",
            "card_bg": "rgba(15,111,255,0.08)",
        },
    },
}

DEFAULT_THEME = "dark"
PRECOMPUTE_STEP_CAP = 10_000


def _install_crash_hook() -> None:
    def _hook(exc_type: type[BaseException], exc: BaseException, tb: Any) -> None:
        logging.getLogger("sorting_viz").exception(
            "Uncaught exception", exc_info=(exc_type, exc, tb)
        )
        try:
            from PyQt6.QtWidgets import QApplication, QMessageBox

            if QApplication.instance() is not None:
                QMessageBox.critical(
                    None,
                    "Unexpected error",
                    "The app hit an unexpected error.\n\nCheck the log file for details.",
                )
        except Exception:
            print("Unexpected error; check logs for details.", file=sys.stderr)

    sys.excepthook = _hook


# ------------------------ Logging ------------------------


def _build_logger() -> logging.Logger:
    from pathlib import Path

    user_log_dir_func: Callable[..., str] | None
    try:
        from platformdirs import user_log_dir as _user_log_dir

        user_log_dir_func = _user_log_dir
    except ImportError:  # pragma: no cover - platformdirs is optional for runtime
        user_log_dir_func = None

    logger = logging.getLogger("sorting_viz")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    if user_log_dir_func is not None:
        log_dir = Path(user_log_dir_func("sorting-visualizer", "org.pysort"))
    else:
        log_dir = Path.cwd() / "logs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        log_dir = Path.cwd() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "sorting_viz.log"
    try:
        fh = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=5)
    except OSError:
        fallback_dir = Path.cwd() / "logs"
        fallback_dir.mkdir(parents=True, exist_ok=True)
        fh = RotatingFileHandler(
            fallback_dir / "sorting_viz.log", maxBytes=1_000_000, backupCount=5
        )
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


LOGGER = _build_logger()


_install_crash_hook()

# ------------------------ Config ------------------------


@dataclass
class VizConfig:
    min_n: int = 5
    max_n: int = 200
    default_n: int = 32
    min_val: int = 1
    max_val: int = 200
    fps_min: int = 1
    fps_max: int = 60
    fps_default: int = 24
    bar_gap_px: int = 2
    padding_px: int = 10
    bg_color: str = "#0f1115"
    bar_color: str = "#4a9eff"  # Brighter blue for better visibility
    cmp_color: str = "#fbbf24"  # Golden yellow for comparison
    swap_color: str = "#f87171"  # Bright red for swaps
    pivot_color: str = "#4ade80"  # Bright green for pivot
    merge_color: str = "#a78bfa"  # Purple for merge
    key_color: str = "#06b6d4"  # Cyan for key
    shift_color: str = "#fb923c"  # Orange for shift
    confirm_color: str = "#10b981"  # Emerald green for confirmed
    hud_color: str = "#ffffff"  # Pure white for HUD text
    checkpoint_stride: int = 200  # snapshot frequency for scrub/reconstruct

    @staticmethod
    def _coerce(expected_type: type[Any] | str, raw: Any) -> Any:
        name = (
            expected_type
            if isinstance(expected_type, str)
            else getattr(expected_type, "__name__", "")
        )
        if expected_type is int or name == "int":
            return int(raw)
        if expected_type is float or name == "float":
            return float(raw)
        if expected_type is bool or name == "bool":
            if isinstance(raw, str):
                return raw.strip().lower() in {"1", "true", "yes", "on"}
            return bool(raw)
        if expected_type is str or name == "str":
            return str(raw)
        return raw

    @classmethod
    def from_settings(cls, settings: QSettings | None = None) -> VizConfig:
        settings = settings or QSettings()
        overrides: dict[str, Any] = {}
        hints = get_type_hints(cls)
        for field in fields(cls):
            settings_key = f"config/{field.name}"
            if settings.contains(settings_key):
                raw = settings.value(settings_key)
            else:
                env_key = f"SORT_VIZ_{field.name.upper()}"
                raw = os.environ.get(env_key)
            if raw not in (None, ""):
                expected = hints.get(field.name, field.type)
                overrides[field.name] = cls._coerce(expected, raw)
        return cls(**overrides)


# ------------------------ Canvas ------------------------


class VisualizationCanvas(QWidget):
    def __init__(
        self, get_state: Callable[[], dict[str, Any]], cfg: VizConfig, parent: QWidget | None = None
    ):
        super().__init__(parent)
        self._get_state = get_state
        self._cfg = cfg
        self._show_labels = False
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def minimumSizeHint(self) -> QSize:
        return QSize(360, 220)

    def set_show_labels(self, show: bool) -> None:
        self._show_labels = show
        self.update()

    def paintEvent(self, _event: QPaintEvent | None) -> None:
        state = self._get_state()
        arr: list[int] = state["array"]
        highlights: dict[str, tuple[int, ...]] = state["highlights"]
        confirms: tuple[int, ...] = state.get("confirm", tuple())
        metrics: dict[str, Any] = state["metrics"]
        hud_visible: bool = state.get("hud_visible", True)

        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(self._cfg.bg_color))

        pen = QPen(QColor("#0d0f14"))
        pen.setCosmetic(True)
        painter.setPen(pen)

        if arr:
            w = self.width()
            h = self.height()
            n = len(arr)
            gap = self._cfg.bar_gap_px
            bar_w = max(1, (w - 2 * self._cfg.padding_px - (n - 1) * gap) // max(1, n))
            x = self._cfg.padding_px

            max_val = max(arr)
            scale = (h - 2 * self._cfg.padding_px) / max(1, max_val)

            base = QBrush(QColor(self._cfg.bar_color))
            cmpb = QBrush(QColor(self._cfg.cmp_color))
            swpb = QBrush(QColor(self._cfg.swap_color))
            pivb = QBrush(QColor(self._cfg.pivot_color))
            mrgb = QBrush(QColor(self._cfg.merge_color))
            keyb = QBrush(QColor(self._cfg.key_color))
            shiftb = QBrush(QColor(self._cfg.shift_color))
            confb = QBrush(QColor(self._cfg.confirm_color))

            cmp_idx = set(highlights.get("compare", ()))
            swap_idx = set(highlights.get("swap", ()))
            pivot_idx = set(highlights.get("pivot", ()))
            merge_idx = set(highlights.get("merge", ()))
            key_idx = set(highlights.get("key", ()))
            shift_idx = set(highlights.get("shift", ()))
            confirm_idx = set(confirms)

            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            for i, v in enumerate(arr):
                bar_h = max(1, int(v * scale))
                y = h - self._cfg.padding_px - bar_h

                if i in confirm_idx:
                    brush = confb
                elif i in key_idx:
                    brush = keyb
                elif i in shift_idx:
                    brush = shiftb
                elif i in swap_idx:
                    brush = swpb
                elif i in cmp_idx:
                    brush = cmpb
                elif i in pivot_idx:
                    brush = pivb
                elif i in merge_idx:
                    brush = mrgb
                else:
                    brush = base

                painter.fillRect(x, y, bar_w, bar_h, brush)

                painter.drawRect(x, y, bar_w, bar_h)
                x += bar_w + gap

            labels_auto = (
                metrics.get("total_steps", 0) > 0
                and metrics.get("step_idx", 0) >= metrics.get("total_steps", 0)
                and n <= 40
            )
            if self._show_labels or labels_auto:
                painter.setPen(QColor(self._cfg.hud_color))
                font = painter.font()
                x = self._cfg.padding_px
                for v in arr:
                    bar_h = max(1, int(v * scale))
                    y = h - self._cfg.padding_px - bar_h
                    text = str(v)

                    if bar_w < 8:
                        x += bar_w + gap
                        continue

                    if bar_w < 14:
                        font.setPointSize(8)
                    elif bar_w < 20:
                        font.setPointSize(9)
                    else:
                        font.setPointSize(10)
                    painter.setFont(font)
                    fm = painter.fontMetrics()
                    tw = fm.horizontalAdvance(text)
                    th = fm.ascent()

                    tx = x + max(0, (bar_w - tw) // 2)
                    ty_above = y - 2
                    ty_inside = y + th + 2
                    if ty_above - th >= 0:
                        painter.drawText(tx, ty_above, text)
                    elif bar_h > th + 4:
                        painter.drawText(tx, ty_inside, text)

                    x += bar_w + gap

        if hud_visible:
            # --- Upgraded HUD (rounded, translucent panel) ---
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setPen(QColor(self._cfg.hud_color))
            painter.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))

            preset_key = metrics.get("preset") or "custom"
            if isinstance(preset_key, str) and preset_key != "custom":
                try:
                    preset_display = get_preset(preset_key).label
                except KeyError:
                    preset_display = preset_key
            else:
                preset_display = "Custom"
            seed_value = metrics.get("seed")
            # Only show seed if there actually is one (not None or empty)
            if seed_value not in (None, ""):
                preset_line = f"Preset: {preset_display} | Seed={seed_value}"
            else:
                preset_line = f"Preset: {preset_display}"
            logical_elapsed = metrics.get("elapsed_s", 0.0)
            wall_elapsed = metrics.get("wall_elapsed_s", logical_elapsed)
            hud_lines = [
                f"Algo: {metrics.get('algo','')}",
                preset_line,
                f"n={len(arr) if arr else 0} | FPS={metrics.get('fps', 0)}",
                f"Compare={metrics.get('comparisons', 0)} | Swaps={metrics.get('swaps', 0)}",
                (
                    f"Steps={metrics.get('step_idx', 0)}/{metrics.get('total_steps','?')} "
                    f"| Time={logical_elapsed:.2f}s"
                    + (f" (wall {wall_elapsed:.2f}s)" if wall_elapsed else "")
                ),
            ]

            fm = painter.fontMetrics()
            line_h = fm.lineSpacing()
            pad = 6
            x_text = self._cfg.padding_px
            y_text = self._cfg.padding_px

            w_text = max(fm.horizontalAdvance(s) for s in hud_lines) if hud_lines else 0
            h_text = line_h * len(hud_lines)

            bg_rect = QRect(x_text - pad, y_text - pad, w_text + pad * 2, h_text + pad * 2)

            # Panel
            painter.setBrush(QColor(0, 0, 0, 120))  # translucent black
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(bg_rect, 6, 6)

            # Text
            painter.setPen(QColor(self._cfg.hud_color))
            for i, line in enumerate(hud_lines):
                # drawText baseline is at y + ascent
                painter.drawText(x_text, y_text + fm.ascent() + i * line_h, line)

        painter.end()


# ------------------------ Base Visualizer ------------------------


class AlgorithmVisualizerBase(QWidget):
    """
    - Non-blocking animation using QTimer
    - Highlight persistence between ticks
    - Scrub mode via stored steps and periodic checkpoints
    - CSV export of step trace
    - Robust UI state machine
    """

    title: str = "Algorithm"
    STEP_LIST_SAMPLE_RATE: int = 5
    STEP_LIST_MAX_ITEMS: int = 10_000

    def __init__(
        self,
        algo_info: AlgoInfo,
        algo_func: AlgorithmFunc,
        cfg: VizConfig | None = None,
        parent: QWidget | None = None,
        *,
        show_controls: bool = True,
    ) -> None:
        super().__init__(parent)
        self._settings = QSettings()
        self.cfg = cfg or VizConfig.from_settings(self._settings)
        self.algo_info = algo_info
        self.algo_func: AlgorithmFunc = algo_func
        self.title = algo_info.name
        self._show_controls = show_controls
        stored_theme = self._settings.value("ui/theme", DEFAULT_THEME)
        if isinstance(stored_theme, bytes):
            stored_theme = stored_theme.decode()
        self._theme = stored_theme if stored_theme in THEME_PRESETS else DEFAULT_THEME
        self._theme_style = THEME_PRESETS[self._theme]["style"].copy()
        self.right_panel: QWidget | None = None
        self.legend_label: QLabel | None = None
        self.metadata_view: QTextBrowser | None = None
        self._hud_visible = True
        self._show_values = False
        self._external_total_steps = 0
        self._precomputed_steps: list[Step] | None = None
        self._total_steps_known = False

        # Debounce timer for auto-applying typed input
        self._input_debounce_timer = QTimer(self)
        self._input_debounce_timer.setSingleShot(True)
        self._input_debounce_timer.setInterval(1500)  # 1.5 second delay after typing stops
        self._input_debounce_timer.timeout.connect(self._try_auto_apply_input)

        # Ensure this widget really paints a dark background (not the parent's light gray)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(self.backgroundRole(), QColor(self.cfg.bg_color))
        self.setPalette(pal)

        # model
        self._array: list[int] = []
        self._initial_array: list[int] = []
        self._step_source: Iterator[Step] | None = None
        self._steps: list[Step] = []
        # checkpoint now stores: (step_idx, snapshot_array, comparisons, swaps)
        self._checkpoints: list[tuple[int, list[int], int, int]] = []
        self._confirm_progress: int = -1

        # viz state
        self._highlights: dict[str, tuple[int, ...]] = {
            "compare": (),
            "swap": (),
            "pivot": (),
            "merge": (),
            "key": (),
            "shift": (),
        }
        self._confirm_indices: tuple[int, ...] = tuple()

        # metrics
        self._comparisons = 0
        self._swaps = 0
        self._step_idx = 0
        self._narration_default = ""
        self._shortcuts: list[QShortcut] = []
        self._current_preset = DEFAULT_PRESET_KEY
        self._current_seed: int | None = None

        # UI
        self.pane = Pane(
            visualizer=self,
            step_forward=self.player_step_forward,
            step_back=self.player_step_back,
            step_index=self.player_step_index,
            total_steps=self.total_steps,
            on_finished=self._start_finish_animation,
        )
        self.transport = _VisualizerTransport(self)

        self._build_ui()
        self._rebind()
        self._install_shortcuts()
        self._restore_preferences()
        self._set_narration()
        self._update_ui_state("idle")

    # ---------- abstract

    def _generate_steps(self, arr: list[int]) -> Iterator[Step]:
        return self.algo_func(arr)

    # ---------- UI construction

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        self.row_container = QWidget()
        row = QHBoxLayout(self.row_container)
        lbl_input = QLabel("Input (comma ints) or choose a preset:")
        lbl_input.setObjectName("caption")
        row.addWidget(lbl_input)
        self.le_input = QLineEdit()
        self.le_input.setPlaceholderText("e.g. 5,2,9,1,5,6")
        self.le_input.setToolTip("Enter comma-separated integers")
        self.cmb_preset = QComboBox()
        self.cmb_preset.setToolTip("Select a dataset preset")
        for preset in get_presets():
            self.cmb_preset.addItem(preset.label, preset.key)
            idx = self.cmb_preset.count() - 1
            self.cmb_preset.setItemData(idx, preset.description, Qt.ItemDataRole.ToolTipRole)
        self.cmb_preset.setFixedWidth(180)
        self.cmb_preset.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.le_seed = QLineEdit()
        self.le_seed.setPlaceholderText("seed (auto)")
        self.le_seed.setFixedWidth(100)
        self.le_seed.setToolTip("Random seed for reproducibility")
        self.btn_random = QPushButton("Generate")
        self.btn_random.setToolTip("Generate random dataset")
        self.btn_random.setObjectName("primary")

        self.btn_start = QPushButton("Start")
        self.btn_start.setToolTip("Start sorting animation (S)")
        self.btn_start.setObjectName("primary")

        self.btn_pause = QPushButton("Pause")
        self.btn_pause.setToolTip("Pause/Resume animation (Space)")

        self.btn_reset = QPushButton("Reset")
        self.btn_reset.setToolTip("Reset to initial array")

        self.btn_export = QPushButton("Export")
        self.btn_export.setToolTip("Export visualization data")

        self.btn_benchmark = QPushButton("Benchmark")
        self.btn_benchmark.setToolTip("Run performance benchmark")

        row.addWidget(self.le_input)
        row.addWidget(self.cmb_preset)
        row.addWidget(self.le_seed)
        row.addWidget(self.btn_random)
        row.addWidget(self.btn_start)
        row.addWidget(self.btn_pause)
        row.addWidget(self.btn_reset)
        row.addWidget(self.btn_export)
        row.addWidget(self.btn_benchmark)
        row.setSpacing(8)
        row.setContentsMargins(8, 6, 8, 0)

        self.speed_container = QWidget()
        speed_row = QHBoxLayout(self.speed_container)
        fps_label = QLabel("FPS:")
        fps_label.setObjectName("caption")
        speed_row.addWidget(fps_label)
        self.sld_fps = QSlider(Qt.Orientation.Horizontal)
        self.sld_fps.setRange(self.cfg.fps_min, self.cfg.fps_max)
        self.sld_fps.setValue(self.cfg.fps_default)
        self.sld_fps.setToolTip("Adjust animation speed")
        speed_row.addWidget(self.sld_fps, 1)
        self.spn_fps = QSpinBox()
        self.spn_fps.setRange(self.cfg.fps_min, self.cfg.fps_max)
        self.spn_fps.setValue(self.cfg.fps_default)
        self.spn_fps.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spn_fps.setFixedWidth(64)
        speed_row.addWidget(self.spn_fps)
        speed_row.setSpacing(8)
        speed_row.setContentsMargins(8, 0, 8, 0)

        self.scrub_container = QWidget()
        scrub_row = QHBoxLayout(self.scrub_container)
        self.lbl_scrub = QLabel("Step: 0/0")
        self.lbl_scrub.setObjectName("caption")
        self.sld_scrub = QSlider(Qt.Orientation.Horizontal)
        self.sld_scrub.setRange(0, 0)
        self.btn_step_fwd = QPushButton("▶")
        self.btn_step_fwd.setToolTip("Step forward (Right Arrow)")
        self.btn_step_fwd.setObjectName("icon_button")
        self.btn_step_fwd.setMaximumWidth(32)

        self.btn_step_back = QPushButton("◀")
        self.btn_step_back.setToolTip("Step backward (Left Arrow)")
        self.btn_step_back.setObjectName("icon_button")
        self.btn_step_back.setMaximumWidth(32)
        self.chk_labels = QCheckBox("Show values")
        self.chk_labels.setToolTip("Display array values above bars")

        icon_size = QSize(16, 16)
        for btn in (
            self.btn_random,
            self.btn_start,
            self.btn_pause,
            self.btn_reset,
            self.btn_export,
            self.btn_benchmark,
            self.btn_step_back,
            self.btn_step_fwd,
        ):
            btn.setIconSize(icon_size)

        scrub_row.addWidget(self.lbl_scrub)
        scrub_row.addWidget(self.sld_scrub)
        scrub_row.addWidget(self.btn_step_back)
        scrub_row.addWidget(self.btn_step_fwd)
        scrub_row.addWidget(self.chk_labels)
        scrub_row.setSpacing(8)
        scrub_row.setContentsMargins(8, 0, 8, 6)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.canvas = VisualizationCanvas(self._get_canvas_state, self.cfg)
        self.canvas.set_show_labels(self._show_values)
        splitter.addWidget(self.canvas)

        self.lbl_narration = QLabel()
        self.lbl_narration.setObjectName("narrationLabel")
        self.lbl_narration.setWordWrap(True)
        self.lbl_narration.setTextFormat(Qt.TextFormat.PlainText)
        self.lbl_narration.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.lbl_narration.setVisible(False)
        self.lbl_narration.setMaximumHeight(self.fontMetrics().height() * 2 + 12)

        right = QVBoxLayout()
        right_w = QWidget()
        self.right_panel = right_w
        right_w.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        right_w.setAutoFillBackground(True)
        rp = right_w.palette()
        rp.setColor(right_w.backgroundRole(), QColor(self.cfg.bg_color))
        right_w.setPalette(rp)
        right_w.setLayout(right)

        details_group = QGroupBox("Algorithm Details")
        details_group.setFlat(True)
        details_layout = QVBoxLayout()
        details_layout.setContentsMargins(8, 8, 8, 8)
        details_group.setLayout(details_layout)
        self.metadata_view = QTextBrowser()
        self.metadata_view.setOpenExternalLinks(True)
        self.metadata_view.setReadOnly(True)
        self.metadata_view.setMinimumHeight(180)
        self.metadata_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.metadata_view.setStyleSheet("background: rgba(35,45,64,0.35);")
        details_layout.addWidget(self.metadata_view)
        right.addWidget(details_group)

        right.addWidget(QLabel("Steps"))
        self.lst_steps = QListWidget()
        right.addWidget(self.lst_steps, 1)
        right.addWidget(QLabel("Log"))
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        right.addWidget(self.txt_log, 1)
        legend = QLabel(
            "<b>Legend</b><br/>"
            f"<span style='color:{self.cfg.key_color};'>■</span> Key  "
            f"<span style='color:{self.cfg.shift_color};'>■</span> Shift  "
            f"<span style='color:{self.cfg.cmp_color};'>■</span> Compare  "
            f"<span style='color:{self.cfg.swap_color};'>■</span> Swap  "
            f"<span style='color:{self.cfg.pivot_color};'>■</span> Pivot"
        )
        legend.setObjectName("legend")
        legend.setWordWrap(True)
        right.addWidget(legend)
        splitter.addWidget(right_w)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([1_000_000, 250_000])

        mono_font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        if mono_font.pointSize() > 0:
            mono_font.setPointSize(max(9, mono_font.pointSize() - 1))
        self.lst_steps.setFont(mono_font)
        self.txt_log.setFont(mono_font)
        self.lst_steps.setStyleSheet("font-size: 11px;")
        self.lst_steps.itemActivated.connect(self._on_step_item_activated)

        focusables = [
            self.le_input,
            self.cmb_preset,
            self.le_seed,
            self.spn_fps,
            self.sld_fps,
            self.sld_scrub,
            self.btn_random,
            self.btn_start,
            self.btn_pause,
            self.btn_reset,
            self.btn_export,
            self.btn_benchmark,
            self.btn_step_back,
            self.btn_step_fwd,
            self.chk_labels,
            self.lst_steps,
            self.txt_log,
        ]
        is_macos = sys.platform == "darwin"
        for w in focusables:
            w.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            if is_macos:
                w.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, False)

        root.addWidget(self.row_container)
        root.addWidget(self.speed_container)
        root.addWidget(self.scrub_container)
        root.addWidget(self.lbl_narration)
        root.addWidget(splitter)
        self._render_metadata()

        # (optional) nice keyboard order; defer until widgets belong to this window
        QWidget.setTabOrder(self.le_input, self.btn_random)
        QWidget.setTabOrder(self.btn_random, self.btn_start)
        QWidget.setTabOrder(self.btn_start, self.btn_pause)
        QWidget.setTabOrder(self.btn_pause, self.btn_reset)
        QWidget.setTabOrder(self.btn_reset, self.btn_export)
        QWidget.setTabOrder(self.btn_export, self.sld_fps)
        QWidget.setTabOrder(self.sld_fps, self.spn_fps)
        QWidget.setTabOrder(self.spn_fps, self.sld_scrub)
        QWidget.setTabOrder(self.sld_scrub, self.btn_step_back)
        QWidget.setTabOrder(self.btn_step_back, self.btn_step_fwd)

        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)
        self.row_container.setVisible(self._show_controls)
        self.speed_container.setVisible(self._show_controls)
        self.scrub_container.setVisible(self._show_controls)

        # Apply professional theme if available, otherwise use default
        if generate_stylesheet is not None and self._show_controls:
            # Only apply professional theme to single viewer
            self.setStyleSheet(generate_stylesheet())
        else:
            self.apply_theme(self._theme)

    def _render_metadata(self) -> None:
        if self.metadata_view is None:
            return

        info = self.algo_info
        traits = [
            "Stable" if info.stable else "Unstable",
            "In-place" if info.in_place else "Out-of-place",
            "Comparison sort" if info.comparison else "Non-comparison",
        ]
        trait_html = " · ".join(escape(t) for t in traits)

        desc_html = (
            f"<p style='margin:4px 0 8px 0;'>{escape(info.description)}</p>"
            if info.description
            else ""
        )

        notes_html = ""
        if info.notes:
            notes_items = "".join(
                f"<li style='margin:2px 0;'>{escape(note)}</li>" for note in info.notes
            )
            notes_html = (
                "<p style='margin:8px 0 4px 0;'><strong>Highlights</strong></p>"
                f"<ul style='margin:0 0 8px 0; padding-left:20px;'>{notes_items}</ul>"
            )

        complexity_rows = []
        for label, key in (("Best", "best"), ("Average", "avg"), ("Worst", "worst")):
            value = info.complexity.get(key)
            if value:
                complexity_rows.append(
                    f"<tr><th style='text-align:left;padding:2px 12px 2px 0;font-weight:500;'>{label}:</th>"
                    f"<td style='padding:2px 0;'>{escape(value)}</td></tr>"
                )
        complexity_html = ""
        if complexity_rows:
            complexity_html = (
                "<p style='margin:8px 0 4px 0;'><strong>Complexity</strong></p>"
                "<table style='border-collapse:collapse;font-size:11px;margin:0 0 8px 0;'>"
                + "".join(complexity_rows)
                + "</table>"
            )

        accent = self._theme_style.get("legend_fg", "#a0a6b8")
        html = f"""
<div style="font-size:12px; line-height:1.5; padding:4px;">
  <p style="font-weight:600; margin:0 0 4px 0; font-size:14px;">{escape(info.name)}</p>
  <p style="margin:0 0 6px 0; color:{accent}; font-size:11px;">{trait_html}</p>
  {desc_html}
  {notes_html}
  {complexity_html}
</div>
"""
        self.metadata_view.setHtml(html)

    # ---------- public adapters (Pane API) ----------

    def set_show_hud(self, show: bool) -> None:
        self._hud_visible = bool(show)
        self.canvas.update()

    def set_show_values(self, show: bool) -> None:
        self._show_values = bool(show)
        self.canvas.set_show_labels(self._show_values)
        self.canvas.update()
        with suppress(AttributeError):
            self.chk_labels.blockSignals(True)
            self.chk_labels.setChecked(self._show_values)
            self.chk_labels.blockSignals(False)
        self._settings.setValue("viz/show_values", int(self._show_values))

    def show_values(self) -> bool:
        return self._show_values

    def total_steps(self) -> int:
        return self._external_total_steps if self._total_steps_known else 0

    def total_steps_known(self) -> bool:
        return self._total_steps_known

    # ---------- player bridge (public, no privates from callers) ----------

    def player_step_forward(self) -> bool:
        # If we have recorded steps and can advance within them
        if self._step_idx < len(self._steps):
            self._seek(self._step_idx + 1)
            return True

        # We're at or past the end of recorded steps
        # Try to generate the next step
        if self._step_source is not None:
            result = self._advance_step()
            # _advance_step will trigger finish animation if done
            return result

        # No more steps and no generator - we're already finished
        # Don't trigger finish animation again, just return false
        return False

    def player_step_back(self) -> bool:
        """Rewind one step if possible for external players."""
        if self._step_idx > 0:
            self._seek(self._step_idx - 1)
            return True
        return False

    def player_step_index(self) -> int:
        return self._step_idx

    def player_reset(self) -> None:
        self.pane.reset()
        if self._initial_array:
            self._set_array(self._initial_array, persist=False)
        self._step_source = None

    def set_fps(self, fps: int) -> None:
        fps_clamped = max(self.cfg.fps_min, min(self.cfg.fps_max, int(fps)))
        for widget in (self.sld_fps, self.spn_fps):
            widget.blockSignals(True)
            widget.setValue(fps_clamped)
            widget.blockSignals(False)
        self.pane.set_visual_fps(fps_clamped)
        self._settings.setValue("viz/fps", fps_clamped)

    def prime_external_run(self, array: list[int]) -> None:
        if not array:
            raise ValueError("Array cannot be empty")
        self.pane.pause()
        self._set_array(list(array), persist=False)
        step_trace: list[Step] = []
        exceeded_cap = False
        try:
            probe_generator = self._generate_steps(list(self._array))
            for idx, step in enumerate(probe_generator, start=1):
                if idx > PRECOMPUTE_STEP_CAP:
                    exceeded_cap = True
                    break
                step_trace.append(step)
        finally:
            # Ensure the probe generator is exhausted if we broke early.
            probe_generator = None

        if exceeded_cap:
            self._precomputed_steps = None
            self._external_total_steps = 0
            self._total_steps_known = False
            self._step_source = self._generate_steps(list(self._array))
        else:
            self._precomputed_steps = step_trace
            self._external_total_steps = len(step_trace)
            self._total_steps_known = True
            self._step_source = iter(step_trace)

        self._update_ui_state("paused")
        self._set_narration()

    def apply_theme(self, theme: str) -> None:
        if theme not in THEME_PRESETS:
            theme = DEFAULT_THEME
        self._theme = theme
        preset = THEME_PRESETS[theme]
        for key, value in preset["cfg"].items():
            setattr(self.cfg, key, value)
        self._theme_style = preset["style"].copy()
        if self.right_panel is not None:
            palette = self.right_panel.palette()
            palette.setColor(self.right_panel.backgroundRole(), QColor(self.cfg.bg_color))
            self.right_panel.setPalette(palette)
        if self.metadata_view is not None:
            self.metadata_view.setStyleSheet(
                f"background:{self._theme_style['card_bg']}; color:{self._theme_style['widget_fg']};"
            )
        self._update_legend_text()
        self._apply_stylesheet()
        self.canvas.update()
        self._render_metadata()

    def _update_legend_text(self) -> None:
        if self.legend_label is None:
            return
        self.legend_label.setText(
            "<b>Legend</b><br/>"
            f"<span style='color:{self.cfg.key_color};'>■</span> Key  "
            f"<span style='color:{self.cfg.shift_color};'>■</span> Shift  "
            f"<span style='color:{self.cfg.cmp_color};'>■</span> Compare  "
            f"<span style='color:{self.cfg.swap_color};'>■</span> Swap  "
            f"<span style='color:{self.cfg.pivot_color};'>■</span> Pivot"
        )

    def _apply_stylesheet_old(self) -> None:
        # Disabled - using professional theme from ui_shared/professional_theme.py
        return

    def _apply_stylesheet(self) -> None:
        # Don't override the professional theme
        return

    def _apply_stylesheet_disabled(self) -> None:
        style = self._theme_style
        self.setStyleSheet(
            f"""
QWidget {{ color:{style['widget_fg']}; background:{style['widget_bg']}; }}

QLabel#caption {{
  color:{style['widget_fg']};
  background:{style['caption_bg']};
  border:1px solid {style['caption_border']};
  border-radius:8px;
  padding:4px 10px;
  font-weight:600;
}}

QLabel#legend {{
  color:{style['legend_fg']};
  padding:6px 8px;
  background:{style['legend_bg']};
  border:1px solid {style['legend_border']};
  border-radius:6px;
  font-size:11px;
}}

QLineEdit, QAbstractSpinBox {{
  color:{style['widget_fg']};
  background:{style['input_bg']};
  border:1px solid {style['input_border']};
  border-radius:6px;
  padding:6px 8px;
}}
QLineEdit::placeholder {{ color:{style['placeholder_fg']}; }}
QLineEdit:focus, QAbstractSpinBox:focus {{
  border-color:{style['focus_border']};
  background:{style['focus_bg']};
}}

QPushButton {{
  color:{style['widget_fg']};
  background:transparent;
  border:1px solid {self.cfg.bar_color};
  border-radius:6px;
  padding:6px 10px;
}}
QPushButton:hover   {{ background:{style['input_bg']}; }}
QPushButton:pressed {{ background:{style['focus_bg']}; }}
QPushButton:disabled{{
  color:{style['disabled_fg']}; border-color:{style['disabled_fg']}; background:transparent;
}}

QListWidget, QTextEdit {{
  color:{style['widget_fg']};
  background:{style['list_bg']};
  border:1px solid {style['list_border']};
  border-radius:6px;
}}
QListWidget::item:selected {{ background:{style['focus_bg']}; }}

QSlider::groove:horizontal {{
  height:8px;
  background:{style['list_bg']};
  border:1px solid {style['list_border']};
  border-radius:4px;
}}
QSlider::handle:horizontal {{
  width:18px;
  background:{style['widget_fg']};
  border:1px solid {style['list_border']};
  border-radius:9px;
  margin:-6px 0;
}}
QSlider::groove:horizontal:focus {{
  border:1px solid {style['slider_focus_border']};
  background:{style['focus_bg']};
}}
QSlider::handle:horizontal:focus {{
  border:2px solid {style['slider_focus_border']};
  margin:-7px 0;
}}
QSlider::sub-page:horizontal,
QSlider::add-page:horizontal {{ background: transparent; border: none; }}

QSpinBox::up-button, QSpinBox::down-button {{ width: 0; height: 0; border: none; }}
"""
        )

    def _rebind(self) -> None:
        self.btn_random.clicked.connect(self._on_randomize)
        self.btn_start.clicked.connect(self._on_start)
        self.btn_pause.clicked.connect(self._on_pause)
        self.btn_reset.clicked.connect(self._on_reset)
        self.sld_fps.valueChanged.connect(self._on_fps_changed)
        self.spn_fps.valueChanged.connect(self._on_fps_changed)
        self.btn_export.clicked.connect(self._on_export)
        self.btn_benchmark.clicked.connect(self._on_benchmark)
        self.le_input.textChanged.connect(self._on_input_changed)
        self.le_input.editingFinished.connect(
            lambda: self._settings.setValue("viz/last_input", self.le_input.text())
        )
        self.sld_scrub.valueChanged.connect(self._on_scrub_move)
        self.btn_step_fwd.clicked.connect(self._on_step_forward)
        self.btn_step_back.clicked.connect(self._on_step_back)
        self.chk_labels.toggled.connect(self._on_labels_toggled)

    # ---------- transport wrappers

    def _transport_play(self) -> None:
        if not self._ensure_run_is_ready():
            return
        self.pane.play()
        self.txt_log.append(f"Started at {self.pane.player._visual_fps} FPS")
        LOGGER.info(
            "Start algo=%s fps=%d n=%d",
            self.title,
            self.pane.player._visual_fps,
            len(self._array),
        )
        self._update_ui_state("running")

    def _transport_toggle_pause(self) -> None:
        if (
            not self.pane.is_running
            and self._step_source is None
            and not self._ensure_run_is_ready()
        ):
            return
        self.pane.toggle_pause()
        running = self.pane.is_running
        self.txt_log.append("Resumed" if running else "Paused")
        self._update_ui_state("running" if running else "paused")

    def _transport_reset(self) -> None:
        self.pane.reset()
        if self._initial_array:
            self._set_array(self._initial_array, persist=False)
        self._step_source = None
        self.txt_log.append("Reset")
        self._update_ui_state("idle")

    def _transport_step_forward(self) -> None:
        # If we have recorded steps and haven't reached the end yet, just step forward
        if self._step_idx < len(self._steps):
            self.pane.step_forward()
            return

        # Check if we're already at the end and finished
        if (
            self._step_source is None
            and self._step_idx >= len(self._steps)
            and len(self._steps) > 0
        ):
            # We're at the end, don't restart
            return

        # Only ensure run is ready if we need to generate new steps
        if not self._ensure_run_is_ready():
            return
        self.pane.step_forward()

    def _transport_step_back(self) -> None:
        self.pane.step_back()

    def _install_shortcuts(self) -> None:
        # Only install shortcuts if we're showing controls (Single mode)
        # In Compare mode, shortcuts are handled by CompareWindow
        if not self._show_controls:
            return

        shortcuts = [
            ("S", self._transport_play),
            ("Space", self._transport_toggle_pause),
            ("R", self._on_randomize),
            ("Left", self._transport_step_back),
            ("Right", self._transport_step_forward),
        ]
        for seq, handler in shortcuts:
            shortcut = QShortcut(QKeySequence(seq), self)
            shortcut.activated.connect(handler)
            self._shortcuts.append(shortcut)

    def disable_shortcuts(self) -> None:
        """Disable all keyboard shortcuts (used in Compare mode)."""
        for shortcut in self._shortcuts:
            shortcut.setEnabled(False)

    def _restore_preferences(self) -> None:
        fps = int(self._settings.value("viz/fps", self.cfg.fps_default))
        for widget in (self.sld_fps, self.spn_fps):
            widget.blockSignals(True)
        self.sld_fps.setValue(fps)
        self.spn_fps.setValue(fps)
        for widget in (self.sld_fps, self.spn_fps):
            widget.blockSignals(False)

        last_input = self._settings.value("viz/last_input", "")
        if isinstance(last_input, bytes):
            last_input = last_input.decode()
        self.le_input.setText(str(last_input))

        preset_key = self._settings.value("viz/preset", DEFAULT_PRESET_KEY)
        if isinstance(preset_key, bytes):
            preset_key = preset_key.decode()
        idx = self.cmb_preset.findData(preset_key)
        if idx >= 0:
            self.cmb_preset.setCurrentIndex(idx)
            self._current_preset = str(preset_key)
        else:
            fallback_idx = self.cmb_preset.findData(DEFAULT_PRESET_KEY)
            if fallback_idx >= 0:
                self.cmb_preset.setCurrentIndex(fallback_idx)
            self._current_preset = DEFAULT_PRESET_KEY

        seed_value = self._settings.value("viz/seed", "")
        if seed_value not in (None, ""):
            self.le_seed.setText(str(seed_value))
            try:
                self._current_seed = int(seed_value)
            except (TypeError, ValueError):
                self._current_seed = None
        else:
            self._current_seed = None

        show_values_pref = self._settings.value("viz/show_values", 0)
        try:
            show_values = bool(int(show_values_pref))
        except (TypeError, ValueError):
            show_values = False
        self.set_show_values(show_values)

    def _persist_last_array(self, arr: list[int]) -> None:
        rendered = ",".join(str(v) for v in arr)
        self._settings.setValue("viz/last_input", rendered)

    def _set_narration(self, text: str | None = None) -> None:
        if getattr(self, "lbl_narration", None) is None:
            return
        message = text.strip() if isinstance(text, str) else ""
        if not message and self._narration_default:
            message = self._narration_default
        self.lbl_narration.setVisible(bool(message))
        self.lbl_narration.setText(message)

    # ---------- UI state machine

    def _update_ui_state(self, state: str) -> None:
        running = state == "running"
        paused = state == "paused"

        can_start_new = not running

        self.le_input.setEnabled(can_start_new)
        self.cmb_preset.setEnabled(can_start_new)
        self.le_seed.setEnabled(can_start_new)
        self.btn_random.setEnabled(can_start_new)
        self.btn_start.setEnabled(can_start_new)

        self.btn_pause.setEnabled(running or paused)

        self.btn_reset.setEnabled(can_start_new and bool(self._initial_array))

        has_steps = bool(self._steps)
        self.btn_export.setEnabled(can_start_new and has_steps)
        self.btn_benchmark.setEnabled(can_start_new)

        allow_scrub = can_start_new and has_steps
        manual_forward_available = can_start_new and (has_steps or self._step_source is not None)
        self.sld_scrub.setEnabled(allow_scrub)
        self.btn_step_fwd.setEnabled(manual_forward_available)
        self.btn_step_back.setEnabled(can_start_new and self._step_idx > 0)

    # ---------- state and metrics

    def _get_canvas_state(self) -> dict[str, Any]:
        # Use external_total_steps when known (algorithm complete)
        # Otherwise use the current step count
        total_steps = self._external_total_steps if self._total_steps_known else len(self._steps)

        return {
            "array": self._array,
            "highlights": self._highlights,
            "confirm": self._confirm_indices,
            "metrics": {
                "algo": self.title,
                "comparisons": self._comparisons,
                "swaps": self._swaps,
                "fps": self.sld_fps.value(),
                "step_idx": self._step_idx,
                "total_steps": total_steps,
                "elapsed_s": self.pane.logical_seconds(),
                "wall_elapsed_s": self.pane.elapsed_seconds(),
                "preset": self._current_preset,
                "seed": self._current_seed,
            },
            "hud_visible": self._hud_visible,
        }

    def _set_array(self, arr: list[int], *, persist: bool = True) -> None:
        if not arr:
            raise ValueError("Array cannot be empty")
        self.pane.reset()
        self._array = list(arr)
        self._initial_array = list(arr)
        self._external_total_steps = 0
        self._precomputed_steps = None
        self._total_steps_known = False
        if persist:
            self._persist_last_array(arr)
            self._current_preset = "custom"
            self._current_seed = None
        self._highlights = {
            "compare": (),
            "swap": (),
            "pivot": (),
            "merge": (),
            "key": (),
            "shift": (),
        }
        self._confirm_indices = tuple()
        self._comparisons = 0
        self._swaps = 0
        self._steps.clear()
        self._checkpoints.clear()
        self._step_idx = 0
        self.lst_steps.clear()
        self._append_checkpoint(0)  # checkpoint at step 0
        self.canvas.update()
        self._update_ui_state("idle")
        self._update_scrub_ui()

    def _append_checkpoint(self, step_idx: int) -> None:
        # store array snapshot and metrics
        self._checkpoints.append((step_idx, list(self._array), self._comparisons, self._swaps))

    # ---------- controls

    def _on_labels_toggled(self, checked: bool) -> None:
        self._show_values = bool(checked)
        self.canvas.set_show_labels(self._show_values)
        self.canvas.update()
        self._settings.setValue("viz/show_values", int(self._show_values))

    def _on_input_changed(self, text: str) -> None:
        """Start debounce timer to auto-apply input after typing stops."""
        # Restart the debounce timer - will auto-apply after user stops typing
        self._input_debounce_timer.start()

    def _try_auto_apply_input(self) -> None:
        """Attempt to parse and apply the current input text automatically."""
        text = self.le_input.text().strip()
        if not text:
            return
        try:
            parsed = self._parse_input()
            if parsed and len(parsed) > 0:
                self._set_array(parsed)
        except (ValueError, TypeError):
            # Invalid input, do nothing
            pass

    def _on_randomize(self) -> None:
        try:
            import random

            n = self.cfg.default_n
            preset_key = self.cmb_preset.currentData(Qt.ItemDataRole.UserRole)
            if not isinstance(preset_key, str):
                preset_key = DEFAULT_PRESET_KEY

            seed = self._resolve_seed()
            rng = random.Random(seed)
            arr = generate_dataset(
                preset_key,
                n,
                self.cfg.min_val,
                self.cfg.max_val,
                rng,
            )
            self._current_preset = preset_key
            self._current_seed = seed
            self.le_input.clear()
            self._set_array(arr, persist=False)
            self._settings.setValue("viz/last_input", "")
            self._settings.setValue("viz/preset", preset_key)
            self._settings.setValue("viz/seed", seed)
            self.txt_log.append(f"Generated preset={preset_key} seed={seed} n={n}")
            LOGGER.info("Generated preset=%s seed=%d n=%d", preset_key, seed, n)
        except Exception as e:
            self._error(str(e))

    def _ensure_run_is_ready(self) -> bool:
        # If we already have a generator in progress, nothing to do.
        if self._step_source is not None:
            return True

        parsed = self._parse_input()

        if parsed:
            self._set_array(parsed)
            self.le_input.setText(",".join(str(x) for x in parsed))
        else:
            if self._initial_array:
                self._set_array(self._initial_array, persist=False)
            else:
                self._on_randomize()
                if not self._array:
                    return False

        self._step_source = self._generate_steps(list(self._array))
        self.pane.reset()
        self._update_ui_state("paused")
        return True

    def _parse_input(self) -> list[int]:
        text = self.le_input.text().strip()
        if not text:
            return []
        parts = [p for p in text.replace(" ", "").split(",") if p]
        arr = [int(p) for p in parts]
        if len(arr) > self.cfg.max_n:
            raise ValueError(f"Max length {self.cfg.max_n}, got {len(arr)}")
        return arr

    def _on_start(self) -> None:
        try:
            self._transport_play()
        except Exception as e:
            self._error(str(e))

    def _on_pause(self) -> None:
        try:
            self._transport_toggle_pause()
        except Exception as e:
            self._error(str(e))

    def _on_reset(self) -> None:
        try:
            self._transport_reset()
        except Exception as e:
            self._error(str(e))

    def _on_fps_changed(self, v: int) -> None:
        # keep slider/spin synchronized without causing recursive events
        for widget in (self.sld_fps, self.spn_fps):
            if widget.value() != v:
                widget.blockSignals(True)
                widget.setValue(v)
                widget.blockSignals(False)

        clamped = max(self.cfg.fps_min, min(self.cfg.fps_max, int(v)))
        self._settings.setValue("viz/fps", clamped)
        self.pane.set_visual_fps(clamped)

    def _on_export(self) -> None:
        if not self._steps:
            self._warn("No steps to export yet.")
            return
        options = QFileDialog.Option.DontUseNativeDialog
        filters = "CSV (*.csv);;JSON (*.json);;PNG (*.png);;GIF (*.gif)"
        path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export",
            "steps",
            filters,
            options=options,
        )
        if not path:
            return
        try:
            suffix = Path(path).suffix.lower()
            filter_default = {
                "CSV (*.csv)": ".csv",
                "JSON (*.json)": ".json",
                "PNG (*.png)": ".png",
                "GIF (*.gif)": ".gif",
            }
            if not suffix:
                suffix = filter_default.get(selected_filter, ".csv")
                path = f"{path}{suffix}"

            if suffix == ".csv":
                self._export_csv(path)
                summary = f"CSV ({len(self._steps)} rows)"
            elif suffix == ".json":
                self._export_json(path)
                summary = "JSON trace"
            elif suffix == ".png":
                self._export_png(path)
                summary = "PNG snapshot"
            elif suffix == ".gif":
                self._export_gif(path)
                summary = "GIF animation"
            else:
                raise ValueError(f"Unsupported export format: {suffix}")

            self.txt_log.append(f"Exported {summary} to {path}")
        except Exception as e:
            self._error(str(e))

    def _on_benchmark(self) -> None:
        try:
            rows = self._collect_benchmark_rows()
            if not rows:
                self._warn("Nothing to benchmark yet.")
                return

            options = QFileDialog.Option.DontUseNativeDialog
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Benchmark Results",
                "benchmark.csv",
                "CSV (*.csv)",
                options=options,
            )
            if not path:
                return
            if Path(path).suffix.lower() != ".csv":
                path = f"{path}.csv"

            with open(path, "w", newline="") as fh:
                writer = csv.writer(fh)
                writer.writerow(
                    [
                        "algo",
                        "run",
                        "preset",
                        "seed",
                        "n",
                        "steps",
                        "comparisons",
                        "swaps",
                        "duration_ms",
                        "sorted",
                        "error",
                    ]
                )
                writer.writerows(rows)

            self.txt_log.append(f"Benchmark wrote {len(rows)} rows to {path}")
        except Exception as exc:
            self._error(str(exc))

    def _export_csv(self, path: str) -> None:
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["idx", "op", "indices", "payload"])
            for idx, step in enumerate(self._steps):
                writer.writerow(
                    [
                        idx,
                        step.op,
                        ".".join(str(i) for i in step.indices),
                        "" if step.payload is None else step.payload,
                    ]
                )

    def _export_json(self, path: str) -> None:
        preset_key = self._current_preset
        preset_label = "Custom"
        if isinstance(preset_key, str) and preset_key != "custom":
            try:
                preset_label = get_preset(preset_key).label
            except KeyError:
                preset_label = preset_key
        payload = {
            "algo": self.title,
            "preset": preset_key,
            "preset_label": preset_label,
            "seed": self._current_seed,
            "config": {
                "n": len(self._array),
                "min": self.cfg.min_val,
                "max": self.cfg.max_val,
                "fps": self.sld_fps.value(),
            },
            "initial": self._initial_array,
            "steps": [self._step_to_mapping(i, step) for i, step in enumerate(self._steps)],
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)

    def _export_png(self, path: str) -> None:
        pixmap = self.canvas.grab()
        pixmap.save(path, "PNG")

    def _export_gif(self, path: str) -> None:
        if not self._steps:
            raise ValueError("Run the algorithm before exporting a GIF.")

        prev_idx = self._step_idx
        indices: list[int] = []
        stride = max(1, len(self._steps) // 120)
        indices.extend(range(0, len(self._steps) + 1, stride))
        if indices[-1] != len(self._steps):
            indices.append(len(self._steps))

        frames: list[Image.Image] = []
        try:
            for idx in indices:
                self._seek(idx)
                QApplication.processEvents()
                qimage = self.canvas.grab().toImage()
                frames.append(fromqimage(qimage).convert("RGBA"))
        finally:
            self._seek(prev_idx)
            QApplication.processEvents()

        if not frames:
            raise ValueError("No frames captured for GIF export.")

        duration_ms = max(20, int(1000 / max(1, self.sld_fps.value())))
        first, *rest = frames
        first.save(
            path,
            format="GIF",
            save_all=True,
            append_images=rest if rest else [first.copy()],
            duration=duration_ms,
            loop=0,
            disposal=2,
        )

    @staticmethod
    def _step_to_mapping(idx: int, step: Step) -> dict[str, Any]:
        payload: Any = step.payload
        if isinstance(payload, tuple):
            payload = list(payload)
        return {
            "idx": idx,
            "op": step.op,
            "indices": list(step.indices),
            "payload": payload,
        }

    def _resolve_seed(self) -> int:
        import random

        seed_text = self.le_seed.text().strip()
        if seed_text:
            try:
                seed = int(seed_text)
            except ValueError as exc:
                raise ValueError("Seed must be an integer") from exc
        else:
            seed = random.SystemRandom().randint(0, 2**32 - 1)
            self.le_seed.setText(str(seed))
        self._current_seed = seed
        return seed

    def _collect_benchmark_rows(self) -> list[list[Any]]:
        import random

        rows: list[list[Any]] = []
        manual_input = self.le_input.text().strip()
        if manual_input:
            dataset = self._parse_input()
            rows.extend(self._benchmark_dataset(dataset, "custom", None, 0))
            return rows

        preset_key = self.cmb_preset.currentData(Qt.ItemDataRole.UserRole)
        if not isinstance(preset_key, str):
            preset_key = DEFAULT_PRESET_KEY

        base_seed = self._resolve_seed()
        self._settings.setValue("viz/seed", base_seed)
        self._settings.setValue("viz/preset", preset_key)

        runs = 3
        for run_idx in range(runs):
            run_seed = base_seed + run_idx
            rng = random.Random(run_seed)
            dataset = generate_dataset(
                preset_key,
                self.cfg.default_n,
                self.cfg.min_val,
                self.cfg.max_val,
                rng,
            )
            rows.extend(self._benchmark_dataset(dataset, preset_key, run_seed, run_idx))

        return rows

    def _benchmark_dataset(
        self,
        dataset: list[int],
        preset_key: str,
        seed: int | None,
        run_idx: int,
    ) -> list[list[Any]]:
        expected = sorted(dataset)
        rows: list[list[Any]] = []
        for name in sorted(INFO.keys()):
            algo = REGISTRY[name]
            metrics = self._measure_algorithm(algo, list(dataset), expected)
            rows.append(
                [
                    name,
                    run_idx,
                    preset_key,
                    "" if seed is None else seed,
                    len(dataset),
                    metrics.get("steps", 0),
                    metrics.get("comparisons", 0),
                    metrics.get("swaps", 0),
                    f"{metrics.get('duration_s', 0.0) * 1000:.3f}",
                    int(metrics.get("sorted", False)),
                    metrics.get("error", ""),
                ]
            )
        return rows

    @staticmethod
    def _measure_algorithm(
        algo: AlgorithmFunc, dataset: list[int], expected: list[int]
    ) -> dict[str, Any]:
        comparisons = 0
        swaps = 0
        steps = 0
        start = time.perf_counter()
        error: str | None = None
        try:
            for step in algo(dataset):
                steps += 1
                if step.op in {"compare", "merge_compare"}:
                    comparisons += 1
                elif step.op == "swap":
                    swaps += 1
        except Exception as exc:  # pragma: no cover - surfaced in benchmark CSV
            error = str(exc)
        duration = time.perf_counter() - start
        return {
            "steps": steps,
            "comparisons": comparisons,
            "swaps": swaps,
            "duration_s": duration,
            "sorted": dataset == expected,
            "error": error or "",
        }

    # ---------- animation tick

    def _advance_step(self) -> bool:
        if self._step_source is None:
            return False
        try:
            step = next(self._step_source)
        except StopIteration:
            self._step_source = None
            self._start_finish_animation()
            return False
        except Exception as exc:  # capture unexpected generator errors
            self._step_source = None
            self._error(str(exc))
            return False

        self._process_step(step)
        return True

    def _process_step(self, step: Step) -> None:
        narration = self._narrate_step(step)
        self._apply_step(step)
        self._steps.append(step)
        if len(self._steps) % self.cfg.checkpoint_stride == 0:
            self._append_checkpoint(len(self._steps))
        self._append_step_list(step)
        self._step_idx = len(self._steps)
        self._update_scrub_ui()
        self.canvas.update()
        self._set_narration(narration)

    def _start_finish_animation(self) -> None:
        self.txt_log.append(f"Finished. Comparisons={self._comparisons}, Swaps={self._swaps}")
        LOGGER.info(
            "Finished algo=%s comps=%d swaps=%d", self.title, self._comparisons, self._swaps
        )
        if not self._external_total_steps:
            self._external_total_steps = len(self._steps)
        self._total_steps_known = True
        self._confirm_progress = 0
        self._confirm_indices = tuple()
        self._set_narration("Sort complete. Finalizing display…")

        # Update canvas to show numbers immediately
        self.canvas.update()

        # Use a new, temporary timer for the finish sweep.
        finish_timer = QTimer(self)  # Parented to self for auto-cleanup
        finish_timer.timeout.connect(lambda: self._finish_tick(finish_timer))
        finish_timer.start(int(1000 / 60))
        self._update_ui_state("finished")

    def _finish_tick(self, timer: QTimer) -> None:
        if self._confirm_progress < len(self._array):
            idx = self._confirm_progress
            self._confirm_indices = tuple(list(self._confirm_indices) + [idx])
            self._confirm_progress += 1
            self.canvas.update()
        else:
            timer.stop()
            timer.deleteLater()  # Clean up the timer
            self._set_narration("Array sorted!")
            self._confirm_progress = -1

    def _append_step_list(self, step: Step) -> None:
        current_idx = len(self._steps)
        important_ops = {"swap", "set", "shift", "pivot", "merge_mark", "key"}
        if (
            current_idx > 1
            and (current_idx % self.STEP_LIST_SAMPLE_RATE != 0)
            and (step.op not in important_ops)
        ):
            return

        display_idx = current_idx
        text = f"{display_idx:04d} | {step.op}: {step.indices}" + (
            f" -> {step.payload}" if step.payload is not None else ""
        )
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, current_idx)
        self.lst_steps.addItem(item)
        if self.lst_steps.count() > self.STEP_LIST_MAX_ITEMS:
            self.lst_steps.takeItem(0)
        self.lst_steps.scrollToBottom()

    def _apply_step(self, step: Step) -> None:
        op = step.op
        idx = step.indices
        # leave last highlight visible until we set a new one here
        if op == "compare":
            self._comparisons += 1
            self._highlights["compare"] = idx
        elif op == "swap":
            self._swaps += 1
            i, j = idx
            self._array[i], self._array[j] = self._array[j], self._array[i]
            self._highlights["swap"] = idx
            self._highlights["shift"] = ()
        elif op == "pivot":
            self._highlights["pivot"] = idx
        elif op == "merge_mark":
            lo, hi = idx
            self._highlights["merge"] = tuple(range(lo, hi + 1))
        elif op == "merge_compare":
            self._comparisons += 1
            self._highlights["compare"] = idx
            self._highlights["merge"] = (step.payload,) if isinstance(step.payload, int) else ()
        elif op == "set":
            k = idx[0]
            payload = step.payload
            if not isinstance(payload, int):
                raise ValueError("set step requires int payload")
            self._array[k] = payload
            self._highlights["merge"] = (k,)
            self._highlights["shift"] = ()
        elif op == "shift":
            k = idx[0]
            payload = step.payload
            if not isinstance(payload, int):
                raise ValueError("shift step requires int payload")
            self._array[k] = payload
            self._highlights["shift"] = (k,)
            self._highlights["merge"] = ()
        elif op == "key":
            self._highlights["key"] = idx
        elif op == "confirm":
            pass
        else:
            raise ValueError(f"Unknown step op: {op}")

    # ---------- scrub mode

    def _update_scrub_ui(self) -> None:
        total = len(self._steps)
        self.sld_scrub.blockSignals(True)
        self.sld_scrub.setRange(0, total)
        self.sld_scrub.setValue(self._step_idx)
        self.sld_scrub.blockSignals(False)
        self.lbl_scrub.setText(f"Step: {self._step_idx}/{total}")

    def _on_scrub_move(self, val: int) -> None:
        self.pane.pause()
        self._seek(val)
        self.pane.sync_to_step(self._step_idx)

    def _seek_from_shortcut(self, target_idx: int):
        self.pane.pause()
        self._seek(target_idx)
        self.pane.sync_to_step(self._step_idx)

    def _on_step_forward(self) -> None:
        try:
            self._transport_step_forward()
        except Exception as e:
            self._error(str(e))

    def _on_step_back(self) -> None:
        try:
            self._transport_step_back()
        except Exception as e:
            self._error(str(e))

    def _seek(self, target_idx: int) -> None:
        target_idx = max(0, min(len(self._steps), target_idx))

        # find nearest checkpoint <= target_idx and restore array + metrics
        ck_idx, ck_arr, ck_comps, ck_swaps = 0, list(self._initial_array), 0, 0
        for s_idx, snap, comps, swaps in self._checkpoints:
            if s_idx <= target_idx:
                ck_idx, ck_arr, ck_comps, ck_swaps = s_idx, list(snap), comps, swaps
            else:
                break

        self._array = ck_arr
        self._comparisons = ck_comps
        self._swaps = ck_swaps
        self._confirm_indices = tuple()
        self._confirm_progress = -1
        self._highlights = {
            "compare": (),
            "swap": (),
            "pivot": (),
            "merge": (),
            "key": (),
            "shift": (),
        }

        narration = ""
        for i in range(ck_idx, target_idx):
            step = self._steps[i]
            narration = self._narrate_step(step)
            self._apply_step(step)

        self._step_idx = target_idx
        self._rebuild_step_list_after_seek(target_idx)
        self._update_scrub_ui()
        self.canvas.update()

        if target_idx == 0:
            self._set_narration()
        else:
            if not narration and target_idx <= len(self._steps):
                last_step = self._steps[target_idx - 1]
                narration = f"Viewing {last_step.op} at {last_step.indices}."
            self._set_narration(narration)

    def _on_step_item_activated(self, item: QListWidgetItem) -> None:
        if item is None:
            return
        step_idx = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(step_idx, int):
            self._seek_from_shortcut(step_idx)

    def _rebuild_step_list_after_seek(self, target_idx: int) -> None:
        """Show a contiguous window of steps around the scrub target for context."""
        if not self._steps:
            self.lst_steps.clear()
            return

        total_steps = len(self._steps)
        window = min(self.STEP_LIST_MAX_ITEMS, total_steps)
        if window <= 0:
            self.lst_steps.clear()
            return

        half_window = window // 2
        start = max(0, target_idx - half_window)
        end = min(total_steps, start + window)
        if end - start < window:
            start = max(0, end - window)

        self.lst_steps.clear()
        selected_row: int | None = None

        for i in range(start, end):
            step = self._steps[i]
            text = f"{step.op}: {step.indices}"
            if step.payload is not None:
                text += f" -> {step.payload}"
            list_item = QListWidgetItem(text)
            list_item.setData(Qt.ItemDataRole.UserRole, i + 1)
            self.lst_steps.addItem(list_item)

            if i == target_idx - 1:
                selected_row = self.lst_steps.count() - 1

        if selected_row is not None and 0 <= selected_row < self.lst_steps.count():
            selected_item = self.lst_steps.item(selected_row)
            if selected_item is not None:
                self.lst_steps.setCurrentItem(selected_item)
                self.lst_steps.scrollToItem(selected_item, QListWidget.ScrollHint.PositionAtCenter)
        elif self.lst_steps.count():
            if target_idx <= 0:
                self.lst_steps.scrollToTop()
            else:
                self.lst_steps.scrollToBottom()

    # ---------- utils

    def pause_if_running(self) -> None:
        if self.pane.is_running:
            self.pane.pause()
            self.txt_log.append("Paused (auto)")
            self._update_ui_state("paused")

    def hideEvent(self, event: QHideEvent | None) -> None:
        self.pause_if_running()
        super().hideEvent(event)

    def _warn(self, msg: str) -> None:
        self.txt_log.append(f"[WARN] {msg}")

    def _error(self, msg: str) -> None:
        self.txt_log.append(f"[ERROR] {msg}")
        LOGGER.exception(msg)
        QMessageBox.critical(self, self.title, msg)

    # ---------- step application and highlights

    def _narrate_step(self, step: Step) -> str:
        arr = self._array
        op = step.op
        idx = step.indices
        payload = step.payload

        def safe_get(i: int) -> int | None:
            return arr[i] if 0 <= i < len(arr) else None

        try:
            if op == "compare":
                i, j = idx
                return f"Comparing {safe_get(i)} (index {i}) with " f"{safe_get(j)} (index {j})."
            if op == "merge_compare":
                i, j = idx
                dest = payload if isinstance(payload, int) else "?"
                return (
                    f"Comparing {safe_get(i)} (index {i}) with {safe_get(j)} (index {j}) "
                    f"for position {dest}."
                )
            if op == "swap":
                i, j = idx
                if payload and isinstance(payload, tuple) and len(payload) == 2:
                    val1, val2 = payload
                    return f"Swapping {val1} (index {i}) with {val2} (index {j})."
                return f"Swapping elements at indices {i} and {j}."
            if op == "set":
                k = idx[0]
                old_val = safe_get(k)
                return f"Setting index {k} from {old_val} to {payload}."
            if op == "shift":
                k = idx[0]
                return f"Shifting {payload} into index {k}."
            if op == "pivot":
                p = idx[0]
                return f"Selecting {safe_get(p)} at index {p} as the pivot."
            if op == "merge_mark":
                lo, hi = idx
                return f"Marking merge range {lo} – {hi}."
            if op == "key":
                if not idx:
                    return "Key placement complete."
                target = idx[0]
                return f"Tracking key {payload} (target index {target})."
            if op == "confirm" and idx:
                i = idx[0]
                return f"Confirming index {i} as sorted."
        except (IndexError, ValueError, TypeError):
            return ""

        return ""


class _VisualizerTransport:
    def __init__(self, visualizer: AlgorithmVisualizerBase) -> None:
        self._viz = visualizer

    def play(self) -> None:
        self._viz._transport_play()

    def toggle_pause(self) -> None:
        self._viz._transport_toggle_pause()

    def pause(self) -> None:
        if self._viz.pane.is_running:
            self._viz._transport_toggle_pause()

    def reset(self) -> None:
        self._viz._transport_reset()

    def step_forward(self) -> None:
        self._viz._transport_step_forward()

    def step_back(self) -> None:
        self._viz._transport_step_back()

    def capabilities(self) -> dict[str, bool]:
        return self._viz.pane.capabilities()

    def set_capability(self, key: str, value: bool) -> None:
        self._viz.pane.set_capability(key, value)

    def is_running(self) -> bool:
        return self._viz.pane.is_running
