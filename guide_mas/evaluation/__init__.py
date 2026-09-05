"""
GUIDE Formal Evaluation Package.
"""

from guide_mas.evaluation.benchmark_tasks import (
    BenchmarkTask,
    get_all_benchmark_tasks,
)
from guide_mas.evaluation.robustness import (
    RobustnessEvaluator,
    RobustnessResult,
    RobustnessTestCase,
    get_all_robustness_cases,
)
from guide_mas.evaluation.statistical_tests import (
    bootstrap_ci_95,
    compute_cohens_kappa,
    compute_median_and_iqr,
    paired_wilcoxon_test,
)

def __getattr__(name: str):
    if name in ("EvaluationRunner", "RunResult"):
        from guide_mas.evaluation.runner import EvaluationRunner, RunResult
        return EvaluationRunner if name == "EvaluationRunner" else RunResult
    raise AttributeError(f"module {__name__} has no attribute {name}")

__all__ = [
    "BenchmarkTask",
    "get_all_benchmark_tasks",
    "RobustnessTestCase",
    "RobustnessResult",
    "RobustnessEvaluator",
    "get_all_robustness_cases",
    "EvaluationRunner",
    "RunResult",
    "compute_median_and_iqr",
    "bootstrap_ci_95",
    "paired_wilcoxon_test",
    "compute_cohens_kappa",
]
