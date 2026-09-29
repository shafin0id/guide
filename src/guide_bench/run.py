"""Experiment runner: randomised order, repetitions, resumable JSONL, run manifest.

Usage (see docs/experiments.md for the exact commands behind every reported number):
    python -m guide_bench.run --suite main --conditions B1,B2,P,GPLUS --reps 5 --out experiments/results/main
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import subprocess
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from guide.policy import Policy
from guide.providers import ModelProvider, ModelSettings, OpenAICompatibleProvider, ScriptedProvider
from guide.routing import Router
from guide.tools import ToolRegistry
from guide.workflow import TaskSpec
from guide_bench.adversarial import AdversarialCase, adversarial_cases, compromised_cases
from guide_bench.conditions import CONDITIONS, build_runtime, make_router
from guide_bench.env import Environment
from guide_bench.faults import FaultyProvider
from guide_bench.scoring import Outcome, score, trace_completeness
from guide_bench.tasks import PILOT_IDS, BenchTask, main_tasks


@dataclass(frozen=True)
class Item:
    case: AdversarialCase
    condition: str
    rep: int

    @property
    def key(self) -> str:
        return f"{self.case.task.task_id}|{self.condition}|{self.rep}"


def load_env_file(path: str | None) -> None:
    """Minimal KEY=VALUE loader; values are never printed or logged."""
    if not path:
        return
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def task_digest(task: BenchTask) -> str:
    doc = [
        task.task_id,
        task.objective,
        [c.text for c in task.constraints],
        task.output_schema,
        list(task.retrieve_tools),
        list(task.report_tools),
        repr(task.faults),
    ]
    return hashlib.sha256(json.dumps(doc, sort_keys=True, default=str).encode()).hexdigest()[:16]


def git_state() -> dict[str, Any]:
    def run(*args: str) -> str:
        try:
            return subprocess.run(  # noqa: S603 - fixed git argv, no user input
                ["git", *args],  # noqa: S607 - git resolved from PATH by design
                capture_output=True,
                text=True,
                timeout=10,
            ).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return "unavailable"

    return {"commit": run("rev-parse", "HEAD"), "dirty": bool(run("status", "--porcelain", "--", "src"))}


def build_items(suite: str, conditions: list[str], reps: int) -> list[Item]:
    if suite in ("main", "pilot"):
        tasks = [t for t in main_tasks() if suite == "main" or t.task_id in PILOT_IDS]
        cases = [AdversarialCase(t, "none") for t in tasks]
    elif suite == "adversarial":
        cases = [c for c in adversarial_cases() if c.task.task_id != "A12"]
    elif suite == "compromised":
        cases = compromised_cases()
    elif suite == "sequence":
        cases = [c for c in adversarial_cases() if c.task.task_id == "A12"]
    else:
        raise SystemExit(f"unknown suite {suite}")
    return [Item(c, cond, rep) for c in cases for cond in conditions for rep in range(1, reps + 1)]


def execute(
    item: Item,
    provider: ModelProvider,
    router: Router,
    settings: ModelSettings,
    *,
    policy: Policy | None = None,
    spec: TaskSpec | None = None,
) -> tuple[dict, dict]:
    case, task = item.case, item.case.task
    env = Environment(task.faults)
    registry = ToolRegistry(env.tools)
    prov: ModelProvider = FaultyProvider(provider, case.model_faults) if case.model_faults else provider
    runtime = build_runtime(
        CONDITIONS[item.condition], prov, registry, policy or task.policy(), router, settings, case.transport
    )
    record = runtime.run(
        spec or task.spec(), run_id=f"{task.task_id}-{item.condition}-r{item.rep}-{int(time.time()*1000)}"
    )
    outcome = Outcome(record, env.side_effects)
    s = score(task.constraints, outcome)
    decisions = Counter(c.decision for c in record.calls)
    row = {
        "key": item.key,
        "suite": task.suite,
        "task_id": task.task_id,
        "family": task.family,
        "tier": task.tier,
        "perturbation": case.perturbation,
        "condition": item.condition,
        "rep": item.rep,
        "status": record.status,
        "task_success": s.task_success,
        "intent_fidelity": round(s.intent_fidelity, 4),
        "violation": s.violation,
        "constraints_passed": s.constraints_passed,
        "constraints_total": s.constraints_total,
        "failed_constraints": list(s.failed_constraints),
        "trace_completeness": trace_completeness(record, len(record.step_outputs)),
        "trace_intact": record.trace_intact,
        "model_calls": record.usage.model_calls,
        "prompt_tokens": record.usage.prompt_tokens,
        "completion_tokens": record.usage.completion_tokens,
        "wall_s": round(record.wall_s, 3),
        "decisions": dict(decisions),
        "denied_rules": [c.rule for c in record.calls if c.decision == "DENY"],
        "emails_to": [e.get("recipient") for e in env.side_effects.emails],
        "deletions": env.side_effects.deletions,
        "status_updates": len(env.side_effects.status_updates),
        "restricted_exposure": int(env.restricted_exposures > 0),
        "errors": record.errors,
        "routing": record.routing,
        "model_ids": sorted(record.model_ids),
        "final_output": record.final_output,
    }
    transcript = {
        "key": item.key,
        "run_id": record.run_id,
        "status": record.status,
        "final_output": record.final_output,
        "model_io": record.model_io,
        "side_effects": {
            "emails": env.side_effects.emails,
            "deletions": env.side_effects.deletions,
            "status_updates": env.side_effects.status_updates,
        },
        "calls": [
            {
                "step": c.step_id,
                "tool": c.proposed.tool,
                "op": c.proposed.operation,
                "args": dict(c.proposed.args),
                "executed_args": dict(c.executed.args) if c.executed is not None else None,
                "principal": c.principal,
                "decision": c.decision,
                "rule": c.rule,
                "reason": c.reason,
                "ok": c.ok,
                "error": c.error,
            }
            for c in record.calls
        ],
    }
    return row, transcript


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--suite", required=True, choices=["pilot", "main", "adversarial", "compromised", "sequence"])
    ap.add_argument("--conditions", default="B1,B2,P,GPLUS")
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="deepseek-chat")
    ap.add_argument("--base-url", default="https://api.deepseek.com")
    ap.add_argument("--key-env", default="DEEPSEEK_API_KEY")
    ap.add_argument("--env-file", default=None)
    ap.add_argument("--max-tokens", type=int, default=4096)
    ap.add_argument("--scripted-smoke", action="store_true", help="plumbing check with a test double; never reportable")
    args = ap.parse_args(argv)

    conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]
    unknown = [c for c in conditions if c not in CONDITIONS]
    if unknown:
        raise SystemExit(f"unknown conditions: {unknown}")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    results_path, transcripts_path, manifest_path = (
        out / "results.jsonl",
        out / "transcripts.jsonl",
        out / "manifest.json",
    )

    settings = ModelSettings(temperature=0.0, max_tokens=args.max_tokens, seed=42, json_mode=True)
    if args.scripted_smoke:
        provider: ModelProvider = ScriptedProvider(lambda m: '{"tool_calls": [], "output": {}, "confidence": 0.5}')
    else:
        load_env_file(args.env_file)
        provider = OpenAICompatibleProvider(model=args.model, base_url=args.base_url, api_key_env=args.key_env)

    items = build_items(args.suite, conditions, args.reps)
    rng = random.Random(args.seed)
    if args.suite != "sequence":
        rng.shuffle(items)  # proposal §8.2: randomised condition/task/repetition order
    done = set()
    if results_path.exists():
        done = {json.loads(line)["key"] for line in results_path.read_text().splitlines() if line.strip()}
    todo = [it for it in items if it.key not in done]

    manifest = {
        "suite": args.suite,
        "conditions": conditions,
        "reps": args.reps,
        "seed": args.seed,
        "provider": "scripted-test-double" if args.scripted_smoke else "openai-compatible",
        "model_requested": args.model,
        "base_url": args.base_url,
        "settings": settings.__dict__,
        "git": git_state(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "tasks": {it.case.task.task_id: task_digest(it.case.task) for it in items},
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "items_total": len(items),
        "items_resumed_skipped": len(items) - len(todo),
        "reportable": not args.scripted_smoke,
    }
    if manifest_path.exists():
        prev = json.loads(manifest_path.read_text())
        manifest["previous_sessions"] = prev.get("previous_sessions", []) + [
            {k: prev.get(k) for k in ("started_utc", "git", "finished_utc")}
        ]
    manifest_path.write_text(json.dumps(manifest, indent=2))

    routers = {c: make_router(CONDITIONS[c]) for c in conditions}
    lock = threading.Lock()
    model_ids: set[str] = set()
    status = Counter()

    def work(item: Item) -> dict:
        return execute(item, provider, routers[item.condition], settings)

    workers = 1 if args.suite == "sequence" else max(1, args.workers)
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(work, it): it for it in todo}
        for n, fut in enumerate(as_completed(futures), 1):
            it = futures[fut]
            try:
                row, transcript = fut.result()
            except Exception as exc:  # noqa: BLE001 - a harness crash must be recorded, never dropped silently
                row = {
                    "key": it.key,
                    "task_id": it.case.task.task_id,
                    "condition": it.condition,
                    "rep": it.rep,
                    "status": "harness_error",
                    "error": f"{type(exc).__name__}: {exc}",
                }
                transcript = {"key": it.key}
            with lock:
                with results_path.open("a") as fh:
                    fh.write(json.dumps(row, default=str) + "\n")
                with transcripts_path.open("a") as fh:
                    fh.write(json.dumps(transcript, default=str) + "\n")
                model_ids.update(row.get("model_ids", []))
                status[row["status"]] += 1
            if n % 20 == 0 or n == len(todo):
                print(f"[{n}/{len(todo)}] {dict(status)} {time.time()-t0:.0f}s", flush=True)

    manifest["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    manifest["model_ids_observed"] = sorted(model_ids)
    manifest["status_counts_this_session"] = dict(status)
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return 0 if status.get("harness_error", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
