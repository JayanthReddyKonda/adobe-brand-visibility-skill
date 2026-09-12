"""test_priority_ranking.py - Exhaustive priority ranking verification.

Tests the mathematical invariant:
    priority_index = 5 * severity + (6 - difficulty)

Across all 20 combinations of:
    severity in {1, 2, 3, 4} (S1=low, S2=medium, S3=high, S4=critical)
    difficulty in {1, 2, 3, 4, 5} (1=easiest, 5=hardest)

Asserts:
- Correct formula calculation for every cell in the 4x5 matrix
- Strict monotonicity: higher severity always yields higher base index
- For equal severity, lower difficulty (easier fix) strictly yields higher priority_index
- Range bounds: min = 6 (S1, diff=5), max = 25 (S4, diff=1)
- Topological sort order matches priority_index descending
"""
import unittest


def calculate_priority_index(severity: int, difficulty: int) -> int:
    """Calculate task ranking index: priority_index = 5 * severity + (6 - difficulty)."""
    if not (1 <= severity <= 4):
        raise ValueError(f"severity must be in 1..4, got {severity}")
    if not (1 <= difficulty <= 5):
        raise ValueError(f"difficulty must be in 1..5, got {difficulty}")
    return 5 * severity + (6 - difficulty)


class TestPriorityRankingFormula(unittest.TestCase):
    """Exhaustive unit tests for all 20 severity x difficulty combinations."""

    # Precomputed truth table for priority_index = 5 * sev + (6 - diff)
    # Rows: severity 1..4; Cols: difficulty 1..5
    EXPECTED_MATRIX = {
        # Severity 1 (Low):
        (1, 1): 10,  # 5*1 + 5
        (1, 2): 9,   # 5*1 + 4
        (1, 3): 8,   # 5*1 + 3
        (1, 4): 7,   # 5*1 + 2
        (1, 5): 6,   # 5*1 + 1 (Absolute Minimum)
        # Severity 2 (Medium):
        (2, 1): 15,  # 5*2 + 5
        (2, 2): 14,  # 5*2 + 4
        (2, 3): 13,  # 5*2 + 3
        (2, 4): 12,  # 5*2 + 2
        (2, 5): 11,  # 5*2 + 1
        # Severity 3 (High):
        (3, 1): 20,  # 5*3 + 5
        (3, 2): 19,  # 5*3 + 4
        (3, 3): 18,  # 5*3 + 3
        (3, 4): 17,  # 5*3 + 2
        (3, 5): 16,  # 5*3 + 1
        # Severity 4 (Critical):
        (4, 1): 25,  # 5*4 + 5 (Absolute Maximum)
        (4, 2): 24,  # 5*4 + 4
        (4, 3): 23,  # 5*4 + 3
        (4, 4): 22,  # 5*4 + 2
        (4, 5): 21,  # 5*4 + 1
    }

    def test_all_20_combinations_exact_values(self):
        """Verify each cell in the 4x5 priority ranking matrix matches mathematical truth."""
        for (sev, diff), expected in self.EXPECTED_MATRIX.items():
            with self.subTest(severity=sev, difficulty=diff):
                actual = calculate_priority_index(sev, diff)
                self.assertEqual(
                    actual,
                    expected,
                    f"Failed for severity={sev}, difficulty={diff}: expected {expected}, got {actual}",
                )

    def test_total_combinations_count(self):
        """Assert exactly 20 distinct pairs are tested."""
        self.assertEqual(len(self.EXPECTED_MATRIX), 20)

    def test_range_bounds(self):
        """Assert min is 6 and max is 25."""
        indices = [calculate_priority_index(s, d) for s in range(1, 5) for d in range(1, 6)]
        self.assertEqual(min(indices), 6)
        self.assertEqual(max(indices), 25)

    def test_monotonic_severity_ordering(self):
        """For any fixed difficulty, higher severity must strictly produce higher priority_index."""
        for diff in range(1, 6):
            for sev in range(1, 4):
                lower_sev_idx = calculate_priority_index(sev, diff)
                higher_sev_idx = calculate_priority_index(sev + 1, diff)
                self.assertGreater(
                    higher_sev_idx,
                    lower_sev_idx,
                    f"Monotonicity violated for diff={diff}: sev={sev} ({lower_sev_idx}) >= sev={sev + 1} ({higher_sev_idx})",
                )
                # In fact, exactly step of 5
                self.assertEqual(higher_sev_idx - lower_sev_idx, 5)

    def test_monotonic_difficulty_ordering(self):
        """For any fixed severity, lower difficulty (easier fix) must strictly produce higher priority_index."""
        for sev in range(1, 5):
            for diff in range(1, 5):
                easier_idx = calculate_priority_index(sev, diff)
                harder_idx = calculate_priority_index(sev, diff + 1)
                self.assertGreater(
                    easier_idx,
                    harder_idx,
                    f"Difficulty ordering violated for sev={sev}: diff={diff} ({easier_idx}) <= diff={diff + 1} ({harder_idx})",
                )
                self.assertEqual(easier_idx - harder_idx, 1)

    def test_invalid_inputs_raise(self):
        """Out of bounds inputs must raise ValueError."""
        with self.assertRaises(ValueError):
            calculate_priority_index(0, 3)
        with self.assertRaises(ValueError):
            calculate_priority_index(5, 3)
        with self.assertRaises(ValueError):
            calculate_priority_index(3, 0)
        with self.assertRaises(ValueError):
            calculate_priority_index(3, 6)

    def test_topological_sort_preserves_priority_order(self):
        """Items sorted by priority_index descending must group highest-urgency items first."""
        items = [
            {"id": f"TASK-{s}-{d}", "severity": s, "difficulty": d, "priority_index": calculate_priority_index(s, d)}
            for s in range(1, 5)
            for d in range(1, 6)
        ]
        sorted_items = sorted(items, key=lambda x: x["priority_index"], reverse=True)
        # First item must be Critical/Easiest (S4, D1 => 25)
        self.assertEqual(sorted_items[0]["priority_index"], 25)
        self.assertEqual(sorted_items[0]["severity"], 4)
        self.assertEqual(sorted_items[0]["difficulty"], 1)

        # Last item must be Low/Hardest (S1, D5 => 6)
        self.assertEqual(sorted_items[-1]["priority_index"], 6)
        self.assertEqual(sorted_items[-1]["severity"], 1)
        self.assertEqual(sorted_items[-1]["difficulty"], 5)


if __name__ == "__main__":
    unittest.main()
