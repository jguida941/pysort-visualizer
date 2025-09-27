from __future__ import annotations

import random

import pytest

from app.presets import DEFAULT_PRESET_KEY, Preset, generate_dataset, get_presets


@pytest.mark.parametrize("preset", get_presets())
def test_preset_values_within_bounds(preset: Preset) -> None:
    rng = random.Random(42)
    lo, hi = 0, 50
    n = 32
    data = preset.generator(n, lo, hi, rng)
    assert len(data) == n
    assert all(lo <= value <= hi for value in data)


@pytest.mark.parametrize("preset_key", [preset.key for preset in get_presets()])
def test_preset_reproducible_with_seed(preset_key: str) -> None:
    seed = 1234
    lo, hi = -20, 20
    n = 24

    rng1 = random.Random(seed)
    rng2 = random.Random(seed)

    data1 = generate_dataset(preset_key, n, lo, hi, rng1)
    data2 = generate_dataset(preset_key, n, lo, hi, rng2)

    assert data1 == data2


def test_default_preset_present() -> None:
    preset_keys = {preset.key for preset in get_presets()}
    assert DEFAULT_PRESET_KEY in preset_keys
