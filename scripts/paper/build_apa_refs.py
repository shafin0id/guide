"""Build an APA 7 reference list from references-final.bib.

Robust brace-depth parser (handles both single-line and multi-line BibTeX entries, nested
braces in titles). Produces:
  - docs/paper/references-apa.md   (markdown list, alphabetised by first-author surname)
  - docs/paper/references-apa.json (key -> apa string, for later programmatic insertion)

No data is invented. Entries with insufficient metadata for a clean APA line are flagged
with a leading '[VERIFY]' marker rather than guessed at, per the project's integrity rule.
"""
import re
import json
import os

BIB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "references-final.bib")
OUT_MD = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "paper", "references-apa.md")
OUT_JSON = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "paper", "references-apa.json")


def split_entries(text):
    """Split raw bib text into (entry_type, key, body) tuples using brace depth, not regex greed."""
    entries = []
    i = 0
    n = len(text)
    while i < n:
        at = text.find("@", i)
        if at == -1:
            break
        m = re.match(r"@(\w+)\{([^,]+),", text[at:])
        if not m:
            i = at + 1
            continue
        etype, key = m.group(1), m.group(2).strip()
        start_body = at + m.end()
        depth = 1
        j = start_body
        while j < n and depth > 0:
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
            j += 1
        body = text[start_body:j - 1]
        entries.append((etype, key, body))
        i = j
    return entries


def parse_fields(body):
    """Parse 'field = {value}' or 'field={value}' pairs at top brace-depth within body."""
    fields = {}
    i = 0
    n = len(body)
    while i < n:
        m = re.match(r"\s*,?\s*([A-Za-z][\w]*)\s*=\s*", body[i:])
        if not m:
            i += 1
            continue
        field = m.group(1).lower()
        start = i + m.end()
        if start < n and body[start] == "{":
            depth = 1
            j = start + 1
            while j < n and depth > 0:
                if body[j] == "{":
                    depth += 1
                elif body[j] == "}":
                    depth -= 1
                j += 1
            value = body[start + 1:j - 1]
            i = j
        else:
            # unbraced value, e.g. month=Apr or year=2025, up to next comma at depth 0
            j = start
            depth = 0
            while j < n and not (body[j] == "," and depth == 0):
                if body[j] in "{[(":
                    depth += 1
                elif body[j] in "}])":
                    depth -= 1
                j += 1
            value = body[start:j].strip()
            i = j
        fields[field] = re.sub(r"\s+", " ", value).strip()
        i += 1
    return fields


def clean_title(t):
    t = re.sub(r"^\{+|\}+$", "", t.strip())
    t = re.sub(r"\{([^{}]*)\}", r"\1", t)  # drop inner protective braces, keep content
    t = re.sub(r"\\textit\{([^{}]*)\}", r"\1", t)  # unescape \textit{...}
    t = t.replace("\\textit", "").replace("$", "")  # drop stray LaTeX math delimiters/macro names
    t = re.sub(r"\s+", " ", t)
    return t.strip()


SURNAME_PREFIX_OVERRIDES = {
    "Tim Van hamme": ("Van hamme", "T."),
}

ET_AL_OVERRIDES = {
    # bib entries where the source metadata collapsed the author list to "X et al."; the full
    # list was not recovered during the systematic review, so this is reported as a single named
    # first author plus "et al." rather than invented co-authors.
    "lamalfa2025": [("La Malfa", None, True)],
}


def parse_authors(author_field):
    """BibTeX author lists come in two shapes in this file:
    - 'Surname, Given and Surname2, Given2 and ...' (DOI-verified entries, has a comma per author)
    - 'Given Surname and Given2 Surname2 and ...' (preprint-kept entries, no comma; last token in
      each name is treated as the surname, which matches every example in this file)
    - 'Surname2012' bare joins with 'and' and no comma or space-split possible (oldest entries,
      e.g. 'Saltzer and Schroeder') -- these have no given name in the source data at all, and
      are left as surname-only rather than guessed at.
    """
    if not author_field:
        return []
    if author_field.strip() in SURNAME_PREFIX_OVERRIDES:
        pass  # handled per-token below via the overrides dict on each split part
    parts = re.split(r"\s+and\s+", author_field.strip())
    authors = []
    for p in parts:
        p = p.strip().rstrip(",")
        if not p:
            continue
        if p in SURNAME_PREFIX_OVERRIDES:
            surname, initials = SURNAME_PREFIX_OVERRIDES[p]
            authors.append((surname, initials))
        elif "," in p:
            surname, given = p.split(",", 1)
            surname = surname.strip()
            given = given.strip()
            initials = " ".join(f"{seg[0]}." for seg in re.split(r"[\s-]+", given) if seg)
            authors.append((surname, initials))
        elif " " in p:
            # 'Given [Middle] Surname' with no comma: last whitespace-separated token is the
            # surname, everything before it is given/middle name(s) to be initialised.
            tokens = p.split()
            surname = tokens[-1]
            given_tokens = tokens[:-1]
            initials = " ".join(f"{seg[0]}." for seg in given_tokens if seg)
            authors.append((surname, initials))
        else:
            # bare surname only, no given name available in the source data at all
            authors.append((p.strip(), None))
    return authors


def format_authors_apa(authors):
    if not authors:
        return None
    parts = []
    all_surname_only = all(initials is None for _, initials in authors)
    for surname, initials in authors:
        if initials:
            parts.append(f"{surname}, {initials}")
        else:
            parts.append(surname)
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]}, & {parts[1]}" if not all_surname_only else f"{parts[0]} & {parts[1]}"
    return ", ".join(parts[:-1]) + f", & {parts[-1]}"


def venue_string(fields, etype):
    venue = fields.get("journal") or fields.get("booktitle") or fields.get("series") or fields.get("collection")
    vol = fields.get("volume")
    num = fields.get("number")
    pages = fields.get("pages", "").replace("–", "-")
    eprint = fields.get("eprint")
    archive_prefix = fields.get("archiveprefix", "")
    out = []
    if venue:
        out.append(venue)
    elif eprint and archive_prefix.lower() == "arxiv":
        out.append(f"arXiv preprint arXiv:{eprint}")
    if vol:
        v = vol
        if num:
            v += f"({num})"
        out.append(v)
    elif num:
        out.append(f"({num})")
    if pages:
        out.append(pages.replace("-", "\u2013"))
    return ", ".join(out)


# Specific, individually verified corrections for entries where the auto-built bib's structured
# fields are incomplete but the correct value is already stated in that same entry's own `note`
# field (so this is reading the project's own prior verification, not inventing new facts).
KNOWN_CORRECTIONS = {
    "lamalfa2025": {"doi": "10.52202/085713-4663", "venue_override": "Advances in Neural Information Processing Systems 38 (NeurIPS 2025)"},
    "khan2025agents": {"doi": None, "note_only": "arXiv:2504.00218; venue per OpenAlex as ACL, proceedings DOI unconfirmed"},
}


def build_apa(key, etype, fields):
    note = fields.get("note", "")
    author_field = fields.get("author", "")
    if key in ET_AL_OVERRIDES:
        authors = [(sur, init) for sur, init, _ in ET_AL_OVERRIDES[key]]
        et_al = True
    else:
        authors = parse_authors(author_field)
        et_al = False
    author_str = format_authors_apa(authors)
    if et_al and author_str:
        author_str += " et al."
    year = fields.get("year", "n.d.")
    title = clean_title(fields.get("title", ""))
    doi = fields.get("doi")
    url = fields.get("url")
    eprint = fields.get("eprint")
    archive_prefix = fields.get("archiveprefix", "")
    venue = venue_string(fields, etype)

    corr = KNOWN_CORRECTIONS.get(key, {})
    if corr.get("doi"):
        doi = corr["doi"]
    if corr.get("venue_override"):
        venue = corr["venue_override"]

    flag = ""
    if not author_str:
        flag = "[VERIFY author] "
    if not title:
        flag += "[VERIFY title] "

    pieces = []
    pieces.append(f"{author_str or '[VERIFY author]'} ({year}).")
    # title: sentence case already mostly as-authored in bib; keep as given (titles are proper nouns/technical terms)
    title_piece = title if title.endswith((".", "?", "!")) else f"{title}."
    pieces.append(title_piece)
    if venue:
        pieces.append(f"{venue}.")
    link = f"https://doi.org/{doi}" if doi else (
        f"https://arxiv.org/abs/{eprint}" if eprint and archive_prefix.lower() == "arxiv" else url
    )
    if link:
        pieces.append(link)

    apa = " ".join(p for p in pieces if p).strip()
    is_preprint = "arxiv" in (venue or "").lower() or "arXiv" in (fields.get("eprint", "") or "") or "/ grey" in note or (not venue and "arxiv" in (url or "").lower())
    return flag + apa, is_preprint


def main():
    text = open(BIB_PATH, encoding="utf-8").read()
    raw_entries = split_entries(text)
    print(f"Parsed {len(raw_entries)} bib entries")

    records = []
    for etype, key, body in raw_entries:
        fields = parse_fields(body)
        apa, is_preprint = build_apa(key, etype, fields)
        surname_sort = fields.get("author", key).split(",")[0].split(" and ")[0].strip().lower() or key
        records.append({"key": key, "apa": apa, "is_preprint": is_preprint, "sort": surname_sort, "year": fields.get("year", "")})

    records.sort(key=lambda r: (r["sort"], r["year"]))

    flagged = [r for r in records if r["apa"].startswith("[VERIFY")]
    print(f"{len(flagged)} entries flagged for missing author/title metadata")

    lines = ["# References (APA 7th)\n",
             f"Generated from `references-final.bib` ({len(records)} entries). "
             f"Entries beginning with [VERIFY] have incomplete metadata in the source bib "
             f"file and must be completed by hand before submission; they are not fabricated here.\n"]
    for r in records:
        lines.append(f"- {r['apa']}")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump({r["key"]: r["apa"] for r in records}, f, indent=2)

    print("Wrote", OUT_MD)
    print("Wrote", OUT_JSON)
    if flagged:
        print("\nFlagged entries (need manual fix):")
        for r in flagged:
            print(" -", r["key"], ":", r["apa"][:100])


if __name__ == "__main__":
    main()
