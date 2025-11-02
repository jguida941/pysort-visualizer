"""Algorithm registry and metadata system.

This module provides the infrastructure for registering sorting algorithms
with their metadata, making them discoverable and accessible throughout the
application.

Key components:
- AlgoInfo: Dataclass holding algorithm metadata (complexity, stability, etc.)
- REGISTRY: Global dictionary mapping algorithm names to implementations
- INFO: Global dictionary mapping algorithm names to their metadata
- @register decorator: Decorator for registering new algorithms

This design allows algorithms to be self-documenting - each algorithm file
uses the @register decorator to declare its metadata alongside its implementation.

Example:
    >>> @register(AlgoInfo(
    ...     name="My Sort",
    ...     stable=True,
    ...     in_place=True,
    ...     comparison=True,
    ...     complexity={"best": "O(n)", "avg": "O(n log n)", "worst": "O(n^2)"},
    ...     description="A custom sorting algorithm"
    ... ))
    ... def my_sort(arr: list[int]) -> Iterator[Step]:
    ...     # Algorithm implementation
    ...     pass
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from importlib import import_module
from typing import TypeAlias

from app.core.step import Step

# Type alias for algorithm functions
# An Algorithm is a callable that takes a mutable list of integers and
# yields Step objects that describe its operations
Algorithm: TypeAlias = Callable[[list[int]], Iterator[Step]]

# Type alias for the register decorator
Decorator: TypeAlias = Callable[[Algorithm], Algorithm]


@dataclass(frozen=True)
class AlgoInfo:
    """Metadata describing a sorting algorithm's properties.

    This class holds all the descriptive information about an algorithm,
    separate from its implementation. This metadata is used for:
    - Displaying algorithm details in the UI
    - Comparing algorithms
    - Filtering/searching algorithms
    - Educational content

    Attributes:
        name: Human-readable name (e.g., "Bubble Sort", "Quick Sort")
        stable: Whether equal elements maintain their relative order
        in_place: Whether the algorithm sorts without extra array space
        comparison: Whether the algorithm uses element comparisons (vs. integer properties)
        complexity: Dict with 'best', 'avg', and 'worst' case time complexities
        description: Brief explanation of how the algorithm works
        notes: Additional bullet points highlighting key features or trade-offs

    Example:
        >>> info = AlgoInfo(
        ...     name="Insertion Sort",
        ...     stable=True,
        ...     in_place=True,
        ...     comparison=True,
        ...     complexity={"best": "O(n)", "avg": "O(n^2)", "worst": "O(n^2)"},
        ...     description="Builds sorted array one element at a time",
        ...     notes=("Efficient for small arrays", "Adaptive to partially sorted data")
        ... )
    """
    name: str
    stable: bool
    in_place: bool
    comparison: bool
    complexity: dict[str, str]
    description: str = ""
    notes: tuple[str, ...] = field(default_factory=tuple)


# Global registries populated by the @register decorator
# Maps algorithm name -> implementation function
REGISTRY: dict[str, Algorithm] = {}
# Maps algorithm name -> metadata
INFO: dict[str, AlgoInfo] = {}

# List of all algorithm modules to load
# Add new algorithm modules here to include them in the visualizer
_ALGO_MODULES: tuple[str, ...] = (
    "app.algos.bubble",
    "app.algos.insertion",
    "app.algos.selection",
    "app.algos.heap",
    "app.algos.shell",
    "app.algos.merge",
    "app.algos.quick",
    "app.algos.cocktail",
    "app.algos.counting",
    "app.algos.radix_lsd",
    "app.algos.bucket",
    "app.algos.comb",
    "app.algos.timsort_trace",
)


def register(info: AlgoInfo) -> Decorator:
    """Decorator to register an algorithm with its metadata.

    This decorator adds the algorithm to the global REGISTRY and INFO
    dictionaries, making it available throughout the application.

    Args:
        info: AlgoInfo instance describing the algorithm

    Returns:
        Decorator function that registers the algorithm and returns it unchanged

    Example:
        >>> @register(AlgoInfo(
        ...     name="Bubble Sort",
        ...     stable=True,
        ...     in_place=True,
        ...     comparison=True,
        ...     complexity={"best": "O(n)", "avg": "O(n^2)", "worst": "O(n^2)"},
        ...     description="Repeatedly swaps adjacent elements if they're in wrong order"
        ... ))
        ... def bubble_sort(arr: list[int]) -> Iterator[Step]:
        ...     # Implementation here
        ...     pass

    Notes:
        - The algorithm name in AlgoInfo.name is used as the registry key
        - The decorator returns the original function unchanged
        - Duplicate names will silently overwrite previous registrations
    """
    def deco(fn: Algorithm) -> Algorithm:
        REGISTRY[info.name] = fn
        INFO[info.name] = info
        return fn

    return deco


def load_all_algorithms() -> None:
    """Import all algorithm modules to populate the registries.

    This function must be called before accessing REGISTRY or INFO to ensure
    all algorithms are loaded. It imports each module in _ALGO_MODULES, which
    triggers the @register decorators in those modules.

    The function is idempotent - calling it multiple times is safe, though
    redundant.

    Usage:
        >>> load_all_algorithms()
        >>> print(list(REGISTRY.keys()))
        ['Bubble Sort', 'Quick Sort', 'Merge Sort', ...]

    Notes:
        - Called automatically by the main application startup
        - Import errors in algorithm modules will propagate
        - Modules are only imported once (Python module caching)
    """
    for module in _ALGO_MODULES:
        import_module(module)
