# tests/unit/test_fluency.py
#
# Unit tests for the fluency metrics (Phase 3, Day 5): accuracy + WCPM.

from app.skills.fluency import accuracy, wcpm


def test_accuracy_basic() -> None:
    assert accuracy(3, 4) == 0.75
    assert accuracy(0, 0) == 1.0  # empty passage is vacuously perfect
    assert accuracy(10, 10) == 1.0


def test_wcpm_basic() -> None:
    assert wcpm(30, 60.0) == 30.0
    assert wcpm(3, 6.0) == 30.0
    assert wcpm(5, 0.0) == 0.0  # no time elapsed -> guard against div by zero
