"""Unit tests for guide_mas.evaluation.statistical_tests."""

import pytest
import numpy as np
from guide_mas.evaluation.statistical_tests import (
    compute_median_and_iqr,
    bootstrap_ci_95,
    paired_wilcoxon_test,
    compute_cohens_kappa,
)


def test_median_and_iqr_empty():
    res = compute_median_and_iqr([])
    assert res == {"median": 0.0, "q25": 0.0, "q75": 0.0, "iqr": 0.0}


def test_median_and_iqr_values():
    data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
    res = compute_median_and_iqr(data)
    assert res["median"] == 4.0
    assert res["q25"] == 2.5
    assert res["q75"] == 5.5
    assert res["iqr"] == 3.0


def test_bootstrap_ci_edge_cases():
    lower, upper = bootstrap_ci_95([])
    assert lower == 0.0 and upper == 0.0

    lower, upper = bootstrap_ci_95([42.0])
    assert lower == 42.0 and upper == 42.0


def test_bootstrap_ci_reproducible():
    data = [10.0, 12.0, 11.0, 14.0, 13.0, 15.0, 12.0]
    low1, up1 = bootstrap_ci_95(data, num_resamples=500, random_seed=42)
    low2, up2 = bootstrap_ci_95(data, num_resamples=500, random_seed=42)
    assert low1 == low2
    assert up1 == up2
    assert low1 <= up1


def test_paired_wilcoxon_validation():
    with pytest.raises(ValueError, match="Sample sizes must match"):
        paired_wilcoxon_test([1, 2], [1])


def test_paired_wilcoxon_identical():
    res = paired_wilcoxon_test([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
    assert res["is_significant"] is False
    assert res["p_value"] == 1.0


def test_paired_wilcoxon_significant():
    sample_a = [10.0, 12.0, 14.0, 15.0, 16.0, 18.0, 20.0, 22.0, 25.0, 28.0]
    sample_b = [1.0, 2.0, 2.0, 3.0, 1.0, 4.0, 2.0, 3.0, 1.0, 2.0]
    res = paired_wilcoxon_test(sample_a, sample_b, alternative="greater")
    assert res["is_significant"] is True
    assert res["p_value"] < 0.05


def test_cohens_kappa_mismatched():
    with pytest.raises(ValueError, match="must have equal lengths"):
        compute_cohens_kappa([1, 0], [1])


def test_cohens_kappa_empty():
    res = compute_cohens_kappa([], [])
    assert res["kappa"] == 1.0


def test_cohens_kappa_perfect():
    rater_a = ["PASS", "FAIL", "PASS", "PASS", "FAIL"]
    rater_b = ["PASS", "FAIL", "PASS", "PASS", "FAIL"]
    res = compute_cohens_kappa(rater_a, rater_b)
    assert res["kappa"] == 1.0
    assert res["observed_agreement_pct"] == 100.0
    assert res["meets_target_080"] is True


def test_cohens_kappa_partial():
    rater_a = [1, 1, 1, 0, 0, 0]
    rater_b = [1, 1, 0, 0, 0, 1]
    res = compute_cohens_kappa(rater_a, rater_b)
    assert -1.0 <= res["kappa"] <= 1.0
