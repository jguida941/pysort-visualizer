"""Insertion Sort implementation.

Insertion Sort builds the final sorted array one item at a time. It iterates
through the input array, and for each element, it finds the correct position
in the sorted portion and inserts it there by shifting other elements.

The algorithm is similar to how you might sort playing cards in your hands:
pick up one card at a time and insert it into its correct position among the
cards you've already sorted.

Algorithm Properties:
- Stable: Yes (equal elements maintain their relative order)
- In-place: Yes (only uses O(1) extra space)
- Adaptive: Yes (O(n) best case for nearly sorted arrays)
- Comparison-based: Yes
- Online: Yes (can sort a list as it receives it)

Time Complexity:
- Best case: O(n) - when array is already sorted
- Average case: O(n²) - typical random input
- Worst case: O(n²) - when array is reverse sorted

Space Complexity: O(1)

Insertion Sort is particularly efficient for:
- Small datasets (often used as base case in hybrid algorithms like Timsort)
- Nearly sorted data (adaptive behavior kicks in)
- Data that arrives in real-time (online sorting)
"""

from collections.abc import Iterator

from app.algos.registry import AlgoInfo, register
from app.core.step import Step


@register(
    AlgoInfo(
        name="Insertion Sort",
        stable=True,
        in_place=True,
        comparison=True,
        complexity={"best": "O(n)", "avg": "O(n^2)", "worst": "O(n^2)"},
        description=(
            "Builds a sorted prefix by inserting each element into place via shifts, "
            "mirroring how you sort playing cards."
        ),
        notes=(
            "Stable",
            "Adaptive: almost-sorted inputs drop to O(n)",
            "Acts as the base case for Timsort",
        ),
    )
)
def insertion_sort(a: list[int]) -> Iterator[Step]:
    """Sort an array using the insertion sort algorithm.

    Builds a sorted array by iteratively taking elements from the unsorted portion
    and inserting them into their correct position in the sorted portion. Elements
    in the sorted portion are shifted to make room for the new element.

    Args:
        a: List of integers to sort (modified in-place)

    Yields:
        Step objects documenting each operation:
        - "key": Mark the current element being inserted
        - "compare": Compare key with elements in sorted portion
        - "shift": Shift an element to make room for the key
        - "set": Place the key in its final position
        - "confirm": Mark element as in its final sorted position

    Example:
        >>> arr = [5, 2, 8, 1, 9]
        >>> steps = list(insertion_sort(arr))
        >>> arr
        [1, 2, 5, 8, 9]

    Algorithm Visualization:
        Start: [5, 2, 8, 1, 9]
        key=2: [2, 5, 8, 1, 9] (insert 2 before 5)
        key=8: [2, 5, 8, 1, 9] (8 already in place)
        key=1: [1, 2, 5, 8, 9] (insert 1 at beginning, shift others)
        key=9: [1, 2, 5, 8, 9] (9 already in place)

    Implementation Notes:
        - The left portion (indices 0..i-1) is always sorted
        - For each element at index i, we find where it belongs in the sorted portion
        - Elements are shifted right to make room, not swapped
        - The "key" steps help visualize which element is being inserted
    """
    n = len(a)

    # Handle edge cases: arrays with 0 or 1 elements are already sorted
    if n <= 1:
        if n == 1:
            yield Step("confirm", (0,))
        return

    # Iterate through each element starting from index 1
    # (Element at index 0 is trivially "sorted")
    for i in range(1, n):
        # Save the current element as the "key" to be inserted
        key = a[i]
        yield Step("key", (i,), key)

        # Find the correct position for the key in the sorted portion (0..i-1)
        j = i - 1

        # Shift elements greater than key to the right
        while j >= 0:
            yield Step("compare", (j, i))
            if a[j] <= key:
                # Found the correct position, stop shifting
                break
            # Shift element at j one position to the right
            a[j + 1] = a[j]
            yield Step("shift", (j + 1,), a[j])
            j -= 1

        # Insert the key at its correct position
        dest = j + 1
        if dest != i:
            a[dest] = key
            yield Step("set", (dest,), key)
        # Show the key in its final position for this iteration
        yield Step("key", (dest,), key)

    # Mark all elements as confirmed sorted
    for idx in range(n):
        yield Step("confirm", (idx,))
