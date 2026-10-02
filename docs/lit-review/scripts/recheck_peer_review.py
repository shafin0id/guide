"""Re-check every extraction.csv row marked peer_reviewed=no against OpenAlex by arXiv ID / DOI /
title, to find a published venue the original single-source extraction missed (common failure:
OpenAlex/Semantic Scholar return the arXiv landing record first even when a peer-reviewed version
of the same paper exists). Writes recheck-results.csv with the live finding per row; does not
mutate extraction.csv (that happens in a second, reviewed pass).
"""
from __future__ import annotations

import csv
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "guide-slr-recheck/1.0 (mailto:guide-review@example.org)"}

NON_PEER_VENUE_MARKERS = {
    "arxiv", "arxiv (cornell university)", "", "biorxiv", "ssrn", "preprints.org",
    "techrxiv", "researchgate", "zenodo",
}


def get(url: str) -> bytes:
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return r.read()
        except Exception:
            time.sleep(2 * (i + 1))
    return b""


def openalex_by_arxiv(aid: str) -> dict:
    # OpenAlex ids arXiv works as W... but also exposes doi 10.48550/arxiv.<id>; try the OA id search
    # via the arXiv DOI, which OpenAlex resolves and links to any published location.
    doi = f"10.48550/arxiv.{aid}"
    raw = get("https://api.openalex.org/works/doi:" + urllib.parse.quote(doi) +
              "?mailto=guide-review@example.org")
    if not raw:
        return {}
    try:
        w = json.loads(raw)
    except Exception:
        return {}
    if "id" not in w:
        return {}
    return extract_best_location(w)


def openalex_by_title(title: str) -> dict:
    raw = get("https://api.openalex.org/works?" + urllib.parse.urlencode(
        {"search": title, "per-page": 3, "mailto": "guide-review@example.org"}))
    if not raw:
        return {}
    try:
        results = json.loads(raw).get("results", [])
    except Exception:
        return {}
    if not results:
        return {}
    # pick the result whose title matches most closely (first is usually best by relevance score)
    return extract_best_location(results[0])


def extract_best_location(w: dict) -> dict:
    locs = w.get("locations", []) or []
    best = None
    for loc in locs:
        src = (loc.get("source") or {})
        name = (src.get("display_name") or "").strip()
        is_oa_only = (src.get("type") or "").lower() == "repository"
        if name and name.lower() not in NON_PEER_VENUE_MARKERS and not is_oa_only:
            best = name
            break
    primary = (w.get("primary_location") or {}).get("source") or {}
    primary_name = (primary.get("display_name") or "").strip()
    return {
        "openalex_id": w.get("id", ""),
        "best_venue": best or "",
        "primary_venue": primary_name,
        "is_oa_flagged_peer_reviewed": bool(best),
        "publication_year": w.get("publication_year", ""),
        "type": w.get("type", ""),
        "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
    }


def main() -> None:
    rows = list(csv.DictReader((ROOT / "extraction.csv").open()))
    todo = [r for r in rows if r["peer_reviewed"] == "no"]
    out = []
    for i, r in enumerate(todo):
        rec = {}
        if r["arxiv"]:
            rec = openalex_by_arxiv(r["arxiv"])
        if not rec.get("best_venue") and r["title"]:
            rec2 = openalex_by_title(r["title"])
            if rec2.get("best_venue"):
                rec = rec2
            elif not rec:
                rec = rec2
        out.append({
            "citation_key": r["citation_key"],
            "title": r["title"],
            "arxiv": r["arxiv"],
            "old_venue": r["venue"],
            "found_peer_venue": rec.get("best_venue", ""),
            "found_primary_venue": rec.get("primary_venue", ""),
            "found_year": rec.get("publication_year", ""),
            "found_type": rec.get("type", ""),
            "found_doi": rec.get("doi", ""),
            "upgrade": "yes" if rec.get("best_venue") else "no",
        })
        if i % 25 == 0:
            print(i, "/", len(todo), "upgrades so far:", sum(1 for o in out if o["upgrade"] == "yes"), flush=True)
    with (ROOT / "recheck-results.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print("DONE. upgrades:", sum(1 for o in out if o["upgrade"] == "yes"), "/", len(out))


if __name__ == "__main__":
    main()
