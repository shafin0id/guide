"""Cohen's kappa between the first screener (screening.csv) and a second screener who filled in
second-screener-sample.csv blind (column 5 = include/exclude). Usage: python3 kappa.py"""
import csv
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent
first = {r["id"]: r["decision"] for r in csv.DictReader((OUT / "screening.csv").open())}
rows = list(csv.reader((OUT / "second-screener-sample.csv").open()))[1:]
pairs = [(first[r[0]], r[4].strip().lower()) for r in rows if len(r) > 4 and r[4].strip()]
if not pairs:
    raise SystemExit("second-screener-sample.csv has no second decisions yet")
n = len(pairs)
po = sum(a == b for a, b in pairs) / n
pa = sum(a == "include" for a, _ in pairs) / n
pb = sum(b == "include" for _, b in pairs) / n
pe = pa * pb + (1 - pa) * (1 - pb)
print(f"n={n} observed agreement={po:.3f} kappa={(po - pe) / (1 - pe):.3f}")
