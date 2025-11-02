"""Playback engine for algorithm visualization.

This module provides the Player class, which is responsible for orchestrating
the playback of algorithm steps at a controlled frame rate. The Player acts as
a bridge between the step generation (algorithm) and the visualization (UI).

Key responsibilities:
- Control playback (play, pause, step forward/back)
- Maintain frame-accurate timing for consistent visualization
- Track both wall-clock time and deterministic logical time
- Emit signals for UI updates (stepped, elapsed_updated, finished)
- Handle backpressure when step generation is too slow

The Player is designed to be UI-agnostic and communicates via callbacks and
Qt signals, making it reusable across different visualization contexts.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

# Version markers for compatibility tracking
STEP_SCHEMA_VERSION = 1  # Version of the Step data structure
PLAYER_API_VERSION = 2   # Version of the Player callback interface


@dataclass(frozen=True)
class _StepCaps:
    """Rate limiting configuration for step execution.

    Controls how many steps can be executed per timer tick and per second,
    preventing overwhelming the UI with too many updates.

    Attributes:
        per_tick: Maximum steps to execute in a single timer tick (prevents UI freezing)
        per_second: Maximum steps to execute per second (overall rate limit)
    """
    per_tick: int = 8      # Max steps per timer tick to prevent UI freezing
    per_second: int = 1000 # Max steps per second overall


# Default jitter tolerance for frame timing (10ms)
# Allows slight timing drift before forcing a catchup frame
DEFAULT_JITTER_BUDGET = 0.010

# Default rate limiting configuration
DEFAULT_CAPS = _StepCaps()


class _Stopwatch:
    """Monotonic stopwatch that can pause and resume.

    A simple accumulating timer that tracks elapsed time while accounting for
    paused periods. Uses perf_counter() for high-resolution timing.

    This is used to track wall-clock playback time in the Player, allowing
    accurate measurement of how long the visualization has been running,
    excluding paused periods.

    Attributes:
        _accum: Accumulated elapsed time (excluding paused periods)
        _t0: Start timestamp of current running period (None when paused)
        _running: Whether the stopwatch is currently running
    """

    __slots__ = ("_accum", "_t0", "_running")

    def __init__(self) -> None:
        """Initialize a stopped stopwatch with zero elapsed time."""
        self._accum: float = 0.0
        self._t0: float | None = None
        self._running: bool = False

    def start(self) -> None:
        """Start or resume the stopwatch.

        If already running, this is a no-op. Otherwise, records the current
        time as the start of a new running period.
        """
        if not self._running:
            self._t0 = perf_counter()
            self._running = True

    def pause(self) -> None:
        """Pause the stopwatch.

        If running, adds the elapsed time since start to the accumulator and
        stops the timer. If already paused, this is a no-op.
        """
        if self._running and self._t0 is not None:
            self._accum += perf_counter() - self._t0
            self._t0 = None
            self._running = False

    def reset(self) -> None:
        """Reset the stopwatch to zero and stop it."""
        self._accum = 0.0
        self._t0 = None
        self._running = False

    def stop(self) -> float:
        """Stop the stopwatch and return the final elapsed time.

        Returns:
            Total elapsed time in seconds (excluding paused periods)
        """
        self.pause()
        return self._accum

    def value(self) -> float:
        """Get the current elapsed time without stopping the watch.

        Returns:
            Total elapsed time in seconds, including the current running period
            if the stopwatch is active.
        """
        if self._running and self._t0 is not None:
            return self._accum + (perf_counter() - self._t0)
        return self._accum


class Player(QObject):
    """Frame-accurate playback engine for algorithm visualization.

    The Player orchestrates the controlled execution of algorithm steps at a
    specified frame rate (FPS). It acts as the bridge between:
    - Algorithm generators (which yield Step objects)
    - The visualizer (which renders the current state)

    Key Features:
        - Smooth, frame-accurate playback using QTimer
        - Dual time tracking: wall-clock time and deterministic logical time
        - Forward and backward stepping support
        - Rate limiting to prevent UI overload
        - Backpressure detection and reporting
        - Pause/resume capability

    The Player communicates through callbacks (for requesting steps) and Qt signals
    (for notifying about state changes). This decoupling makes it reusable across
    different visualization contexts.

    Timing Model:
        - Wall-clock time: Actual elapsed time (pauses excluded)
        - Logical time: Deterministic time based on step count × (1/FPS)
          This ensures reproducible timing regardless of hardware performance

    Signals:
        stepped(int): Emitted after each step, with the current step index
        elapsed_updated(float): Emitted periodically with wall-clock elapsed time
        logical_elapsed_updated(float): Emitted with deterministic logical time
        finished(): Emitted when all steps are completed
        backpressure(dict): Emitted when rate limits are hit (with details)

    Example:
        >>> def step_forward():
        ...     # Generate next step
        ...     return True  # or False if done
        >>> def step_index():
        ...     return current_step_idx
        >>> def total_steps():
        ...     return 100
        >>> def on_finished():
        ...     print("Algorithm complete!")
        >>>
        >>> player = Player(
        ...     step_forward=step_forward,
        ...     step_index=step_index,
        ...     total_steps=total_steps,
        ...     on_finished=on_finished
        ... )
        >>> player.set_visual_fps(30)
        >>> player.play()
    """

    # Qt Signals for communicating state changes
    stepped = pyqtSignal(int)              # Emitted after each step with index
    elapsed_updated = pyqtSignal(float)    # Wall-clock playback time
    logical_elapsed_updated = pyqtSignal(float)  # Deterministic step time (Σ 1/fps)
    finished = pyqtSignal()                # Emitted when algorithm completes
    backpressure = pyqtSignal(dict)        # Emitted when rate limits are hit

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
        """Initialize the playback engine.

        Args:
            step_forward: Callback to advance one step. Returns True if successful,
                False if no more steps available.
            step_back: Optional callback to rewind one step. Returns True if successful.
                If None, backward stepping will be disabled.
            step_index: Callback that returns the current step index (0-based).
            total_steps: Callback that returns the total number of steps, or 0 if unknown.
            on_finished: Callback invoked when algorithm completes (before finished signal).
            jitter_budget: Tolerance for frame timing drift in seconds (default 10ms).
                Larger values allow more timing flexibility but less frame accuracy.
            parent: Optional QObject parent for Qt memory management.

        Notes:
            - Callbacks are invoked from the Qt event loop (main thread)
            - step_forward should be lightweight to avoid blocking the UI
            - total_steps can return 0 if the total is not known in advance
        """
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
        """Get a copy of the current capability flags.

        Capabilities describe what features are available:
        - step_back: Whether backward stepping is supported
        - true_time: Whether logical time tracking is accurate
        - detach: Whether the player can detach from the visualizer
        - true_total: Whether the total step count is known

        Returns:
            Dictionary mapping capability names to boolean values
        """
        return dict(self._capabilities)

    def set_capability(self, key: str, value: bool) -> None:
        """Set a capability flag.

        Args:
            key: Capability name (e.g., 'step_back', 'true_total')
            value: Whether the capability is enabled
        """
        self._capabilities[key] = bool(value)

    # ------------------------------------------------------------------ configuration

    def set_visual_fps(self, fps: int) -> None:
        """Set the target playback frame rate.

        Updates the timer interval to match the new FPS. If playback is active,
        the timer is restarted with the new interval immediately.

        Args:
            fps: Target frames per second (clamped to minimum of 1)

        Notes:
            - Higher FPS = smoother animation but more CPU usage
            - Lower FPS = choppier animation but better for slow observation
            - The actual FPS may be lower if step generation is too slow
        """
        fps = max(1, int(fps))
        self._visual_fps = fps
        self._interval_ms = max(1, int(1000 / fps))
        if self._timer.isActive():
            self._timer.start(self._interval_ms)

    def set_step_caps(self, *, per_tick: int | None = None, per_second: int | None = None) -> None:
        """Configure rate limiting for step execution.

        Args:
            per_tick: Maximum steps to execute per timer tick (default: 8)
                Prevents UI freezing from processing too many steps at once
            per_second: Maximum steps to execute per second (default: 1000)
                Overall rate limit to prevent overwhelming the system

        Notes:
            - per_tick prevents blocking the UI thread for too long
            - per_second provides an overall throughput cap
            - If limits are hit, backpressure signal is emitted
        """
        per_tick_val = self._caps.per_tick if per_tick is None else max(1, int(per_tick))
        per_sec_val = self._caps.per_second if per_second is None else max(1, int(per_second))
        self._caps = _StepCaps(per_tick=per_tick_val, per_second=per_sec_val)

    # ------------------------------------------------------------------ derived state

    @property
    def is_running(self) -> bool:
        """Check if playback is currently active.

        Returns:
            True if playing, False if paused or stopped
        """
        return self._running

    @property
    def step_index(self) -> int:
        """Get the current step index from the callback.

        Returns:
            Current 0-based step index
        """
        return self._step_index_cb()

    def elapsed_seconds(self) -> float:
        """Get wall-clock elapsed time (excluding paused periods).

        Returns:
            Elapsed time in seconds since playback started
        """
        return self._stopwatch.value()

    def logical_seconds(self) -> float:
        """Get deterministic logical time.

        Logical time is computed as the sum of (1/fps) for each step executed,
        providing a reproducible time measurement independent of hardware speed.

        Returns:
            Logical elapsed time in seconds
        """
        return self._logical_accum

    # ------------------------------------------------------------------ transport

    def play(self) -> None:
        """Start or resume playback.

        Begins executing steps at the configured frame rate. If already playing
        or completed, this is a no-op.

        Emits:
            elapsed_updated: With current elapsed time
        """
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
        """Pause playback.

        Stops the timer and pauses the stopwatch. If already paused, this is a no-op.

        Emits:
            elapsed_updated: With current elapsed time
        """
        if not self._running:
            return
        self._timer.stop()
        self._stopwatch.pause()
        self._running = False
        self.elapsed_updated.emit(self.elapsed_seconds())

    def toggle_pause(self) -> None:
        """Toggle between playing and paused states.

        Convenience method that calls play() if paused, or pause() if playing.
        """
        if self._running:
            self.pause()
        else:
            self.play()

    def reset(self) -> None:
        """Reset the player to initial state.

        Pauses playback, resets all timers, clears accumulated state, and marks
        the player as not completed (ready to play again).

        Emits:
            elapsed_updated: With zero elapsed time
            logical_elapsed_updated: With zero logical time
            backpressure: To clear any active backpressure warnings
        """
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
        """Synchronize internal timers to match an external seek operation.

        This is called after the visualizer performs a scrub/seek to update the
        player's logical time to match the new step position. This ensures that
        timing remains consistent after seeking.

        Args:
            step_index: The target step index (0-based) to sync to

        Emits:
            logical_elapsed_updated: With the new logical time

        Notes:
            - Reconstructs logical time as step_index × (1/fps)
            - Rebuilds the step durations list to match
            - Clears completion flag to allow resuming playback
        """
        target = max(0, int(step_index))

        # Recalculate logical time based on the target step index
        dt = self._step_duration_nominal()
        self._logical_accum = target * dt

        # Rebuild the step durations list to match
        self._step_durations = [dt] * target

        # If we're at step 0, clear everything
        if target == 0:
            self._logical_accum = 0.0
            self._step_durations.clear()

        self._frames = target
        self._completed = False
        self.logical_elapsed_updated.emit(self.logical_seconds())

    def step_forward(self) -> None:
        """Execute a single step forward manually.

        Pauses playback (if running) and advances by exactly one step. If the
        algorithm is already completed, this is a no-op.

        This is typically bound to keyboard shortcuts or step buttons in the UI.
        """
        self.pause()
        if self._completed:
            return
        self._step_once()

    def step_back(self) -> None:
        """Execute a single step backward manually.

        Pauses playback (if running) and rewinds by exactly one step. This only
        works if the step_back callback was provided and the 'step_back' capability
        is enabled.

        Emits:
            stepped: With the new step index
            elapsed_updated: With current elapsed time
            logical_elapsed_updated: With updated logical time

        Notes:
            - Requires step_back callback to be provided at initialization
            - Clears the completion flag if we step back from a finished state
        """
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
        """Handle timer tick for frame-accurate playback.

        This is the core of the frame-timing algorithm. It ensures that steps
        are executed at the correct rate to match the target FPS, even if the
        timer fires slightly early or late.

        Algorithm:
        1. Calculate how many steps we should have executed by now based on
           wall-clock time
        2. Execute steps to catch up (up to per_tick limit)
        3. If we're ahead of schedule, execute just one step
        4. Enforce rate limits to prevent UI overload

        Notes:
            - Uses frame-accurate timing, not just interval-based steps
            - Handles jitter by allowing small timing deviations
            - Enforces both per-tick and per-second rate limits
        """
        now = perf_counter()

        steps_this_tick = 0
        # Catch up if we're behind schedule (up to per_tick limit)
        while steps_this_tick < self._caps.per_tick:
            # Calculate ideal time for the next frame
            ideal_time = self._clock_anchor + (self._frames / self._visual_fps)
            # If we're ahead of schedule (within jitter tolerance), stop catching up
            if now <= ideal_time + self._jitter_budget:
                break
            if not self._step_once():
                return  # Algorithm finished
            steps_this_tick += 1
            self._frames += 1
            # Check if we've hit the per-second rate limit
            if not self._enforce_step_rate(now):
                break

        # If we didn't catch up any steps, execute at least one
        if steps_this_tick == 0:
            if not self._step_once():
                return  # Algorithm finished
            self._frames += 1
            self._enforce_step_rate(now)

        # Notify UI of elapsed time update
        self.elapsed_updated.emit(self.elapsed_seconds())

    def _enforce_step_rate(self, now: float) -> bool:
        """Enforce per-second rate limiting and detect backpressure.

        Tracks steps executed in the current 1-second window and prevents
        exceeding the per_second cap. Emits backpressure signals when limits
        are hit or cleared.

        Args:
            now: Current timestamp from perf_counter()

        Returns:
            True if we can continue stepping, False if rate limit was hit

        Emits:
            backpressure: When entering or exiting backpressure state
        """
        window_elapsed = now - self._window_start
        # Reset window every second
        if window_elapsed >= 1.0:
            self._window_start = now
            self._steps_in_window = 0
            # Clear backpressure flag if it was set
            if self._under_backpressure:
                self._under_backpressure = False
                self.backpressure.emit({"active": False})

        self._steps_in_window += 1
        # Check if we've exceeded the per-second limit
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
        """Execute a single step and handle completion.

        Calls the step_forward callback, updates logical time, emits signals,
        and checks for algorithm completion.

        Returns:
            True if step was executed successfully, False if algorithm finished

        Emits:
            stepped: With the new step index
            logical_elapsed_updated: With updated logical time
            finished: If algorithm completes
        """
        advanced = self._step_forward_cb()
        if advanced:
            idx = self._step_index_cb()
            self._record_step_forward_logical()
            self.stepped.emit(idx)

            # Check if we've reached the total (if known)
            total = self._safe_total_steps()
            if total > 0 and idx >= total:
                self._finish()
                return False

            self.logical_elapsed_updated.emit(self.logical_seconds())
            return True

        # Step callback returned False - algorithm is done
        self._finish()
        return False

    def _safe_total_steps(self) -> int:
        """Safely call the total_steps callback with error handling.

        Returns:
            Total steps from callback, or 0 if callback fails or returns invalid value
        """
        try:
            total = self._total_steps_cb()
        except Exception:  # pragma: no cover - defensive
            return 0
        try:
            return max(0, int(total))
        except (TypeError, ValueError):
            return 0

    def _finish(self) -> None:
        """Mark playback as finished and emit completion signals.

        Stops the timer, stopwatch, and marks as completed. Calls the on_finished
        callback before emitting the finished signal.

        Emits:
            finished: Algorithm completion signal
            elapsed_updated: Final elapsed time
            logical_elapsed_updated: Final logical time
        """
        if self._completed:
            return  # Already finished, don't double-trigger
        self._timer.stop()
        self._stopwatch.stop()
        self._running = False
        self._completed = True
        self._after_finish_cb()  # Call user callback first
        self.finished.emit()
        self.elapsed_updated.emit(self.elapsed_seconds())
        self.logical_elapsed_updated.emit(self.logical_seconds())

    # ------------------------------------------------------------------ logical-time helpers

    def _step_duration_nominal(self) -> float:
        """Calculate the nominal duration of one step at current FPS.

        Returns:
            Duration in seconds (1 / fps)
        """
        return 1.0 / max(1, self._visual_fps)

    def _record_step_forward_logical(self) -> None:
        """Record a forward step in logical time tracking.

        Adds the nominal step duration to the logical accumulator and
        saves it in the durations list for potential rewind.
        """
        dt = self._step_duration_nominal()
        self._logical_accum += dt
        self._step_durations.append(dt)

    def _record_step_back_logical(self) -> None:
        """Record a backward step in logical time tracking.

        Pops the most recent duration from the stack and subtracts it
        from the logical accumulator. If the stack is empty, uses the
        nominal duration.
        """
        dt = self._step_durations.pop() if self._step_durations else self._step_duration_nominal()
        self._logical_accum = max(0.0, self._logical_accum - dt)
