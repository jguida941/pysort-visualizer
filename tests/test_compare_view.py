from __future__ import annotations

from PyQt6.QtWidgets import QApplication

from app.core.compare import CompareView


def test_compare_view_shared_start_stop(qapp: QApplication) -> None:  # noqa: F811
    view = CompareView()
    view.array_edit.setText("4,1,3,2")
    view.fps_slider.setValue(15)
    view.apply_theme("high-contrast")
    view._on_start_clicked()
    qapp.processEvents()
    view._on_pause_clicked()
    view._on_reset_clicked()
    view.apply_theme("dark")
