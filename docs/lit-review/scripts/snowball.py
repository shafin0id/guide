"""One round of backward + forward snowballing (Wohlin 2014) on the core set via OpenAlex.

Core set = the included works coded closest to SQ2/SQ3 (listed in CORE). Writes
../data/snowball_candidates.jsonl: works cited by or citing a core work, published 2022+, that are not
already in records.jsonl (dedup by DOI / arXiv id / normalised title).
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

D = Path(__file__).resolve().parent.parent / "data"
M = "guide-review@example.org"
CORE = ("R1153 R1572 R1622 R1242 R1222 R0976 R0799 R1162 R0756 R0918 R1183 R1263 R1267 R1171 R1172 "
        "R2058 R2130 R1702 R1145 R0712 R0716 R2511 R1179 R1266 R2103 R0289 R0561 R0814 R0903 R1216 "
        "R0704 R2557 R0242 R0751 R1169 R0748 R2095 R0544 R0541 R0803 R0817 R0416 R2584").split()


def get(url: str) -> dict:
    for i in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": f"guide-slr (mailto:{M})"}), timeout=60) as r:
                return json.loads(r.read())
        except Exception:
            time.sleep(3 * (i + 1))
    return {}


def norm(t: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (t or "").lower())[:120]


def inv(idx):
    if not idx:
        return ""
    return " ".join(w for _, w in sorted((p, w) for w, ps in idx.items() for p in ps))


def work_of(r: dict) -> dict:
    if r.get("openalex"):
        return get(r["openalex"].replace("https://openalex.org/", "https://api.openalex.org/works/") + f"?mailto={M}")
    doi = r.get("doi") or (f"10.48550/arxiv.{r['arxiv']}" if r.get("arxiv") else "")
    if doi:
        w = get(f"https://api.openalex.org/works/doi:{doi}?mailto={M}")
        if w:
            return w
    s = get("https://api.openalex.org/works?" + urllib.parse.urlencode({"search": r["title"], "per-page": 1, "mailto": M}))
    res = s.get("results") or []
    return res[0] if res and norm(res[0].get("title")) == norm(r["title"]) else {}


def slim(w: dict, via: str, seed: str) -> dict:
    ids = w.get("ids") or {}
    doi = (w.get("doi") or "").replace("https://doi.org/", "").lower()
    arx = doi.split("arxiv.")[-1] if "arxiv." in doi else ""
    src = ((w.get("primary_location") or {}).get("source") or {}).get("display_name", "")
    return {"title": w.get("title") or "", "year": w.get("publication_year"), "doi": doi, "arxiv": arx,
            "openalex": w.get("id"), "venue": src, "abstract": inv(w.get("abstract_inverted_index")),
            "via": via, "seed": seed, "pmid": ids.get("pmid", "")}


def main() -> None:
    recs = {json.loads(l)["id"]: json.loads(l) for l in (D / "records.jsonl").open()}
    known = set()
    for r in recs.values():
        known |= {k for k in (r.get("doi"), r.get("arxiv"), norm(r["title"])) if k}
    out, seen, log = [], set(), []
    for rid in CORE:
        w = work_of(recs[rid])
        if not w:
            log.append((rid, "unresolved", 0, 0)); continue
        wid = w["id"].rsplit("/", 1)[-1]
        back = w.get("referenced_works") or []
        cands = []
        for i in range(0, len(back), 50):
            chunk = "|".join(x.rsplit("/", 1)[-1] for x in back[i:i + 50])
            cands += [("backward", x) for x in get(f"https://api.openalex.org/works?filter=openalex:{chunk}&per-page=50&mailto={M}").get("results", [])]
        fwd = get(f"https://api.openalex.org/works?filter=cites:{wid}&per-page=200&mailto={M}").get("results", [])
        cands += [("forward", x) for x in fwd]
        log.append((rid, wid, len(back), len(fwd)))
        for via, x in cands:
            s = slim(x, via, rid)
            keys = {k for k in (s["doi"], s["arxiv"], norm(s["title"])) if k}
            if (s["year"] or 0) < 2022 or keys & known or keys & seen:
                continue
            seen |= keys
            out.append(s)
        time.sleep(0.5)
    with (D / "snowball_candidates.jsonl").open("w") as fh:
        for s in out:
            fh.write(json.dumps(s) + "\n")
    with (D / "snowball_log.json").open("w") as fh:
        json.dump(log, fh, indent=0)
    print(f"core={len(CORE)} resolved={sum(1 for l in log if l[1] != 'unresolved')} "
          f"backward_refs={sum(l[2] for l in log)} forward={sum(l[3] for l in log)} new_candidates={len(out)}")


if __name__ == "__main__" and len(__import__("sys").argv) == 1:
    main()


# ---- Backward supplement via Semantic Scholar (OpenAlex holds few reference lists for arXiv preprints)
def s2_backward() -> None:
    recs = {json.loads(l)["id"]: json.loads(l) for l in (D / "records.jsonl").open()}
    known = set()
    for r in recs.values():
        known |= {k for k in (r.get("doi"), r.get("arxiv"), norm(r["title"])) if k}
    prev = [json.loads(l) for l in (D / "snowball_candidates.jsonl").open()]
    for s in prev:
        known |= {k for k in (s["doi"], s["arxiv"], norm(s["title"])) if k}
    add, n_refs = [], 0
    for rid in CORE:
        r = recs[rid]
        pid = f"arXiv:{r['arxiv']}" if r.get("arxiv") else (f"DOI:{r['doi']}" if r.get("doi") else "")
        if not pid:
            continue
        url = (f"https://api.semanticscholar.org/graph/v1/paper/{pid}/references?"
               "fields=title,year,externalIds,abstract,venue&limit=500")
        d = {}
        for i in range(6):
            try:
                with urllib.request.urlopen(url, timeout=60) as resp:
                    d = json.loads(resp.read()); break
            except Exception:
                time.sleep(8 * (i + 1))
        for item in d.get("data") or []:
            p = item.get("citedPaper") or {}
            n_refs += 1
            ex = p.get("externalIds") or {}
            s = {"title": p.get("title") or "", "year": p.get("year"), "doi": (ex.get("DOI") or "").lower(),
                 "arxiv": ex.get("ArXiv") or "", "openalex": "", "venue": p.get("venue") or "",
                 "abstract": p.get("abstract") or "", "via": "backward-s2", "seed": rid, "pmid": ""}
            keys = {k for k in (s["doi"], s["arxiv"], norm(s["title"])) if k}
            if (s["year"] or 0) < 2022 or not keys or keys & known:
                continue
            known |= keys
            add.append(s)
        time.sleep(4)
    with (D / "snowball_candidates.jsonl").open("a") as fh:
        for s in add:
            fh.write(json.dumps(s) + "\n")
    print(f"s2 backward refs={n_refs} new_candidates={len(add)}")


if __name__ == "__main__" and len(__import__("sys").argv) > 1 and __import__("sys").argv[1] == "s2":
    s2_backward()
