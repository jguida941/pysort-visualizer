from __future__ import annotations

import pytest
from PyQt6.QtTest import QSignalSpy

from app.core.player import Player


def _build_player(state: dict[str, int], total: int = 3) -> Player:
    def step_forward() -> bool:
        if state["idx"] < total:
            state["idx"] += 1
            return True
        return False

    def step_back() -> bool:
        if state["idx"] > 0:
            state["idx"] -= 1
            return True
        return False

    def on_finished() -> None:
        state["finished"] += 1

    player = Player(
        step_forward=step_forward,
        step_back=step_back,
        step_index=lambda: state["idx"],
        total_steps=lambda: total,
        on_finished=on_finished,
    )
    player.set_capability("step_back", True)
    return player


def test_player_manual_stepping() -> None:
    state = {"idx": 0, "finished": 0}
    player = _build_player(state)
    player.step_forward()
    assert state["idx"] == 1
    player.step_back()
    assert state["idx"] == 0
    player.step_forward()
    player.step_forward()
    player.step_forward()
    assert state["idx"] == 3
    assert state["finished"] == 1


def test_player_elapsed_independent_of_fps(qtbot):  # noqa: F811
    state = {"idx": 0, "finished": 0}
    player = _build_player(state, total=100)

    player.set_visual_fps(60)
    player.play()
    qtbot.wait(100)
    player.pause()
    elapsed_fast = player.elapsed_seconds()
    steps_fast = state["idx"]

    state["idx"] = 0
    state["finished"] = 0
    player.reset()
    player.set_visual_fps(10)
    player.play()
    qtbot.wait(100)
    player.pause()
    elapsed_slow = player.elapsed_seconds()
    steps_slow = state["idx"]

    assert elapsed_fast > 0
    assert abs(elapsed_fast - elapsed_slow) < 0.1
    assert steps_fast > steps_slow  # fewer frames at low FPS but elapsed similar


def test_player_backpressure_emits_once(qtbot):  # noqa: F811
    state = {"idx": 0, "finished": 0}
    player = _build_player(state, total=500)
    player.set_step_caps(per_tick=2, per_second=5)
    spy = QSignalSpy(player.backpressure)
    player.play()
    qtbot.wait(500)
    player.pause()
    assert len(spy) <= 2  # enter + exit at most


def test_player_manual_step_updates_elapsed() -> None:
    state = {"idx": 0, "finished": 0}
    player = _build_player(state, total=5)
    baseline_wall = player.elapsed_seconds()
    baseline_logical = player.logical_seconds()
    player.step_forward()
    assert player.elapsed_seconds() == pytest.approx(baseline_wall)
    assert player.logical_seconds() > baseline_logical
    player.step_back()
    assert player.logical_seconds() == pytest.approx(0.0, abs=1e-6)
