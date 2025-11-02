"""Bubble Sort implementation.

Bubble Sort is one of the simplest sorting algorithms, making it ideal for
educational purposes. It repeatedly steps through the list, compares adjacent
elements, and swaps them if they're in the wrong order. The pass through the
list is repeated until the list is sorted.

The name comes from the way smaller elements "bubble" to the top (beginning)
of the list with each iteration, while larger elements "sink" to the bottom.

Algorithm Properties:
- Stable: Yes (equal elements maintain their relative order)
- In-place: Yes (only uses O(1) extra space)
- Adaptive: Yes (O(n) best case when array is already sorted)
- Comparison-based: Yes

Time Complexity:
- Best case: O(n) - when array is already sorted (with early exit optimization)
- Average case: O(n²) - typical random input
- Worst case: O(n²) - when array is reverse sorted

Space Complexity: O(1)

This implementation includes an optimization that terminates early if no swaps
occur during a pass, indicating the array is already sorted.
"""

from collections.abc import Iterator

from app.algos.registry import AlgoInfo, register
from app.core.step import Step


@register(
    AlgoInfo(
        name="Bubble Sort",
        stable=True,
        in_place=True,
        comparison=True,
        complexity={"best": "O(n)", "avg": "O(n^2)", "worst": "O(n^2)"},
        description=(
            "Adjacent swaps bubble the largest values toward the end each pass, "
            "with an early-exit optimisation when no swaps occur."
        ),
        notes=(
            "Stable",
            "Great for teaching because every compare/swap is visible",
            "Best case O(n) thanks to swap detection",
        ),
    )
)
def bubble_sort(a: list[int]) -> Iterator[Step]:
    """Sort an array using the bubble sort algorithm.

    Repeatedly passes through the array, comparing adjacent elements and swapping
    them if they're in the wrong order. After each pass, the largest unsorted
    element is guaranteed to be in its final position (at the end of the unsorted
    portion).

    The algorithm includes an optimization: if a full pass occurs without any
    swaps, the array is sorted and the algorithm terminates early.

    Args:
        a: List of integers to sort (modified in-place)

    Yields:
        Step objects documenting each operation:
        - "compare": Compare two adjacent elements
        - "swap": Swap two adjacent elements (with values in payload)
        - "confirm": Mark element as in its final sorted position

    Example:
        >>> arr = [5, 2, 8, 1, 9]
        >>> steps = list(bubble_sort(arr))
        >>> arr
        [1, 2, 5, 8, 9]

    Algorithm Visualization:
        Pass 1: [5, 2, 8, 1, 9] -> [2, 5, 1, 8, 9] (9 in final position)
        Pass 2: [2, 5, 1, 8, 9] -> [2, 1, 5, 8, 9] (8 in final position)
        Pass 3: [2, 1, 5, 8, 9] -> [1, 2, 5, 8, 9] (5 in final position)
        Pass 4: [1, 2, 5, 8, 9] -> [1, 2, 5, 8, 9] (no swaps, done!)

    Implementation Notes:
        - The outer loop runs n times (one pass per element)
        - The inner loop shrinks by 1 each pass (n-i-1) because the largest
          elements are already in their final positions
        - The 'swapped' flag enables early termination when array is sorted
        - Each swap includes the values as payload for better narration
    """
    n = len(a)

    # Handle edge cases: arrays with 0 or 1 elements are already sorted
    if n <= 1:
        if n == 1:
            yield Step("confirm", (0,))
        return

    # Outer loop: one pass per element
    for i in range(n):
        swapped = False  # Track if any swaps occurred this pass

        # Inner loop: compare adjacent elements
        # After i passes, the last i elements are in their final positions
        for j in range(0, n - i - 1):
            # Compare adjacent elements
            yield Step("compare", (j, j + 1))

            # If they're out of order, swap them
            if a[j] > a[j + 1]:
                # Include values in payload for better narration
                payload = (a[j], a[j + 1])
                yield Step("swap", (j, j + 1), payload=payload)

                # Perform the actual swap
                a[j], a[j + 1] = a[j + 1], a[j]
                swapped = True

        # Early exit optimization: if no swaps occurred, array is sorted
        if not swapped:
            break

    # Mark all elements as confirmed sorted
    for idx in range(n):
        yield Step("confirm", (idx,))
