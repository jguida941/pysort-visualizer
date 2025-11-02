"""Step data structure for algorithm visualization.

This module defines the fundamental Step class that represents a single operation
performed by a sorting algorithm. Steps are emitted by algorithm generators and
consumed by the UI for visualization and replay.

The Step abstraction allows algorithms to communicate their internal operations
(comparisons, swaps, pivots, etc.) to the visualization layer without coupling
the algorithm implementation to the UI.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

# Type alias for all supported step operations
# Each operation type represents a specific algorithm action:
# - key: Mark an element as the "key" being inserted (insertion-based algorithms)
# - compare: Compare two elements at given indices
# - swap: Swap two elements at given indices
# - shift: Move an element to a new position (e.g., in insertion sort)
# - set: Set an element at an index to a specific value (e.g., in merge sort)
# - pivot: Mark an element as the pivot (quicksort, etc.)
# - merge_mark: Mark a range being merged
# - merge_compare: Compare two elements during merge operation
# - confirm: Mark an element as being in its final sorted position
Op = Literal[
    "key",
    "compare",
    "swap",
    "shift",
    "set",
    "pivot",
    "merge_mark",
    "merge_compare",
    "confirm",
]


@dataclass(frozen=True)
class Step:
    """Immutable step representing a single operation in a sorting algorithm.

    A Step captures what operation occurred, which array indices were involved,
    and any additional data needed to understand or replay the operation. Steps
    are designed to be lightweight, serializable, and stateless.

    Attributes:
        op: The type of operation performed (compare, swap, pivot, etc.)
        indices: Tuple of array indices involved in this operation. For example:
            - (i, j) for compare/swap operations
            - (i,) for single-element operations like pivot or key
            - (lo, hi) for range operations like merge_mark
        payload: Optional additional data for the operation. Examples:
            - For 'set' or 'shift': the value being written
            - For 'swap': tuple of (value1, value2) for narration
            - For 'key': the key value being tracked
            - For 'merge_compare': the destination index

    Example:
        >>> # A comparison between indices 0 and 1
        >>> step = Step(op="compare", indices=(0, 1))
        >>>
        >>> # A swap with values for narration
        >>> step = Step(op="swap", indices=(2, 5), payload=(42, 17))
        >>>
        >>> # Setting index 3 to value 99
        >>> step = Step(op="set", indices=(3,), payload=99)

    Design Notes:
        - Steps are frozen (immutable) to prevent accidental modification
        - Steps are stateless - they describe an action but don't hold array state
        - The indices tuple allows flexible arity (1, 2, or more indices)
        - The payload field provides extensibility for operation-specific data
    """

    op: Op
    indices: tuple[int, ...]
    payload: Any = None

    def to_dict(self) -> dict[str, Any]:
        """Convert step to a JSON-serializable dictionary.

        Useful for exporting step sequences to JSON format for analysis,
        debugging, or sharing algorithm traces.

        Returns:
            Dictionary with 'op', 'indices' (as list), and 'payload' keys.

        Example:
            >>> step = Step(op="swap", indices=(1, 3), payload=(5, 2))
            >>> step.to_dict()
            {'op': 'swap', 'indices': [1, 3], 'payload': (5, 2)}
        """
        data = asdict(self)
        data["indices"] = list(self.indices)
        return data

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Step:
        """Reconstruct a Step from a dictionary representation.

        This is the inverse of to_dict(), used for deserializing steps from
        JSON exports or other serialized formats.

        Args:
            data: Dictionary containing 'op', 'indices', and optionally 'payload'

        Returns:
            Step instance reconstructed from the dictionary

        Example:
            >>> data = {'op': 'compare', 'indices': [0, 1]}
            >>> step = Step.from_dict(data)
            >>> step.op
            'compare'
            >>> step.indices
            (0, 1)
        """
        return Step(op=data["op"], indices=tuple(data["indices"]), payload=data.get("payload"))
