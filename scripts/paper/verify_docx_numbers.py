"""Check every number in the revised manuscript against the results corpus (summaries written from raw data).

Prints numbers that do not occur in any source file, with their paragraph, for manual review.
Usage: python scripts/paper/verify_docx_numbers.py docs/paper/revision-v2/GUIDE_Manuscript_Revised_V2.docx
"""

from __future__ import annotations

import glob
import re
import sys
from pathlib import Path

import docx

ROOT = Path(__file__).resolve().parents[2]
SOURCES = [
    "docs/experiments.md", "docs/lit-review/literature-review.md", "docs/lit-review/protocol.md",
    "docs/step3-results.md", "docs/protocol-v9a.md", "docs/protocol-v9b.md",
    "experiments/results/step3/summary.md", "experiments/results/final-v8/paper_numbers.json",
    "experiments/mining/summary.md", "experiments/mining/funnel.json",
    *glob.glob(str(ROOT / "experiments/results/*/summary.md")), *glob.glob(str(ROOT / "experiments/results/*/summary.json")),
    *glob.glob(str(ROOT / "experiments/results/*/*/summary.md")),
]
NUM = re.compile(r"(?<![\w.])\d{1,3}(?:,\d{3})+(?:\.\d+)?|(?<![\w.])\d+\.\d+|(?<![\w.])\d{2,}")
IGNORE = {"2022", "2023", "2024", "2025", "2026", "2027", "1975", "1976", "2004", "2007", "2009", "2012", "2014", "2018",
          "2021", "1927", "1947", "1988", "57000", "4.1", "3.5", "3.1", "2.5", "1017", "120B", "0.1", "0.3", "0.5"}


def variants(n: str) -> set[str]:
    v = {n, n.replace(",", "")}
    try:
        f = float(n.replace(",", ""))
        v |= {f"{f:.1f}", f"{f:.3f}", f"{f / 100:.3f}", f"{f / 100:.4f}"[:6], str(int(f)) if f.is_integer() else n}
    except ValueError:
        pass
    return v


def main() -> None:
    corpus = "\n".join(Path(s if Path(s).is_absolute() else ROOT / s).read_text(errors="ignore")
                       for s in SOURCES if Path(s if Path(s).is_absolute() else ROOT / s).exists())
    d = docx.Document(sys.argv[1])
    blocks = [(f"p{i}", p.text) for i, p in enumerate(d.paragraphs) if p.text.strip()]
    blocks += [(f"t{ti}r{ri}", " | ".join(c.text for c in r.cells)) for ti, t in enumerate(d.tables) for ri, r in enumerate(t.rows)]
    refs_start = next(i for i, (k, t) in enumerate(blocks) if t.strip() == "References")
    unmatched = []
    for k, (loc, text) in enumerate(blocks):
        if k > refs_start and loc.startswith("p"):
            continue
        for n in NUM.findall(text):
            if n in IGNORE or re.fullmatch(r"(19|20)\d\d", n):
                continue
            if not any(v in corpus for v in variants(n)):
                unmatched.append((loc, n, text[:110].replace("\n", " ")))
    for u in unmatched:
        print(*u, sep=" | ")
    print("UNMATCHED", len(unmatched))


if __name__ == "__main__":
    main()
