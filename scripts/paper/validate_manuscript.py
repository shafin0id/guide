#!/usr/bin/env python3
"""Validate manuscript-draft.md strictly against shafin-writing-skill-v2 and project requirements."""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MANUSCRIPT_FILE = REPO_ROOT / "docs" / "paper" / "manuscript-draft.md"
REFS_BIB_FILE = REPO_ROOT / "references-final.bib"

BANNED_WORDS = [
    "delve", "pivotal", "crucial", "tapestry", "testament", "underscore", "vibrant",
    "intricate", "meticulous", "garner", "bolster", "foster", "enhance", "showcase",
    "highlight", "landscape", "align with", "boasts", "enduring", "leverage", "robust",
    "seamless", "seamlessly", "comprehensive", "holistic", "paradigm", "realm",
    "navigate", "streamline", "cutting-edge", "state-of-the-art", "transformative",
    "game-changer", "revolutionize", "unlock", "empower", "harness", "underpin",
    "paramount", "multifaceted", "nuanced", "myriad", "plethora", "noteworthy",
    "notably", "remarkable", "invaluable", "ever-evolving", "rapidly evolving",
    "groundbreaking", "innovative", "furthermore", "utilize", "facilitate",
    "encompass", "commendable", "shed light", "pave the way", "deep dive",
    "tailored", "elevate", "spearhead", "bridge the gap"
]

CONTRACTIONS = [
    "can't", "won't", "didn't", "doesn't", "isn't", "aren't", "haven't", "hasn't",
    "it's", "they're", "we're", "you're", "i'm", "there's", "that's", "couldn't",
    "wouldn't", "shouldn't"
]

FIRST_PERSON = [
    r"\bI\b", r"\bwe\b", r"\bour\b", r"\bmy\b", r"\bus\b"
]

def validate():
    text = MANUSCRIPT_FILE.read_text(encoding="utf-8")
    errors = []
    
    # 1. Check for horizontal rules ---
    hr_matches = re.findall(r"^---$", text, re.MULTILINE)
    if hr_matches:
        errors.append(f"Found {len(hr_matches)} horizontal rules (---). Remove all.")

    # Exclude references and code/tables for text-only rules
    ref_idx = text.find("## References")
    body_text = text[:ref_idx] if ref_idx != -1 else text

    # Strip code blocks, tables, and display math from prose checks
    prose_lines = []
    in_code = False
    for line in body_text.splitlines():
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code or line.startswith("|") or line.startswith("#") or line.startswith("![") or line.strip().startswith("$$"):
            continue
        prose_lines.append(line)
    prose = " ".join(prose_lines)
    # Strip inline math from prose checks so mathematical variables ($i$) are not treated as pronouns
    prose = re.sub(r"\$[^$]+\$", "", prose)

    # 2. Check for semicolons
    if ";" in prose:
        errors.append("Found semicolon(s) in body prose.")

    # 3. Check for em dashes and en dashes
    if "—" in prose or "–" in prose:
        errors.append("Found em dash (—) or en dash (–) in body prose.")

    # 4. Check for contractions
    for c in CONTRACTIONS:
        if re.search(r"\b" + c + r"\b", prose, re.IGNORECASE):
            errors.append(f"Found contraction '{c}' in body prose.")

    # 5. Check for first person
    for fp in FIRST_PERSON:
        matches = re.findall(fp, prose, re.IGNORECASE)
        # allow 'us' only if part of another context, but fp uses \b
        if matches:
            errors.append(f"Found first-person pronoun matching '{fp}' ({len(matches)} occurrences).")

    # 6. Check for banned words
    for bw in BANNED_WORDS:
        m = re.findall(r"\b" + bw + r"\b", prose, re.IGNORECASE)
        if m:
            errors.append(f"Found banned word/phrase '{bw}' ({len(m)} occurrences).")

    # 7. Check for sentence length (> 30 words)
    # Split sentences roughly by . ! ? followed by space or newline
    sentences = re.split(r"[.!?]+(?:\s+|\n+)", prose)
    long_sentences = []
    for s in sentences:
        s_clean = s.strip()
        if not s_clean:
            continue
        words = s_clean.split()
        if len(words) > 30:
            long_sentences.append((len(words), s_clean[:80]))
    if long_sentences:
        errors.append(f"Found {len(long_sentences)} sentences over 30 words: {long_sentences[:3]}")

    # 8. Check for tables 1 through 12
    for t_num in range(1, 13):
        t_str = f"Table {t_num}"
        if t_str not in text:
            errors.append(f"Missing {t_str} in manuscript.")

    # 9. Check for internal repo paths in prose
    for path_str in ["docs/", "experiments/results/", "plan gate", "docs/experiments.md"]:
        if path_str in prose:
            errors.append(f"Found internal path/gate in prose: '{path_str}'")

    print(f"Validation completed with {len(errors)} issues.")
    for e in errors:
        print(f"  ERROR: {e}")
    return len(errors) == 0

if __name__ == "__main__":
    if not validate():
        sys.exit(1)
    print("Manuscript passed all style and structural rules!")
