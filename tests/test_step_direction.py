import sys

sys.path.insert(0, "src")

from app.algos.registry import REGISTRY, load_all_algorithms

load_all_algorithms()

# Test if algorithms are actually running backwards
test_array = [5, 2, 8, 1, 9]
algo = REGISTRY["Bubble Sort"]

steps = list(algo(list(test_array)))
print(f"Total steps for Bubble Sort: {len(steps)}")
print("First 5 steps:")
for i, step in enumerate(steps[:5]):
    print(f"  Step {i}: {step.op} at indices {step.indices}")

# Apply steps one by one
work_array = list(test_array)
print(f"\nInitial array: {work_array}")

for i in range(min(3, len(steps))):
    step = steps[i]
    if step.op == "compare":
        print(f"Step {i}: Compare {work_array[step.indices[0]]} and {work_array[step.indices[1]]}")
    elif step.op == "swap":
        a, b = step.indices
        work_array[a], work_array[b] = work_array[b], work_array[a]
        print(f"Step {i}: Swap indices {a} and {b} -> {work_array}")

print("\nIf array progresses towards sorted, algorithm is working correctly.")
print("If array gets more scrambled, there's a problem.")
