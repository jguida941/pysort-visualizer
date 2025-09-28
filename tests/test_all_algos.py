import random

from app.algos.registry import REGISTRY, load_all_algorithms
from app.core.replay import apply_step_sequence

load_all_algorithms()

# Test various edge cases
test_cases = [
    [],  # empty
    [1],  # single
    [1, 1, 1, 1],  # duplicates
    [5, 4, 3, 2, 1],  # reverse sorted
    [1, 2, 3, 4, 5],  # already sorted
    [-5, -1, 0, 3, 10],  # mixed positive/negative
    [random.randint(-100, 100) for _ in range(20)],  # random
]

print("Testing all algorithms with various cases...")
print("=" * 60)

for name in sorted(REGISTRY.keys()):
    algo = REGISTRY[name]
    failures = []

    for i, test_arr in enumerate(test_cases):
        src = list(test_arr)
        work = list(test_arr)
        try:
            steps = list(algo(work))
            result = apply_step_sequence(src, steps)
            expected = sorted(test_arr)
            if result != expected:
                failures.append(f"Case {i}: Expected {expected}, got {result}")
        except Exception as e:
            failures.append(f"Case {i}: Error - {str(e)}")

    if failures:
        print(f"❌ {name:15} - FAILED")
        for failure in failures:
            print(f"   {failure}")
    else:
        print(f"✅ {name:15} - PASSED all test cases")

print("=" * 60)
