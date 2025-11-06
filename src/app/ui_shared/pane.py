from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import QObject

from app.core.player import Player


class Pane(QObject):
    """Adapter that exposes a public control surface over a legacy visualizer."""

    def __init__(
        self,
        visualizer,
        *,
        step_forward: Callable[[], bool],
        step_back: Callable[[], bool] | None,
        step_index: Callable[[], int],
        total_steps: Callable[[], int],
        on_finished: Callable[[], None],
    ) -> None:
        super().__init__(visualizer)
        self.visualizer = visualizer
        self._details_visible = False
        self._hud_visible = True
        self._show_values = bool(getattr(visualizer, "show_values", lambda: False)())

        self.player = Player(
            step_forward=step_forward,
            step_back=step_back,
            step_index=step_index,
            total_steps=total_steps,
            on_finished=on_finished,
            parent=self,
        )

        # Convenience aliases so callers do not have to reach into player directly.
        self.stepped = self.player.stepped
        self.elapsed_updated = self.player.elapsed_updated
        self.logical_elapsed_updated = self.player.logical_elapsed_updated
        self.finished = self.player.finished
        self.backpressure = self.player.backpressure

    # ------------------------------------------------------------------ capabilities

    def capabilities(self) -> dict[str, bool]:
        """Return a copy of the pane capability map."""
        return self.player.capabilities

    def set_capability(self, key: str, value: bool) -> None:
        self.player.set_capability(key, value)

    def set_visual_fps(self, fps: int) -> None:
        self.player.set_visual_fps(fps)

    # ------------------------------------------------------------------ transport controls

    def play(self) -> None:
        self.player.play()

    def pause(self) -> None:
        self.player.pause()

    def toggle_pause(self) -> None:
        self.player.toggle_pause()

    def reset(self) -> None:
        self.player.reset()

    def step_forward(self) -> None:
        self.player.step_forward()

    def step_back(self) -> None:
        self.player.step_back()

    # ------------------------------------------------------------------ state queries

    @property
    def is_running(self) -> bool:
        return self.player.is_running

    def step_index(self) -> int:
        return self.player.step_index

    def elapsed_seconds(self) -> float:
        return self.player.elapsed_seconds()

    def logical_seconds(self) -> float:
        return self.player.logical_seconds()

    def sync_to_step(self, step_index: int) -> None:
        self.player.sync_to_step(step_index)

    @property
    def visual_fps(self) -> int:
        """Expose the player's configured FPS."""
        return self.player.visual_fps

    # ------------------------------------------------------------------ view helpers

    def set_hud_visible(self, show: bool) -> None:
        self._hud_visible = bool(show)
        if hasattr(self.visualizer, "set_show_hud"):
            self.visualizer.set_show_hud(self._hud_visible)

    def hud_visible(self) -> bool:
        return self._hud_visible

    def set_show_values(self, show: bool) -> None:
        self._show_values = bool(show)
        if hasattr(self.visualizer, "set_show_values"):
            self.visualizer.set_show_values(self._show_values)

    def show_values(self) -> bool:
        return self._show_values

    def toggle_details(self, on: bool) -> None:
        self._details_visible = bool(on)

    def details_visible(self) -> bool:
        return self._details_visible
