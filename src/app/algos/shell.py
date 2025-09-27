from collections.abc import Iterator

from app.algos.registry import AlgoInfo, register
from app.core.step import Step


@register(
    AlgoInfo(
        name="Shell Sort",
        stable=False,
        in_place=True,
        comparison=True,
        complexity={"best": "O(n log n)", "avg": "O(n^2)", "worst": "O(n^2)"},
        description=(
            "Generalises insertion sort to gapped subsequences, shrinking the gap "
            "factor until a final pass with gap=1 finishes the job."
        ),
        notes=(
            "Not stable",
            "Gap sequence influences performance; using n/2 → 1 works well for demos",
            "Visualises diminishing disorder nicely",
        ),
    )
)
def shell_sort(a: list[int]) -> Iterator[Step]:
    n = len(a)
    if n <= 1:
        if n == 1:
            yield Step("confirm", (0,))
        return

    gap = n // 2
    while gap > 0:
        for i in range(gap, n):
            key = a[i]
            yield Step("key", (i,), key)
            j = i
            while j >= gap:
                yield Step("compare", (j - gap, j))
                if a[j - gap] <= key:
                    break
                a[j] = a[j - gap]
                yield Step("shift", (j,), a[j])
                j -= gap
            if j != i:
                a[j] = key
                yield Step("set", (j,), key)
            yield Step("key", (j,), key)
        gap //= 2
    yield Step("key", ())

    for idx in range(n):
        yield Step("confirm", (idx,))
