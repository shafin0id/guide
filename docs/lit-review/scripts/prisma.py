"""PRISMA 2020 flow counts and diagram (SVG) from screening.csv and the raw search records."""
from __future__ import annotations

import collections
import csv
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent
D = OUT / "data"


def main() -> None:
    raw = sum(1 for _ in (D / "raw_records.jsonl").open())
    rows = list(csv.DictReader((OUT / "screening.csv").open()))
    db = [r for r in rows if r["id"].startswith("R")]
    sn = [r for r in rows if r["id"].startswith("S")]
    cnt = lambda rs, st: sum(r["stage"] == st and r["decision"] == "exclude" for r in rs)
    reasons = lambda rs, st: dict(collections.Counter(r["reason"] for r in rs if r["stage"] == st and r["decision"] == "exclude"))
    c = {
        "identified_database": raw, "duplicates_removed": raw - len(db), "unique": len(db),
        "prefilter_excluded": cnt(db, "prefilter"), "prefilter_reasons": reasons(db, "prefilter"),
        "title_screened": len(db) - cnt(db, "prefilter"), "title_excluded": cnt(db, "title"),
        "title_reasons": reasons(db, "title"),
        "abstract_assessed": len(db) - cnt(db, "prefilter") - cnt(db, "title"),
        "abstract_excluded": cnt(db, "abstract"), "abstract_reasons": reasons(db, "abstract"),
        "included_database": sum(r["decision"] == "include" for r in db),
        "snowball_identified": len(sn), "snowball_prefilter_excluded": cnt(sn, "snowball-prefilter"),
        "snowball_title_excluded": cnt(sn, "snowball-title"),
        "included_snowball": sum(r["decision"] == "include" for r in sn),
    }
    c["included_total"] = c["included_database"] + c["included_snowball"]
    (OUT / "prisma-counts.json").write_text(json.dumps(c, indent=1))
    boxes = [
        (40, 20, f"Records identified (OpenAlex, arXiv, Semantic Scholar; 6 strings x 3 sources, cap 200): n = {c['identified_database']}"),
        (40, 90, f"Duplicates removed: n = {c['duplicates_removed']}  ->  unique records: n = {c['unique']}"),
        (40, 160, f"Rule pre-filter (no LLM + agent terms) excluded: n = {c['prefilter_excluded']} (incl. 7 rescued false negatives re-admitted)"),
        (40, 230, f"Titles screened: n = {c['title_screened']}; excluded: n = {c['title_excluded']}  {c['title_reasons']}"),
        (40, 300, f"Abstracts assessed: n = {c['abstract_assessed']}; excluded: n = {c['abstract_excluded']}  {c['abstract_reasons']}"),
        (40, 370, f"Included from databases: n = {c['included_database']}"),
        (40, 440, f"Snowballing (1 round, 43 core works; OpenAlex forward + S2 backward): new records n = {c['snowball_identified']};"
                  f" pre-filter excl. {c['snowball_prefilter_excluded']}; title excl. {c['snowball_title_excluded']}; included {c['included_snowball']}"),
        (40, 510, f"Studies included in the review: n = {c['included_total']}  (core set coded by hand: 26; full text read for the SQ3-decisive works)"),
    ]
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1180" height="580" font-family="Helvetica,Arial,sans-serif" font-size="13">',
           '<rect width="100%" height="100%" fill="#ffffff"/>']
    for i, (x, y, t) in enumerate(boxes):
        svg.append(f'<rect x="{x}" y="{y}" width="1100" height="48" rx="6" fill="#f2f5fa" stroke="#3b5b8c"/>')
        svg.append(f'<text x="{x + 12}" y="{y + 29}" fill="#111">{t.replace("&", "and").replace("<", "").replace(">", "")}</text>')
        if i < len(boxes) - 1:
            svg.append(f'<line x1="590" y1="{y + 48}" x2="590" y2="{y + 70}" stroke="#3b5b8c" stroke-width="2"/>')
    svg.append("</svg>")
    (OUT / "prisma.svg").write_text("\n".join(svg))
    print(json.dumps(c))


if __name__ == "__main__":
    main()
