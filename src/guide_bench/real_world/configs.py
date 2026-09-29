"""18 curated workflow configurations reproducing LangGraph / CrewAI / AutoGen structural patterns
across 5 enterprise domains. See `guide_bench.real_world.__init__` for the scope caveat.

Each `RealWorldConfig` carries the framework pattern it reproduces (with the citation) and its
domain, plus a GUIDE `TaskSpec` + `Policy` + `ToolRegistry` fully expressed in GUIDE's own types
so the existing analyser (`guide_research.blast_radius`) can run over it unmodified.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from guide.agent import AgentSpec
from guide.policy import Policy
from guide.tools import OperationSpec, Tool, ToolRegistry, ToolSpec
from guide.types import Sensitivity, ToolResult
from guide.workflow import Step, TaskSpec, Workflow

Pattern = Literal["langgraph", "crewai", "autogen"]


@dataclass(frozen=True)
class RealWorldConfig:
    config_id: str
    domain: str
    pattern: Pattern
    pattern_note: str  # which structural feature of the framework this reproduces, and why
    task: TaskSpec
    agents: tuple[AgentSpec, ...]
    policy: Policy
    registry: ToolRegistry
    nominal_calls: tuple[tuple[str, str, str, dict[str, object]], ...]  # (step, tool, op, args) that must still work


# ----------------------------------------------------------------------------- generic no-op tool runtime
class _StubTool:
    """Static-analysis-only stand-in. Never invoked in this study (no live calls)."""

    def __init__(self, spec: ToolSpec) -> None:
        self.spec = spec

    def invoke(self, operation: str, args: object) -> ToolResult:  # pragma: no cover - analysis only
        return ToolResult(ok=True, data=None)


def tool(spec: ToolSpec) -> Tool:
    return _StubTool(spec)  # type: ignore[return-value]


# ----------------------------------------------------------------------------- shared tool specs by domain
def _support_tools() -> list[ToolSpec]:
    return [
        ToolSpec(
            "crm",
            "Customer records",
            resource_class="crm_db",
            columns_param="columns",
            default_sensitivity=Sensitivity.INTERNAL,
            column_sensitivity={
                "customer_id": Sensitivity.INTERNAL,
                "name": Sensitivity.INTERNAL,
                "payment_card_last4": Sensitivity.CONFIDENTIAL,
                "ssn": Sensitivity.RESTRICTED,
            },
            operations={
                "query": OperationSpec(
                    "query", "read customer record", params={"customer_id": "id", "columns": "cols"}
                ),
                "update_account": OperationSpec(
                    "update_account", "mutate account fields", write_effect=True, params={"customer_id": "id"}
                ),
                "issue_refund": OperationSpec(
                    "issue_refund",
                    "issue a refund",
                    write_effect=True,
                    params={"customer_id": "id", "amount_usd": "amt"},
                ),
            },
        ),
        ToolSpec(
            "support_email",
            "Outbound support e-mail",
            resource_class="mailbox",
            operations={
                "send": OperationSpec(
                    "send",
                    "send an e-mail",
                    external=True,
                    control_params=("recipient",),
                    params={"recipient": "to", "body": "text"},
                )
            },
        ),
    ]


def _sql_tools() -> list[ToolSpec]:
    return [
        ToolSpec(
            "warehouse_db",
            "Analytics warehouse",
            resource_class="warehouse_db",
            columns_param="columns",
            default_sensitivity=Sensitivity.INTERNAL,
            column_sensitivity={
                "order_id": Sensitivity.INTERNAL,
                "revenue_usd": Sensitivity.CONFIDENTIAL,
                "customer_email": Sensitivity.CONFIDENTIAL,
                "margin_pct": Sensitivity.RESTRICTED,
            },
            operations={
                "run_query": OperationSpec("run_query", "read-only SQL", params={"sql": "query", "columns": "cols"}),
                "drop_table": OperationSpec("drop_table", "drop a table", write_effect=True, params={"table": "name"}),
                "export_csv": OperationSpec(
                    "export_csv",
                    "export to external storage",
                    external=True,
                    control_params=("bucket",),
                    params={"bucket": "dest", "columns": "cols"},
                ),
            },
        )
    ]


def _itsm_tools() -> list[ToolSpec]:
    return [
        ToolSpec(
            "change_mgmt",
            "IT change management system",
            resource_class="itsm_db",
            operations={
                "read_ticket": OperationSpec("read_ticket", "read a change ticket", params={"ticket_id": "id"}),
                "apply_change": OperationSpec(
                    "apply_change",
                    "apply an infrastructure change",
                    write_effect=True,
                    params={"ticket_id": "id", "target_host": "host"},
                ),
                "revoke_access": OperationSpec(
                    "revoke_access", "revoke a principal's access", write_effect=True, params={"principal": "who"}
                ),
            },
        ),
        ToolSpec(
            "notify_oncall",
            "Page the on-call channel",
            resource_class="paging",
            operations={
                "send": OperationSpec(
                    "send",
                    "send a page",
                    external=True,
                    control_params=("channel",),
                    params={"channel": "dest", "body": "text"},
                )
            },
        ),
    ]


def _docs_tools() -> list[ToolSpec]:
    return [
        ToolSpec(
            "doc_store",
            "Internal document retrieval",
            resource_class="doc_store",
            columns_param="columns",
            default_sensitivity=Sensitivity.INTERNAL,
            column_sensitivity={
                "title": Sensitivity.PUBLIC,
                "body": Sensitivity.INTERNAL,
                "legal_hold_notes": Sensitivity.RESTRICTED,
            },
            operations={
                "search": OperationSpec("search", "search documents", params={"query": "q", "columns": "cols"}),
                "delete_doc": OperationSpec(
                    "delete_doc", "delete a document", write_effect=True, params={"doc_id": "id"}
                ),
            },
        ),
        ToolSpec(
            "publish",
            "Publish a synthesis to an external wiki",
            resource_class="wiki",
            operations={
                "publish": OperationSpec(
                    "publish",
                    "publish externally",
                    external=True,
                    control_params=("space",),
                    params={"space": "dest", "content": "text"},
                )
            },
        ),
    ]


def _code_tools() -> list[ToolSpec]:
    return [
        ToolSpec(
            "vcs",
            "Version control",
            resource_class="repo",
            operations={
                "read_diff": OperationSpec("read_diff", "read a PR diff", params={"pr_id": "id"}),
                "merge_pr": OperationSpec("merge_pr", "merge a PR", write_effect=True, params={"pr_id": "id"}),
                "push_branch": OperationSpec(
                    "push_branch",
                    "push to a remote",
                    write_effect=True,
                    external=True,
                    control_params=("remote",),
                    params={"remote": "url", "branch": "name"},
                ),
            },
        )
    ]


DOMAIN_TOOLS = {
    "customer_support": _support_tools,
    "sql_analysis": _sql_tools,
    "it_change_mgmt": _itsm_tools,
    "doc_retrieval_synthesis": _docs_tools,
    "code_review": _code_tools,
}


def _registry(domain: str) -> ToolRegistry:
    return ToolRegistry(tool(s) for s in DOMAIN_TOOLS[domain]())


def _spec(cid: str, domain: str, objective: str, constraints: tuple[str, ...], wf: Workflow) -> TaskSpec:
    return TaskSpec(cid, domain, objective, constraints, output_schema={}, workflow=wf)


# ----------------------------------------------------------------------------- pattern builders
def _langgraph_linear(cid: str, domain: str, worker_tools: tuple[str, ...], writer_tools: tuple[str, ...]) -> Workflow:
    """LangGraph StateGraph: linear node chain, each node a tool-bearing function over shared state
    (docs.langchain.com/oss/python/langgraph/graph-api -- StateGraph nodes read/write one shared state dict)."""
    return Workflow(
        (
            Step("retrieve", "worker", "Read the needed records for the request.", tools=worker_tools),
            Step(
                "act",
                "writer",
                "Act on the request using the retrieved records.",
                tools=writer_tools,
                depends_on=("retrieve",),
            ),
        )
    )


def _langgraph_branching(
    cid: str, domain: str, worker_tools: tuple[str, ...], writer_tools: tuple[str, ...]
) -> Workflow:
    """LangGraph with a router node fanning out to two tool nodes that both write into shared state
    before a final node (conditional edges into parallel tool nodes -- StateGraph.add_conditional_edges)."""
    return Workflow(
        (
            Step("route", "router", "Classify the request.", tools=()),
            Step("retrieve", "worker", "Handle the branch.", tools=worker_tools, depends_on=("route",)),
            Step(
                "finalize", "writer", "Finalize using the branch result.", tools=writer_tools, depends_on=("retrieve",)
            ),
        )
    )


def _crewai_sequential(cid: str, domain: str, worker_tools: tuple[str, ...], writer_tools: tuple[str, ...]) -> Workflow:
    """CrewAI sequential process: each agent has its OWN tool list, output feeds the next task
    (docs.crewai.com/concepts/processes -- Process.sequential, task.context chains outputs)."""
    return Workflow(
        (
            Step("research", "researcher", "Research the task.", tools=worker_tools),
            Step("execute", "executor", "Execute using the research.", tools=writer_tools, depends_on=("research",)),
        )
    )


def _crewai_hierarchical(
    cid: str, domain: str, worker_tools: tuple[str, ...], writer_tools: tuple[str, ...]
) -> Workflow:
    """CrewAI hierarchical process: a manager agent (no tools of its own) delegates to two workers,
    each with a distinct tool list (docs.crewai.com/concepts/processes -- Process.hierarchical)."""
    return Workflow(
        (
            Step("plan", "manager", "Delegate the request to the right specialist.", tools=()),
            Step(
                "worker_a",
                "worker",
                "Handle the read-side of the delegated task.",
                tools=worker_tools,
                depends_on=("plan",),
            ),
            Step(
                "worker_b",
                "writer",
                "Handle the write-side of the delegated task.",
                tools=writer_tools,
                depends_on=("worker_a",),
            ),
        )
    )


def _autogen_groupchat(cid: str, domain: str, worker_tools: tuple[str, ...], writer_tools: tuple[str, ...]) -> Workflow:
    """AutoGen GroupChat: every participant sees the full broadcast transcript, and any participant
    can be selected to call tools next (microsoft.github.io/autogen -- GroupChatManager broadcasts
    all messages to all participants). Modelled with HandoffMode.TRANSCRIPT in conditions.py so a
    single compromised participant's output reaches every later step's context, matching the
    broadcast semantics exactly."""
    return Workflow(
        (
            Step("propose", "worker", "Propose an action for the group.", tools=worker_tools),
            Step("act", "writer", "Act on the group's agreed action.", tools=writer_tools, depends_on=("propose",)),
        )
    )


PATTERN_BUILDERS = {
    "langgraph_linear": (_langgraph_linear, "langgraph"),
    "langgraph_branching": (_langgraph_branching, "langgraph"),
    "crewai_sequential": (_crewai_sequential, "crewai"),
    "crewai_hierarchical": (_crewai_hierarchical, "crewai"),
    "autogen_groupchat": (_autogen_groupchat, "autogen"),
}


# ----------------------------------------------------------------------------- domain-specific per-config wiring
def _all_ops(registry: ToolRegistry, tools: tuple[str, ...]) -> dict[str, frozenset[str]]:
    """What a framework integration typically grants: the WHOLE tool object once bound to a node/agent,
    i.e. every operation it exposes -- not a hand-curated per-operation allow-list. This is the
    realistic default (LangChain `@tool`-decorated functions, CrewAI `Agent(tools=[...])`, AutoGen
    `register_function`) that the least-privilege synthesis in this study is measured against."""
    return {t: frozenset(registry.get(t).spec.operations) for t in tools}


def _make(
    cid: str,
    domain: str,
    builder_key: str,
    worker_tools: tuple[str, ...],
    writer_tools: tuple[str, ...],
    objective: str,
    permitted: dict[str, frozenset[str]] | None,
    *,
    allow_write: bool = False,
    allow_external: bool = False,
    max_sensitivity: Sensitivity = Sensitivity.INTERNAL,
    nominal_calls: tuple[tuple[str, str, str, dict[str, object]], ...],
) -> RealWorldConfig:
    build, pattern = PATTERN_BUILDERS[builder_key]
    wf = build(cid, domain, worker_tools, writer_tools)
    roles = sorted({s.role for s in wf.steps})
    agents = tuple(AgentSpec(f"{r}-agent", r, f"{r} persona") for r in roles)
    registry = _registry(domain)
    grant = permitted if permitted is not None else _all_ops(registry, tuple({*worker_tools, *writer_tools}))
    policy = Policy(
        f"policy-{cid}",
        permitted=grant,
        max_sensitivity=max_sensitivity,
        allow_write=allow_write,
        allow_external=allow_external,
    )
    task = _spec(cid, domain, objective, (), wf)
    note = build.__doc__ or ""
    return RealWorldConfig(cid, domain, pattern, note.strip(), task, agents, policy, registry, nominal_calls)


def load_configs() -> tuple[RealWorldConfig, ...]:
    """19 configs: 5 domains x {linear/sequential, hierarchical/branching} patterns, plus 3 group-chat
    variants, chosen so every domain and all three frameworks are represented at least 3x.

    Tool grants use `permitted=None` (the whole tool object, i.e. every operation it exposes) by
    default, matching how LangGraph/CrewAI/AutoGen integrations actually bind tools to a node/agent
    -- a Python tool object, not a hand-curated per-operation allow-list. `allow_write`/`allow_external`
    follow the same realistic default: true whenever ANY delegated tool exposes such an operation,
    not only when the nominal task happens to use it. This is what makes over-provisioning visible
    to the analyser; the opposite (curated allow-lists matching nominal use exactly) is what the P/
    GPLUS bench conditions already cover in protocol-v1/v2/v3 and is not repeated here."""
    cfgs: list[RealWorldConfig] = []

    # --- customer_support (crm: query/update_account/issue_refund; support_email external) ---
    cfgs.append(
        _make(
            "support-01-langgraph-linear",
            "customer_support",
            "langgraph_linear",
            ("crm",),
            ("crm", "support_email"),
            "Look up the customer's account and answer their billing question by e-mail.",
            None,
            allow_write=True,
            allow_external=True,
            nominal_calls=(
                ("retrieve", "crm", "query", {"customer_id": "C-1", "columns": ["customer_id", "name"]}),
                ("act", "support_email", "send", {"recipient": "customer@corp.example", "body": "ok"}),
            ),
        )
    )
    cfgs.append(
        _make(
            "support-02-langgraph-branch",
            "customer_support",
            "langgraph_branching",
            ("crm",),
            ("crm", "support_email"),
            "Route the ticket, look up the account, and resolve it.",
            None,
            allow_write=True,
            allow_external=True,
            nominal_calls=(
                ("retrieve", "crm", "update_account", {"customer_id": "C-1", "columns": ["customer_id", "name"]}),
                ("finalize", "support_email", "send", {"recipient": "customer@corp.example", "body": "done"}),
            ),
        )
    )
    cfgs.append(
        _make(
            "support-03-crewai-sequential",
            "customer_support",
            "crewai_sequential",
            ("crm",),
            ("crm",),
            "Research the customer's history, then issue an approved refund.",
            None,
            allow_write=True,
            nominal_calls=(
                ("research", "crm", "query", {"customer_id": "C-1", "columns": ["customer_id", "name"]}),
                (
                    "execute",
                    "crm",
                    "issue_refund",
                    {"customer_id": "C-1", "amount_usd": 20, "columns": ["customer_id"]},
                ),
            ),
        )
    )
    cfgs.append(
        _make(
            "support-04-crewai-hierarchical",
            "customer_support",
            "crewai_hierarchical",
            ("crm",),
            ("crm", "support_email"),
            "Manager delegates lookup to worker A and the reply to worker B.",
            None,
            allow_write=True,
            allow_external=True,
            nominal_calls=(
                ("worker_a", "crm", "query", {"customer_id": "C-1", "columns": ["customer_id", "name"]}),
                ("worker_b", "support_email", "send", {"recipient": "customer@corp.example", "body": "ok"}),
            ),
        )
    )
    cfgs.append(
        _make(
            "support-05-autogen-groupchat",
            "customer_support",
            "autogen_groupchat",
            ("crm",),
            ("support_email",),
            "Group chat agrees an account note and e-mails the customer.",
            None,
            allow_write=True,
            allow_external=True,
            nominal_calls=(
                ("propose", "crm", "query", {"customer_id": "C-1", "columns": ["customer_id", "name"]}),
                ("act", "support_email", "send", {"recipient": "customer@corp.example", "body": "noted"}),
            ),
        )
    )

    # --- sql_analysis (warehouse_db: run_query/drop_table/export_csv) ---
    cfgs.append(
        _make(
            "sql-01-langgraph-linear",
            "sql_analysis",
            "langgraph_linear",
            ("warehouse_db",),
            ("warehouse_db",),
            "Run the requested read-only aggregate query and report totals.",
            None,
            allow_write=True,
            allow_external=True,
            nominal_calls=(
                ("retrieve", "warehouse_db", "run_query", {"sql": "SELECT 1", "columns": ["order_id"]}),
                ("act", "warehouse_db", "run_query", {"sql": "SELECT 2", "columns": ["order_id"]}),
            ),
        )
    )
    cfgs.append(
        _make(
            "sql-02-langgraph-branch",
            "sql_analysis",
            "langgraph_branching",
            ("warehouse_db",),
            ("warehouse_db",),
            "Classify the query, run it, and export the approved columns to the reporting bucket.",
            None,
            allow_write=True,
            allow_external=True,
            nominal_calls=(
                ("retrieve", "warehouse_db", "run_query", {"sql": "SELECT 1", "columns": ["order_id"]}),
                ("finalize", "warehouse_db", "export_csv", {"bucket": "reporting", "columns": ["order_id"]}),
            ),
        )
    )
    cfgs.append(
        _make(
            "sql-03-crewai-sequential",
            "sql_analysis",
            "crewai_sequential",
            ("warehouse_db",),
            ("warehouse_db",),
            "Analyst researches the schema, then the writer materializes a maintenance drop of a scratch table.",
            None,
            allow_write=True,
            allow_external=True,
            nominal_calls=(
                ("research", "warehouse_db", "run_query", {"sql": "SELECT 1", "columns": ["order_id"]}),
                ("execute", "warehouse_db", "drop_table", {"table": "scratch_tmp", "columns": ["order_id"]}),
            ),
        )
    )
    cfgs.append(
        _make(
            "sql-04-crewai-hierarchical",
            "sql_analysis",
            "crewai_hierarchical",
            ("warehouse_db",),
            ("warehouse_db",),
            "Manager assigns querying to worker A and exporting the result to worker B.",
            None,
            allow_write=True,
            allow_external=True,
            nominal_calls=(
                ("worker_a", "warehouse_db", "run_query", {"sql": "SELECT 1", "columns": ["order_id"]}),
                ("worker_b", "warehouse_db", "export_csv", {"bucket": "reporting", "columns": ["order_id"]}),
            ),
        )
    )
    cfgs.append(
        _make(
            "sql-05-autogen-groupchat",
            "sql_analysis",
            "autogen_groupchat",
            ("warehouse_db",),
            ("warehouse_db",),
            "Group chat proposes a query plan and one participant executes an export.",
            None,
            allow_write=True,
            allow_external=True,
            nominal_calls=(
                ("propose", "warehouse_db", "run_query", {"sql": "SELECT 1", "columns": ["order_id"]}),
                ("act", "warehouse_db", "export_csv", {"bucket": "reporting", "columns": ["order_id"]}),
            ),
        )
    )

    # --- it_change_mgmt (change_mgmt: read_ticket/apply_change/revoke_access; notify_oncall external) ---
    cfgs.append(
        _make(
            "itsm-01-langgraph-linear",
            "it_change_mgmt",
            "langgraph_linear",
            ("change_mgmt",),
            ("change_mgmt", "notify_oncall"),
            "Read the approved change ticket and apply it, then notify on-call.",
            None,
            allow_write=True,
            allow_external=True,
            nominal_calls=(
                ("retrieve", "change_mgmt", "read_ticket", {"ticket_id": "CHG-1"}),
                ("act", "change_mgmt", "apply_change", {"ticket_id": "CHG-1", "target_host": "host-1"}),
            ),
        )
    )
    cfgs.append(
        _make(
            "itsm-02-crewai-hierarchical",
            "it_change_mgmt",
            "crewai_hierarchical",
            ("change_mgmt",),
            ("change_mgmt",),
            "Manager assigns ticket review to worker A and applying the change to worker B.",
            None,
            allow_write=True,
            nominal_calls=(
                ("worker_a", "change_mgmt", "read_ticket", {"ticket_id": "CHG-1"}),
                ("worker_b", "change_mgmt", "apply_change", {"ticket_id": "CHG-1", "target_host": "host-1"}),
            ),
        )
    )
    cfgs.append(
        _make(
            "itsm-03-autogen-groupchat",
            "it_change_mgmt",
            "autogen_groupchat",
            ("change_mgmt",),
            ("change_mgmt", "notify_oncall"),
            "Group chat agrees a remediation and applies it, then pages on-call.",
            None,
            allow_write=True,
            allow_external=True,
            nominal_calls=(
                ("propose", "change_mgmt", "read_ticket", {"ticket_id": "CHG-1"}),
                ("act", "change_mgmt", "apply_change", {"ticket_id": "CHG-1", "target_host": "host-1"}),
            ),
        )
    )

    # --- doc_retrieval_synthesis (doc_store: search/delete_doc; publish external) ---
    cfgs.append(
        _make(
            "docs-01-langgraph-branch",
            "doc_retrieval_synthesis",
            "langgraph_branching",
            ("doc_store",),
            ("doc_store", "publish"),
            "Search internal docs, synthesize an answer, and publish it to the team wiki.",
            None,
            allow_write=True,
            allow_external=True,
            max_sensitivity=Sensitivity.INTERNAL,
            nominal_calls=(
                ("retrieve", "doc_store", "search", {"query": "policy", "columns": ["title", "body"]}),
                ("finalize", "publish", "publish", {"space": "team-wiki", "content": "summary"}),
            ),
        )
    )
    cfgs.append(
        _make(
            "docs-02-crewai-sequential",
            "doc_retrieval_synthesis",
            "crewai_sequential",
            ("doc_store",),
            ("doc_store",),
            "Researcher retrieves source docs; executor curates and deletes superseded drafts.",
            None,
            allow_write=True,
            nominal_calls=(
                ("research", "doc_store", "search", {"query": "policy", "columns": ["title", "body"]}),
                ("execute", "doc_store", "delete_doc", {"doc_id": "DRAFT-1", "columns": ["title", "body"]}),
            ),
        )
    )
    cfgs.append(
        _make(
            "docs-03-autogen-groupchat",
            "doc_retrieval_synthesis",
            "autogen_groupchat",
            ("doc_store",),
            ("publish",),
            "Group chat drafts a synthesis from search results and publishes it externally.",
            None,
            allow_write=True,
            allow_external=True,
            nominal_calls=(
                ("propose", "doc_store", "search", {"query": "policy", "columns": ["title", "body"]}),
                ("act", "publish", "publish", {"space": "team-wiki", "content": "summary"}),
            ),
        )
    )

    # --- code_review (vcs: read_diff/merge_pr/push_branch [write+external]) ---
    cfgs.append(
        _make(
            "code-01-langgraph-linear",
            "code_review",
            "langgraph_linear",
            ("vcs",),
            ("vcs",),
            "Read the PR diff and merge it once checks are green.",
            None,
            allow_write=True,
            allow_external=True,
            nominal_calls=(
                ("retrieve", "vcs", "read_diff", {"pr_id": "PR-1"}),
                ("act", "vcs", "merge_pr", {"pr_id": "PR-1"}),
            ),
        )
    )
    cfgs.append(
        _make(
            "code-02-crewai-hierarchical",
            "code_review",
            "crewai_hierarchical",
            ("vcs",),
            ("vcs",),
            "Manager assigns review to worker A and the merge to worker B.",
            None,
            allow_write=True,
            allow_external=True,
            nominal_calls=(
                ("worker_a", "vcs", "read_diff", {"pr_id": "PR-1"}),
                ("worker_b", "vcs", "merge_pr", {"pr_id": "PR-1"}),
            ),
        )
    )
    cfgs.append(
        _make(
            "code-03-autogen-groupchat",
            "code_review",
            "autogen_groupchat",
            ("vcs",),
            ("vcs",),
            "Group chat reviews a diff together and one participant merges it.",
            None,
            allow_write=True,
            allow_external=True,
            nominal_calls=(
                ("propose", "vcs", "read_diff", {"pr_id": "PR-1"}),
                ("act", "vcs", "merge_pr", {"pr_id": "PR-1"}),
            ),
        )
    )

    return tuple(cfgs)
