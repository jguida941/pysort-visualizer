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
    n = len(a)
    if n <= 1:
        if n == 1:
            yield Step("confirm", (0,))
        return
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            yield Step("compare", (j, j + 1))
            if a[j] > a[j + 1]:
                # Add payload for stateless narration
                payload = (a[j], a[j + 1])
                yield Step("swap", (j, j + 1), payload=payload)
                a[j], a[j + 1] = a[j + 1], a[j]
                swapped = True
        if not swapped:
            break

    for idx in range(n):
        yield Step("confirm", (idx,))
