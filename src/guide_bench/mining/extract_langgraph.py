"""Protocol v7b: LangGraph structural extractor (static, ast only). See plan §3.3.

Reads `StateGraph(...)`, `.add_node(name, fn_or_agent)`, `.add_edge(a, b)`,
`.add_conditional_edges(src, fn, mapping_or_list)`, `ToolNode([...])`,
`create_react_agent(model, tools=[...])` and `<llm>.bind_tools([...])` inside a node
function defined in the same file. Each node = one agent. Mined code is parsed only.
"""

from __future__ import annotations

import ast

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


def _str_const(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _list_of_names(node: ast.AST | None) -> list[str]:
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


def _collect_tools_for_name(tree: ast.Module, target: str) -> tuple[list[str], bool]:
    """Resolve the tool list bound to `target` (a node-function name, a ToolNode var, or a
    react-agent var), within the same module. Returns (tools, resolved)."""
    # 1) target is directly a ToolNode([...]) or create_react_agent(..., tools=[...]) assignment
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id != target:
                continue
            call_name = _call_name(node.value)
            if call_name == "ToolNode" and isinstance(node.value, ast.Call) and node.value.args:
                return _list_of_names(node.value.args[0]), True
            if call_name == "create_react_agent" and isinstance(node.value, ast.Call):
                return _list_of_names(_kw(node.value, "tools")), True
    # 2) target is a function name: look for .bind_tools([...]) calls inside its body
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == target:
            for inner in ast.walk(node):
                if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Attribute) and inner.func.attr == "bind_tools":
                    return _list_of_names(inner.args[0]) if inner.args else [], True
            return [], False  # function exists but no bind_tools found inside -- 0 tools, resolved
    return [], False


def _assign_target_key(node: ast.Assign) -> str | None:
    """Returns a stable key for a `StateGraph(...)` assignment target: the bare name for
    `g = StateGraph(...)`, or `self.<attr>` for `self.graph = StateGraph(...)` (a common
    builder-class idiom). Returns None for any other target shape."""
    if len(node.targets) != 1:
        return None
    t = node.targets[0]
    if isinstance(t, ast.Name):
        return t.id
    if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self":
        return f"self.{t.attr}"
    return None


def extract_langgraph(source: str, file_path: str) -> list[ExtractedConfig]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    graph_vars: set[str] = set()
    nodes: dict[str, dict[str, list[str]]] = {}  # graph_var -> {node_name: [edges handled separately]}
    node_targets: dict[str, dict[str, str]] = {}  # graph_var -> {node_name: target_name (fn/var)}
    edges: dict[str, list[tuple[str, str]]] = {}  # graph_var -> [(src, dst)]
    cond_edges: dict[str, list[tuple[str, list[str]]]] = {}  # graph_var -> [(src, [dst,...])]
    entry_points: dict[str, str] = {}

    class Visitor(ast.NodeVisitor):
        def visit_Assign(self, node: ast.Assign) -> None:
            key = _assign_target_key(node)
            if key is not None and _call_name(node.value) == "StateGraph":
                graph_vars.add(key)
                nodes[key] = {}
                node_targets[key] = {}
                edges[key] = []
                cond_edges[key] = []
            self.generic_visit(node)

        def visit_Expr(self, node: ast.Expr) -> None:
            self._handle_call(node.value)
            self.generic_visit(node)

        def visit_Call(self, node: ast.Call) -> None:
            self._handle_call(node)
            self.generic_visit(node)

        def _handle_call(self, call: ast.AST) -> None:
            if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute):
                return
            receiver = call.func.value
            if isinstance(receiver, ast.Name):
                graph_var = receiver.id
            elif isinstance(receiver, ast.Attribute) and isinstance(receiver.value, ast.Name) and receiver.value.id == "self":
                graph_var = f"self.{receiver.attr}"
            else:
                return
            if graph_var not in graph_vars:
                return
            method = call.func.attr
            args = call.args
            if method == "add_node" and len(args) >= 2:
                name = _str_const(args[0])
                target = args[1].id if isinstance(args[1], ast.Name) else _call_name(args[1])
                if name:
                    node_targets[graph_var][name] = target or name
                    nodes[graph_var][name] = []
            elif method == "add_edge" and len(args) >= 2:
                a, b = _str_const(args[0]), _str_const(args[1])
                if a and b:
                    edges[graph_var].append((a, b))
            elif method == "add_conditional_edges" and len(args) >= 2:
                src = _str_const(args[0])
                targets: list[str] = []
                mapping_or_list = args[2] if len(args) >= 3 else None
                if isinstance(mapping_or_list, ast.Dict):
                    targets = [v for v in (_str_const(v) for v in mapping_or_list.values) if v]
                elif isinstance(mapping_or_list, ast.List):
                    targets = [v for v in (_str_const(e) for e in mapping_or_list.elts) if v]
                if src:
                    cond_edges[graph_var].append((src, targets))
            elif method == "set_entry_point" and args:
                ep = _str_const(args[0])
                if ep:
                    entry_points[graph_var] = ep

    Visitor().visit(tree)

    configs: list[ExtractedConfig] = []
    for gv in graph_vars:
        node_names = [n for n in nodes[gv] if n not in ("START", "END")]
        if len(node_names) < 2:
            continue
        depends: dict[str, list[str]] = {n: [] for n in node_names}
        for a, b in edges[gv]:
            if b in depends and a not in ("START",):
                depends[b].append(a)
        for src, targets in cond_edges[gv]:
            for t in targets:
                if t in depends and t not in ("END",):
                    depends[t].append(src)

        agents: list[ExtractedAgent] = []
        steps: list[ExtractedStep] = []
        unresolved: list[str] = []
        for name in node_names:
            target = node_targets[gv].get(name, name)
            tools, resolved = _collect_tools_for_name(tree, target)
            if not resolved:
                unresolved.append(f"node_tools:{name}")
            agents.append(ExtractedAgent(name=name, role=name, tools=tools))
            steps.append(ExtractedStep(step_id=name, agent=name, tools=tools, depends_on=sorted(set(depends[name]))))

        configs.append(
            ExtractedConfig(
                framework="langgraph", repo="", sha="", file=file_path,
                agents=agents, steps=steps, process="graph", unresolved=unresolved,
            )
        )
    return configs
