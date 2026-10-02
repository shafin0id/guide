"""Protocol v7b: GitHub repository sampling frame (FROZEN). See plan §3.2.

Unauthenticated GitHub REST search works (10 requests/min). If `gh auth login` has been
run, `gh api` may be used instead with the identical query string -- this module uses the
unauthenticated REST endpoint directly since that is confirmed reachable in this run.
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SNAPSHOT_DIR = Path("experiments/mining")

QUERIES: dict[str, str] = {
    "crewai": "crewai in:name,description,readme language:Python fork:false archived:false pushed:>=2025-04-01",
    "langgraph": "langgraph in:name,description,readme language:Python fork:false archived:false pushed:>=2025-04-01",
    "autogen": "autogen in:name,description,readme language:Python fork:false archived:false pushed:>=2025-04-01",
}

FRAMEWORK_OWN_REPOS = {"crewAIInc", "joaomdmoura", "langchain-ai", "microsoft", "ag2ai"}
EXCLUDE_NAME_RE = re.compile(r"(?i)(awesome|course|curriculum|roadmap|interview|paper|list)")

_API = "https://api.github.com/search/repositories"


def _get(url: str, retries: int = 3) -> dict:
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "guide-v7b-mining"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 403 and attempt < retries - 1:
                time.sleep(65)  # rate limit: unauthenticated search is 10/min
                continue
            raise
    raise RuntimeError(f"exhausted retries for {url}")


def fetch_search_pages(framework: str, pages: tuple[int, ...] = (1, 2)) -> list[dict]:
    """Fetch and save raw search pages for one framework. Returns combined `items`."""
    query = QUERIES[framework]
    all_items: list[dict] = []
    for page in pages:
        url = f"{_API}?q={urllib.parse.quote(query)}&sort=stars&order=desc&per_page=100&page={page}"
        data = _get(url)
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        snapshot = {"framework": framework, "page": page, "query": query, "fetched_utc": timestamp, "raw": data}
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        (SNAPSHOT_DIR / f"search_snapshot_{framework}_p{page}.json").write_text(json.dumps(snapshot, indent=2))
        all_items.extend(data.get("items", []))
        time.sleep(7)  # stay under 10 req/min unauthenticated
    return all_items


def apply_exclusions(framework: str, items: list[dict], seen_full_names: set[str]) -> tuple[list[dict], list[dict]]:
    """Returns (included, excluded) where excluded entries carry {"item", "rule"}."""
    included: list[dict] = []
    excluded: list[dict] = []
    for item in items:
        full_name = item["full_name"]
        owner = item["owner"]["login"]
        name = item["name"]
        if owner in FRAMEWORK_OWN_REPOS:
            excluded.append({"item": item, "rule": "framework_own_repo"})
            continue
        if EXCLUDE_NAME_RE.search(name):
            excluded.append({"item": item, "rule": "excluded_name_pattern"})
            continue
        if full_name in seen_full_names:
            excluded.append({"item": item, "rule": "duplicate_across_frameworks"})
            continue
        if item.get("size", 0) > 200_000:  # GitHub API `size` is in KB
            excluded.append({"item": item, "rule": "over_200mb"})
            continue
        included.append(item)
        seen_full_names.add(full_name)
    return included, excluded
