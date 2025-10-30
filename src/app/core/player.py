from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

STEP_SCHEMA_VERSION = 1
PLAYER_API_VERSION = 2


@dataclass(frozen=True)
class _StepCaps:
    per_tick: int = 8
    per_second: int = 1000


DEFAULT_JITTER_BUDGET = 0.010  # 10 milliseconds
DEFAULT_CAPS = _StepCaps()


class _Stopwatch:
    """Monotonic stopwatch that can pause/resume."""

    __slots__ = ("_accum", "_t0", "_running")

    def __init__(self) -> None:
        self._accum: float = 0.0
        self._t0: float | None = None
        self._running: bool = False

    def start(self) -> None:
        if not self._running:
            self._t0 = perf_counter()
            self._running = True

    def pause(self) -> None:
        if self._running and self._t0 is not None:
            self._accum += perf_counter() - self._t0
            self._t0 = None
            self._running = False

    def reset(self) -> None:
        self._accum = 0.0
        self._t0 = None
        self._running = False

    def stop(self) -> float:
        self.pause()
        return self._accum

    def value(self) -> float:
        if self._running and self._t0 is not None:
            return self._accum + (perf_counter() - self._t0)
        return self._accum


class Player(QObject):
    """Iterator-backed playback driver decoupled from UI widgets."""

    stepped = pyqtSignal(int)
    elapsed_updated = pyqtSignal(float)  # wall-clock playback time
    logical_elapsed_updated = pyqtSignal(float)  # deterministic step time (Σ 1/fps)
    finished = pyqtSignal()
    backpressure = pyqtSignal(dict)

    def __init__(
        self,
        *,
        step_forward: Callable[[], bool],
        step_back: Callable[[], bool] | None = None,
        step_index: Callable[[], int],
        total_steps: Callable[[], int],
        on_finished: Callable[[], None],
        jitter_budget: float = DEFAULT_JITTER_BUDGET,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._step_forward_cb = step_forward
        self._step_back_cb = step_back
        self._step_index_cb = step_index
        self._total_steps_cb = total_steps
        self._after_finish_cb = on_finished

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)

        self._visual_fps = 24
        self._interval_ms = max(1, int(1000 / self._visual_fps))
        self._jitter_budget = max(0.0, jitter_budget)
        self._caps = DEFAULT_CAPS

        self._running = False
        self._completed = False

        self._stopwatch = _Stopwatch()  # wall-clock playback time
        self._logical_accum = 0.0  # Σ(1/fps) for emitted steps
        self._step_durations: list[float] = []  # stack for logical rewind

        self._frames = 0
        self._steps_in_window = 0
        self._window_start = perf_counter()
        self._under_backpressure = False

        self._clock_anchor = perf_counter()

        self._capabilities: dict[str, bool] = {
            "step_back": bool(step_back),
            "true_time": True,
            "detach": False,
            "true_total": True,
        }

    # ------------------------------------------------------------------ capabilities

    @property
    def capabilities(self) -> dict[str, bool]:
        return dict(self._capabilities)

    def set_capability(self, key: str, value: bool) -> None:
        self._capabilities[key] = bool(value)

    # ------------------------------------------------------------------ configuration

    def set_visual_fps(self, fps: int) -> None:
        fps = max(1, int(fps))
        self._visual_fps = fps
        self._interval_ms = max(1, int(1000 / fps))
        if self._timer.isActive():
            self._timer.start(self._interval_ms)

    def set_step_caps(self, *, per_tick: int | None = None, per_second: int | None = None) -> None:
        per_tick_val = self._caps.per_tick if per_tick is None else max(1, int(per_tick))
        per_sec_val = self._caps.per_second if per_second is None else max(1, int(per_second))
        self._caps = _StepCaps(per_tick=per_tick_val, per_second=per_sec_val)

    # ------------------------------------------------------------------ derived state

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def step_index(self) -> int:
        return self._step_index_cb()

    def elapsed_seconds(self) -> float:
        return self._stopwatch.value()

    def logical_seconds(self) -> float:
        return self._logical_accum

    # ------------------------------------------------------------------ transport

    def play(self) -> None:
        if self._running or self._completed:
            return
        if self._visual_fps <= 0:
            self.set_visual_fps(24)
        self._clock_anchor = perf_counter()
        self._window_start = self._clock_anchor
        self._stopwatch.start()
        self._timer.start(self._interval_ms)
        self._running = True
        self.elapsed_updated.emit(self.elapsed_seconds())

    def pause(self) -> None:
        if not self._running:
            return
        self._timer.stop()
        self._stopwatch.pause()
        self._running = False
        self.elapsed_updated.emit(self.elapsed_seconds())

    def toggle_pause(self) -> None:
        if self._running:
            self.pause()
        else:
            self.play()

    def reset(self) -> None:
        self.pause()
        self._stopwatch.reset()
        self._logical_accum = 0.0
        self._step_durations.clear()
        self._frames = 0
        self._steps_in_window = 0
        self._window_start = perf_counter()
        if self._under_backpressure:
            self._under_backpressure = False
            self.backpressure.emit({"active": False})
        self._completed = False
        self.elapsed_updated.emit(self.elapsed_seconds())
        self.logical_elapsed_updated.emit(self.logical_seconds())

    def sync_to_step(self, step_index: int) -> None:
        """Force internal timers to match an external seek operation."""
        target = max(0, int(step_index))
        current = len(self._step_durations)

        if target < current:
            removed = self._step_durations[target:]
            if removed:
                self._logical_accum = max(0.0, self._logical_accum - sum(removed))
                del self._step_durations[target:]
        elif target > current:
            dt = self._step_duration_nominal()
            missing = target - current
            if missing > 0:
                self._step_durations.extend([dt] * missing)
                self._logical_accum += missing * dt

        if target == 0:
            self._logical_accum = 0.0
            self._step_durations.clear()

        self._frames = target
        self._completed = False
        self.logical_elapsed_updated.emit(self.logical_seconds())

    def step_forward(self) -> None:
        self.pause()
        if self._completed:
            return
        self._step_once()

    def step_back(self) -> None:
        if not self._capabilities.get("step_back"):
            return
        self.pause()
        if self._step_back_cb and self._step_back_cb():
            self._record_step_back_logical()
            self.stepped.emit(self._step_index_cb())
            self._completed = False
            self.elapsed_updated.emit(self.elapsed_seconds())
            self.logical_elapsed_updated.emit(self.logical_seconds())

    # ------------------------------------------------------------------ internals

    def _on_tick(self) -> None:
        now = perf_counter()

        steps_this_tick = 0
        while steps_this_tick < self._caps.per_tick:
            ideal_time = self._clock_anchor + (self._frames / self._visual_fps)
            if now <= ideal_time + self._jitter_budget:
                break
            if not self._step_once():
                return
            steps_this_tick += 1
            self._frames += 1
            if not self._enforce_step_rate(now):
                break

        if steps_this_tick == 0:
            if not self._step_once():
                return
            self._frames += 1
            self._enforce_step_rate(now)

        self.elapsed_updated.emit(self.elapsed_seconds())

    def _enforce_step_rate(self, now: float) -> bool:
        window_elapsed = now - self._window_start
        if window_elapsed >= 1.0:
            self._window_start = now
            self._steps_in_window = 0
            if self._under_backpressure:
                self._under_backpressure = False
                self.backpressure.emit({"active": False})

        self._steps_in_window += 1
        if self._steps_in_window > self._caps.per_second:
            if not self._under_backpressure:
                self._under_backpressure = True
                self.backpressure.emit(
                    {
                        "active": True,
                        "reason": "per_second_cap",
                        "per_second": self._caps.per_second,
                    }
                )
            return False
        return True

    def _step_once(self) -> bool:
        advanced = self._step_forward_cb()
        if advanced:
            idx = self._step_index_cb()
            self._record_step_forward_logical()
            self.stepped.emit(idx)

            total = self._safe_total_steps()
            if total > 0 and idx >= total:
                self._finish()
                return False

            self.logical_elapsed_updated.emit(self.logical_seconds())
            return True

        self._finish()
        return False

    def _safe_total_steps(self) -> int:
        try:
            total = self._total_steps_cb()
        except Exception:  # pragma: no cover - defensive
            return 0
        try:
            return max(0, int(total))
        except (TypeError, ValueError):
            return 0

    def _finish(self) -> None:
        if self._completed:
            return
        self._timer.stop()
        self._stopwatch.stop()
        self._running = False
        self._completed = True
        self._after_finish_cb()
        self.finished.emit()
        self.elapsed_updated.emit(self.elapsed_seconds())
        self.logical_elapsed_updated.emit(self.logical_seconds())

    # ------------------------------------------------------------------ logical-time helpers

    def _step_duration_nominal(self) -> float:
        return 1.0 / max(1, self._visual_fps)

    def _record_step_forward_logical(self) -> None:
        dt = self._step_duration_nominal()
        self._logical_accum += dt
        self._step_durations.append(dt)

    def _record_step_back_logical(self) -> None:
        dt = self._step_durations.pop() if self._step_durations else self._step_duration_nominal()
        self._logical_accum = max(0.0, self._logical_accum - dt)
