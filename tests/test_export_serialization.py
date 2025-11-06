from __future__ import annotations

import json
from pathlib import Path

import pytest
from PyQt6.QtWidgets import QApplication

from app.algos.registry import INFO, REGISTRY, load_all_algorithms
from app.core.base import AlgorithmVisualizerBase, VizConfig
from app.core.replay import apply_step_sequence
from app.core.step import Step

VisualizerBundle = tuple[AlgorithmVisualizerBase, list[int], list[Step]]


@pytest.fixture
def bubble_visualizer(qapp: QApplication) -> VisualizerBundle:  # noqa: F811 - shared fixture
    load_all_algorithms()
    info = INFO["Bubble Sort"]
    visualizer = AlgorithmVisualizerBase(info, REGISTRY[info.name], VizConfig())

    original = [5, 3, 1, 4]
    visualizer._initial_array = list(original)

    working = list(original)
    steps = list(REGISTRY[info.name](working))

    visualizer._array = working
    visualizer._steps = steps
    visualizer._checkpoints = [(0, list(original), 0, 0)]
    visualizer._current_preset = "random"
    visualizer._current_seed = 99

    return visualizer, original, steps


def test_export_json_roundtrip(bubble_visualizer: VisualizerBundle, tmp_path: Path) -> None:
    visualizer, original, steps = bubble_visualizer
    export_path = tmp_path / "session.json"

    visualizer._export_json(str(export_path))

    assert export_path.exists()

    data = json.loads(export_path.read_text(encoding="utf-8"))
    assert data["algo"] == "Bubble Sort"
    assert data["preset"] == "random"
    assert data["seed"] == 99

    exported_steps = [
        Step(entry["op"], tuple(entry["indices"]), entry.get("payload")) for entry in data["steps"]
    ]

    restored = apply_step_sequence(original, exported_steps)
    assert restored == visualizer._array
    assert len(exported_steps) == len(steps)


def test_export_csv_creates_rows(bubble_visualizer: VisualizerBundle, tmp_path: Path) -> None:
    visualizer, _original, steps = bubble_visualizer
    export_path = tmp_path / "steps.csv"

    visualizer._export_csv(str(export_path))

    contents = export_path.read_text(encoding="utf-8").strip().splitlines()
    # header + one row per step
    assert len(contents) == len(steps) + 1
    assert contents[0].split(",")[:2] == ["idx", "op"]


def test_benchmark_dataset_returns_entries(
    bubble_visualizer: VisualizerBundle,
) -> None:
    visualizer, original, _steps = bubble_visualizer
    rows = visualizer._benchmark_dataset(list(original), "random", 101, 0)
    assert rows, "Benchmark returned no rows"
    first_row = rows[0]
    # algo, run, preset, seed, n, steps, comparisons, swaps, duration_cpu_ms, duration_visual_ms, sorted, error
    assert len(first_row) == 12
    assert first_row[0] == "Bubble Sort"
    assert first_row[2] == "random"
    assert first_row[3] in ("", "101", 101)
    assert first_row[10] in (0, 1)
    assert first_row[11] == ""
