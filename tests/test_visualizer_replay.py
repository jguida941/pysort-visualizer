from __future__ import annotations

from PyQt6.QtTest import QSignalSpy, QTest

from app.algos.registry import INFO, REGISTRY, load_all_algorithms
from app.core.base import AlgorithmVisualizerBase

load_all_algorithms()


def test_repeated_generate_and_start(qapp):  # noqa: F811
    algo_name = "Bubble Sort"
    info = INFO[algo_name]
    viz = AlgorithmVisualizerBase(
        algo_info=info, algo_func=REGISTRY[algo_name], show_controls=False
    )
    pane = viz.pane
    assert pane is not None

    viz.prime_external_run([5, 3, 2, 1])
    pane.reset()
    spy = QSignalSpy(pane.finished)
    pane.play()
    for _ in range(40):
        if len(spy) >= 1:
            break
        QTest.qWait(50)
    assert len(spy) >= 1
    pane.reset()

    # third run to ensure start-on-finished works without manual reset
    viz.prime_external_run([1, 2, 3, 4])
    spy = QSignalSpy(pane.finished)
    pane.play()
    for _ in range(40):
        if len(spy) >= 1:
            break
        QTest.qWait(50)
    assert len(spy) >= 1

    viz.prime_external_run([4, 2, 1, 3])
    pane.reset()
    spy = QSignalSpy(pane.finished)
    pane.play()
    for _ in range(40):
        if len(spy) >= 1:
            break
        QTest.qWait(50)
    assert len(spy) >= 1

    assert pane.step_index() == viz.total_steps()
    assert pane.logical_seconds() > 0.0
