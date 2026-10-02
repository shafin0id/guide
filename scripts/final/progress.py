#!/usr/bin/env python3
"""Final Run Progress Tracker and Logger (Protocol v8).

Maintains experiments/results/final-v8/progress.json and writes live log lines
to stdout and experiments/results/final-v8/run.log.
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
import time
from pathlib import Path
from typing import Any

STAGE_WEIGHTS: dict[str, float] = {
    "M3": 5.0,
    "M1": 30.0,
    "M1b": 2.0,
    "M2": 13.0,
    "M5": 15.0,
    "M4": 25.0,
    "M6": 10.0,
}

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_OUT_DIR = REPO_ROOT / "experiments" / "results" / "final-v8"


class Progress:
    """Thread-safe / process-safe progress tracker backed by JSON."""

    def __init__(self, out_dir: Path | str | None = None) -> None:
        self.out_dir = Path(out_dir) if out_dir else DEFAULT_OUT_DIR
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.ledger_path = self.out_dir / "progress.json"
        self.log_path = self.out_dir / "run.log"
        self._stage_start_times: dict[str, float] = {}
        self._ensure_ledger()

    def _ensure_ledger(self) -> dict[str, Any]:
        if not self.ledger_path.exists():
            data: dict[str, Any] = {
                stage: {
                    "done": 0,
                    "total": 0,
                    "started_utc": None,
                    "finished_utc": None,
                }
                for stage in STAGE_WEIGHTS
            }
            self._save_ledger(data)
            return data
        try:
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for stage in STAGE_WEIGHTS:
                    if stage not in data:
                        data[stage] = {
                            "done": 0,
                            "total": 0,
                            "started_utc": None,
                            "finished_utc": None,
                        }
                return data
        except Exception:
            data = {
                stage: {
                    "done": 0,
                    "total": 0,
                    "started_utc": None,
                    "finished_utc": None,
                }
                for stage in STAGE_WEIGHTS
            }
            self._save_ledger(data)
            return data

    def _load_ledger(self) -> dict[str, Any]:
        return self._ensure_ledger()

    def _save_ledger(self, data: dict[str, Any]) -> None:
        temp_path = self.ledger_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        temp_path.replace(self.ledger_path)

    def overall_percentage(self, data: dict[str, Any] | None = None) -> float:
        if data is None:
            data = self._load_ledger()
        pct = 0.0
        for stage, weight in STAGE_WEIGHTS.items():
            stage_info = data.get(stage, {})
            done = stage_info.get("done", 0)
            total = stage_info.get("total", 0)
            if total > 0:
                pct += weight * min(1.0, max(0.0, done / total))
        return pct

    def _log(self, text: str) -> None:
        print(text, flush=True)
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(text + "\n")
        except Exception as e:
            sys.stderr.write(f"Warning: could not write to run.log: {e}\n")

    def start_stage(self, stage: str, total: int | None = None) -> None:
        data = self._load_ledger()
        if stage not in data:
            data[stage] = {"done": 0, "total": 0, "started_utc": None, "finished_utc": None}
        if total is not None:
            data[stage]["total"] = total
        data[stage]["done"] = 0
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        data[stage]["started_utc"] = now_iso
        data[stage]["finished_utc"] = None
        self._save_ledger(data)
        self._stage_start_times[stage] = time.time()
        stage_total = data[stage].get("total", 0)
        self._log(f"===== {stage} START: {stage_total} units =====")

    def finish_stage(self, stage: str) -> None:
        data = self._load_ledger()
        if stage not in data:
            data[stage] = {"done": 0, "total": 0, "started_utc": None, "finished_utc": None}
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        data[stage]["finished_utc"] = now_iso
        self._save_ledger(data)
        start_t = self._stage_start_times.get(stage)
        elapsed_str = f" in {time.time() - start_t:.1f}s" if start_t else ""
        done = data[stage].get("done", 0)
        total = data[stage].get("total", 0)
        self._log(f"===== {stage} DONE: {done}/{total}{elapsed_str} =====")

    def set_total(self, stage: str, total: int) -> None:
        data = self._load_ledger()
        if stage not in data:
            data[stage] = {"done": 0, "total": total, "started_utc": None, "finished_utc": None}
        else:
            data[stage]["total"] = total
        self._save_ledger(data)

    def mark(self, stage: str, message: str, step: int = 1) -> None:
        data = self._load_ledger()
        if stage not in data:
            data[stage] = {"done": 0, "total": 0, "started_utc": None, "finished_utc": None}
        data[stage]["done"] += step
        if not data[stage].get("started_utc"):
            data[stage]["started_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if data[stage]["total"] > 0 and data[stage]["done"] >= data[stage]["total"] and not data[stage].get("finished_utc"):
            data[stage]["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self._save_ledger(data)

        done = data[stage]["done"]
        total = data[stage]["total"]
        stage_pct = (done / total * 100.0) if total > 0 else 0.0
        overall_pct = self.overall_percentage(data)

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Format example:
        # [2026-10-03 10:12:44] [overall  41.7%] [M1  412/949  43.4%] banking user_task_3 x injection_task_2 -> CONTAINED (sink calls denied 1/1)
        line = (
            f"[{now_str}] "
            f"[overall {overall_pct:5.1f}%] "
            f"[{stage:<3} {done:>4}/{total:<4} {stage_pct:5.1f}%] "
            f"{message}"
        )
        self._log(line)

    def show(self) -> None:
        data = self._load_ledger()
        overall = self.overall_percentage(data)
        print(f"Overall Completion: {overall:.1f}%")
        print("-" * 55)
        print(f"{'Stage':<6} {'Weight':<8} {'Done':<6} {'Total':<6} {'Stage %':<10} {'Started':<20}")
        print("-" * 55)
        for stage, weight in STAGE_WEIGHTS.items():
            info = data.get(stage, {})
            done = info.get("done", 0)
            total = info.get("total", 0)
            stage_pct = (done / total * 100.0) if total > 0 else 0.0
            started = info.get("started_utc") or "-"
            if started != "-":
                started = started[:19]
            print(f"{stage:<6} {weight:<8.1f} {done:<6} {total:<6} {stage_pct:<10.1f} {started:<20}")
        print("-" * 55)


def main() -> None:
    parser = argparse.ArgumentParser(description="GUIDE Protocol v8 Progress Tracker")
    parser.add_argument("--set-total", nargs=2, metavar=("STAGE", "TOTAL"), help="Set total units for stage")
    parser.add_argument("--mark", nargs=2, metavar=("STAGE", "MSG"), help="Increment done and log message")
    parser.add_argument("--show", action="store_true", help="Show current progress")
    parser.add_argument("--start", metavar="STAGE", help="Mark stage start banner")
    parser.add_argument("--finish", metavar="STAGE", help="Mark stage finish banner")

    args = parser.parse_args()
    p = Progress()

    if args.set_total:
        stage, total_s = args.set_total
        p.set_total(stage, int(total_s))
        print(f"Set {stage} total to {total_s}")
    elif args.mark:
        stage, msg = args.mark
        p.mark(stage, msg)
    elif args.start:
        p.start_stage(args.start)
    elif args.finish:
        p.finish_stage(args.finish)
    elif args.show:
        p.show()
    else:
        p.show()


if __name__ == "__main__":
    main()
