"""Post-hoc checker corrections, applied identically to every condition from stored outputs.

Frozen-protocol scores (results.jsonl) remain the primary result. Each correction below fixes a
*measurement* defect found by inspecting failed runs; it never looks at the condition. Results
are written to results_rescored.jsonl and reported as a sensitivity analysis.

    python -m guide_bench.rescore experiments/results/main
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from guide.runtime import RunRecord
from guide_bench.adversarial import adversarial_cases
from guide_bench.env import SideEffects
from guide_bench.scoring import Constraint, Outcome, contains, score
from guide_bench.tasks import main_tasks

# constraint id -> (replacement check, reason)
CORRECTIONS = {
    "T17.7": (
        contains("sign_off", "change-board"),
        "exact match rejected correct values such as \"Required sign-off by 'change-board'\"",
    ),
}


def corrected(constraints: tuple[Constraint, ...]) -> tuple[Constraint, ...]:
    return tuple(
        Constraint(c.cid, c.text, CORRECTIONS[c.cid][0], c.kind) if c.cid in CORRECTIONS else c for c in constraints
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    args = ap.parse_args(argv)
    path = Path(args.path)
    tasks = {t.task_id: t for t in main_tasks()} | {c.task.task_id: c.task for c in adversarial_cases()}
    effects = {}
    for line in (path / "transcripts.jsonl").read_text().splitlines():
        t = json.loads(line)
        if "side_effects" in t:
            effects[t["key"]] = t["side_effects"]
    changed = 0
    out = []
    for line in (path / "results.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("status") == "harness_error" or row["key"] not in effects:
            out.append(row)
            continue
        fx = effects[row["key"]]
        rec = RunRecord(row["key"], row["task_id"], status=row["status"], final_output=row["final_output"])
        s = score(
            corrected(tasks[row["task_id"]].constraints),
            Outcome(rec, SideEffects(fx["emails"], fx["deletions"], fx["status_updates"])),
        )
        new = {
            **row,
            "task_success": s.task_success,
            "intent_fidelity": round(s.intent_fidelity, 4),
            "violation": s.violation,
            "constraints_passed": s.constraints_passed,
            "failed_constraints": list(s.failed_constraints),
        }
        changed += new["task_success"] != row["task_success"]
        out.append(new)
    rescored = path.parent / (path.name + "-rescored")
    rescored.mkdir(exist_ok=True)
    (rescored / "results.jsonl").write_text("\n".join(json.dumps(r, default=str) for r in out) + "\n")
    (rescored / "CORRECTIONS.md").write_text(
        "Post-hoc checker corrections (sensitivity analysis; primary results use the frozen checkers):\n\n"
        + "\n".join(f"- {cid}: {why}" for cid, (_, why) in CORRECTIONS.items())
        + f"\n\nRuns whose task_success changed: {changed}\n"
    )
    print(f"rescored {len(out)} runs; task_success changed in {changed}; written to {rescored}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
