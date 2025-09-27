from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass

PresetGenerator = Callable[[int, int, int, random.Random], list[int]]


@dataclass(frozen=True)
class Preset:
    key: str
    label: str
    description: str
    generator: PresetGenerator


def _random_uniform(n: int, lo: int, hi: int, rng: random.Random) -> list[int]:
    return [rng.randint(lo, hi) for _ in range(n)]


def _sorted_ascending(n: int, lo: int, hi: int, rng: random.Random) -> list[int]:
    data = _random_uniform(n, lo, hi, rng)
    data.sort()
    return data


def _sorted_descending(n: int, lo: int, hi: int, rng: random.Random) -> list[int]:
    data = _sorted_ascending(n, lo, hi, rng)
    data.reverse()
    return data


def _nearly_sorted(n: int, lo: int, hi: int, rng: random.Random) -> list[int]:
    data = _sorted_ascending(n, lo, hi, rng)
    swaps = max(1, n // 8)
    for _ in range(swaps):
        i = rng.randrange(0, n)
        j = rng.randrange(0, n)
        if i == j:
            continue
        data[i], data[j] = data[j], data[i]
    return data


def _reverse_run(n: int, lo: int, hi: int, rng: random.Random) -> list[int]:
    data = _sorted_descending(n, lo, hi, rng)
    run = max(2, n // 6)
    start = rng.randrange(0, max(1, n - run))
    segment = data[start : start + run]
    segment.reverse()
    data[start : start + run] = segment
    return data


def _few_unique(n: int, lo: int, hi: int, rng: random.Random) -> list[int]:
    unique_target = min(5, max(1, hi - lo + 1))
    pool: set[int] = set()
    while len(pool) < unique_target:
        pool.add(rng.randint(lo, hi))
    choices = tuple(sorted(pool))
    return [choices[rng.randrange(0, len(choices))] for _ in range(n)]


PRESETS: tuple[Preset, ...] = (
    Preset(
        key="random",
        label="Random (uniform)",
        description="Each element is drawn independently from the configured min/max range.",
        generator=_random_uniform,
    ),
    Preset(
        key="nearly_sorted",
        label="Nearly sorted",
        description="Ascending order with a handful of random swaps injected.",
        generator=_nearly_sorted,
    ),
    Preset(
        key="reverse_sorted",
        label="Reverse sorted",
        description="Descending order to stress algorithms that assume ascending inputs.",
        generator=_sorted_descending,
    ),
    Preset(
        key="reverse_run",
        label="Reverse run",
        description="Mostly descending but one sub-run is flipped to ascending for visual variety.",
        generator=_reverse_run,
    ),
    Preset(
        key="few_unique",
        label="Few unique",
        description="Only a handful of distinct values, encouraging duplicate-heavy traces.",
        generator=_few_unique,
    ),
    Preset(
        key="sorted",
        label="Sorted ascending",
        description="Ascending order – showcase best-case behaviour for adaptive algorithms.",
        generator=_sorted_ascending,
    ),
)

PRESET_LOOKUP: dict[str, Preset] = {preset.key: preset for preset in PRESETS}

DEFAULT_PRESET_KEY = "random"


def get_presets() -> tuple[Preset, ...]:
    return PRESETS


def get_preset(key: str) -> Preset:
    return PRESET_LOOKUP[key]


def generate_dataset(
    key: str,
    n: int,
    lo: int,
    hi: int,
    rng: random.Random,
) -> list[int]:
    preset = get_preset(key)
    return preset.generator(n, lo, hi, rng)
