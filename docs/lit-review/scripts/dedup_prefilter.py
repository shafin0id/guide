"""Deduplicate raw records and apply the deterministic pre-filter (protocol.md §5.1-5.2).

Inputs: ../data/raw_records.jsonl. Outputs: ../data/records.jsonl (one row per unique work with
`prefilter` = pass|fail and the strings/sources that retrieved it), ../data/prefilter_audit_sample.jsonl
(100 random fails, seed 2026, for the false-negative check) and printed PRISMA counts.
"""
from __future__ import annotations

import json
import random
import re
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
LM = re.compile(r"\b(llms?|language models?|gpt|foundation models?|chatgpt|mllms?|vlms?)\b", re.I)
AGENTIC = re.compile(r"\b(ai agents?|agentic|ai-driven actions?|autonomous ai|ai systems? with tools|least autonomy)\b", re.I)
AG = re.compile(r"\b(agents?|agentic|tool[- ]?(use|using|calling|augmented)?|tools|multi-agent)\b", re.I)


def norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]", "", t.lower())[:120]


def main() -> None:
    raw = [json.loads(line) for line in (DATA / "raw_records.jsonl").open()]
    merged: dict[str, dict] = {}
    alias: dict[str, str] = {}
    for r in raw:
        keys = [k for k in (f"doi:{r['doi']}" if r.get("doi") else "",
                             f"arxiv:{r['arxiv']}" if r.get("arxiv") else "",
                             f"t:{norm_title(r['title'])}") if k and k != "t:"]
        hit = next((alias[k] for k in keys if k in alias), None)
        if hit is None:
            hit = keys[0]
            merged[hit] = {**r, "strings": set(), "sources": set()}
        m = merged[hit]
        m["strings"].add(r["string"]); m["sources"].add(r["source"])
        for f in ("doi", "arxiv", "abstract", "venue", "openalex", "s2"):
            if not m.get(f) and r.get(f):
                m[f] = r[f]
        # prefer a peer-reviewed venue over arXiv when both are known
        if m.get("venue", "").lower() in ("arxiv", "arxiv.org", "") and r.get("venue") and \
                "arxiv" not in r["venue"].lower():
            m["venue"] = r["venue"]
        for k in keys:
            alias[k] = hit
    out = []
    for i, m in enumerate(merged.values()):
        text = f"{m['title']} {m.get('abstract', '')}"
        # widened after the first audit (protocol §5.2): 4/100 false negatives used 'AI agent'/'agentic' phrasing
        ok = bool((LM.search(text) and AG.search(text)) or AGENTIC.search(text))
        out.append({**m, "id": f"R{i + 1:04d}", "strings": sorted(m["strings"]),
                    "sources": sorted(m["sources"]), "prefilter": "pass" if ok else "fail",
                    "has_abstract": bool(m.get("abstract"))})
    with (DATA / "records.jsonl").open("w") as fh:
        for r in out:
            fh.write(json.dumps(r) + "\n")
    fails = [r for r in out if r["prefilter"] == "fail"]
    random.Random(2026).shuffle(fails)
    with (DATA / "prefilter_audit_sample.jsonl").open("w") as fh:
        for r in fails[:100]:
            fh.write(json.dumps({"id": r["id"], "title": r["title"], "abstract": r["abstract"][:400]}) + "\n")
    n_pass = sum(r["prefilter"] == "pass" for r in out)
    print(f"identified={len(raw)} unique={len(out)} duplicates_removed={len(raw) - len(out)} "
          f"prefilter_pass={n_pass} prefilter_fail={len(out) - n_pass} "
          f"no_abstract={sum(not r['has_abstract'] for r in out)}")


if __name__ == "__main__":
    main()
