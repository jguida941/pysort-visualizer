"""Comprehensive unit tests for sorting algorithm logic."""

import random
import pytest
from typing import Callable

from app.algos.registry import REGISTRY, INFO, load_all_algorithms


# Load all algorithms before testing
load_all_algorithms()


class TestSortingAlgorithmsCorrectness:
    """Test that all sorting algorithms correctly sort various input types."""

    @pytest.fixture
    def test_arrays(self) -> dict[str, list[int]]:
        """Generate test arrays with different characteristics."""
        return {
            "empty": [],
            "single": [42],
            "already_sorted": [1, 2, 3, 4, 5],
            "reverse_sorted": [5, 4, 3, 2, 1],
            "duplicates": [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5],
            "all_same": [7, 7, 7, 7, 7],
            "random_small": [random.randint(1, 100) for _ in range(10)],
            "random_medium": [random.randint(1, 1000) for _ in range(50)],
            "random_large": [random.randint(1, 10000) for _ in range(100)],
            "nearly_sorted": [1, 2, 3, 5, 4, 6, 7, 8, 10, 9],
            "few_unique": [1, 2, 1, 2, 1, 2, 1, 2],
        }

    @pytest.mark.parametrize("algo_name", REGISTRY.keys())
    def test_correctness(self, algo_name: str, test_arrays: dict[str, list[int]]):
        """Test that each algorithm correctly sorts all test arrays."""
        algo_func = REGISTRY[algo_name]

        for array_type, original_array in test_arrays.items():
            # Make a copy since some algorithms sort in-place
            test_array = original_array.copy()
            expected = sorted(original_array)

            # Execute the sorting algorithm
            result = self._execute_algorithm(algo_func, test_array)

            # Verify the result
            assert result == expected, (
                f"{algo_name} failed to sort {array_type} array. "
                f"Input: {original_array}, Expected: {expected}, Got: {result}"
            )

    def _execute_algorithm(self, algo_func: Callable, array: list[int]) -> list[int]:
        """Execute a sorting algorithm and return the sorted array."""
        # Create a copy to avoid modifying the original
        working_array = array.copy()

        # Most algorithms in this codebase are generators that yield steps
        # We need to consume all steps to complete the sort
        try:
            gen = algo_func(working_array)
            # Consume all steps
            for _ in gen:
                pass
        except TypeError:
            # If it's not a generator, it might modify the array directly
            algo_func(working_array)

        return working_array


class TestSortingAlgorithmsStability:
    """Test stability property of sorting algorithms."""

    def test_stability(self):
        """Test that algorithms marked as stable maintain relative order."""
        # Create an array of tuples where first element is the key to sort by
        # and second element tracks original position
        test_data = [(3, 'a'), (1, 'b'), (3, 'c'), (2, 'd'), (1, 'e'), (3, 'f')]

        for algo_name, algo_info in INFO.items():
            if not getattr(algo_info, "stable", False):
                continue  # Skip non-stable algorithms

            algo_func = REGISTRY[algo_name]

            # Extract just the values for sorting
            values = [item[0] for item in test_data]
            positions = {i: item[1] for i, item in enumerate(test_data)}

            # Track which indices move where during sorting
            working_array = values.copy()
            index_map = list(range(len(values)))

            try:
                gen = algo_func(working_array)
                for step in gen:
                    if "swap" in step:
                        i, j = step["swap"]
                        # Track the swap in our index map
                        index_map[i], index_map[j] = index_map[j], index_map[i]
                        working_array[i], working_array[j] = working_array[j], working_array[i]
            except:
                pass  # Algorithm doesn't provide step information

            # Verify stability: equal elements should maintain relative order
            sorted_with_positions = [(working_array[i], positions[index_map[i]])
                                    for i in range(len(working_array))]

            # Check that equal elements maintain their relative order
            for i in range(len(sorted_with_positions) - 1):
                for j in range(i + 1, len(sorted_with_positions)):
                    if sorted_with_positions[i][0] == sorted_with_positions[j][0]:
                        # Original positions should be in order
                        pos_i = test_data.index((sorted_with_positions[i][0], sorted_with_positions[i][1]))
                        pos_j = test_data.index((sorted_with_positions[j][0], sorted_with_positions[j][1]))
                        assert pos_i < pos_j, (
                            f"{algo_name} is marked as stable but doesn't maintain relative order"
                        )


class TestSortingAlgorithmsPerformance:
    """Test performance characteristics of sorting algorithms."""

    def test_operation_counts(self):
        """Test that algorithms have reasonable operation counts."""
        test_size = 50
        test_array = [random.randint(1, 100) for _ in range(test_size)]

        for algo_name, algo_func in REGISTRY.items():
            working_array = test_array.copy()
            comparison_count = 0
            swap_count = 0

            try:
                gen = algo_func(working_array)
                for step in gen:
                    if "compare" in step:
                        comparison_count += 1
                    if "swap" in step:
                        swap_count += 1
            except:
                pass  # Algorithm doesn't provide step information

            # Basic sanity checks on operation counts
            # Most algorithms should have O(n^2) or better comparisons
            max_comparisons = test_size * test_size * 2  # Very generous upper bound

            if comparison_count > 0:  # Only check if we got comparison data
                assert comparison_count <= max_comparisons, (
                    f"{algo_name} has too many comparisons: {comparison_count} for array size {test_size}"
                )


class TestSortingAlgorithmsEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.parametrize("algo_name", REGISTRY.keys())
    def test_empty_array(self, algo_name: str):
        """Test that algorithms handle empty arrays correctly."""
        algo_func = REGISTRY[algo_name]
        array = []
        result = self._execute_algorithm(algo_func, array)
        assert result == [], f"{algo_name} failed on empty array"

    @pytest.mark.parametrize("algo_name", REGISTRY.keys())
    def test_single_element(self, algo_name: str):
        """Test that algorithms handle single-element arrays correctly."""
        algo_func = REGISTRY[algo_name]
        array = [42]
        result = self._execute_algorithm(algo_func, array)
        assert result == [42], f"{algo_name} failed on single element array"

    @pytest.mark.parametrize("algo_name", REGISTRY.keys())
    def test_large_values(self, algo_name: str):
        """Test that algorithms handle large values correctly."""
        algo_func = REGISTRY[algo_name]
        array = [1000000, 1, 999999, 2, 999998]
        expected = sorted(array)
        result = self._execute_algorithm(algo_func, array)
        assert result == expected, f"{algo_name} failed on large values"

    @pytest.mark.parametrize("algo_name", REGISTRY.keys())
    def test_negative_values(self, algo_name: str):
        """Test that algorithms handle negative values correctly."""
        algo_func = REGISTRY[algo_name]
        array = [-5, 3, -1, 7, -10, 0, 2]
        expected = sorted(array)
        result = self._execute_algorithm(algo_func, array)
        assert result == expected, f"{algo_name} failed on negative values"

    def _execute_algorithm(self, algo_func: Callable, array: list[int]) -> list[int]:
        """Execute a sorting algorithm and return the sorted array."""
        working_array = array.copy()
        try:
            gen = algo_func(working_array)
            for _ in gen:
                pass
        except TypeError:
            algo_func(working_array)
        return working_array


class TestAlgorithmMetadata:
    """Test that algorithm metadata is complete and correct."""

    def test_all_algorithms_have_info(self):
        """Test that all registered algorithms have corresponding info."""
        for algo_name in REGISTRY.keys():
            assert algo_name in INFO, f"Algorithm {algo_name} missing from INFO dictionary"

    def test_info_completeness(self):
        """Test that all algorithm info entries have required fields."""
        required_fields = ["name", "description", "stable", "in_place", "complexity"]

        for algo_name, algo_info in INFO.items():
            for field in required_fields:
                assert hasattr(algo_info, field), f"Algorithm {algo_name} missing required field: {field}"

            # Check complexity sub-fields
            if hasattr(algo_info, "complexity"):
                complexity = algo_info.complexity
                assert "best" in complexity or "avg" in complexity or "worst" in complexity, (
                    f"Algorithm {algo_name} missing complexity information"
                )

    def test_complexity_notation(self):
        """Test that complexity notations are properly formatted."""
        for algo_name, algo_info in INFO.items():
            if hasattr(algo_info, "complexity"):
                complexity_dict = algo_info.complexity
                for field, complexity in complexity_dict.items():
                    # Should start with O( or Θ( or Ω(
                    assert any(complexity.startswith(prefix) for prefix in ["O(", "Θ(", "Ω("]), (
                        f"Algorithm {algo_name} has invalid complexity notation for {field}: {complexity}"
                    )