"""Fail if a lower layer imports a higher one (Core <- Research <- Bench). Stdlib only."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

FORBIDDEN = {"guide": ("guide_research", "guide_bench"), "guide_research": ("guide_bench",)}


def main() -> int:
    root = Path(__file__).resolve().parent.parent / "src"
    bad = []
    for pkg, banned in FORBIDDEN.items():
        for path in (root / pkg).rglob("*.py"):
            for node in ast.walk(ast.parse(path.read_text(), str(path))):
                names = (
                    [a.name for a in node.names]
                    if isinstance(node, ast.Import)
                    else ([node.module or ""] if isinstance(node, ast.ImportFrom) else [])
                )
                bad += [f"{path.relative_to(root)} imports {n}" for n in names if n.split(".")[0] in banned]
    for line in bad:
        print(line)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
