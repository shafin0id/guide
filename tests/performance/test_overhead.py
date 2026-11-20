"""Framework-only overhead (no model latency): signing, gate, trace and provenance per run.

Run as a script for the numbers reported in docs/experiments.md:
    PYTHONPATH=src:tests python tests/performance/test_overhead.py
"""

from __future__ import annotations

import statistics
import time

from conftest import make_script
from guide import ModelSettings, ScriptedProvider, ToolRegistry
from guide_bench.conditions import CONDITIONS, build_runtime, make_router
from guide_bench.env import Environment
from guide_bench.tasks import main_tasks

TASK = next(t for t in main_tasks() if t.task_id == "T06")
FINAL = {"vendor_count": 4}
SCRIPT = make_script({"tool": "procurement_db", "operation": "query", "args": {}}, FINAL)


def per_run_ms(cond: str, n: int = 50) -> float:
    times = []
    for _ in range(n):
        env = Environment()
        rt = build_runtime(
            CONDITIONS[cond],
            ScriptedProvider(SCRIPT),
            ToolRegistry(env.tools),
            TASK.policy(),
            make_router(CONDITIONS[cond]),
            ModelSettings(),
        )
        t0 = time.perf_counter()
        rt.run(TASK.spec())
        times.append((time.perf_counter() - t0) * 1000)
    return statistics.median(times)


def test_governance_overhead_is_small():
    base = per_run_ms("B2", 20)
    full = per_run_ms("GPLUS", 20)
    assert full - base < 50.0, f"governance overhead {full - base:.1f} ms per 3-step run"


if __name__ == "__main__":
    for c in ("B1", "B2", "P", "GPLUS"):
        print(f"{c}: {per_run_ms(c, 200):.2f} ms median per 3-step run (scripted model)")
