"""W1 diagnosis: replay all 949 pairs and list the admitted (EXECUTED) attacker sink calls."""

import collections
import json
from pathlib import Path

from guide_agentdojo import compromise_replay as cr

out = Path(__file__).resolve().parents[2] / "experiments" / "results" / "v9" / "w1"
out.mkdir(parents=True, exist_ok=True)
rows = [cr.replay_pair(s, u, i) for s, u, i in cr.iter_grid()]
(out / "m1_rows_strict.json").write_text(json.dumps(rows))
c = collections.Counter()
for r in rows:
    if r["outcome"] == "EXECUTED":
        for cl in r["call_records"]:
            if cl["is_sink"] and cl["runtime_decision"] != "DENY":
                c[(r["suite"], r["injection_task_id"], cl["function"], cl["admitted_reason"], json.dumps(cl["args"])[:80])] += 1
for k, v in sorted(c.items()):
    print(v, k)
print(collections.Counter(r["outcome"] for r in rows))
