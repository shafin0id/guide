"""Protocol v7a: predicting GUIDE's benign-task utility cost from the static bound alone.

For every AgentDojo benign user task, ask whether the ground-truth call sequence is
admissible under GPLUS (gate="rule+provenance", provenance_match="substring", trusted
corpus built from the task PROMPT alone, exactly as the live pipeline builds it). If any
ground-truth call is not admissible, predict that GUIDE will block the task. Compare the
prediction against what actually happened in the frozen protocol-v6 traces.

No model calls. No heuristics beyond the bound's own `Capability.admits`. See
docs/static-analysis-extensions-plan.md §1 for the frozen specification; do not change
this file's predictor logic after `protocol-v7a` is tagged (fix bugs only as a disclosed
`.1` version per §1.4 step 4).
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agentdojo.benchmark import get_suite
from agentdojo.types import FunctionCall

from guide.agent import AgentSpec
from guide.runtime import HandoffMode
from guide.workflow import Step, Workflow
from guide_agentdojo.policy import build_suite_policy
from guide_agentdojo.specs import build_tool_registry
from guide_research.blast_radius import Capability, SystemModel, authority
from guide_research.provenance import corpus_of

SUITES = ("banking", "slack", "travel", "workspace")
EXPECTED_BENIGN_COUNTS = {"banking": 16, "slack": 21, "travel": 20, "workspace": 40}
BENCHMARK_VERSION = "v1.2.2"

RESULTS_DIR = Path("experiments/results/predict-utility-v7a")
V6_RESULTS_DIR = Path("experiments/results/agentdojo-v6")


# --------------------------------------------------------------------------- predictor


@dataclass(frozen=True)
class CallVerdict:
    function: str
    blocked: bool
    reason: str  # "admitted" | "missing_capability" | "<param>=<value>"


def _build_model(suite_name: str, suite: Any, prompt: str) -> SystemModel:
    registry = build_tool_registry(suite.tools)
    policy = build_suite_policy(suite_name, suite.tools)
    tool_names = tuple(f.name for f in suite.tools)
    step = Step(step_id="agent-step", role="agent", instruction="", tools=tool_names)
    return SystemModel(
        workflow=Workflow((step,)),
        agents=(AgentSpec("agent-1", "agent", "agent"),),
        policy=policy,
        registry=registry,
        trusted_corpus=corpus_of({"objective": prompt}),
        mode=HandoffMode.SIGNED,
        gate="rule+provenance",
        provenance_match="substring",
    )


def _caps_by_key(model: SystemModel) -> dict[tuple[str, str], Capability]:
    step = model.workflow.steps[0]
    return {(c.tool, c.operation): c for c in authority(model, step)}


def _verdict(fc: FunctionCall, caps: dict[tuple[str, str], Capability]) -> CallVerdict:
    key = (fc.function, fc.function)
    cap = caps.get(key)
    if cap is None:
        return CallVerdict(fc.function, True, "missing_capability")
    if cap.admits(dict(fc.args)):
        return CallVerdict(fc.function, False, "admitted")
    # Identify the first blocking parameter for diagnostics (mirrors Capability.admits order).
    for pname, vs in cap.params:
        if not vs.admits(dict(fc.args), pname):
            return CallVerdict(fc.function, True, f"{pname}={fc.args.get(pname)!r}")
    return CallVerdict(fc.function, True, "blocked_unspecified")


def predict_suite(suite_name: str, benchmark_version: str = BENCHMARK_VERSION) -> list[dict[str, Any]]:
    suite = get_suite(benchmark_version, suite_name)
    rows: list[dict[str, Any]] = []
    for task_id, user_task in sorted(suite.user_tasks.items()):
        row: dict[str, Any] = {"suite": suite_name, "user_task_id": task_id}
        try:
            env = suite.load_and_inject_default_environment({})
            gt = user_task.ground_truth(env)
        except Exception as exc:  # noqa: BLE001 - frozen predictor must record, not crash
            row.update(
                predict_status="gt_error",
                error=f"{type(exc).__name__}: {exc}",
                predicted_block=None,
                blocking_function=None,
                blocking_param=None,
                blocking_value=None,
            )
            rows.append(row)
            continue

        model = _build_model(suite_name, suite, user_task.PROMPT)
        caps = _caps_by_key(model)
        verdicts = [_verdict(fc, caps) for fc in gt]
        blocked = [v for v in verdicts if v.blocked]
        predicted_block = len(blocked) > 0
        first = blocked[0] if blocked else None
        row.update(
            predict_status="ok",
            error=None,
            predicted_block=predicted_block,
            blocking_function=first.function if first else None,
            blocking_param=(
                "missing_capability"
                if first and first.reason == "missing_capability"
                else (first.reason.split("=", 1)[0] if first and "=" in first.reason else None)
            ),
            blocking_value=(first.reason.split("=", 1)[1] if first and "=" in first.reason else None),
            n_ground_truth_calls=len(gt),
            n_blocked_calls=len(blocked),
        )
        rows.append(row)
    return rows


# --------------------------------------------------------------------------- observed outcomes


def load_observed(results_dir: Path, suite_name: str) -> dict[str, dict[str, Any]]:
    """Observed outcomes from protocol-v6 benign (`none`) traces for one suite."""
    base = results_dir / suite_name / "guide-gplus-local" / suite_name
    out: dict[str, dict[str, Any]] = {}
    if not base.is_dir():
        return out
    for task_dir in sorted(base.iterdir()):
        if not task_dir.is_dir():
            continue
        trace_path = task_dir / "none" / "none.json"
        if not trace_path.is_file():
            continue
        data = json.loads(trace_path.read_text())
        task_id = data.get("user_task_id", task_dir.name)
        denied_calls: list[list[str]] = []
        for msg in data.get("messages", []):
            if msg.get("role") == "tool":
                err = msg.get("error")
                if isinstance(err, str) and err.startswith("DENIED_BY_POLICY ("):
                    denied_calls.append([msg.get("tool_call_id", ""), err[:120]])
        out[task_id] = {
            "observed_denial": len(denied_calls) > 0,
            "observed_utility": bool(data.get("utility")),
            "denied_calls": denied_calls,
        }
    return out


# --------------------------------------------------------------------------- metrics


def wilson_interval(successes: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Wilson score 95% confidence interval for a binomial proportion. (0.0, 0.0) if n == 0."""
    if n == 0:
        return (0.0, 0.0)
    p = successes / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    lo = (centre - margin) / denom
    hi = (centre + margin) / denom
    return (max(0.0, lo), min(1.0, hi))


def classify_mismatch(predicted_block: bool | None, observed_denial: bool) -> str:
    if predicted_block is None:
        return "excluded_gt_error"
    if predicted_block and observed_denial:
        return "agree_block"
    if not predicted_block and not observed_denial:
        return "agree_pass"
    if predicted_block and not observed_denial:
        return "fp_model_detoured"
    return "fn_offpath_or_onpath"  # split further once denied_calls vs. gt overlap is checked


def _confusion(pairs: list[tuple[bool, bool]]) -> dict[str, Any]:
    tp = sum(1 for p, o in pairs if p and o)
    fp = sum(1 for p, o in pairs if p and not o)
    fn = sum(1 for p, o in pairs if not p and o)
    tn = sum(1 for p, o in pairs if not p and not o)
    n = len(pairs)
    acc = (tp + tn) / n if n else float("nan")
    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    lo, hi = wilson_interval(tp + tn, n)
    return {
        "n": n,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "accuracy": acc,
        "accuracy_wilson95": [lo, hi],
        "precision": precision,
        "recall": recall,
    }


def build_summary(
    all_rows: list[dict[str, Any]], observed_by_suite: dict[str, dict[str, dict[str, Any]]]
) -> dict[str, Any]:
    per_suite: dict[str, Any] = {}
    overall_denial_pairs: list[tuple[bool, bool]] = []
    overall_utility_pairs: list[tuple[bool, bool]] = []
    mismatch_counts: dict[str, int] = {}
    fn_onpath_cases: list[dict[str, Any]] = []
    enriched_rows: list[dict[str, Any]] = []

    for suite_name in SUITES:
        suite_rows = [r for r in all_rows if r["suite"] == suite_name]
        observed = observed_by_suite.get(suite_name, {})
        denial_pairs: list[tuple[bool, bool]] = []
        utility_pairs: list[tuple[bool, bool]] = []
        predicted_blocks: list[bool] = []
        for row in suite_rows:
            obs = observed.get(row["user_task_id"])
            if obs is None:
                row["mismatch_class"] = "missing_observed_trace"
                row["observed_denial"] = None
                row["observed_utility"] = None
                row["denied_calls"] = []
                enriched_rows.append(row)
                continue
            pb = row["predicted_block"]
            row["observed_denial"] = obs["observed_denial"]
            row["observed_utility"] = obs["observed_utility"]
            row["denied_calls"] = obs["denied_calls"]
            if pb is None:
                row["mismatch_class"] = "excluded_gt_error"
                enriched_rows.append(row)
                continue

            predicted_blocks.append(pb)
            denial_pairs.append((pb, obs["observed_denial"]))
            overall_denial_pairs.append((pb, obs["observed_denial"]))
            utility_pairs.append((pb, not obs["observed_utility"]))
            overall_utility_pairs.append((pb, not obs["observed_utility"]))

            if not pb and not obs["observed_denial"] and not obs["observed_utility"]:
                mclass = "model_error"
            elif pb and obs["observed_denial"]:
                mclass = "agree_block"
            elif not pb and not obs["observed_denial"]:
                mclass = "agree_pass"
            elif pb and not obs["observed_denial"]:
                mclass = "fp_model_detoured"
            else:  # not pb and obs["observed_denial"]
                blocking_fns = {c[0] for c in obs["denied_calls"]}
                # fn_onpath: a denial landed on a function that WAS in the ground-truth call set
                # (checked via the per-task gt call list recorded during prediction).
                mclass = (
                    "fn_onpath"
                    if row.get("_gt_functions") and (set(row["_gt_functions"]) & blocking_fns)
                    else "fn_offpath_call"
                )
                if mclass == "fn_onpath":
                    fn_onpath_cases.append(
                        {"suite": suite_name, "user_task_id": row["user_task_id"], "denied_calls": obs["denied_calls"]}
                    )
            row["mismatch_class"] = mclass
            mismatch_counts[mclass] = mismatch_counts.get(mclass, 0) + 1
            row.pop("_gt_functions", None)
            enriched_rows.append(row)

        per_suite[suite_name] = {
            "n_tasks": len(suite_rows),
            "n_scored": len(denial_pairs),
            "confusion_denial": _confusion(denial_pairs),
            "confusion_not_utility": _confusion(utility_pairs),
            "predicted_utility_ceiling": 1 - (sum(predicted_blocks) / len(predicted_blocks))
            if predicted_blocks
            else float("nan"),
            "observed_benign_utility": (
                sum(1 for t in observed.values() if t["observed_utility"]) / len(observed) if observed else float("nan")
            ),
        }

    overall = {
        "confusion_denial": _confusion(overall_denial_pairs),
        "confusion_not_utility": _confusion(overall_utility_pairs),
        "mismatch_counts": mismatch_counts,
    }
    return {
        "per_suite": per_suite,
        "overall": overall,
        "fn_onpath_cases": fn_onpath_cases,
        "rows": enriched_rows,
    }


def _render_markdown(summary: dict[str, Any]) -> str:
    lines = ["# Protocol v7a: static utility-cost prediction — summary", ""]
    lines.append("## Per-suite confusion (predicted_block vs observed_denial)")
    lines.append(
        "| suite | n | tp | fp | fn | tn | accuracy | 95% CI | precision | recall | pred. ceiling | obs. utility |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for s in SUITES:
        d = summary["per_suite"][s]
        c = d["confusion_denial"]
        lo, hi = c["accuracy_wilson95"]
        lines.append(
            f"| {s} | {c['n']} | {c['tp']} | {c['fp']} | {c['fn']} | {c['tn']} | "
            f"{c['accuracy']:.3f} | [{lo:.3f}, {hi:.3f}] | {c['precision']:.3f} | {c['recall']:.3f} | "
            f"{d['predicted_utility_ceiling']:.3f} | {d['observed_benign_utility']:.3f} |"
        )
    oc = summary["overall"]["confusion_denial"]
    lo, hi = oc["accuracy_wilson95"]
    lines.append(
        f"| **overall** | {oc['n']} | {oc['tp']} | {oc['fp']} | {oc['fn']} | {oc['tn']} | "
        f"{oc['accuracy']:.3f} | [{lo:.3f}, {hi:.3f}] | {oc['precision']:.3f} | {oc['recall']:.3f} | — | — |"
    )
    lines.append("")
    lines.append("## Mismatch classes (overall)")
    for k, v in sorted(summary["overall"]["mismatch_counts"].items()):
        lines.append(f"- `{k}`: {v}")
    lines.append("")
    lines.append("## fn_onpath cases (soundness-critical — must be investigated)")
    if not summary["fn_onpath_cases"]:
        lines.append("None found.")
    else:
        for case in summary["fn_onpath_cases"]:
            lines.append(f"- {case['suite']}/{case['user_task_id']}: {case['denied_calls']}")
    return "\n".join(lines) + "\n"


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    all_rows: list[dict[str, Any]] = []
    gt_functions_by_key: dict[tuple[str, str], list[str]] = {}

    for suite_name in SUITES:
        suite = get_suite(BENCHMARK_VERSION, suite_name)
        for task_id, user_task in sorted(suite.user_tasks.items()):
            try:
                env = suite.load_and_inject_default_environment({})
                gt = user_task.ground_truth(env)
                gt_functions_by_key[(suite_name, task_id)] = [fc.function for fc in gt]
            except Exception:  # noqa: BLE001
                gt_functions_by_key[(suite_name, task_id)] = []
        all_rows.extend(predict_suite(suite_name))

    for row in all_rows:
        row["_gt_functions"] = gt_functions_by_key.get((row["suite"], row["user_task_id"]), [])

    observed_by_suite = {s: load_observed(V6_RESULTS_DIR, s) for s in SUITES}

    # Stop condition: exactly 97 benign traces total, matching per-suite expected counts.
    trace_counts = {s: len(observed_by_suite[s]) for s in SUITES}
    total_traces = sum(trace_counts.values())
    if total_traces != 97 or trace_counts != EXPECTED_BENIGN_COUNTS:
        gap_report = {
            "stop_condition_triggered": "fewer_than_97_benign_traces" if total_traces < 97 else "trace_count_mismatch",
            "expected": EXPECTED_BENIGN_COUNTS,
            "found": trace_counts,
            "total_found": total_traces,
        }
        (RESULTS_DIR / "trace_count_gap.json").write_text(json.dumps(gap_report, indent=2))
        print(f"STOP CONDITION: {gap_report}")
        return

    summary = build_summary(all_rows, observed_by_suite)

    with (RESULTS_DIR / "predictions.jsonl").open("w") as f:
        for row in summary["rows"]:
            f.write(json.dumps(row) + "\n")
    (RESULTS_DIR / "summary.json").write_text(
        json.dumps(
            {
                "per_suite": summary["per_suite"],
                "overall": summary["overall"],
                "fn_onpath_cases": summary["fn_onpath_cases"],
            },
            indent=2,
        )
    )
    (RESULTS_DIR / "summary.md").write_text(_render_markdown(summary))
    print("v7a complete. Wrote predictions.jsonl, summary.json, summary.md to", RESULTS_DIR)


if __name__ == "__main__":
    main()
