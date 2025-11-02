from __future__ import annotations

from PyQt6.QtCore import QObject


class CompareController(QObject):
    """Fan out transport controls across two visualizer panes."""

    def __init__(self, left: object, right: object, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.left = left
        self.right = right

    def play(self) -> None:
        self.left.play()
        self.right.play()

    def toggle_pause(self) -> None:
        self.left.toggle_pause()
        self.right.toggle_pause()

    def reset(self) -> None:
        self.left.reset()
        self.right.reset()

    def step_forward(self) -> None:
        self.left.step_forward()
        self.right.step_forward()

    def step_back(self) -> None:
        if self.left.capabilities().get("step_back", False):
            self.left.step_back()
        if self.right.capabilities().get("step_back", False):
            self.right.step_back()

    def is_running(self) -> bool:
        """Check if either pane is currently running."""
        return self.left.is_running or self.right.is_running
