#!/usr/bin/env python3
"""Final Run Orchestrator (Protocol v8).

Usage:
    uv run python -u scripts/final/run_final.py --stage <stage>
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.final.progress import Progress


def run_cmd(cmd: list[str] | str, check: bool = True, shell: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, shell=shell, cwd=REPO_ROOT, text=True, capture_output=True)


def stage_m3_verify(progress: Progress) -> None:
    progress.set_total("M3", 6)
    progress.start_stage("M3", 6)

    commands = [
        (["uv", "run", "pytest", "tests/unit/test_blast_radius.py", "-q"], "full blast_radius suite run 1/3"),
        (["uv", "run", "pytest", "tests/unit/test_blast_radius.py", "-q"], "full blast_radius suite run 2/3"),
        (["uv", "run", "pytest", "tests/unit/test_blast_radius.py", "-q"], "full blast_radius suite run 3/3"),
        (["uv", "run", "pytest", "tests/unit/test_blast_radius.py::test_property_coverage_is_not_vacuous", "-q"], "isolated coverage run 1/3"),
        (["uv", "run", "pytest", "tests/unit/test_blast_radius.py::test_property_coverage_is_not_vacuous", "-q"], "isolated coverage run 2/3"),
        (["uv", "run", "pytest", "tests/unit/test_blast_radius.py::test_property_coverage_is_not_vacuous", "-q"], "isolated coverage run 3/3"),
    ]

    for cmd, desc in commands:
        t0 = time.time()
        res = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True)
        elapsed = time.time() - t0
        if res.returncode != 0:
            msg = f"{desc} -> FAILED in {elapsed:.1f}s: {res.stderr or res.stdout}"
            progress.mark("M3", msg)
            sys.stderr.write(f"Error in {desc}:\n{res.stdout}\n{res.stderr}\n")
            raise RuntimeError(f"M3 verification failed: {desc}")
        msg = f"{desc} -> PASSED in {elapsed:.1f}s"
        progress.mark("M3", msg)

    progress.finish_stage("M3")


def stage_m1(progress: Progress) -> None:
    from guide_agentdojo.compromise_replay import run_all
    run_all(progress)


def stage_m1b(progress: Progress) -> None:
    from guide_agentdojo.compromise_replay import run_m1b
    run_m1b(progress)


def stage_m2(progress: Progress) -> None:
    from guide_research.topology_theory import run_topology_v8
    run_topology_v8(progress)


def stage_numbers(progress: Progress) -> None:
    from scripts.paper.generate_numbers import generate_paper_numbers
    generate_paper_numbers(progress)


def stage_check_numbers(progress: Progress) -> None:
    from scripts.paper.generate_numbers import check_manuscript_numbers
    check_manuscript_numbers(progress)


def stage_m5_lookup(progress: Progress) -> None:
    from scripts.lit.ref_fixer import run_ref_lookups
    run_ref_lookups(progress)


def stage_m5_search(progress: Progress) -> None:
    from scripts.lit.ref_fixer import run_competitor_searches
    run_competitor_searches(progress)


def main() -> None:
    parser = argparse.ArgumentParser(description="GUIDE Protocol v8 Final Run")
    parser.add_argument(
        "--stage",
        required=True,
        choices=[
            "m3_verify",
            "m1",
            "m1b",
            "m2",
            "numbers",
            "check_numbers",
            "m5_lookup",
            "m5_search",
            "compute",
        ],
        help="Stage to execute",
    )
    args = parser.parse_args()
    progress = Progress()

    if args.stage == "m3_verify":
        stage_m3_verify(progress)
    elif args.stage == "m1":
        stage_m1(progress)
    elif args.stage == "m1b":
        stage_m1b(progress)
    elif args.stage == "m2":
        stage_m2(progress)
    elif args.stage == "numbers":
        stage_numbers(progress)
    elif args.stage == "check_numbers":
        stage_check_numbers(progress)
    elif args.stage == "m5_lookup":
        stage_m5_lookup(progress)
    elif args.stage == "m5_search":
        stage_m5_search(progress)
    elif args.stage == "compute":
        stage_m1(progress)
        stage_m1b(progress)
        stage_m2(progress)
        stage_numbers(progress)


if __name__ == "__main__":
    main()
