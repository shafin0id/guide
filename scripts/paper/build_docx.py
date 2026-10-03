"""Build the two supervisor documents (.docx) from Markdown and apply consistent print formatting.

Usage: uv run python scripts/paper/build_docx.py
Requires pandoc on PATH. Output: docs/paper/out/*.docx
"""
import subprocess
from pathlib import Path

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "docs/paper"
OUT = PAPER / "out"
OUT.mkdir(exist_ok=True)
DOCS = ["manuscript-draft", "differences-from-submitted"]


def pandoc(name):
    subprocess.run(
        ["pandoc", str(PAPER / f"{name}.md"), "-o", str(OUT / f"{name}.docx"),
         f"--reference-doc={PAPER / 'reference-style.docx'}", f"--resource-path={PAPER}:{ROOT}"],
        check=True, cwd=ROOT)


def set_borders(table):
    tbl = table._tbl
    pr = tbl.tblPr
    for old in pr.findall(qn("w:tblBorders")):
        pr.remove(old)
    b = OxmlElement("w:tblBorders")
    for edge, sz in (("top", 8), ("bottom", 8), ("insideH", 2)):
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), str(sz))
        e.set(qn("w:space"), "0")
        e.set(qn("w:color"), "000000")
        b.append(e)
    pr.append(b)


def format_tables(d):
    for t in d.tables:
        set_borders(t)
        t.autofit = False
        pr = t._tbl.tblPr
        w = pr.find(qn("w:tblW"))
        if w is None:
            w = OxmlElement("w:tblW")
            pr.append(w)
        w.set(qn("w:type"), "pct")
        w.set(qn("w:w"), "5000")
        lay = OxmlElement("w:tblLayout")
        lay.set(qn("w:type"), "fixed") if False else None
        for ri, row in enumerate(t.rows):
            trPr = row._tr.get_or_add_trPr()
            cs = OxmlElement("w:cantSplit")
            trPr.append(cs)
            if ri == 0:
                h = OxmlElement("w:tblHeader")
                trPr.append(h)
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.space_before = Pt(1)
                    p.paragraph_format.space_after = Pt(1)
                    for r in p.runs:
                        r.font.size = Pt(8)
                        if ri == 0:
                            r.font.bold = True


def format_captions_and_refs(d, is_paper):
    in_refs = False
    for p in d.paragraphs:
        txt = p.text.strip()
        if p.style.name.startswith("Heading"):
            in_refs = txt == "References"
            continue
        is_table_cap = txt.startswith("Table ") and txt[6:8].rstrip(".").replace(" ", "").isalnum() and "." in txt[:9]
        is_fig_cap = txt.startswith("Figure ") and "." in txt[:12]
        if is_table_cap:
            p.paragraph_format.keep_with_next = True
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(3)
            for r in p.runs:
                r.font.size = Pt(10)
            if p.runs:
                label = txt.split(".", 1)[0] + "."
                first = p.runs[0]
                if first.text.startswith(label):
                    rest = first.text[len(label):]
                    first.text = label
                    first.font.bold = True
                    nr = p.add_run(rest)
                    nr.font.size = Pt(10)
                    first._r.addnext(nr._r)
        elif is_fig_cap:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(10)
            for r in p.runs:
                r.font.size = Pt(10)
        elif in_refs and txt and is_paper:
            p.paragraph_format.left_indent = Pt(36)
            p.paragraph_format.first_line_indent = Pt(-36)
            p.paragraph_format.space_after = Pt(4)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for r in p.runs:
                r.font.size = Pt(10)
    # centre and keep each figure with its caption
    for p in d.paragraphs:
        if p._p.xpath(".//w:drawing"):
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.keep_with_next = True


def main():
    for name in DOCS:
        pandoc(name)
        path = OUT / f"{name}.docx"
        d = docx.Document(path)
        format_tables(d)
        format_captions_and_refs(d, name == "manuscript-draft")
        d.save(path)
        print("built", path)


main()
