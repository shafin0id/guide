"""CLI runner for AgentDojo benchmarks with GUIDE GPLUS containment.

Supports live terminal logging, tee to file, token usage tracking, and off-peak checking.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import time
from pathlib import Path

from agentdojo.attacks.attack_registry import load_attack
from agentdojo.benchmark import (
    get_suite,
    run_task_with_injection_tasks,
    run_task_without_injection_tasks,
)
from agentdojo.logging import OutputLogger

from guide_agentdojo.pipeline import GuideGplusPipeline


def is_beijing_off_peak(dt: datetime.datetime | None = None) -> tuple[bool, str]:
    """Checks if current time in Beijing (UTC+8) is inside an off-peak pricing window.

    Off-peak: before 09:00, 12:00-14:00, after 18:00 Mon-Fri, and all weekend.
    Peak: 09:00-12:00 and 14:00-18:00 Mon-Fri.
    """
    if dt is None:
        tz = datetime.timezone(datetime.timedelta(hours=8))
        dt = datetime.datetime.now(tz)
    weekday = dt.weekday()  # 0=Mon, 6=Sun
    hour = dt.hour
    minute = dt.minute
    time_val = hour + minute / 60.0

    if weekday >= 5:  # Saturday or Sunday
        return True, f"Weekend ({dt.strftime('%A %H:%M')} UTC+8) is off-peak"

    # Weekday windows
    if time_val < 9.0:
        return True, f"Early morning ({dt.strftime('%H:%M')} UTC+8 < 09:00) is off-peak"
    if 12.0 <= time_val < 14.0:
        return True, f"Midday window ({dt.strftime('%H:%M')} UTC+8 in 12:00-14:00) is off-peak"
    if time_val >= 18.0:
        return True, f"Evening ({dt.strftime('%H:%M')} UTC+8 >= 18:00) is off-peak"

    return False, f"Current time ({dt.strftime('%H:%M')} UTC+8) is PEAK (peak windows: 09:00-12:00, 14:00-18:00)"


class TeeLogger:
    """Tees output to both stdout and a log file."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file = open(self.file_path, "a", encoding="utf-8")
        self.stdout = sys.stdout

    def write(self, message: str) -> None:
        self.stdout.write(message)
        self.file.write(message)
        self.flush()

    def flush(self) -> None:
        self.stdout.flush()
        self.file.flush()

    def close(self) -> None:
        self.file.close()


def append_token_ledger(
    ledger_path: Path,
    suite: str,
    phase_label: str,
    prompt_tokens: int,
    completion_tokens: int,
    model: str,
    utility_rate: float,
    security_rate: float,
) -> None:
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    cost = (prompt_tokens / 1_000_000 * 1.0) + (completion_tokens / 1_000_000 * 4.0)
    record = {
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "phase": phase_label,
        "suite": suite,
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "estimated_cny_cost_offpeak": round(cost, 6),
        "utility_rate": round(utility_rate, 4),
        "security_rate": round(security_rate, 4),
    }
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def run_benchmark(
    suite_name: str,
    benchmark_version: str = "v1.2.2",
    attack_name: str | None = None,
    user_task_ids: list[str] | None = None,
    smoke: bool = False,
    logdir: Path = Path("experiments/results/agentdojo-v6"),
    strict_offpeak: bool = False,
    max_tokens_per_call: int = 1024,
) -> int:
    off_peak, msg = is_beijing_off_peak()
    if not off_peak and strict_offpeak:
        print(f"ERROR: Cannot start phase outside off-peak pricing window: {msg}")
        return 1

    print(f"Pricing check: {msg}")

    suite_dir = logdir / suite_name
    suite_dir.mkdir(parents=True, exist_ok=True)
    log_file = suite_dir / "run.log"
    tee = TeeLogger(log_file)
    sys.stdout = tee

    t0 = time.time()
    try:
        suite = get_suite(benchmark_version, suite_name)
        model_name = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")

        # In smoke mode, restrict to minimal tokens (capped at 512 for reasoning models) and 1-2 tasks
        if smoke:
            max_tokens_per_call = min(max_tokens_per_call, 512)
            tasks_to_run = user_task_ids or list(suite.user_tasks.keys())[:2]
        else:
            tasks_to_run = user_task_ids or list(suite.user_tasks.keys())

        pipeline = GuideGplusPipeline(
            model=model_name,
            max_tokens=max_tokens_per_call,
            name="guide-gplus-local",
        )

        print("================================================================================")
        print(f"Starting AgentDojo benchmark: suite='{suite_name}' model='{model_name}'")
        print(f"Tasks to run: {len(tasks_to_run)} | Attack: {attack_name or 'none'} | Smoke mode: {smoke}")
        print("================================================================================")

        utility_results: dict[str, bool] = {}
        security_results: dict[str, bool] = {}

        total_tasks = len(tasks_to_run)
        with OutputLogger(str(suite_dir)):
            for idx, ut_id in enumerate(tasks_to_run, 1):
                user_task = suite.get_user_task_by_id(ut_id)

                if attack_name is None or attack_name.lower() in ("none", ""):
                    print(f"[{suite_name}] [task {idx}/{total_tasks}] running {ut_id} (no attack)...", flush=True)
                    task_t0 = time.time()
                    util, sec = run_task_without_injection_tasks(
                        suite=suite,
                        agent_pipeline=pipeline,
                        task=user_task,
                        logdir=suite_dir,
                        force_rerun=True,
                        benchmark_version=benchmark_version,
                    )
                    utility_results[ut_id] = util
                    security_results[ut_id] = sec
                    elapsed = time.time() - task_t0
                    print(
                        f"[{suite_name}] [{idx}/{total_tasks}] {ut_id} -> util={util} sec={sec} ({elapsed:.1f}s) | "
                        f"Tokens: in={pipeline.tracker.prompt_tokens} out={pipeline.tracker.completion_tokens} "
                        f"total={pipeline.tracker.total_tokens} (~{pipeline.tracker.cost_cny():.4f} CNY)",
                        flush=True,
                    )
                else:
                    attacker = load_attack(attack_name, suite, pipeline)
                    inj_tasks = list(suite.injection_tasks.keys())
                    if smoke:
                        inj_tasks = inj_tasks[:1]
                    total_injections = len(inj_tasks)
                    for inj_idx, inj_id in enumerate(inj_tasks, 1):
                        print(
                            f"[{suite_name}] [task {idx}/{total_tasks}] [attack {inj_idx}/{total_injections}] "
                            f"running {ut_id} + {inj_id}...",
                            flush=True,
                        )
                        task_t0 = time.time()
                        u_dict, s_dict = run_task_with_injection_tasks(
                            suite=suite,
                            agent_pipeline=pipeline,
                            user_task=user_task,
                            attack=attacker,
                            logdir=suite_dir,
                            force_rerun=True,
                            injection_tasks=[inj_id],
                            benchmark_version=benchmark_version,
                        )
                        util = u_dict.get((ut_id, inj_id), False)
                        sec = s_dict.get((ut_id, inj_id), False)
                        utility_results[f"{ut_id}_{inj_id}"] = util
                        security_results[f"{ut_id}_{inj_id}"] = sec
                        elapsed = time.time() - task_t0
                        print(
                            f"[{suite_name}] [task {idx}/{total_tasks}] [attack {inj_idx}/{total_injections}] "
                            f"result: util={util} sec={sec} ({elapsed:.1f}s) | "
                            f"Tokens: in={pipeline.tracker.prompt_tokens} out={pipeline.tracker.completion_tokens} "
                            f"total={pipeline.tracker.total_tokens} (~{pipeline.tracker.cost_cny():.4f} CNY)",
                            flush=True,
                        )

        # Compute summary rates
        avg_util = sum(utility_results.values()) / max(len(utility_results), 1)
        # Note: in AgentDojo, security check returning False means the attack was prevented!
        # If security check is True, attack succeeded. So containment rate = 1 - avg_sec
        avg_sec = sum(security_results.values()) / max(len(security_results), 1)

        phase_num = {"banking": 1, "slack": 2, "travel": 3, "workspace": 4}.get(suite_name, 1)
        phase_label = "Phase 0 (Smoke)" if smoke else f"Phase {phase_num} ({suite_name}:{attack_name or 'none'})"
        append_token_ledger(
            ledger_path=logdir / "token_usage.jsonl",
            suite=suite_name,
            phase_label=phase_label,
            prompt_tokens=pipeline.tracker.prompt_tokens,
            completion_tokens=pipeline.tracker.completion_tokens,
            model=model_name,
            utility_rate=avg_util,
            security_rate=avg_sec,
        )

        # Save summary json
        summary_path = suite_dir / ("smoke_summary.json" if smoke else f"summary_{attack_name or 'none'}.json")
        summary_data = {
            "suite": suite_name,
            "smoke": smoke,
            "benchmark_version": benchmark_version,
            "model": model_name,
            "attack": attack_name or "none",
            "total_tasks": total_tasks,
            "utility_results": utility_results,
            "security_results": security_results,
            "avg_utility": avg_util,
            "avg_security": avg_sec,
            "tokens": {
                "prompt": pipeline.tracker.prompt_tokens,
                "completion": pipeline.tracker.completion_tokens,
                "total": pipeline.tracker.total_tokens,
                "calls": pipeline.tracker.model_calls,
                "cost_cny": pipeline.tracker.cost_cny(),
            },
            "wall_s": time.time() - t0,
        }
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2)

        print("--------------------------------------------------------------------------------")
        print(
            f"PHASE COMPLETE: suite='{suite_name}' | Utility: {avg_util * 100:.1f}% | "
            f"Tokens used: {pipeline.tracker.total_tokens} (~{pipeline.tracker.cost_cny():.4f} CNY) | "
            f"Wall clock: {time.time() - t0:.1f}s"
        )
        print("--------------------------------------------------------------------------------")
        return 0

    except Exception as exc:  # noqa: BLE001
        print(f"\nPHASE FAILED: Exception occurred during run: {exc}", flush=True)
        import traceback

        traceback.print_exc()
        return 1
    finally:
        tee.close()
        sys.stdout = tee.stdout


def main() -> None:
    parser = argparse.ArgumentParser(description="GUIDE AgentDojo Benchmark Runner")
    parser.add_argument("--suite", default="banking", choices=["banking", "slack", "travel", "workspace"])
    parser.add_argument("--benchmark-version", default="v1.2.2")
    parser.add_argument("--attack", default=None, help="Attack name (or None for utility-only baseline)")
    parser.add_argument("--smoke", action="store_true", help="Run tiny smoke test with 1-2 tasks and minimal tokens")
    parser.add_argument(
        "-ut", "--user-task", action="append", dest="user_tasks", help="Specific user task ID(s) to run"
    )
    parser.add_argument("--logdir", default="experiments/results/agentdojo-v6", type=Path)
    parser.add_argument("--strict-offpeak", action="store_true", help="Enforce off-peak check before running")
    parser.add_argument("--max-tokens", default=1024, type=int)

    args = parser.parse_args()
    code = run_benchmark(
        suite_name=args.suite,
        benchmark_version=args.benchmark_version,
        attack_name=args.attack,
        user_task_ids=args.user_tasks,
        smoke=args.smoke,
        logdir=args.logdir,
        strict_offpeak=args.strict_offpeak,
        max_tokens_per_call=args.max_tokens,
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
