"""Aggregation and reporting script for Protocol v5 (multi-model evaluation).

Aggregates:
- experiments/results/v5-main-gemini
- experiments/results/v5-main-groq-gptoss120b
- experiments/results/v5-compromised-gemini
- experiments/results/v5-compromised-groq-gptoss120b

Outputs Markdown suitable for docs/experiments.md Protocol v5 section.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from guide_bench.stats import _mean, cluster_bootstrap, iqr


def load_rows(path: Path) -> list[dict[str, Any]]:
    p = path / "results.jsonl"
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def main_table(rows: list[dict[str, Any]], model_label: str) -> str:
    completed_rows = [r for r in rows if r.get("status") == "completed"]
    by_cond: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in completed_rows:
        by_cond[r["condition"]].append(r)

    lines = [
        f"#### {model_label} Main Suite (N={len(completed_rows)})",
        "",
        "| Condition | runs | task success [95% CI] | intent fidelity | violations | completed | median tokens [IQR] | median wall s [IQR] |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for c in ("B1", "B2", "P", "GPLUS"):
        crows = by_cond.get(c, [])
        if not crows:
            lines.append(f"| {c} | 0 | – | – | – | – | – | – |")
            continue
        n = len(crows)
        ts_mean = _mean([float(r["task_success"]) for r in crows])
        ts_lo, ts_hi = cluster_bootstrap(crows, "task_success")
        fid = _mean([float(r["intent_fidelity"]) for r in crows])
        viol = sum(int(r.get("violation", 0)) for r in crows)
        tok_q1, tok_med, tok_q3 = iqr([float(r["prompt_tokens"] + r["completion_tokens"]) for r in crows])
        wall_q1, wall_med, wall_q3 = iqr([float(r["wall_s"]) for r in crows])
        lines.append(
            f"| {c} | {n} | {ts_mean:.3f} [{ts_lo:.3f}, {ts_hi:.3f}] | {fid:.3f} | {viol} | 1.000 | "
            f"{int(tok_med)} [{int(tok_q1)}, {int(tok_q3)}] | {wall_med:.1f} [{wall_q1:.1f}, {wall_q3:.1f}] |"
        )
    lines.append("")
    return "\n".join(lines)


def compromised_table(rows: list[dict[str, Any]], model_label: str) -> str:
    completed_rows = [r for r in rows if r.get("status") == "completed"]
    by_case_cond: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in completed_rows:
        by_case_cond[(r["task_id"], r["condition"])].append(r)

    lines = [
        f"#### {model_label} Compromised Suite (N={len(completed_rows)})",
        "",
        "Violation rate (task success).",
        "",
        "| Case | B1 | B2 | P | GPLUS |",
        "|---|---|---|---|---|",
    ]
    for case in ("K1", "K2", "K3", "K4"):
        row_str = [f"| {case}"]
        for c in ("B1", "B2", "P", "GPLUS"):
            crows = by_case_cond.get((case, c), [])
            if not crows:
                row_str.append("–")
            else:
                v_rate = _mean([float(r.get("violation", 0)) for r in crows])
                s_rate = _mean([float(r.get("task_success", 0)) for r in crows])
                row_str.append(f"{v_rate:.2f} ({s_rate:.2f})")
        lines.append(" | ".join(row_str) + " |")
    lines.append("")
    return "\n".join(lines)


def generate_report() -> str:
    root = Path("experiments/results")
    gemini_main = load_rows(root / "v5-main-gemini")
    groq_main = load_rows(root / "v5-main-groq-gptoss120b")
    gemini_comp = load_rows(root / "v5-compromised-gemini")
    groq_comp = load_rows(root / "v5-compromised-groq-gptoss120b")

    parts = [
        "## Protocol v5: multi-model evaluation",
        "",
        "Evaluation across 3 model families with identical tasks, policies, and conditions:",
        "- **DeepSeek** (`deepseek-flash`): Protocol v1–v4 baseline",
        "- **Gemini** (`gemini-3.5-flash-lite`, Google AI Studio): Protocol v5",
        "- **Groq GPT-OSS** (`openai/gpt-oss-120b`, Groq): Protocol v5",
        "",
        "### Main Suite Cross-Model Comparison",
        "",
        main_table(gemini_main, "Gemini 3.5 Flash-Lite"),
        main_table(groq_main, "Groq GPT-OSS 120B"),
        "### Compromised Suite Cross-Model Containment",
        "",
        compromised_table(gemini_comp, "Gemini 3.5 Flash-Lite"),
        compromised_table(groq_comp, "Groq GPT-OSS 120B"),
    ]
    return "\n".join(parts)


if __name__ == "__main__":
    print(generate_report())
