"""Build a minimal pandoc reference .docx that mimics the MKA template's plain style:
Times New Roman body text, plain sentence-case headings with no heavy box/shading, single
title block, no decorative TOC styling. Uses python-docx to define styles, then pandoc
--reference-doc picks up these style definitions for the real conversion.
"""
import subprocess
import sys

try:
    import docx
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "python-docx"], check=True)
    import docx

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

# Base body style: Times New Roman 11pt, matching a typical plain academic template
style = doc.styles["Normal"]
style.font.name = "Times New Roman"
style.font.size = Pt(11)
style.paragraph_format.space_after = Pt(8)
style.paragraph_format.line_spacing = 1.15

for i, size in zip([1, 2, 3], [14, 12, 11]):
    h = doc.styles[f"Heading {i}"]
    h.font.name = "Times New Roman"
    h.font.size = Pt(size)
    h.font.bold = True
    h.font.color.rgb = None
    h.paragraph_format.space_before = Pt(12)
    h.paragraph_format.space_after = Pt(6)
    # strip any default heading background/border shading inherited from the Normal docx theme
    h.paragraph_format.keep_with_next = False

title_style = doc.styles["Title"]
title_style.font.name = "Times New Roman"
title_style.font.size = Pt(16)
title_style.font.bold = True

# page setup: standard A4, moderate margins, matching the look of the shared template
for section in doc.sections:
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)

doc.save("docs/paper/reference-style.docx")
print("Wrote docs/paper/reference-style.docx")
