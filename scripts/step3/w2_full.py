"""Full-grid (949 pairs) assumed-compromise containment per enforcement variant, plus the residual uncontained cases.

Why 588 of 949: a pair is in scope only if the injection goal's ground-truth calls contain at least one sink
(write-effect or external) call. The other pairs have nothing to contain: their goals are read-only.
"""

from __future__ import annotations

import collections
import json
from pathlib import Path

from agentdojo.benchmark import get_suite
from w2_variants import VARIANT_ORDER, containment, split_tasks  # type: ignore[import-not-found]

from guide_agentdojo import compromise_replay as cr
from guide_agentdojo.specs import DOJO_TOOL_SECURITY

OUT = Path(__file__).resolve().parents[2] / "experiments" / "results" / "step3" / "w2"


def main() -> None:
    grid = cr.iter_grid()
    splits = {s: split_tasks(get_suite("v1.2.2", s)) for s in cr.SUITES}
    res: dict = {"grid": len(grid)}
    scope = collections.Counter()
    residual: dict[str, list] = {}
    for v in VARIANT_ORDER:
        by = {s: [0, 0] for s in cr.SUITES}
        resid = collections.Counter()
        part = {"dev": [0, 0], "heldout": [0, 0]}
        for s, u, i in grid:
            o = containment(v, s, u, i)
            if o is None:
                scope["out_of_scope"] += v == "strict"
                continue
            scope["in_scope"] += v == "strict"
            by[s][1] += 1
            by[s][0] += o == "CONTAINED"
            p = "dev" if u in splits[s][0] else "heldout"
            part[p][1] += 1
            part[p][0] += o == "CONTAINED"
            if o != "CONTAINED":
                suite, env = cr._get_suite_and_env(s)
                gt = suite.injection_tasks[i].ground_truth(env)
                sinks = [c.function for c in gt if (x := DOJO_TOOL_SECURITY.get(c.function)) and (x[0] or x[1])]
                resid[(s, i, ",".join(sorted(set(sinks))))] += 1
        res[v] = {"by_suite": by, "total": [sum(x[0] for x in by.values()), sum(x[1] for x in by.values())], "split": part}
        residual[v] = [[*k, n] for k, n in sorted(resid.items())]
        print(v, res[v]["total"], flush=True)
    res["scope"] = dict(scope)
    res["residual"] = residual
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "full_grid.json").write_text(json.dumps(res, indent=1))
    print("scope", dict(scope))
    for v in ("strict", "cred", "flexI_cred"):
        print(v, residual[v])


if __name__ == "__main__":
    main()
