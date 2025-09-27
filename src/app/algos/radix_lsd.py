from collections.abc import Iterator

from app.algos.registry import AlgoInfo, register
from app.core.step import Step


@register(
    AlgoInfo(
        name="Radix Sort LSD",
        stable=True,
        in_place=False,
        comparison=False,
        complexity={"best": "O(d(n + k))", "avg": "O(d(n + k))", "worst": "O(d(n + k))"},
        description=(
            "Processes digits from least- to most-significant using counting-sort "
            "passes, keeping the process stable."
        ),
        notes=(
            "Stable",
            "Supports negatives by offsetting before the digit passes",
            "Digit base 10 keeps the trace readable",
        ),
    )
)
def radix_sort_lsd(a: list[int]) -> Iterator[Step]:
    n = len(a)
    if n <= 1:
        if n == 1:
            yield Step("confirm", (0,))
        return

    original = list(a)
    min_val = min(original)
    if min_val < 0:
        offset = -min_val
        original = [value + offset for value in original]
    else:
        offset = 0

    max_val = max(original)
    exp = 1

    while max_val // exp > 0:
        counts = [0] * 10

        for value in original:
            digit = (value // exp) % 10
            counts[digit] += 1

        for i in range(1, 10):
            counts[i] += counts[i - 1]

        output = [0] * n
        for value in reversed(original):
            digit = (value // exp) % 10
            counts[digit] -= 1
            position = counts[digit]
            output[position] = value

        for idx, val in enumerate(output):
            actual = val - offset
            a[idx] = actual
            yield Step("set", (idx,), actual)
            yield Step("key", (idx,), actual)

        original = output
        exp *= 10

    for idx in range(n):
        yield Step("confirm", (idx,))
