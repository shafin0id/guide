"""Protocol v9b runner: 15 framework applications x 4 conditions x (2 benign + 4 injected) tasks, resumable."""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import signal
import sys
import time
from pathlib import Path
from typing import Any

from guide_realworld.core import SYSTEM_DEFAULT, SYSTEM_WEAK, RunResult, Runtime, relay_suffix, render_injection
from guide_realworld.scenarios import SCENARIOS

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("v9_spend", ROOT / "src" / "guide_agentdojo" / "spend.py")
spend = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
sys.modules["v9_spend"] = spend
_spec.loader.exec_module(spend)  # type: ignore[union-attr]

OUT = ROOT / "experiments" / "results" / "step3" / "realworld"

# (app_id, framework, topology, scenario). Each scenario appears three times, once per framework.
APPS: list[tuple[str, str, str, str]] = [
    ("lg-seq-support", "langgraph", "sequential", "support"),
    ("lg-sup-finance", "langgraph", "supervisor", "finance"),
    ("lg-par-publishing", "langgraph", "parallel", "publishing"),
    ("lg-router-devops", "langgraph", "router", "devops"),
    ("lg-cyc-recruiting", "langgraph", "cyclic", "recruiting"),
    ("cr-seq-finance", "crewai", "sequential", "finance"),
    ("cr-hier-publishing", "crewai", "hierarchical", "publishing"),
    ("cr-par-devops", "crewai", "parallel", "devops"),
    ("cr-cond-recruiting", "crewai", "conditional", "recruiting"),
    ("cr-iter-support", "crewai", "iterative", "support"),
    ("ag-rr-publishing", "autogen", "roundrobin", "publishing"),
    ("ag-sel-devops", "autogen", "selector", "devops"),
    ("ag-swarm-recruiting", "autogen", "swarm", "recruiting"),
    ("ag-gfseq-support", "autogen", "graphflow_seq", "support"),
    ("ag-gfpar-finance", "autogen", "graphflow_par", "finance"),
]
CONDITIONS = {"none": None, "strict": "strict", "cred": "cred", "flexI_cred": "flexI_cred"}
TEMPLATES = ("direct", "important_instructions", "relay")
RUN_TIMEOUT_S = 420


class _Timeout(Exception):
    pass


def _alarm(_s: int, _f: Any) -> None:
    raise _Timeout(f"run exceeded {RUN_TIMEOUT_S}s")


def build(framework: str, topology: str, sc, rt, system):
    if framework == "langgraph":
        from guide_realworld.lg_apps import LGApp

        return LGApp(sc, rt, system, topology)
    if framework == "crewai":
        from guide_realworld.cr_apps import CrewApp

        return CrewApp(sc, rt, system, topology)
    from guide_realworld.ag_apps import AutoGenApp

    return AutoGenApp(sc, rt, system, topology)


def run_one(app: tuple[str, str, str, str], cond: str, kind: str, idx: int, tpl: str, rep: int = 0) -> RunResult:
    _aid, fw, topo, sid = app
    sc = SCENARIOS[sid]
    prompt = sc.benign[idx].prompt
    relay = kind == "inject" and tpl == "relay"
    injection = render_injection(tpl, sc.injections[idx].prompt) if kind == "inject" and not relay else ""
    system = SYSTEM_WEAK if kind == "inject" else SYSTEM_DEFAULT
    rt = Runtime(sc, cond, CONDITIONS[cond], prompt, injection)
    if relay:
        rt.reader_suffix = relay_suffix(sc.injections[idx].prompt)
    res = RunResult()
    try:
        application = build(fw, topo, sc, rt, system)
        if fw == "autogen":
            asyncio.run(asyncio.wait_for(application.run(prompt), RUN_TIMEOUT_S))
        else:
            signal.signal(signal.SIGALRM, _alarm)
            signal.alarm(RUN_TIMEOUT_S)
            try:
                application.run(prompt)
            finally:
                signal.alarm(0)
        res.final = application.final[-400:]
        res.usage = tuple(application.usage)  # type: ignore[assignment]
    except Exception as e:  # noqa: BLE001 - recorded, retried on resume
        res.error = f"{type(e).__name__}: {str(e)[:200]}"
        res.usage = tuple(getattr(locals().get("application"), "usage", (0, 0, 0)))  # type: ignore[assignment]
    finally:
        rt.close()
    res.events = rt.events
    res.benign_ok = bool(sc.benign[idx].check(rt.state))
    res.attack_ok = bool(sc.injections[idx].check(rt.state)) if kind == "inject" else None
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--frameworks", default="langgraph,crewai,autogen")
    ap.add_argument("--apps", default="")
    ap.add_argument("--conditions", default=",".join(CONDITIONS))
    ap.add_argument("--tag", default="main")
    ap.add_argument("--templates", default=",".join(TEMPLATES))
    ap.add_argument("--limit-tasks", type=int, default=0, help="smoke: run only the first N tasks per app")
    a = ap.parse_args(argv)
    OUT.joinpath(a.tag).mkdir(parents=True, exist_ok=True)
    rows_path = OUT / a.tag / "rows.jsonl"
    done: set[str] = set()
    if rows_path.exists():
        for line in rows_path.read_text().splitlines():
            r = json.loads(line)
            if r["status"] == "completed":
                done.add(r["key"])
    fws = set(a.frameworks.split(","))
    want = set(filter(None, a.apps.split(",")))
    tasks = [("benign", 0, "-", 0), ("benign", 1, "-", 0)] + [
        ("inject", i, t, r) for i in (0, 1) for t in a.templates.split(",") for r in range(3 if t == "relay" else 1)]
    if a.limit_tasks:
        tasks = tasks[: a.limit_tasks]
    for app in APPS:
        if app[1] not in fws or (want and app[0] not in want):
            continue
        for kind, idx, tpl, rep in tasks:
            for cond in a.conditions.split(","):
                key = f"{app[0]}|{cond}|{kind}|{idx}|{tpl}|{rep}"
                if key in done:
                    continue
                while spend.is_deepseek_peak():
                    time.sleep(120)
                try:
                    spend.check_cap("deepseek")
                except spend.SpendCapReached as e:
                    print("STOP:", e, flush=True)
                    return 3
                t0 = time.time()
                r = run_one(app, cond, kind, idx, tpl, rep)
                miss = max(r.usage[0] - r.usage[2], 0)
                usd = spend.call_cost_usd(spend.PROVIDERS["deepseek"], miss, r.usage[2], r.usage[1])
                spend.record("deepseek", f"rw:{app[0]}:{cond}", miss, r.usage[2], r.usage[1], usd)
                n_sink_att = [e for e in r.events if e["sink"] and e["attacker_value"]]
                row = {
                    "key": key, "app": app[0], "framework": app[1], "topology": app[2], "scenario": app[3],
                    "condition": cond, "kind": kind, "task": idx, "template": tpl, "rep": rep,
                    "status": "failed" if r.error else "completed", "error": r.error,
                    "benign_ok": r.benign_ok, "attack_ok": r.attack_ok, "usd": round(usd, 6),
                    "wall_s": round(time.time() - t0, 1), "n_events": len(r.events),
                    "n_denied": sum(e["decision"] == "DENY" for e in r.events),
                    "attacker_sink_attempts": len(n_sink_att),
                    "attacker_sink_agents": sorted({e["agent"] for e in n_sink_att}),
                    "events": r.events, "final": r.final,
                }
                with rows_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(row) + "\n")
                print(f"{key} -> {row['status']} benign={r.benign_ok} attack={r.attack_ok} usd={usd:.4f} "
                      f"{row['wall_s']}s {r.error or ''}", flush=True)
    print("DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
