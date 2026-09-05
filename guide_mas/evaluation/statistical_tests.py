"""
Non-Parametric Statistical Hypothesis Testing Module.

Implements rigorous empirical evaluation metrics specified in Section 6.4:
- Paired Wilcoxon signed-rank test (significance threshold alpha = 0.05)
- 95% Bootstrap Confidence Intervals (1,000 resamples)
- Median & Interquartile Range (IQR) computation
- Cohen's Kappa inter-rater reliability calculation (target kappa >= 0.80)
"""

from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import numpy as np
from scipy.stats import wilcoxon


def compute_median_and_iqr(data: Union[List[float], np.ndarray]) -> Dict[str, float]:
    """
    Computes median, 25th percentile (Q1), 75th percentile (Q3), and IQR.

    Args:
        data: Numeric data array or list.

    Returns:
        Dict with keys 'median', 'q25', 'q75', 'iqr'.
    """
    arr = np.asarray(data, dtype=float)
    if len(arr) == 0:
        return {"median": 0.0, "q25": 0.0, "q75": 0.0, "iqr": 0.0}

    median_val = float(np.median(arr))
    q25, q75 = np.percentile(arr, [25.0, 75.0])
    iqr_val = float(q75 - q25)

    return {
        "median": round(median_val, 4),
        "q25": round(float(q25), 4),
        "q75": round(float(q75), 4),
        "iqr": round(iqr_val, 4),
    }


def bootstrap_ci_95(
    data: Union[List[float], np.ndarray],
    num_resamples: int = 1000,
    statistic_fn: Callable[[np.ndarray], float] = np.mean,
    random_seed: int = 42
) -> Tuple[float, float]:
    """
    Computes 95% bootstrap confidence interval using empirical percentile method.

    Args:
        data: Numeric observations.
        num_resamples: Number of bootstrap iterations (default 1,000).
        statistic_fn: Estimator function applied to resamples (default np.mean).
        random_seed: Random seed for reproducibility.

    Returns:
        Tuple of (ci_lower_2.5, ci_upper_97.5).
    """
    arr = np.asarray(data, dtype=float)
    if len(arr) <= 1:
        val = float(arr[0]) if len(arr) == 1 else 0.0
        return val, val

    rng = np.random.default_rng(random_seed)
    n = len(arr)
    boot_stats = np.empty(num_resamples)

    for i in range(num_resamples):
        sample = rng.choice(arr, size=n, replace=True)
        boot_stats[i] = statistic_fn(sample)

    lower_ci = float(np.percentile(boot_stats, 2.5))
    upper_ci = float(np.percentile(boot_stats, 97.5))

    return round(lower_ci, 4), round(upper_ci, 4)


def paired_wilcoxon_test(
    sample_a: Union[List[float], np.ndarray],
    sample_b: Union[List[float], np.ndarray],
    alternative: str = "two-sided"
) -> Dict[str, Any]:
    """
    Executes paired Wilcoxon signed-rank test to assess statistical significance.

    Args:
        sample_a: Observations under Condition P.
        sample_b: Paired observations under Baseline (B1 or B2).
        alternative: 'two-sided', 'greater', or 'less'.

    Returns:
        Dict with statistic, p_value, is_significant (p < 0.05).
    """
    arr_a = np.asarray(sample_a, dtype=float)
    arr_b = np.asarray(sample_b, dtype=float)

    if len(arr_a) != len(arr_b):
        raise ValueError(f"Sample sizes must match: {len(arr_a)} vs {len(arr_b)}")

    diffs = arr_a - arr_b
    non_zero = diffs[diffs != 0]

    if len(non_zero) == 0:
        return {
            "statistic": 0.0,
            "p_value": 1.0,
            "is_significant": False,
            "interpretation": "Identical paired distributions (all zero differences)"
        }

    res = wilcoxon(arr_a, arr_b, alternative=alternative, zero_method="wilcox")
    stat = float(res.statistic)
    pval = float(res.pvalue)

    return {
        "statistic": round(stat, 4),
        "p_value": round(pval, 6),
        "is_significant": bool(pval < 0.05),
        "interpretation": f"Statistically significant at alpha=0.05: {pval < 0.05}"
    }


def compute_cohens_kappa(
    rater_a: Union[List[int], List[str]],
    rater_b: Union[List[int], List[str]]
) -> Dict[str, Any]:
    """
    Computes Cohen's Kappa coefficient for inter-rater reliability on scoring rubrics.

    Args:
        rater_a: Categorical evaluations from first assessor.
        rater_b: Categorical evaluations from second assessor.

    Returns:
        Dict with kappa, observed_agreement, expected_agreement.
    """
    if len(rater_a) != len(rater_b):
        raise ValueError("Rater observation lists must have equal lengths")

    n = len(rater_a)
    if n == 0:
        return {"kappa": 1.0, "p_o": 1.0, "p_e": 1.0}

    categories = sorted(list(set(rater_a) | set(rater_b)))
    cat_to_idx = {c: i for i, c in enumerate(categories)}
    num_cats = len(categories)

    # Confusion matrix
    conf_mat = np.zeros((num_cats, num_cats), dtype=int)
    for a, b in zip(rater_a, rater_b):
        conf_mat[cat_to_idx[a], cat_to_idx[b]] += 1

    # Observed agreement
    p_o = float(np.trace(conf_mat)) / n

    # Expected chance agreement
    row_sums = conf_mat.sum(axis=1) / n
    col_sums = conf_mat.sum(axis=0) / n
    p_e = float(np.dot(row_sums, col_sums))

    if np.isclose(p_e, 1.0):
        kappa = 1.0
    else:
        kappa = (p_o - p_e) / (1.0 - p_e)

    return {
        "kappa": round(float(kappa), 4),
        "observed_agreement_pct": round(p_o * 100.0, 2),
        "chance_agreement_pct": round(p_e * 100.0, 2),
        "meets_target_080": bool(kappa >= 0.80)
    }
