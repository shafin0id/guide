"""Run the frozen search strings (protocol.md §3) against OpenAlex, arXiv and DBLP.

Writes raw records to ../data/raw_records.jsonl and one log row per (string, source) to
../search-log.csv. Standard library only, so it runs without the project venv.
Usage: python3 docs/lit-review/scripts/search.py
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
DATA = OUT / "data"
CAP = 200
MAILTO = "guide-review@example.org"
UA = {"User-Agent": f"guide-slr/1.0 (mailto:{MAILTO})"}

# Protocol strings, translated per source. Logical content is identical to protocol.md §3.
STRINGS = {
    "S1": {
        "openalex": '("multi-agent" OR "multi agent" OR agentic) AND ("large language model" OR LLM) AND (orchestration OR routing OR delegation OR "hand-off" OR handoff)',
        "arxiv": '(abs:"multi-agent" OR abs:"multi agent" OR abs:agentic) AND (abs:"large language model" OR abs:LLM) AND (abs:orchestration OR abs:routing OR abs:delegation OR abs:"hand-off" OR abs:handoff)',
        "dblp": "multi-agent|agentic llm|language orchestration|routing|delegation|handoff",
    },
    "S2": {
        "openalex": '(LLM OR "language model") AND agent AND ("prompt injection" OR "tool misuse" OR privilege OR "confused deputy" OR "compromised agent")',
        "arxiv": '(abs:LLM OR abs:"language model") AND abs:agent AND (abs:"prompt injection" OR abs:"tool misuse" OR abs:privilege OR abs:"confused deputy" OR abs:"compromised agent")',
        "dblp": "agent|agents injection|privilege|deputy|compromised llm|language",
    },
    "S3": {
        "openalex": '(LLM OR agent) AND ("information flow" OR taint OR capability OR "least privilege" OR "access control" OR "policy enforcement")',
        "arxiv": '(abs:LLM OR abs:agent) AND (abs:"information flow" OR abs:taint OR abs:capability OR abs:"least privilege" OR abs:"access control" OR abs:"policy enforcement")',
        "dblp": "llm|agent|agents information-flow|taint|privilege|access-control|policy-enforcement",
    },
    "S4": {
        "openalex": '(LLM OR agent) AND ("static analysis" OR reachability OR "blast radius" OR "formal verification" OR soundness)',
        "arxiv": '(abs:LLM OR abs:agent) AND (abs:"static analysis" OR abs:reachability OR abs:"blast radius" OR abs:"formal verification" OR abs:soundness)',
        "dblp": "llm|agent|agents static-analysis|reachability|blast|verification|soundness",
    },
    "S5": {
        "openalex": '("LLM agent" OR "tool use") AND (benchmark OR evaluation) AND (security OR "policy compliance" OR safety)',
        "arxiv": '(abs:"LLM agent" OR abs:"tool use") AND (abs:benchmark OR abs:evaluation) AND (abs:security OR abs:"policy compliance" OR abs:safety)',
        "dblp": "agent|agents|tool benchmark|evaluation security|safety|compliance llm|language",
    },
    "S6": {
        "openalex": '(LLM OR agent) AND (provenance OR "audit trail" OR traceability OR "tamper-evident" OR signature)',
        "arxiv": '(abs:LLM OR abs:agent) AND (abs:provenance OR abs:"audit trail" OR abs:traceability OR abs:"tamper-evident" OR abs:signature)',
        "dblp": "llm|agent|agents provenance|audit|traceability|tamper|signature",
    },
}


def get(url: str, tries: int = 4) -> bytes:
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except Exception:  # transient network / 429
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"failed: {url}")


def inv_abstract(idx: dict | None) -> str:
    if not idx:
        return ""
    pos = sorted((p, w) for w, ps in idx.items() for p in ps)
    return " ".join(w for _, w in pos)


def openalex(q: str) -> tuple[list[dict], int]:
    recs, total, page = [], 0, 1
    while len(recs) < CAP:
        url = "https://api.openalex.org/works?" + urllib.parse.urlencode({
            "search": q, "filter": "from_publication_date:2022-01-01",
            "per-page": 100, "page": page, "mailto": MAILTO})
        d = json.loads(get(url))
        total = d["meta"]["count"]
        for w in d["results"]:
            loc = (w.get("primary_location") or {}).get("source") or {}
            ids = w.get("ids") or {}
            recs.append({
                "title": w.get("title") or "", "year": w.get("publication_year"),
                "doi": (w.get("doi") or "").replace("https://doi.org/", "").lower(),
                "openalex": w.get("id"), "venue": loc.get("display_name") or "",
                "type": w.get("type"), "abstract": inv_abstract(w.get("abstract_inverted_index")),
                "authors": "; ".join(a["author"]["display_name"] for a in w.get("authorships", [])[:6]),
                "arxiv": "", "pmid": ids.get("pmid", "")})
        if not d["results"] or page * 100 >= total:
            break
        page += 1
        time.sleep(1)
    return recs[:CAP], total


ATOM = "{http://www.w3.org/2005/Atom}"


def arxiv(q: str) -> tuple[list[dict], int]:
    full = f"({q}) AND submittedDate:[202201010000 TO 202612312359]"
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({
        "search_query": full, "start": 0, "max_results": CAP, "sortBy": "relevance"})
    root = ET.fromstring(get(url))
    total = int(root.find("{http://a9.com/-/spec/opensearch/1.1/}totalResults").text)
    recs = []
    for e in root.findall(f"{ATOM}entry"):
        aid = e.find(f"{ATOM}id").text.rsplit("/abs/", 1)[-1]
        aid = aid.split("v")[0] if "v" in aid else aid
        doi = e.find("{http://arxiv.org/schemas/atom}doi")
        recs.append({
            "title": " ".join(e.find(f"{ATOM}title").text.split()),
            "year": int(e.find(f"{ATOM}published").text[:4]),
            "doi": (doi.text.lower() if doi is not None else ""), "openalex": "",
            "venue": "arXiv", "type": "preprint",
            "abstract": " ".join(e.find(f"{ATOM}summary").text.split()),
            "authors": "; ".join(a.find(f"{ATOM}name").text for a in e.findall(f"{ATOM}author")[:6]),
            "arxiv": aid, "pmid": ""})
    time.sleep(3)
    return recs, total


def dblp(q: str) -> tuple[list[dict], int]:
    url = "https://dblp.org/search/publ/api?" + urllib.parse.urlencode({"q": q, "format": "json", "h": CAP})
    d = json.loads(get(url))["result"]["hits"]
    recs = []
    for h in d.get("hit", []):
        i = h["info"]
        y = int(i.get("year", 0) or 0)
        if y < 2022:
            continue
        au = i.get("authors", {}).get("author", [])
        au = au if isinstance(au, list) else [au]
        ee = i.get("ee", "")
        ee = ee[0] if isinstance(ee, list) else ee
        arx = ee.rsplit("/abs/", 1)[-1] if "arxiv.org/abs/" in ee else ""
        recs.append({"title": i.get("title", "").rstrip("."), "year": y,
                     "doi": i.get("doi", "").lower(), "openalex": "", "venue": i.get("venue", ""),
                     "type": i.get("type", ""), "abstract": "", "arxiv": arx, "pmid": "",
                     "authors": "; ".join(a.get("text", "") for a in au[:6])})
    time.sleep(2)
    return recs, int(d.get("@total", 0))


def main() -> None:
    DATA.mkdir(exist_ok=True)
    today = dt.date.today().isoformat()
    log = []
    with (DATA / "raw_records.jsonl").open("w") as fh:
        for sid, per in STRINGS.items():
            for src, fn in (("openalex", openalex), ("arxiv", arxiv), ("dblp", dblp)):
                recs, total = fn(per[src])
                for r in recs:
                    r.update(string=sid, source=src)
                    fh.write(json.dumps(r) + "\n")
                log.append([today, sid, src, per[src], total, len(recs)])
                print(sid, src, total, len(recs), flush=True)
    with (OUT / "search-log.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "string", "source", "query_as_sent", "hits_reported", "records_retrieved"])
        w.writerows(log)


if __name__ == "__main__":
    main()
