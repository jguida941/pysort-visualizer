from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFormLayout, QLabel, QVBoxLayout, QWidget


class DebugPanel(QWidget):
    """Diagnostics panel that displays live Player/Pane state."""

    def __init__(self, pane: Any, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._pane = pane
        self._player = getattr(pane, "player", None)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)
        layout.addStretch(1)

        self.step_label = QLabel("0 / ?")
        self.logical_label = QLabel("0.00 s")
        self.wall_label = QLabel("0.00 s")
        self.state_label = QLabel("idle")
        self.backpressure_label = QLabel("-")

        for lab in (
            self.step_label,
            self.logical_label,
            self.wall_label,
            self.state_label,
            self.backpressure_label,
        ):
            lab.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        form.addRow("Step", self.step_label)
        form.addRow("Logical", self.logical_label)
        form.addRow("Wall", self.wall_label)
        form.addRow("State", self.state_label)
        form.addRow("Backpressure", self.backpressure_label)

        source = self._pane if hasattr(self._pane, "stepped") else self._player
        if source is None:
            return

        getattr(source, "stepped", self._NoopSignal()).connect(self._on_step)
        getattr(source, "logical_elapsed_updated", self._NoopSignal()).connect(self._on_logical)
        getattr(source, "elapsed_updated", self._NoopSignal()).connect(self._on_wall)
        getattr(source, "finished", self._NoopSignal()).connect(self._on_finished)
        if hasattr(source, "backpressure"):
            source.backpressure.connect(self._on_backpressure)

        self._refresh_all()

    # ------------------------------------------------------------ slots

    def _on_step(self, idx: int) -> None:
        total = self._total_steps()
        self.step_label.setText(f"{idx}/{total if total is not None else '?'}")
        self._refresh_state()

    def _on_logical(self, seconds: float) -> None:
        self.logical_label.setText(f"{seconds:.2f} s")
        self._refresh_state()

    def _on_wall(self, seconds: float) -> None:
        self.wall_label.setText(f"{seconds:.2f} s")
        self._refresh_state()

    def _on_finished(self) -> None:
        self.state_label.setText("finished")

    def _on_backpressure(self, payload: dict) -> None:
        active = bool(payload.get("active"))
        self.backpressure_label.setText(str(payload.get("reason", "cap")) if active else "-")

    # ------------------------------------------------------------ helpers

    def _refresh_all(self) -> None:
        step_idx = self._step_index()
        total = self._total_steps()
        self.step_label.setText(f"{step_idx}/{total if total is not None else '?'}")
        self.logical_label.setText(f"{self._logical_seconds():.2f} s")
        self.wall_label.setText(f"{self._wall_seconds():.2f} s")
        self._refresh_state()

    def _refresh_state(self) -> None:
        if self._is_finished():
            self.state_label.setText("finished")
        else:
            self.state_label.setText("running" if self._is_running() else "paused")

    def _step_index(self) -> int:
        pane = self._pane
        try:
            if pane and hasattr(pane, "step_index"):
                return int(pane.step_index())
        except Exception:
            pass
        try:
            if self._player and hasattr(self._player, "step_index"):
                return int(self._player.step_index)
        except Exception:
            pass
        return 0

    def _total_steps(self) -> int | None:
        pane = self._pane
        try:
            if pane and hasattr(pane, "total_steps"):
                total = int(pane.total_steps())
                return total if total > 0 else None
        except Exception:
            pass
        return None

    def _logical_seconds(self) -> float:
        pane = self._pane
        try:
            if pane and hasattr(pane, "logical_seconds"):
                return float(pane.logical_seconds())
        except Exception:
            pass
        try:
            if self._player and hasattr(self._player, "logical_seconds"):
                return float(self._player.logical_seconds())
        except Exception:
            pass
        return 0.0

    def _wall_seconds(self) -> float:
        pane = self._pane
        try:
            if pane and hasattr(pane, "elapsed_seconds"):
                return float(pane.elapsed_seconds())
        except Exception:
            pass
        try:
            if self._player and hasattr(self._player, "elapsed_seconds"):
                return float(self._player.elapsed_seconds())
        except Exception:
            pass
        return 0.0

    def _is_running(self) -> bool:
        pane = self._pane
        try:
            if pane and hasattr(pane, "is_running"):
                return bool(pane.is_running)
        except Exception:
            pass
        try:
            if self._player and hasattr(self._player, "is_running"):
                return bool(self._player.is_running)
        except Exception:
            pass
        return False

    def _is_finished(self) -> bool:
        total = self._total_steps()
        return total is not None and self._step_index() >= total

    class _NoopSignal:
        def connect(self, *_: Any, **__: Any) -> None:
            return
