"""Protocol v7b: CrewAI structural extractor (static, ast + yaml only). See plan §3.3.

Handles two forms:
1. Plain Python: `Agent(role=..., tools=[...])`, `Task(description=..., agent=<var>,
   tools=[...], context=[...])`, `Crew(agents=[...], tasks=[...], process=...)`.
2. YAML + `@CrewBase`: `config/agents.yaml` + `config/tasks.yaml` read alongside
   `@agent`/`@task`/`@crew` decorated methods in a `@CrewBase` class.

Mined code is NEVER executed or imported -- parsed with `ast` and `yaml` only.
"""

from __future__ import annotations

import ast
from pathlib import Path

import yaml

from guide_bench.mining.common import ExtractedAgent, ExtractedConfig, ExtractedStep


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call):
        f = node.func
        if isinstance(f, ast.Name):
            return f.id
        if isinstance(f, ast.Attribute):
            return f.attr
    return None


def _kw(call: ast.Call, name: str) -> ast.AST | None:
    for kw in call.keywords:
        if kw.arg == name:
            return kw.value
    return None


def _list_of_names(node: ast.AST | None) -> list[str]:
    """Best-effort extraction of names/strings from a list literal, e.g. tools=[Tool(), Tool2()]."""
    out: list[str] = []
    if isinstance(node, ast.List):
        for elt in node.elts:
            n = _call_name(elt)
            if n:
                out.append(n)
            elif isinstance(elt, ast.Name):
                out.append(elt.id)
            elif isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                out.append(elt.value)
    return out


def _str_const(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Attribute):  # e.g. Process.sequential
        return node.attr
    return None


def extract_crewai_python(source: str, file_path: str) -> list[ExtractedConfig]:
    """Extracts CrewAI configs from a single Python source string (plain Agent/Task/Crew form)."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    agent_vars: dict[str, ExtractedAgent] = {}  # var name -> agent
    task_vars: dict[str, dict] = {}  # var name -> {description, agent_var, tools, context}
    crews: list[dict] = []

    class Visitor(ast.NodeVisitor):
        def visit_Assign(self, node: ast.Assign) -> None:
            if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
                self.generic_visit(node)
                return
            var_name = node.targets[0].id
            call_name = _call_name(node.value)
            if call_name == "Agent" and isinstance(node.value, ast.Call):
                role = _str_const(_kw(node.value, "role")) or var_name
                tools = _list_of_names(_kw(node.value, "tools"))
                agent_vars[var_name] = ExtractedAgent(name=var_name, role=role, tools=tools)
            elif call_name == "Task" and isinstance(node.value, ast.Call):
                agent_node = _kw(node.value, "agent")
                agent_var = agent_node.id if isinstance(agent_node, ast.Name) else None
                tools = _list_of_names(_kw(node.value, "tools"))
                context_node = _kw(node.value, "context")
                context_vars = (
                    [e.id for e in context_node.elts if isinstance(e, ast.Name)]
                    if isinstance(context_node, ast.List)
                    else []
                )
                task_vars[var_name] = {"agent_var": agent_var, "tools": tools, "context": context_vars}
            elif call_name == "Crew" and isinstance(node.value, ast.Call):
                agents_node = _kw(node.value, "agents")
                tasks_node = _kw(node.value, "tasks")
                agent_names = (
                    [e.id for e in agents_node.elts if isinstance(e, ast.Name)]
                    if isinstance(agents_node, ast.List)
                    else []
                )
                task_names = (
                    [e.id for e in tasks_node.elts if isinstance(e, ast.Name)]
                    if isinstance(tasks_node, ast.List)
                    else []
                )
                process = _str_const(_kw(node.value, "process")) or "sequential"
                crews.append({"agents": agent_names, "tasks": task_names, "process": process})
            self.generic_visit(node)

    Visitor().visit(tree)
    if not crews:
        return []

    configs: list[ExtractedConfig] = []
    for _i, crew in enumerate(crews):
        agents = [agent_vars[a] for a in crew["agents"] if a in agent_vars]
        unresolved: list[str] = []
        steps: list[ExtractedStep] = []
        prev_step_id: str | None = None
        hierarchical = crew["process"] == "hierarchical"
        if hierarchical:
            steps.append(ExtractedStep(step_id="manager", agent="__manager__", tools=[], depends_on=[]))
            prev_step_id = "manager"
        for tv in crew["tasks"]:
            t = task_vars.get(tv)
            if t is None:
                unresolved.append(f"task:{tv}")
                continue
            agent_var = t["agent_var"]
            if agent_var not in agent_vars:
                unresolved.append(f"task_agent:{tv}:{agent_var}")
            agent_tools = agent_vars[agent_var].tools if agent_var in agent_vars else []
            depends = list(t["context"]) if t["context"] else ([prev_step_id] if prev_step_id else [])
            if hierarchical and prev_step_id == "manager" and not t["context"]:
                depends = ["manager"]
            steps.append(
                ExtractedStep(
                    step_id=tv,
                    agent=agent_var or "__unresolved__",
                    tools=sorted(set(agent_tools + t["tools"])),
                    depends_on=depends,
                )
            )
            prev_step_id = tv
        configs.append(
            ExtractedConfig(
                framework="crewai",
                repo="",
                sha="",
                file=file_path,
                agents=agents,
                steps=steps,
                process=crew["process"],
                unresolved=unresolved,
            )
        )
    return configs


def extract_crewai_yaml(repo_root: Path, agents_yaml: Path, tasks_yaml: Path, file_path: str) -> ExtractedConfig | None:
    """Extracts one CrewAI config from a `config/agents.yaml` + `config/tasks.yaml` pair.

    Tool bindings in the YAML form live in the decorated Python methods, not the YAML
    itself (CrewAI's `@CrewBase` convention binds `tools=[...]` in the `@agent` method).
    Since this function only reads the YAML (no safe way to resolve the sibling Python
    method bodies without a second, caller-supplied AST pass), tool lists are left empty
    here; the caller (`extract_one_repo`) merges in tools found via a best-effort scan of
    the same directory's `*.py` files for `@agent`-decorated methods returning `Agent(...,
    tools=[...])`, keyed by role name.
    """
    try:
        agents_doc = yaml.safe_load(agents_yaml.read_text()) or {}
        tasks_doc = yaml.safe_load(tasks_yaml.read_text()) or {}
    except yaml.YAMLError:
        return None
    if not isinstance(agents_doc, dict) or not isinstance(tasks_doc, dict):
        return None

    agents = [ExtractedAgent(name=k, role=(v or {}).get("role", k), tools=[]) for k, v in agents_doc.items()]
    agent_names = {a.name for a in agents}
    steps: list[ExtractedStep] = []
    unresolved: list[str] = []
    prev_step_id: str | None = None
    for task_id, task_body in tasks_doc.items():
        if not isinstance(task_body, dict):
            continue
        agent_key = task_body.get("agent")
        if agent_key not in agent_names:
            unresolved.append(f"task_agent:{task_id}:{agent_key}")
        context = task_body.get("context") or []
        depends = list(context) if context else ([prev_step_id] if prev_step_id else [])
        steps.append(ExtractedStep(step_id=task_id, agent=agent_key or "__unresolved__", tools=[], depends_on=depends))
        prev_step_id = task_id

    return ExtractedConfig(
        framework="crewai",
        repo="",
        sha="",
        file=file_path,
        agents=agents,
        steps=steps,
        process="sequential",
        unresolved=unresolved,
    )


def merge_yaml_config_tools(cfg: ExtractedConfig, py_source: str) -> None:
    """Best-effort: fill in per-agent tools for a YAML-form config by scanning the sibling
    Python module's `@agent`-decorated methods for `tools=[...]` and matching by variable
    name used as the dict key under `config=self.agents_config['<key>']`."""
    try:
        tree = ast.parse(py_source)
    except SyntaxError:
        return
    by_key: dict[str, list[str]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        is_agent_method = any(
            (isinstance(d, ast.Name) and d.id == "agent") or (isinstance(d, ast.Attribute) and d.attr == "agent")
            for d in node.decorator_list
        )
        if not is_agent_method:
            continue
        for inner in ast.walk(node):
            if _call_name(inner) == "Agent" and isinstance(inner, ast.Call):
                config_node = _kw(inner, "config")
                key = None
                if isinstance(config_node, ast.Subscript):
                    idx = config_node.slice
                    if isinstance(idx, ast.Constant) and isinstance(idx.value, str):
                        key = idx.value
                tools = _list_of_names(_kw(inner, "tools"))
                if key and tools:
                    by_key[key] = tools
    for agent in cfg.agents:
        if agent.name in by_key:
            agent.tools = by_key[agent.name]
    # propagate into steps whose `agent` matches an updated agent name
    tools_by_agent = {a.name: a.tools for a in cfg.agents}
    for step in cfg.steps:
        if step.agent in tools_by_agent and not step.tools:
            step.tools = tools_by_agent[step.agent]
