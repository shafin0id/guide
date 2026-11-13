"""Grid-completeness check for Step 3: every expected (condition, cell) has a completed row."""

import collections
import json

from agentdojo.benchmark import get_suite

from guide_agentdojo.run_v9 import make_sample

S = "experiments/results/step3/"
samp = make_sample()
pairs = {(s, u, i) for s, v in samp.items() for u, i in v}
tasks = {(s, u, "none") for s in ("banking", "slack", "travel", "workspace") for u in get_suite("v1.2.2", s).user_tasks}
G = ["none", "strict", "cred", "flexI_cred"]
B = ["tool_filter", "spotlighting", "repeat_user_prompt", "pi_detector"]


def check(path, conds, cells):
    ok = collections.defaultdict(set)
    for line in open(path):
        r = json.loads(line)
        if r["status"] != "completed" or (r["condition"] == "tool_filter" and "impl" not in r):
            continue
        ok[r["condition"]].add((r["suite"], r["user_task"], r["injection_task"]))
    print(path.split("step3/")[1].ljust(46), len(cells), "cells, missing:", {c: len(cells - ok[c]) for c in conds})


check(S + "runs/main/rows_none_default.jsonl", G + B, tasks)
for t in ("rep2", "rep3"):
    check(S + f"runs/{t}/rows_none_default.jsonl", G, tasks)
for a in ("direct", "important_instructions"):
    check(S + f"runs/main/rows_{a}_weak.jsonl", G + B, pairs)
check(S + "runs/main/rows_guide_aware_weak.jsonl", G, pairs)
ad = collections.Counter()
for line in open(S + "runs/main/rows_adaptive_weak.jsonl"):
    r = json.loads(line)
    if r["status"] == "completed":
        ad[r["condition"]] += 1
print("adaptive completed per condition (target 30 each):", dict(ad))
rw = {json.loads(x)["key"] for x in open(S + "realworld/main/rows.jsonl") if json.loads(x)["status"] == "completed"}
print("realworld unique completed keys:", len(rw), "/ 720")
