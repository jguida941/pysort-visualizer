from __future__ import annotations

from app.core.compare import CompareView


def test_compare_manual_step_advances(qapp):  # noqa: F811
    view = CompareView()
    dataset = [5, 3, 1]
    view.prepare_dataset(dataset)
    left_pane = view.left_pane
    right_pane = view.right_pane
    assert left_pane is not None and right_pane is not None

    left_before = left_pane.step_index()
    right_before = right_pane.step_index()
    view.controller.step_forward()
    qapp.processEvents()
    assert left_pane.step_index() > left_before
    assert right_pane.step_index() > right_before


def test_compare_details_toggle_hides_hud(qapp):  # noqa: F811
    view = CompareView()
    view.prepare_dataset([4, 1, 3])
    left_pane = view.left_pane
    assert left_pane is not None

    assert left_pane.hud_visible() is True
    view.toggle_details_for_side("left", True)
    qapp.processEvents()
    assert left_pane.details_visible() is True
    assert left_pane.hud_visible() is False
    view.toggle_details_for_side("left", False)
    qapp.processEvents()
    assert left_pane.details_visible() is False
    assert left_pane.hud_visible() is True
