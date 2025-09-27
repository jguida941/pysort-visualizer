from collections.abc import Iterator

from app.algos.registry import AlgoInfo, register
from app.core.step import Step


@register(
    AlgoInfo(
        name="Counting Sort",
        stable=True,
        in_place=False,
        comparison=False,
        complexity={"best": "O(n + k)", "avg": "O(n + k)", "worst": "O(n + k)"},
        description=(
            "Counts occurrences of each value within a bounded range, then writes "
            "them back in order using prefix sums."
        ),
        notes=(
            "Stable",
            "Handles negatives via an offset into the counts array",
            "Great for integers with small value ranges",
        ),
    )
)
def counting_sort(a: list[int]) -> Iterator[Step]:
    n = len(a)
    if n <= 1:
        if n == 1:
            yield Step("confirm", (0,))
        return

    original = list(a)
    min_val = min(original)
    max_val = max(original)
    size = max_val - min_val + 1

    if size > 10 * max(1, n):
        for idx, value in enumerate(sorted(original)):
            a[idx] = value
            yield Step("set", (idx,), value)
            yield Step("key", (idx,), value)
        for idx in range(n):
            yield Step("confirm", (idx,))
        return

    offset = -min_val

    counts = [0] * size
    for value in original:
        counts[value + offset] += 1

    total = 0
    for i, cnt in enumerate(counts):
        counts[i] = total
        total += cnt

    for value in reversed(original):
        bucket = value + offset
        position = counts[bucket]
        counts[bucket] += 1
        a[position] = value
        yield Step("set", (position,), value)
        yield Step("key", (position,), value)

    for idx in range(n):
        yield Step("confirm", (idx,))
