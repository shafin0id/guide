"""Protocol v7b: AutoGen structural extractor (0.2 and 0.4+, static, ast only). See plan §3.3.

Reads `AssistantAgent(name, ..., tools=[...])`, `register_function(f, caller=A, executor=B)`,
`UserProxyAgent(..., code_execution_config=<not False>)` (adds a synthetic `code_executor`
tool), `GroupChat(agents=[...])`, `RoundRobinGroupChat([...])`, `SelectorGroupChat([...])`
and `Swarm([...])`. Steps are the agents in list order, each depending on the previous one.
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


def _code_execution_enabled(node: ast.AST | None) -> bool:
    """code_execution_config=<not False>: True unless the literal is exactly False or {} is absent."""
    if node is None:
        return False
    if isinstance(node, ast.Constant) and node.value is False:
        return False
    return True  # a dict literal, a Name, or anything else counts as "not False"


_AGENT_CTORS = {"AssistantAgent", "UserProxyAgent", "ConversableAgent"}
_GROUP_CTORS = {"GroupChat", "RoundRobinGroupChat", "SelectorGroupChat", "Swarm"}


def extract_autogen(source: str, file_path: str) -> list[ExtractedConfig]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    agent_vars: dict[str, ExtractedAgent] = {}
    registered_functions: list[tuple[str, str, str]] = []  # (func_name, caller_var, executor_var)
    groups: list[dict] = []

    class Visitor(ast.NodeVisitor):
        def visit_Assign(self, node: ast.Assign) -> None:
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                var_name = node.targets[0].id
                call_name = _call_name(node.value)
                if call_name in _AGENT_CTORS and isinstance(node.value, ast.Call):
                    tools = _list_of_names(_kw(node.value, "tools"))
                    if call_name == "UserProxyAgent" and _code_execution_enabled(_kw(node.value, "code_execution_config")):
                        tools.append("code_executor")
                    name_arg = node.value.args[0] if node.value.args else _kw(node.value, "name")
                    role = _str_const(name_arg) or var_name
                    agent_vars[var_name] = ExtractedAgent(name=var_name, role=role, tools=tools)
                elif call_name in _GROUP_CTORS and isinstance(node.value, ast.Call):
                    agents_node = node.value.args[0] if node.value.args else _kw(node.value, "agents")
                    agent_names = [e.id for e in agents_node.elts if isinstance(e, ast.Name)] if isinstance(agents_node, ast.List) else []
                    groups.append({"var": var_name, "agents": agent_names, "kind": call_name})
            self.generic_visit(node)

        def visit_Call(self, node: ast.Call) -> None:
            if _call_name(node) == "register_function":
                caller_node = _kw(node, "caller")
                executor_node = _kw(node, "executor")
                func_node = node.args[0] if node.args else None
                func_name = func_node.id if isinstance(func_node, ast.Name) else (_call_name(func_node) or "unknown_fn")
                caller = caller_node.id if isinstance(caller_node, ast.Name) else None
                executor = executor_node.id if isinstance(executor_node, ast.Name) else None
                if caller and executor:
                    registered_functions.append((func_name, caller, executor))
            self.generic_visit(node)

    Visitor().visit(tree)

    # register_function grants the tool to BOTH caller (proposes) and executor (runs it);
    # record on the executor, since that is where the effect actually happens.
    for func_name, caller, executor in registered_functions:
        if executor in agent_vars:
            agent_vars[executor].tools.append(func_name)

    if not groups:
        return []

    configs: list[ExtractedConfig] = []
    for group in groups:
        members = [agent_vars[a] for a in group["agents"] if a in agent_vars]
        unresolved = [f"group_member:{a}" for a in group["agents"] if a not in agent_vars]
        if len(members) < 2:
            continue
        steps: list[ExtractedStep] = []
        prev: str | None = None
        for agent in members:
            steps.append(ExtractedStep(step_id=agent.name, agent=agent.name, tools=agent.tools, depends_on=[prev] if prev else []))
            prev = agent.name
        configs.append(
            ExtractedConfig(
                framework="autogen", repo="", sha="", file=file_path,
                agents=members, steps=steps, process=group["kind"], unresolved=unresolved,
            )
        )
    return configs
