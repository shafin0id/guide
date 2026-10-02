"""Build the paper's final reference list (not the SLR corpus).

Inputs : references.bib (81 verified entries), docs/lit-review/extraction.csv (721 corpus).
Outputs: references-final.bib, docs/references-final.md.
Rule   : <=20% non-peer-reviewed; preprints kept only when novelty-critical or must-cite
         with no peer-reviewed version. Corpus picks are fetched by DOI (doi.org
         content negotiation) so authors/venue come from the publisher, not OpenAlex.
"""
import csv, json, re, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BIB = (ROOT / "references.bib").read_text()

# (group, use-in-paper) -> keys from references.bib, all peer-reviewed venues
BIB_PR = {
    ("Method & foundations", "§3 Method, §4 Design"): [
        "saltzer1975", "denning1976", "cheney2009", "bernstein2012", "auer2002",
        "kaufmann2012", "backes2018", "hevner2004", "peffers2007", "page2021", "wohlin2014"],
    ("LLM agents & multi-agent systems", "§1 Intro, §2.1"): [
        "park2023", "wang2024", "guo2026", "dang2025", "wu2023", "zhou2024",
        "lamalfa2025", "mohammadi2025", "becker2026", "ji2025", "yu2025",
        "zhang2025icra", "wang2025macca"],
    ("Agent security: attacks, defences, benchmarks", "§2.2-2.4, §5 Evaluation"): [
        "debenedetti2024", "zhan2024", "greshake2023", "liu2024", "debenedetti2025",
        "wu2025isolategpt", "wang2025agentspec", "asb2024", "saga2025", "atag2025",
        "promptinfection2024", "gsafeguard2025", "blindguard2025", "tamas2025",
        "paul2026", "safin2026", "pasupuleti2026"],
}
# Non-peer-reviewed, kept on purpose (cap 20). Reason shown in the table.
BIB_PP = {
    "parisel2026leastautonomy": "closest prior work; decides C3 novelty",
    "muruaga2026boundedagents": "closest prior work; same compromise protocol",
    "moon2026containment": "closest prior work; mechanised proof (limitation)",
    "camelot2026": "static per-plan checking (Table 1)",
    "agentflow2026adg": "static code-level analysis (Table 1)",
    "agentaudit2026": "static config scanning (Table 1)",
    "matra2026": "attack-tree modelling (Table 1)",
    "miniscope2025": "least-privilege synthesis (Table 1)",
    "aethelgard2026": "learned capability scoping (Table 1)",
    "shi2025": "Progent: privilege control baseline (Table 1)",
    "costa2025": "FIDES: IFC baseline (Table 1)",
    "capmas2026": "attenuating delegation tokens (Table 1)",
    "safeflow2026": "multi-agent taint IFC (Table 1)",
    "containmentbench2026": "multi-agent containment benchmark (Table 1)",
    "ajar2026": "open-privilege metric (RQ evaluation)",
    "fiducia2026": "hand-off attenuation evidence (RQ3 discussion)",
    "proposesdisposes2026": "pre-registered ablation exemplar (Method)",
    "triedman2025": "MAS arbitrary-code execution (Intro); COLM venue unverified",
    "yao2024": "tau-bench (Evaluation); venue unverified",
    "kitchenham2007": "SLR guideline (technical report)",
}
# Peer-reviewed corpus additions: extraction.csv id -> group
CORPUS = {
    "LLM agents & multi-agent systems": ["R0086", "R0409", "R0058", "R0217", "R0094", "R2607"],
    "Agent security: attacks, defences, benchmarks": [
        "R0563", "R0576", "R0580", "R0585", "R0639", "R0732", "R0749", "R0897", "R0902",
        "R0989", "R2749", "S0337",
        "R0718", "S0288", "S0362", "R2218", "R0912", "R2104", "R2266", "S0248",
        "R1280", "R1664", "S0353", "R2242", "R0492", "R0922",
        "S0368", "S0372", "S0366", "R0971", "S0598", "S0607", "S0444", "S0430", "R2074",
        "R1265", "R2206", "R0605", "R2684", "R0894", "R0872",
        "S0047", "S0075", "S0003"],
}
USE = {"LLM agents & multi-agent systems": "§1 Intro, §2.1",
       "Agent security: attacks, defences, benchmarks": "§2.2-2.4, §5 Evaluation"}


def bib_entry(key):
    m = re.search(r"(@\w+\{" + re.escape(key) + r",.*?\n\})", BIB, re.S)
    return m.group(1) if m else None


def field(entry, name):
    m = re.search(name + r"\s*=\s*\{+(.+?)\}+\s*,?\n", entry, re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def fetch_doi(doi):
    req = urllib.request.Request("https://doi.org/" + doi,
                                 headers={"Accept": "application/x-bibtex", "User-Agent": "guide-slr/1.0"})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.read().decode("utf-8", "replace").strip()
        except Exception:
            time.sleep(2)
    return None


def main():
    rows = {r["id"]: r for r in csv.DictReader(open(ROOT / "docs/lit-review/extraction.csv"))}
    out_bib, table, missing = [], [], []
    n_pr = n_pp = 0
    for (grp, use), keys in BIB_PR.items():
        for k in keys:
            e = bib_entry(k)
            if not e:
                missing.append(k); continue
            out_bib.append(e); n_pr += 1
            table.append((grp, k, field(e, "title"), field(e, "year"),
                          field(e, "booktitle") or field(e, "journal") or field(e, "note")[:60], "PR", use))
    for k, why in BIB_PP.items():
        e = bib_entry(k)
        if not e:
            missing.append(k); continue
        out_bib.append(e); n_pp += 1
        table.append(("Preprints kept (novelty-critical)", k, field(e, "title"), field(e, "year"),
                      "arXiv / grey", "PP", why))
    for grp, ids in CORPUS.items():
        for i in ids:
            r = rows[i]
            doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", r["doi"].strip())
            if not doi and r["arxiv"].strip():
                doi = "10.48550/arXiv." + r["arxiv"].strip()
            fetched = fetch_doi(doi) if doi else None
            key = r["citation_key"] or i.lower()
            if fetched:
                au = re.search(r"author\s*=\s*\{([^,}]+?)(,| and |\})", fetched)
                sur = re.sub(r"[^a-z]", "", (au.group(1).split()[-1] if au else "anon").lower()) or "anon"
                word = re.sub(r"[^a-z]", "", r["title"].split()[0].lower())
                key = f"{sur}{r['year']}{word}"
                fetched = re.sub(r"^@(\w+)\{[^,]*,", "@\\1{" + key + ",", fetched, count=1)
                status = "DOI-verified"
                if re.search(r"10\.48550|publisher\s*=\s*\{arXiv", fetched, re.I):
                    # Published work whose only DOI is arXiv's: cite the venue, keep arXiv id as note.
                    journal = re.search(r"Journal|Transactions|Trans\.|Access|Electronics|Sciences|"
                                        r"Cybersecurity|Information Sc", r["venue"])
                    typ, fld = ("article", "journal") if journal else ("inproceedings", "booktitle")
                    fetched = re.sub(r"^@\w+\{", "@" + typ + "{", fetched, count=1)
                    fetched = re.sub(r"\n\s*(doi|url|publisher|copyright|keywords)\s*=\s*\{.*?\},?(?=\n)", "",
                                     fetched, flags=re.I)
                    fetched = fetched.rstrip().rstrip("}").rstrip().rstrip(",") + (
                        f",\n  {fld} = {{{r['venue']}}},\n"
                        f"  note = {{Venue per OpenAlex; arXiv:{r['arxiv']}. Confirm proceedings/DOI before submission.}}\n}}")
                    status = "venue-from-OpenAlex"
            else:
                fetched = (f"@inproceedings{{{key},\n  title = {{{r['title']}}},\n  year = {{{r['year']}}},\n"
                           f"  booktitle = {{{r['venue']}}},\n  note = {{VERIFY: no DOI metadata; arXiv {r['arxiv']}}}\n}}")
                status = "VERIFY"
            out_bib.append(fetched); n_pr += 1
            table.append((grp, key, r["title"], r["year"], r["venue"][:60], "PR (" + status + ")", USE[grp]))
            time.sleep(0.3)
    (ROOT / "references-final.bib").write_text("\n\n".join(out_bib) + "\n")
    json.dump({"peer_reviewed": n_pr, "non_peer_reviewed": n_pp, "total": n_pr + n_pp,
               "missing": missing, "rows": table},
              open(ROOT / "docs/lit-review/data/final_refs.json", "w"), indent=1)
    print("PR", n_pr, "PP", n_pp, "total", n_pr + n_pp, "missing", missing,
          "verify", sum("VERIFY" in t[5] for t in table))


if __name__ == "__main__":
    main()
