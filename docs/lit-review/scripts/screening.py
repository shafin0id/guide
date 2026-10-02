"""Build screening.csv (every unique record, final decision + stage + reason) and PRISMA counts.

Decisions come from: the deterministic pre-filter (records.jsonl), the title-stage include lists
(screen/title_includes_*.txt) and the abstract-stage exclusions recorded below. Title-stage excludes get a
reason code by rule (protocol §5); the human decision was include/exclude, the code is derived.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

D = Path(__file__).resolve().parent.parent / "data"
OUT = D.parent

# Abstract-stage exclusions (author decision after reading the abstract), reason code.
# Second-pass rescue of pre-filter false negatives (protocol amendment A3).
RESCUE = {"0915", "1179", "1215", "1263", "1273", "2508", "2512"}

ABSTRACT_EXCLUDE = {
    "0003": "E3", "0068": "E6", "0083": "E6", "0389": "E3", "0895": "E3", "0911": "E5",
    "0947": "E6", "1568": "E6", "1968": "E6", "0375": "E3", "0120": "E3", "0395": "E3",
    "0448": "E3", "0497": "E3", "0553": "E3", "0796": "E3", "0841": "E3", "0864": "E3",
    "1189": "E3", "2115": "E3", "2197": "E3", "2193": "E3", "0757": "E3", "0730": "E3",
    "2482": "E3",
}


def title_reason(t: str) -> str:
    t = t.lower()
    if re.search(r"survey|review|overview|perspective|position|primer|vision|outlook|sok\b|taxonomy", t):
        return "E3"
    if re.search(r"jailbreak|align|hallucin|watermark|toxic|bias|rlhf|unlearning", t):
        return "E1"
    if re.search(r"reinforcement learning|marl|robot", t) and not re.search(r"llm|language model", t):
        return "E2"
    return "E6"


def main() -> None:
    recs = [json.loads(line) for line in (D / "records.jsonl").open()]
    title_inc = set()
    for f in sorted((D / "screen").glob("title_includes_*.txt")):
        title_inc |= set(f.read_text().split())
    rows, n = [], {"prefilter_fail": 0, "title_excl": 0, "abstract_excl": 0, "included": 0}
    for r in recs:
        k = r["id"][1:]
        if r["prefilter"] == "fail" and r["id"] != "R0587" and k not in RESCUE:
            dec, stage, why = "exclude", "prefilter", title_reason(r["title"]) if re.search(
                r"llm|language model|agent", r["title"], re.I) else "E6"
            n["prefilter_fail"] += 1
        elif k not in title_inc and k not in RESCUE:
            dec, stage, why = "exclude", "title", title_reason(r["title"])
            n["title_excl"] += 1
        elif k in ABSTRACT_EXCLUDE:
            dec, stage, why = "exclude", "abstract", ABSTRACT_EXCLUDE[k]
            n["abstract_excl"] += 1
        else:
            dec, stage, why = "include", "abstract", ""
            n["included"] += 1
        rows.append([r["id"], r["title"], r["year"], r.get("venue", ""), r.get("doi", ""),
                     r.get("arxiv", ""), ";".join(r["strings"]), ";".join(r["sources"]), dec, stage, why])
    snow = json.load((D / "snowball_screened_input.json").open())
    s_inc = set((D / "screen" / "snowball_includes.txt").read_text().split())
    n.update({"snow_identified": len(snow), "snow_prefilter_fail": 0, "snow_title_excl": 0, "snow_included": 0})
    for x in snow:
        k = x["sid"][1:]
        if x["prefilter"] == "fail":
            dec, stage, why = "exclude", "snowball-prefilter", "E6"; n["snow_prefilter_fail"] += 1
        elif k not in s_inc:
            dec, stage, why = "exclude", "snowball-title", title_reason(x["title"]); n["snow_title_excl"] += 1
        else:
            dec, stage, why = "include", "snowball-title", ""; n["snow_included"] += 1
        rows.append([x["sid"], x["title"], x["year"], x.get("venue", ""), x.get("doi", ""), x.get("arxiv", ""),
                     "snowball:" + x["via"] + ":" + x["seed"], "openalex/s2", dec, stage, why])
    with (OUT / "screening.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "title", "year", "venue", "doi", "arxiv", "strings", "sources",
                    "decision", "stage", "reason"])
        w.writerows(rows)
    print(json.dumps(n))


if __name__ == "__main__":
    main()
