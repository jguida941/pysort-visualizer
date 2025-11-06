"""Unit tests for the renderer step translator."""

import pytest

from app.core.step import Step
from app.rendering.step_translator import (
    STEP_COLOR_MAP,
    STEP_KIND_MAP,
    StepRenderEvent,
    StepTranslator,
)


def test_translate_all_known_ops() -> None:
    """Every supported Step op should translate to the documented render kind."""
    translator = StepTranslator()
    cases = {
        "compare": ("compare", (0, 1), None),
        "swap": ("swap", (2, 4), None),
        "shift": ("shift", (3,), 42),
        "set": ("set", (5,), 99),
        "write": ("write", (1,), -3),
        "pivot": ("pivot", (4,), None),
        "merge_mark": ("merge_mark", (0, 7), None),
        "merge_compare": ("merge_compare", (2, 5), 3),
        "confirm": ("confirm", (6,), None),
        "key": ("key", (8,), None),
        "note": ("note", tuple(), "fallback=sorted"),
    }

    for op, (expected_kind, indices, payload) in cases.items():
        step = Step(op=op, indices=indices, payload=payload)
        event = translator.translate(step)
        assert isinstance(event, StepRenderEvent)
        assert event.op == op
        assert event.kind == expected_kind
        assert event.indices == indices
        assert event.payload == payload
        # Every event should map to a colour key that exists in the palette.
        assert event.color_key() in STEP_COLOR_MAP


def test_swap_adjacency_flag_and_color() -> None:
    """Adjacent swaps should expose the adjacency helper and use the correct colour."""
    translator = StepTranslator()
    adjacent = translator.translate(Step(op="swap", indices=(1, 2)))
    distant = translator.translate(Step(op="swap", indices=(1, 5)))

    assert adjacent.is_adjacent_swap is True
    assert adjacent.color_key() == "swap_adjacent"
    assert adjacent.color() == STEP_COLOR_MAP["swap_adjacent"]

    assert distant.is_adjacent_swap is False
    assert distant.color_key() == "swap"
    assert distant.color() == STEP_COLOR_MAP["swap"]


def test_unknown_operation_raises() -> None:
    """The translator should fail loudly on unexpected operations."""
    translator = StepTranslator()
    bogus = Step(op="teleport", indices=(0,))

    with pytest.raises(ValueError, match="Unsupported step operation"):
        translator.translate(bogus)


def test_palette_contains_required_keys() -> None:
    """Ensure the palette covers all normalised kinds and has a deterministic default."""
    # Every documented kind should have a mapping.
    for kind in STEP_KIND_MAP.values():
        if kind == "swap":
            # Swap uses an additional derived colour for adjacency.
            assert "swap" in STEP_COLOR_MAP
            assert "swap_adjacent" in STEP_COLOR_MAP
            continue
        assert kind in STEP_COLOR_MAP

    assert STEP_COLOR_MAP["default"] == "#8E8E93"


def test_write_like_ops_share_colour() -> None:
    """All write-like operations should resolve to the same palette colour."""
    translator = StepTranslator()
    colours = {
        translator.translate(Step(op=name, indices=(0,), payload=1)).color()
        for name in ("set", "shift", "write")
    }
    assert len(colours) == 1, f"Expected unified colour for write ops, got {colours}"
