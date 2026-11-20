"""Protocol v7b: per-repo extraction driver. See plan §3.3 for file-walking rules.

Walks a cloned repo (already on disk; this module never clones or deletes), finds
candidate source files per framework, and extracts configs via the matching extractor.
Mined code is read as text and parsed with ast/yaml only -- never executed or imported.
"""

from __future__ import annotations

from pathlib import Path

from guide_bench.mining.common import ExtractedConfig
from guide_bench.mining.extract_autogen import extract_autogen
from guide_bench.mining.extract_crewai import extract_crewai_python, extract_crewai_yaml, merge_yaml_config_tools
from guide_bench.mining.extract_langgraph import extract_langgraph

MAX_FILE_BYTES = 2_000_000  # skip pathologically large files; mined repos can contain data dumps


def _iter_py_files(repo_root: Path):
    for p in repo_root.rglob("*.py"):
        try:
            if not p.is_file() or p.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue  # broken symlink or file removed mid-walk; skip
        if any(part in {".git", "node_modules", "venv", ".venv", "test", "tests"} for part in p.parts):
            continue
        yield p


def extract_crewai_from_repo(repo_root: Path, repo_full_name: str, sha: str) -> list[ExtractedConfig]:
    configs: list[ExtractedConfig] = []
    for py_file in _iter_py_files(repo_root):
        try:
            source = py_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "Crew(" not in source and "crewai" not in source.lower():
            continue
        rel = str(py_file.relative_to(repo_root))
        for cfg in extract_crewai_python(source, rel):
            cfg.repo = repo_full_name
            cfg.sha = sha
            configs.append(cfg)

    for agents_yaml in repo_root.rglob("agents.yaml"):
        tasks_yaml = agents_yaml.parent / "tasks.yaml"
        if not tasks_yaml.is_file():
            continue
        rel = str(agents_yaml.relative_to(repo_root))
        cfg = extract_crewai_yaml(repo_root, agents_yaml, tasks_yaml, rel)
        if cfg is None:
            continue
        # best-effort: merge in tool bindings from sibling Python modules under the same crew dir
        crew_dir = agents_yaml.parent.parent  # config/ -> crew package dir
        for py_file in crew_dir.glob("*.py"):
            try:
                merge_yaml_config_tools(cfg, py_file.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                continue
        cfg.repo = repo_full_name
        cfg.sha = sha
        configs.append(cfg)
    return configs


def extract_langgraph_from_repo(repo_root: Path, repo_full_name: str, sha: str) -> list[ExtractedConfig]:
    configs: list[ExtractedConfig] = []
    for py_file in _iter_py_files(repo_root):
        try:
            source = py_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "StateGraph" not in source:
            continue
        rel = str(py_file.relative_to(repo_root))
        for cfg in extract_langgraph(source, rel):
            cfg.repo = repo_full_name
            cfg.sha = sha
            configs.append(cfg)
    return configs


def extract_autogen_from_repo(repo_root: Path, repo_full_name: str, sha: str) -> list[ExtractedConfig]:
    configs: list[ExtractedConfig] = []
    for py_file in _iter_py_files(repo_root):
        try:
            source = py_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "GroupChat" not in source and "Swarm(" not in source:
            continue
        rel = str(py_file.relative_to(repo_root))
        for cfg in extract_autogen(source, rel):
            cfg.repo = repo_full_name
            cfg.sha = sha
            configs.append(cfg)
    return configs


EXTRACTORS = {
    "crewai": extract_crewai_from_repo,
    "langgraph": extract_langgraph_from_repo,
    "autogen": extract_autogen_from_repo,
}
