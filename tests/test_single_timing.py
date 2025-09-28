from __future__ import annotations

import pytest

from app.algos.registry import INFO, load_all_algorithms
from app.ui_single.window import SuiteWindow

load_all_algorithms()


@pytest.fixture
def single_window(qapp):  # noqa: F811
    window = SuiteWindow()
    yield window
    window.close()


def test_single_manual_step_updates_logical_time(single_window, qtbot):  # noqa: F811
    names = sorted(INFO.keys())
    target = names[0]
    viz = single_window.visualizer_for(target)
    pane = single_window.pane_for(target)
    assert pane is not None
    assert viz is not None

    array = [5, 4, 3, 2]
    viz.prime_external_run(array)
    pane.reset()

    baseline_logical = pane.logical_seconds()
    pane.step_forward()
    assert pane.logical_seconds() > baseline_logical

    pane.step_back()
    assert pane.logical_seconds() == pytest.approx(0.0, abs=1e-6)


def test_single_play_pause_updates_wall_clock(single_window, qtbot):  # noqa: F811
    names = sorted(INFO.keys())
    target = names[0]
    viz = single_window.visualizer_for(target)
    pane = single_window.pane_for(target)
    assert pane is not None
    assert viz is not None

    viz.prime_external_run([3, 2, 1])
    pane.reset()

    baseline = pane.elapsed_seconds()
    pane.play()
    qtbot.wait(150)
    pane.pause()
    assert pane.elapsed_seconds() > baseline

    pause_value = pane.elapsed_seconds()
    qtbot.wait(150)
    assert pane.elapsed_seconds() == pytest.approx(pause_value)
