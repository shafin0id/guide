"""Verify every must-check reference (plan L3) against a live bibliographic source.

DOI -> Crossref; arXiv id -> arXiv API; otherwise OpenAlex title search. Writes ../must-check.csv with
what the source returned, so title/author/year/venue can be compared with how we cite the work.
"""
from __future__ import annotations

import csv
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "guide-slr/1.0 (mailto:guide-review@example.org)"}

# key, how cited, identifier (doi:/arxiv:/title:)
ITEMS = [
    ("auer2002", "Auer et al. 2002 MLJ", "doi:10.1023/A:1013689704352"),
    ("becker2026", "Becker et al. 2026 EACL Findings", "doi:10.18653/v1/2026.findings-eacl.268"),
    ("bernstein2012", "Bernstein et al. 2012 JCE", "doi:10.1007/s13389-012-0027-1"),
    ("cheney2009", "Cheney et al. 2009 FnT DB", "doi:10.1561/1900000006"),
    ("collini2025", "Collini et al. 2025 MARVEL", "arxiv:2505.11963"),
    ("cuadros2026", "Cuadros et al. 2026", "arxiv:2605.04264"),
    ("dang2025", "Dang et al. 2025 NeurIPS", "title:Multi-agent collaboration via evolving orchestration"),
    ("dash2026", "Dash et al. 2026", "arxiv:2606.04329"),
    ("guo2026", "Guo et al. 2026 AAAI MCP-AgentBench", "doi:10.1609/aaai.v40i37.40347"),
    ("hevner2004", "Hevner et al. 2004 MISQ", "doi:10.2307/25148625"),
    ("jamshidi2026", "Jamshidi et al. 2026", "arxiv:2606.07937"),
    ("ji2025", "Ji et al. 2025 ACL Findings", "doi:10.18653/v1/2025.findings-acl.78"),
    ("kaufmann2012", "Kaufmann et al. 2012 AISTATS", "title:On Bayesian upper confidence bounds for bandit problems"),
    ("lamalfa2025", "La Malfa et al. 2025", "arxiv:2505.21298"),
    ("lam2026", "Lam et al. 2026 SSGM", "arxiv:2603.11768"),
    ("liu2024", "Liu et al. 2024 USENIX Sec", "title:Formalizing and Benchmarking Prompt Injection Attacks and Defenses"),
    ("maloyan2026", "Maloyan & Namiot 2026", "arxiv:2601.17548"),
    ("mohammadi2025", "Mohammadi et al. 2025 KDD", "doi:10.1145/3711896.3736570"),
    ("park2023", "Park et al. 2023 UIST", "doi:10.1145/3586183.3606763"),
    ("pasupuleti2026", "Pasupuleti et al. 2026 ICAISET", "doi:10.1109/ICAISET66439.2026.11541969"),
    ("peffers2007", "Peffers et al. 2007 JMIS", "doi:10.2753/MIS0742-1222240302"),
    ("tallam2026", "Tallam 2026", "arxiv:2605.05440"),
    ("triedman2025", "Triedman et al. 2025 COLM", "arxiv:2503.12188"),
    ("wang2024", "Wang et al. 2024 FCS", "doi:10.1007/s11704-024-40231-1"),
    ("wang2025macca", "Wang et al. 2025a MACCA TMLR", "title:MACCA: Offline Multi-agent Reinforcement Learning with Causal Credit Assignment"),
    ("wu2023", "Wu et al. 2023 AutoGen", "arxiv:2308.08155"),
    ("yu2025", "Yu et al. 2025 EMNLP Findings", "doi:10.18653/v1/2025.findings-emnlp.246"),
    ("zhang2025icra", "Zhang et al. 2025 ICRA", "arxiv:2503.09621"),
    ("zhou2024", "Zhou et al. 2024 WebArena ICLR", "arxiv:2307.13854"),
    ("debenedetti2024", "AgentDojo NeurIPS 2024 D&B", "arxiv:2406.13352"),
    ("zhan2024", "InjecAgent ACL Findings 2024", "arxiv:2403.02691"),
    ("greshake2023", "Greshake et al. AISec 2023", "arxiv:2302.12173"),
    ("debenedetti2025", "CaMeL 2025", "arxiv:2503.18813"),
    ("yao2024", "tau-bench 2024", "arxiv:2406.12045"),
    ("costa2025", "FIDES 2025", "arxiv:2505.23643"),
    ("shi2025", "Progent 2025", "arxiv:2504.11703"),
    ("wu2025isolategpt", "IsolateGPT NDSS 2025", "arxiv:2403.04960"),
    ("wang2025agentspec", "AgentSpec 2025", "arxiv:2503.18666"),
    ("agentaudit2026", "Agent Audit", "arxiv:2603.22853"),
    ("capmas2026", "CAPMAS", "arxiv:2609.06500"),
    ("safeflow2026", "SafeFlow", "arxiv:2607.25255"),
    ("paul2026", "Paul & Nandy 2026 Beyond Single-Model Injection", "arxiv:2609.22949"),
    ("safin2026", "Safin et al. 2026 IEEE CARS", "arxiv:2609.17648"),
    ("containmentbench2026", "ContainmentBench", "arxiv:2607.23999"),
    ("tamas2025", "TAMAS", "arxiv:2511.05269"),
    ("backes2018", "Backes et al. 2018 FMCAD Zelkova", "title:Semantic-based Automated Reasoning for AWS Access Policies using SMT"),
    ("page2021", "PRISMA 2020, Page et al. 2021 BMJ", "doi:10.1136/bmj.n71"),
    ("wohlin2014", "Wohlin 2014 EASE snowballing", "doi:10.1145/2601248.2601268"),
    ("kitchenham2007", "Kitchenham & Charters 2007 EBSE tech report", "title:Guidelines for performing Systematic Literature Reviews in Software Engineering"),
    ("saltzer1975", "Saltzer & Schroeder 1975", "doi:10.1109/PROC.1975.9939"),
    ("denning1976", "Denning 1976 CACM lattice IFC", "doi:10.1145/360051.360056"),
]


def get(url: str) -> bytes:
    for i in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return r.read()
        except Exception:
            time.sleep(3 * (i + 1))
    return b""


def crossref(doi: str) -> dict:
    raw = get("https://api.crossref.org/works/" + urllib.parse.quote(doi))
    if not raw:
        return {}
    m = json.loads(raw)["message"]
    au = "; ".join(f"{a.get('family', '')}" for a in m.get("author", [])[:4])
    y = (m.get("issued", {}).get("date-parts") or [[None]])[0][0]
    return {"title": (m.get("title") or [""])[0], "authors": au, "year": y,
            "venue": (m.get("container-title") or [""])[0], "doi": doi}


A = "{http://www.w3.org/2005/Atom}"


def arxiv(aid: str) -> dict:
    raw = get("https://export.arxiv.org/api/query?id_list=" + aid)
    if not raw:
        return {}
    e = ET.fromstring(raw).find(f"{A}entry")
    if e is None or e.find(f"{A}title") is None:
        return {}
    j = e.find("{http://arxiv.org/schemas/atom}journal_ref")
    d = e.find("{http://arxiv.org/schemas/atom}doi")
    time.sleep(3)
    return {"title": " ".join(e.find(f"{A}title").text.split()),
            "authors": "; ".join(a.find(f"{A}name").text for a in e.findall(f"{A}author")[:4]),
            "year": e.find(f"{A}published").text[:4],
            "venue": j.text if j is not None else "arXiv", "doi": d.text if d is not None else ""}


def openalex(title: str) -> dict:
    raw = get("https://api.openalex.org/works?" + urllib.parse.urlencode(
        {"search": title, "per-page": 1, "mailto": "guide-review@example.org"}))
    if not raw or not json.loads(raw)["results"]:
        return {}
    w = json.loads(raw)["results"][0]
    src = ((w.get("primary_location") or {}).get("source") or {}).get("display_name", "")
    return {"title": w.get("title"), "year": w.get("publication_year"), "venue": src,
            "authors": "; ".join(a["author"]["display_name"] for a in w["authorships"][:4]),
            "doi": (w.get("doi") or "").replace("https://doi.org/", "")}


def main() -> None:
    rows = []
    for key, cited, ident in ITEMS:
        kind, val = ident.split(":", 1)
        rec = {"doi": crossref, "arxiv": arxiv, "title": openalex}[kind](val)
        rows.append([key, cited, ident, "found" if rec else "NOT FOUND", rec.get("title", ""),
                     rec.get("authors", ""), rec.get("year", ""), rec.get("venue", ""), rec.get("doi", "")])
        print(key, rows[-1][3], (rec.get("title") or "")[:70], flush=True)
    with (OUT / "must-check.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["key", "as_cited", "identifier", "status", "found_title", "found_authors",
                    "found_year", "found_venue", "found_doi"])
        w.writerows(rows)


if __name__ == "__main__":
    main()
