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
    n = len(a)
    if n <= 1:
        if n == 1:
            yield Step("confirm", (0,))
        return

    for i in range(1, n):
        key = a[i]
        yield Step("key", (i,), key)
        j = i - 1

        while j >= 0:
            yield Step("compare", (j, i))
            if a[j] <= key:
                break
            a[j + 1] = a[j]
            yield Step("shift", (j + 1,), a[j])
            j -= 1

        dest = j + 1
        if dest != i:
            a[dest] = key
            yield Step("set", (dest,), key)
        yield Step("key", (dest,), key)

    for idx in range(n):
        yield Step("confirm", (idx,))
