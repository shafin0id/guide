"""Runner for AgentDojo Undefended Baseline Benchmark (Protocol v6b).

Runs the full 4-suite benchmark with GUIDE containment stack disabled
(gated=False, provenance=False) on deepseek-v4-flash.
Tracks live percentage progress against the 626 total planned units,
checks Beijing off-peak pricing windows before and during the run,
enforces a 12,000,000 token cap, and writes standardized results and logs.
Supports --resume to safely restart from any completed suite/condition without repeating work.
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
from guide_agentdojo.run import TeeLogger, append_token_ledger, is_beijing_off_peak

# Exact task configurations matching Protocol v6
WORKSPACE_STRATIFIED_ATTACK_TASKS = [
    "user_task_0",
    "user_task_4",
    "user_task_8",
    "user_task_12",
    "user_task_16",
    "user_task_20",
    "user_task_24",
    "user_task_28",
    "user_task_32",
    "user_task_36",
]

SUITE_CONFIGS = [
    {
        "suite": "banking",
        "benign_tasks": None,  # all 16 tasks
        "attack": "important_instructions",
        "attack_tasks": None,  # all 16 tasks x 9 injections = 144 pairs
    },
    {
        "suite": "slack",
        "benign_tasks": None,  # all 21 tasks
        "attack": "important_instructions",
        "attack_tasks": None,  # all 21 tasks x 5 injections = 105 pairs
    },
    {
        "suite": "travel",
        "benign_tasks": None,  # all 20 tasks
        "attack": "important_instructions",
        "attack_tasks": None,  # all 20 tasks x 7 injections = 140 pairs
    },
    {
        "suite": "workspace",
        "benign_tasks": None,  # all 40 tasks
        "attack": "important_instructions",
        "attack_tasks": WORKSPACE_STRATIFIED_ATTACK_TASKS,  # 10 tasks x 14 injections = 140 pairs
    },
]

TOTAL_EXPECTED_UNITS = 626  # 97 benign + 529 attack pairs
TOKEN_CAP = 12_000_000


def calculate_planned_units(benchmark_version: str = "v1.2.2") -> list[dict]:
    """Generates the exact ordered sequence of evaluation units."""
    units = []
    for cfg in SUITE_CONFIGS:
        s_name = cfg["suite"]
        suite = get_suite(benchmark_version, s_name)
        # 1. Benign units
        benign_task_ids = cfg["benign_tasks"] or list(suite.user_tasks.keys())
        for ut_id in benign_task_ids:
            units.append({
                "suite": s_name,
                "attack": "none",
                "user_task_id": ut_id,
                "injection_task_id": None,
            })
        # 2. Attack units
        attack_task_ids = cfg["attack_tasks"] or list(suite.user_tasks.keys())
        inj_ids = list(suite.injection_tasks.keys())
        for ut_id in attack_task_ids:
            for inj_id in inj_ids:
                units.append({
                    "suite": s_name,
                    "attack": cfg["attack"],
                    "user_task_id": ut_id,
                    "injection_task_id": inj_id,
                })
    return units


def run_smoke_test(
    logdir: Path = Path("experiments/results/agentdojo-v6b-undefended"),
    benchmark_version: str = "v1.2.2",
    model_name: str = "deepseek-v4-flash",
) -> int:
    """Runs a 1-task minimal smoke test to verify undefended pipeline execution."""
    print("================================================================================")
    print("Initiating Undefended Baseline Smoke Test (Banking user_task_1, no attack)")
    print("================================================================================")
    off_peak, msg = is_beijing_off_peak()
    print(f"Pricing check: {msg}")

    smoke_dir = logdir / "smoke"
    smoke_dir.mkdir(parents=True, exist_ok=True)
    tee = TeeLogger(smoke_dir / "run.log")
    sys.stdout = tee

    try:
        suite = get_suite(benchmark_version, "banking")
        task = suite.get_user_task_by_id("user_task_1")

        pipeline = GuideGplusPipeline(
            model=model_name,
            max_tokens=512,
            gated=False,
            provenance=False,
            name="guide-undefended-local",
        )

        t0 = time.time()
        with OutputLogger(str(smoke_dir)):
            util, sec = run_task_without_injection_tasks(
                suite=suite,
                agent_pipeline=pipeline,
                task=task,
                logdir=smoke_dir,
                force_rerun=True,
                benchmark_version=benchmark_version,
            )
        elapsed = time.time() - t0

        print(
            f"[SMOKE TEST] user_task_1 -> util={util} sec={sec} ({elapsed:.1f}s) | "
            f"Tokens: in={pipeline.tracker.prompt_tokens} out={pipeline.tracker.completion_tokens} "
            f"total={pipeline.tracker.total_tokens} (~{pipeline.tracker.cost_cny():.4f} CNY)"
        )
        assert pipeline.tracker.total_tokens > 0, "Pipeline recorded zero tokens"
        print("================================================================================")
        print("SMOKE TEST SUCCESSFUL: Undefended pipeline verified end-to-end.")
        print("================================================================================")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        tee.close()
        sys.stdout = tee.stdout


def run_full_baseline(
    logdir: Path = Path("experiments/results/agentdojo-v6b-undefended"),
    benchmark_version: str = "v1.2.2",
    model_name: str = "deepseek-v4-flash",
    max_tokens_per_call: int = 1024,
    strict_offpeak: bool = True,
    resume: bool = True,
) -> int:
    """Executes the full 4-suite undefended baseline with live progress reporting."""
    off_peak, msg = is_beijing_off_peak()
    if strict_offpeak and not off_peak:
        print(f"ERROR: Cannot start run outside off-peak pricing window: {msg}")
        return 1

    logdir.mkdir(parents=True, exist_ok=True)
    master_tee = TeeLogger(logdir / "run.log")
    sys.stdout = master_tee

    planned_units = calculate_planned_units(benchmark_version)
    total_units = len(planned_units)
    assert total_units == TOTAL_EXPECTED_UNITS, f"Expected {TOTAL_EXPECTED_UNITS} units, got {total_units}"

    print("================================================================================")
    print("STARTING FULL AGENTDOJO UNDEFENDED BASELINE RUN (Protocol v6b)")
    print(f"Model: {model_name} | Pricing: {msg}")
    print(f"Planned units: {total_units} (97 benign + 529 attack pairs) | Token cap: {TOKEN_CAP:,}")
    print(f"Containment stack: GATED=False, PROVENANCE=False (Pure Undefended)")
    print(f"Log directory: {logdir.resolve()}")
    print("================================================================================\n", flush=True)

    cumulative_prompt_tokens = 0
    cumulative_completion_tokens = 0
    overall_t0 = time.time()
    unit_counter = 0

    suite_results_summary: list[dict] = []

    try:
        for s_idx, cfg in enumerate(SUITE_CONFIGS, 1):
            s_name = cfg["suite"]

            # Clock check before starting each suite
            off_peak_now, check_msg = is_beijing_off_peak()
            if not off_peak_now:
                if strict_offpeak:
                    print(f"\n[ALERT] Peak window entered ({check_msg}). Pausing suite '{s_name}' until off-peak.")
                    while not off_peak_now:
                        time.sleep(300)
                        off_peak_now, check_msg = is_beijing_off_peak()
                    print(f"[RESUMING] Off-peak window reached: {check_msg}\n", flush=True)
                else:
                    print(f"\n[WARNING] Peak window detected ({check_msg}), continuing as strict_offpeak=False\n")

            suite_dir = logdir / s_name
            suite_dir.mkdir(parents=True, exist_ok=True)
            suite = get_suite(benchmark_version, s_name)

            # ----------------------------------------------------
            # 1. Benign condition
            # ----------------------------------------------------
            benign_tasks = cfg["benign_tasks"] or list(suite.user_tasks.keys())
            b_summary_path = suite_dir / "summary_none.json"

            benign_loaded = False
            if resume and b_summary_path.exists():
                try:
                    with open(b_summary_path, encoding="utf-8") as f:
                        existing_b = json.load(f)
                    if len(existing_b.get("utility_results", {})) == len(benign_tasks):
                        unit_counter += len(benign_tasks)
                        pct = (unit_counter / total_units) * 100.0
                        b_avg_util = existing_b["avg_utility"]
                        b_avg_sec = existing_b["avg_security"]
                        b_tokens = existing_b["tokens"]["total"]
                        cumulative_prompt_tokens += existing_b["tokens"]["prompt"]
                        cumulative_completion_tokens += existing_b["tokens"]["completion"]
                        print(
                            f"--- [Suite {s_idx}/4: {s_name.upper()}] [Condition: BENIGN (none)] "
                            f"ALREADY COMPLETE ({len(benign_tasks)} tasks) | Progress: [{unit_counter}/{total_units}] ({pct:5.1f}%) | "
                            f"Loaded {b_tokens:,} tokens ---",
                            flush=True,
                        )
                        benign_loaded = True
                except Exception as e:
                    print(f"[WARNING] Could not load existing summary_none.json for {s_name}: {e}")
                    benign_loaded = False

            if not benign_loaded:
                benign_pipeline = GuideGplusPipeline(
                    model=model_name,
                    max_tokens=max_tokens_per_call,
                    gated=False,
                    provenance=False,
                    name="guide-undefended-local",
                )
                benign_util: dict[str, bool] = {}
                benign_sec: dict[str, bool] = {}
                benign_t0 = time.time()

                print(f"--- [Suite {s_idx}/4: {s_name.upper()}] [Condition: BENIGN (none)] ({len(benign_tasks)} tasks) ---")
                with OutputLogger(str(suite_dir)):
                    for ut_id in benign_tasks:
                        unit_counter += 1
                        pct = (unit_counter / total_units) * 100.0
                        user_task = suite.get_user_task_by_id(ut_id)

                        t_start = time.time()
                        util, sec = run_task_without_injection_tasks(
                            suite=suite,
                            agent_pipeline=benign_pipeline,
                            task=user_task,
                            logdir=suite_dir,
                            force_rerun=True,
                            benchmark_version=benchmark_version,
                        )
                        t_elapsed = time.time() - t_start
                        benign_util[ut_id] = util
                        benign_sec[ut_id] = sec

                        curr_total_prompt = cumulative_prompt_tokens + benign_pipeline.tracker.prompt_tokens
                        curr_total_comp = cumulative_completion_tokens + benign_pipeline.tracker.completion_tokens
                        curr_total = curr_total_prompt + curr_total_comp
                        curr_cny = (curr_total_prompt / 1_000_000 * 1.0) + (curr_total_comp / 1_000_000 * 4.0)

                        print(
                            f"[suite:{s_name}] [attack:none] [unit {unit_counter}/{total_units}] ({pct:5.1f}%) "
                            f"{ut_id} -> util={util} sec={sec} ({t_elapsed:4.1f}s) | "
                            f"Cumulative tokens: in={curr_total_prompt:,} out={curr_total_comp:,} tot={curr_total:,} "
                            f"(~{curr_cny:.4f} CNY)",
                            flush=True,
                        )

                        if curr_total >= TOKEN_CAP:
                            raise RuntimeError(f"ABORT: Cumulative token usage {curr_total:,} reached TOKEN_CAP {TOKEN_CAP:,}")

                cumulative_prompt_tokens += benign_pipeline.tracker.prompt_tokens
                cumulative_completion_tokens += benign_pipeline.tracker.completion_tokens

                b_avg_util = sum(benign_util.values()) / max(len(benign_util), 1)
                b_avg_sec = sum(benign_sec.values()) / max(len(benign_sec), 1)
                b_summary_data = {
                    "suite": s_name,
                    "smoke": False,
                    "benchmark_version": benchmark_version,
                    "model": model_name,
                    "attack": "none",
                    "total_tasks": len(benign_tasks),
                    "utility_results": benign_util,
                    "security_results": benign_sec,
                    "avg_utility": b_avg_util,
                    "avg_security": b_avg_sec,
                    "tokens": {
                        "prompt": benign_pipeline.tracker.prompt_tokens,
                        "completion": benign_pipeline.tracker.completion_tokens,
                        "total": benign_pipeline.tracker.total_tokens,
                        "calls": benign_pipeline.tracker.model_calls,
                        "cost_cny": benign_pipeline.tracker.cost_cny(),
                    },
                    "wall_s": time.time() - benign_t0,
                }
                with open(b_summary_path, "w", encoding="utf-8") as f:
                    json.dump(b_summary_data, f, indent=2)

                append_token_ledger(
                    ledger_path=logdir / "token_usage.jsonl",
                    suite=s_name,
                    phase_label=f"Phase {s_idx} ({s_name}:none)",
                    prompt_tokens=benign_pipeline.tracker.prompt_tokens,
                    completion_tokens=benign_pipeline.tracker.completion_tokens,
                    model=model_name,
                    utility_rate=b_avg_util,
                    security_rate=b_avg_sec,
                )

                print(
                    f"\nPHASE COMPLETE: suite='{s_name}' condition='none' | Utility: {b_avg_util*100:.1f}% | "
                    f"Tokens used: {benign_pipeline.tracker.total_tokens:,} (~{benign_pipeline.tracker.cost_cny():.4f} CNY) | "
                    f"Wall clock: {time.time()-benign_t0:.1f}s\n",
                    flush=True,
                )

            # ----------------------------------------------------
            # 2. Attack condition
            # ----------------------------------------------------
            attack_name = cfg["attack"]
            attack_tasks = cfg["attack_tasks"] or list(suite.user_tasks.keys())
            inj_tasks = list(suite.injection_tasks.keys())
            total_pairs = len(attack_tasks) * len(inj_tasks)

            a_summary_path = suite_dir / f"summary_{attack_name}.json"
            attack_loaded = False
            if resume and a_summary_path.exists():
                try:
                    with open(a_summary_path, encoding="utf-8") as f:
                        existing_a = json.load(f)
                    if len(existing_a.get("utility_results", {})) == total_pairs:
                        unit_counter += total_pairs
                        pct = (unit_counter / total_units) * 100.0
                        a_avg_util = existing_a["avg_utility"]
                        a_avg_sec = existing_a["avg_security"]
                        a_tokens = existing_a["tokens"]["total"]
                        cumulative_prompt_tokens += existing_a["tokens"]["prompt"]
                        cumulative_completion_tokens += existing_a["tokens"]["completion"]
                        print(
                            f"--- [Suite {s_idx}/4: {s_name.upper()}] [Condition: ATTACK ({attack_name})] "
                            f"ALREADY COMPLETE ({total_pairs} pairs) | Progress: [{unit_counter}/{total_units}] ({pct:5.1f}%) | "
                            f"Loaded {a_tokens:,} tokens ---",
                            flush=True,
                        )
                        attack_loaded = True
                except Exception as e:
                    print(f"[WARNING] Could not load existing summary_{attack_name}.json for {s_name}: {e}")
                    attack_loaded = False

            if not attack_loaded:
                attack_pipeline = GuideGplusPipeline(
                    model=model_name,
                    max_tokens=max_tokens_per_call,
                    gated=False,
                    provenance=False,
                    name="guide-undefended-local",
                )
                attacker = load_attack(attack_name, suite, attack_pipeline)
                attack_util: dict[str, bool] = {}
                attack_sec: dict[str, bool] = {}
                attack_t0 = time.time()

                print(f"--- [Suite {s_idx}/4: {s_name.upper()}] [Condition: ATTACK ({attack_name})] ({total_pairs} pairs) ---")
                with OutputLogger(str(suite_dir)):
                    for ut_id in attack_tasks:
                        user_task = suite.get_user_task_by_id(ut_id)
                        for inj_id in inj_tasks:
                            unit_counter += 1
                            pct = (unit_counter / total_units) * 100.0

                            t_start = time.time()
                            u_dict, s_dict = run_task_with_injection_tasks(
                                suite=suite,
                                agent_pipeline=attack_pipeline,
                                user_task=user_task,
                                attack=attacker,
                                logdir=suite_dir,
                                force_rerun=True,
                                injection_tasks=[inj_id],
                                benchmark_version=benchmark_version,
                            )
                            t_elapsed = time.time() - t_start

                            pair_key = f"{ut_id}_{inj_id}"
                            util = u_dict.get((ut_id, inj_id), False)
                            sec = s_dict.get((ut_id, inj_id), False)
                            attack_util[pair_key] = util
                            attack_sec[pair_key] = sec

                            curr_total_prompt = cumulative_prompt_tokens + attack_pipeline.tracker.prompt_tokens
                            curr_total_comp = cumulative_completion_tokens + attack_pipeline.tracker.completion_tokens
                            curr_total = curr_total_prompt + curr_total_comp
                            curr_cny = (curr_total_prompt / 1_000_000 * 1.0) + (curr_total_comp / 1_000_000 * 4.0)

                            print(
                                f"[suite:{s_name}] [attack:{attack_name}] [unit {unit_counter}/{total_units}] ({pct:5.1f}%) "
                                f"{ut_id}+{inj_id} -> util={util} sec={sec} ({t_elapsed:4.1f}s) | "
                                f"Cumulative tokens: in={curr_total_prompt:,} out={curr_total_comp:,} tot={curr_total:,} "
                                f"(~{curr_cny:.4f} CNY)",
                                flush=True,
                            )

                            if curr_total >= TOKEN_CAP:
                                raise RuntimeError(f"ABORT: Cumulative token usage {curr_total:,} reached TOKEN_CAP {TOKEN_CAP:,}")

                cumulative_prompt_tokens += attack_pipeline.tracker.prompt_tokens
                cumulative_completion_tokens += attack_pipeline.tracker.completion_tokens

                a_avg_util = sum(attack_util.values()) / max(len(attack_util), 1)
                a_avg_sec = sum(attack_sec.values()) / max(len(attack_sec), 1)
                a_summary_data = {
                    "suite": s_name,
                    "smoke": False,
                    "benchmark_version": benchmark_version,
                    "model": model_name,
                    "attack": attack_name,
                    "total_tasks": len(attack_tasks),
                    "utility_results": attack_util,
                    "security_results": attack_sec,
                    "avg_utility": a_avg_util,
                    "avg_security": a_avg_sec,
                    "tokens": {
                        "prompt": attack_pipeline.tracker.prompt_tokens,
                        "completion": attack_pipeline.tracker.completion_tokens,
                        "total": attack_pipeline.tracker.total_tokens,
                        "calls": attack_pipeline.tracker.model_calls,
                        "cost_cny": attack_pipeline.tracker.cost_cny(),
                    },
                    "wall_s": time.time() - attack_t0,
                }
                with open(a_summary_path, "w", encoding="utf-8") as f:
                    json.dump(a_summary_data, f, indent=2)

                append_token_ledger(
                    ledger_path=logdir / "token_usage.jsonl",
                    suite=s_name,
                    phase_label=f"Phase {s_idx} ({s_name}:{attack_name})",
                    prompt_tokens=attack_pipeline.tracker.prompt_tokens,
                    completion_tokens=attack_pipeline.tracker.completion_tokens,
                    model=model_name,
                    utility_rate=a_avg_util,
                    security_rate=a_avg_sec,
                )

                print(
                    f"\nPHASE COMPLETE: suite='{s_name}' condition='{attack_name}' | Utility: {a_avg_util*100:.1f}% | "
                    f"ASR (compromised): {a_avg_sec*100:.1f}% | Containment: {(1.0-a_avg_sec)*100:.1f}% | "
                    f"Tokens used: {attack_pipeline.tracker.total_tokens:,} (~{attack_pipeline.tracker.cost_cny():.4f} CNY) | "
                    f"Wall clock: {time.time()-attack_t0:.1f}s\n",
                    flush=True,
                )

            # Record in suite summary
            suite_results_summary.append({
                "suite": s_name,
                "benign_tasks": len(benign_tasks),
                "benign_util": b_avg_util,
                "attack_pairs": total_pairs,
                "attack_util": a_avg_util,
                "attack_sec": a_avg_sec,  # ASR
                "containment": 1.0 - a_avg_sec,
            })

        # ----------------------------------------------------
        # Final Summary
        # ----------------------------------------------------
        tot_time = time.time() - overall_t0
        total_tokens = cumulative_prompt_tokens + cumulative_completion_tokens
        total_cost = (cumulative_prompt_tokens / 1_000_000 * 1.0) + (cumulative_completion_tokens / 1_000_000 * 4.0)

        print("================================================================================")
        print("RUN COMPLETE — 100% (All 4 Suites Finished Cleanly)")
        print(f"Total units evaluated: {unit_counter}/{total_units} (100.0%)")
        print(f"Total tokens consumed: {total_tokens:,} (Prompt: {cumulative_prompt_tokens:,}, Output: {cumulative_completion_tokens:,})")
        print(f"Total off-peak cost: ~{total_cost:.4f} CNY (~${total_cost/7.12:.2f} USD)")
        print(f"Total wall clock time: {tot_time:.1f}s ({tot_time/60.0:.1f} mins)")
        print("================================================================================")
        print("\n| Suite | Benign Tasks | Benign Util | Attack Pairs | Attack Util | ASR (Compromised) | Containment |")
        print("|---|---|---|---|---|---|---|")
        for r in suite_results_summary:
            print(
                f"| **{r['suite'].capitalize()}** | {r['benign_tasks']} | {r['benign_util']*100:.1f}% | "
                f"{r['attack_pairs']} | {r['attack_util']*100:.1f}% | {r['attack_sec']*100:.1f}% | "
                f"{r['containment']*100:.1f}% |"
            )
        print("================================================================================\n", flush=True)

        return 0

    except Exception as exc:  # noqa: BLE001
        print(f"\nRUN FAILED: Exception occurred at unit {unit_counter}/{total_units}: {exc}", flush=True)
        import traceback

        traceback.print_exc()
        return 1
    finally:
        master_tee.close()
        sys.stdout = master_tee.stdout


def main() -> None:
    parser = argparse.ArgumentParser(description="AgentDojo Undefended Baseline Runner (Protocol v6b)")
    parser.add_argument("--smoke", action="store_true", help="Run tiny smoke test (Banking 1 task) and exit")
    parser.add_argument("--logdir", default="experiments/results/agentdojo-v6b-undefended", type=Path)
    parser.add_argument("--benchmark-version", default="v1.2.2")
    parser.add_argument("--model", default="deepseek-v4-flash")
    parser.add_argument("--max-tokens", default=1024, type=int)
    parser.add_argument("--strict-offpeak", action="store_true", default=True)
    parser.add_argument("--allow-peak", action="store_false", dest="strict_offpeak")
    parser.add_argument("--no-resume", action="store_false", dest="resume", help="Force re-run all suites from scratch")

    args = parser.parse_args()

    if args.smoke:
        code = run_smoke_test(
            logdir=args.logdir,
            benchmark_version=args.benchmark_version,
            model_name=args.model,
        )
    else:
        code = run_full_baseline(
            logdir=args.logdir,
            benchmark_version=args.benchmark_version,
            model_name=args.model,
            max_tokens_per_call=args.max_tokens,
            strict_offpeak=args.strict_offpeak,
            resume=args.resume,
        )
    sys.exit(code)


if __name__ == "__main__":
    main()
