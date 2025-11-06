"""Utilities for translating `Step` objects into renderer-friendly events.

The existing algorithm engine emits `Step` instances with operation names such as
``compare``, ``swap``, ``set`` or ``merge_mark``. 3D renderers need a stable and
well-documented mapping from those low-level ops to visual categories and colors.
This module centralises that knowledge so both 2D and future 3D views can stay in
sync without reimplementing conditional logic everywhere.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from app.core.step import Step

# Keep a single source of truth for how Step ops map to renderer semantics.
# The keys must mirror Step.op values to stay backward compatible.
STEP_KIND_MAP: Mapping[str, str] = {
    "compare": "compare",
    "swap": "swap",
    "shift": "shift",
    "set": "set",
    "write": "write",
    "pivot": "pivot",
    "merge_mark": "merge_mark",
    "merge_compare": "merge_compare",
    "confirm": "confirm",
    "key": "key",
    "note": "note",
}

# Consistent palette used by both the roadmap and the visualiser.
# Having the mapping here keeps doc/spec/code aligned and avoids magic strings.
STEP_COLOR_MAP: Mapping[str, str] = {
    "compare": "#4A90E2",
    "swap": "#E94B3C",
    "swap_adjacent": "#FF6B6B",
    "set": "#52C41A",
    "shift": "#52C41A",
    "write": "#52C41A",
    "pivot": "#FFD700",
    "merge_mark": "#FFB347",
    "merge_compare": "#F8D27C",
    "key": "#9B59B6",
    "confirm": "#95E1D3",
    "note": "#8E8E93",
    "default": "#8E8E93",
}


@dataclass(frozen=True, slots=True)
class StepRenderEvent:
    """Renderer-friendly representation of a :class:`Step`.

    Attributes:
        op: Original operation name (e.g. ``"set"`` or ``"swap"``).
        kind: Normalised rendering category produced by :data:`STEP_KIND_MAP`.
        indices: Tuple of indices affected by the event.
        payload: Optional payload forwarded from the original step.
        is_adjacent_swap: Convenience flag so renderers can highlight tight swaps differently.
    """

    op: str
    kind: str
    indices: tuple[int, ...]
    payload: Any | None = None
    is_adjacent_swap: bool = False

    def color_key(self) -> str:
        """Return the palette key that best represents this event."""
        if self.kind == "swap" and self.is_adjacent_swap:
            return "swap_adjacent"
        return self.kind if self.kind in STEP_COLOR_MAP else "default"

    def color(self) -> str:
        """Return the hex color assigned to this event."""
        return STEP_COLOR_MAP[self.color_key()]


class StepTranslator:
    """Convert :class:`Step` instances into :class:`StepRenderEvent` objects.

    Translating once keeps renderer pipelines simple and guarantees that colour
    selection or behavioural branches all rely on exactly the same semantics.
    """

    def translate(self, step: Step) -> StepRenderEvent:
        """Translate a :class:`Step` into a :class:`StepRenderEvent`.

        Args:
            step: Step emitted by an algorithm generator.

        Returns:
            A :class:`StepRenderEvent` describing how the renderer should treat the input.

        Raises:
            ValueError: If the step operation is unknown. We surface this early so new
                operations cannot silently bypass the rendering pipeline.
        """

        kind = STEP_KIND_MAP.get(step.op)
        if kind is None:
            raise ValueError(f"Unsupported step operation for rendering: {step.op!r}")

        is_adjacent_swap = False
        if step.op == "swap" and len(step.indices) >= 2:
            i, j = step.indices[:2]
            is_adjacent_swap = abs(i - j) == 1

        return StepRenderEvent(
            op=step.op,
            kind=kind,
            indices=tuple(step.indices),
            payload=step.payload,
            is_adjacent_swap=is_adjacent_swap,
        )
