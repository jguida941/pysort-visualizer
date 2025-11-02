"""Replay functionality for step sequences.

This module provides utilities for replaying recorded step sequences to reconstruct
array states at any point in an algorithm's execution. This is essential for:
- Scrubbing through algorithm visualizations
- Validating that step sequences produce correct results
- Testing and debugging algorithm implementations
"""

from app.core.step import Step


def apply_step_sequence(arr: list[int], steps: list[Step]) -> list[int]:
    """Apply a sequence of steps to an array, returning the resulting array.

    This function reconstructs the array state after executing a series of
    algorithm steps. It only applies state-modifying operations (swap, set, shift)
    and ignores visualization-only operations (compare, pivot, merge_mark, etc.).

    This is the core replay mechanism used for:
    - Seeking to arbitrary positions in the visualization
    - Reconstructing array state from checkpoints
    - Validating algorithm correctness

    Args:
        arr: The initial array state to start from
        steps: List of Step objects to apply in sequence

    Returns:
        A new list representing the array after applying all steps

    Raises:
        ValueError: If a 'set' or 'shift' step is missing its required payload

    Example:
        >>> arr = [3, 1, 2]
        >>> steps = [
        ...     Step(op="compare", indices=(0, 1)),
        ...     Step(op="swap", indices=(0, 1)),
        ...     Step(op="compare", indices=(1, 2)),
        ...     Step(op="swap", indices=(1, 2))
        ... ]
        >>> result = apply_step_sequence(arr, steps)
        >>> result
        [1, 2, 3]

    Notes:
        - Creates a copy of the input array to avoid modifying the original
        - Only swap/set/shift operations modify array state
        - Compare, pivot, and merge_mark operations are ignored (visualization only)
        - The function is deterministic - same input always produces same output
    """
    # Create a copy to avoid modifying the original array
    a = list(arr)

    for step in steps:
        if step.op == "swap":
            # Swap two elements at the given indices
            i, j = step.indices
            a[i], a[j] = a[j], a[i]
        elif step.op in {"set", "shift"}:
            # Set or shift an element to a new value
            # Both operations write a value to an index
            (k,) = step.indices
            if step.payload is None:
                raise ValueError("Set/shift step requires a payload")
            a[k] = int(step.payload)
        # Note: Compare, pivot, and merge_mark operations don't change array state
        # They're purely for visualization and are safely ignored here

    return a
