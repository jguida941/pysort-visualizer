from __future__ import annotations

from PyQt6.QtWidgets import QApplication

from app.core.compare import CompareView


def test_compare_view_shared_start_stop(qapp: QApplication) -> None:  # noqa: F811
    view = CompareView()
    dataset = [4, 1, 3, 2]
    view.prepare_dataset(dataset)
    view.fps_slider.setValue(15)
    view.apply_theme("high-contrast")
    view.controller.play()
    qapp.processEvents()
    view.controller.toggle_pause()
    view.controller.reset()
    view.apply_theme("dark")
