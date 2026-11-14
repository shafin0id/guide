"""One-line progress report for all Step 3 live runs."""
import glob
import json

S = "experiments/results/step3/"
def comp(pattern, field_ok=lambda r: True):
    last = {}
    for f in glob.glob(pattern):
        for l in open(f):
            r = json.loads(l)
            if r.get("condition") == "tool_filter" and "impl" not in r and "rows_" in f and "realworld" not in f:
                continue
            last[r["key"]] = r
    ok = sum(r["status"] == "completed" for r in last.values())
    return ok, len(last) - ok
tf = lambda pat: comp(S + pat)
targets = {"benign main (97x8)": ("runs/main/rows_none_default.jsonl", 776), "benign rep2 (97x4)": ("runs/rep2/rows_none_default.jsonl", 388),
           "benign rep3 (97x4)": ("runs/rep3/rows_none_default.jsonl", 388), "direct (200x8)": ("runs/main/rows_direct_weak.jsonl", 1600),
           "important (200x8)": ("runs/main/rows_important_instructions_weak.jsonl", 1600), "guide_aware (200x4)": ("runs/main/rows_guide_aware_weak.jsonl", 800),
           "adaptive (30x4)": ("runs/main/rows_adaptive_weak.jsonl", 120), "realworld (15x12x4)": ("realworld/main/rows.jsonl", 720)}
tot = 0
for name, (p, t) in targets.items():
    ok, bad = tf(p)
    tot += ok
    print(f"{name:24s} {ok:5d}/{t:<5d} failed={bad}")
print("total completed", tot, "/ 6368")
