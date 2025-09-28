from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from app.core.compare import CompareView


def test_compare_shortcuts_scope(qapp):  # noqa: F811
    view = CompareView()
    dataset = [5, 4, 3, 2]
    view.prepare_dataset(dataset)
    qapp.processEvents()

    left_pane = view.left_pane
    right_pane = view.right_pane
    assert left_pane is not None and right_pane is not None
    left_canvas = left_pane.visualizer.canvas
    right_canvas = right_pane.visualizer.canvas

    # Focus left pane and trigger playback via keyboard
    QTest.mouseClick(left_canvas, Qt.MouseButton.LeftButton)
    qapp.processEvents()
    right_baseline = right_pane.step_index()
    QTest.keyClick(left_canvas, Qt.Key.Key_Right)
    qapp.processEvents()

    assert right_pane.step_index() == right_baseline

    # Focus right pane and ensure shortcuts stay scoped
    QTest.mouseClick(right_canvas, Qt.MouseButton.LeftButton)
    qapp.processEvents()
    right_before = right_pane.step_index()
    left_before = left_pane.step_index()
    QTest.keyClick(right_canvas, Qt.Key.Key_Right)
    qapp.processEvents()

    assert right_pane.step_index() >= right_before
    assert left_pane.step_index() == left_before
