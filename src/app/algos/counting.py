import math
from collections.abc import Iterator

from app.algos.registry import AlgoInfo, register
from app.core.step import Step

# Maximum key range to prevent huge allocations
MAX_K = 10_000_000


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

    # Use more reasonable threshold: n*log2(n) or 10*n, whichever is larger
    threshold = max(10 * n, int(n * math.log2(max(2, n))))

    # Guard against pathological ranges to avoid huge allocations
    if size > threshold or size > MAX_K:
        # Tag the fallback for honest metrics
        yield Step("note", (), f"fallback=sorted k={size} n={n}")
        for idx, value in enumerate(sorted(original)):
            a[idx] = value
            yield Step("write", (idx,), value)
        for idx in range(n):
            yield Step("confirm", (idx,))
        return

    # Use offset for negative values
    offset = -min_val

    # Count phase
    counts = [0] * size
    for value in original:
        counts[value + offset] += 1

    # Prefix sum phase (exclusive prefix sum in single pass)
    total = 0
    for i, cnt in enumerate(counts):
        counts[i], total = total, total + cnt

    # Write phase - iterate in reverse for stability
    for value in reversed(original):
        bucket = value + offset
        position = counts[bucket]
        counts[bucket] += 1
        a[position] = value
        yield Step("write", (position,), value)

    for idx in range(n):
        yield Step("confirm", (idx,))
