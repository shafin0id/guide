"""AutoGen (AgentChat 0.7) applications: round-robin, selector, swarm handoffs, GraphFlow sequential and parallel."""

from __future__ import annotations

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import DiGraphBuilder, GraphFlow, RoundRobinGroupChat, SelectorGroupChat, Swarm
from autogen_core.tools import FunctionTool
from autogen_ext.models.openai import OpenAIChatCompletionClient

from guide_realworld import common
from guide_realworld.core import Runtime, Scenario, ToolDef

DONE = "TASK_DONE"


def make_fn(rt: Runtime, agent: str, td: ToolDef) -> FunctionTool:
    params = list(td.params)
    sig = ", ".join(f"{p}: str" for p in params)
    body = "{" + ", ".join(f"{p!r}: {p}" for p in params) + "}"
    ns: dict = {"_call": lambda a: rt.call(agent, td.name, a)}
    exec(f"def {td.name}({sig}) -> str:\n    return _call({body})\n", ns)  # noqa: S102 - generated from fixed tool metadata
    return FunctionTool(ns[td.name], description=td.desc, name=td.name)


class AutoGenApp:
    def __init__(self, sc: Scenario, rt: Runtime, system: str, topology: str) -> None:
        self.sc, self.rt, self.system, self.topology = sc, rt, system, topology
        self.client = OpenAIChatCompletionClient(
            model=common.MODEL, base_url=common.BASE_URL, api_key=common.api_key(), temperature=0,
            model_info={"vision": False, "function_calling": True, "json_output": True, "family": "unknown",
                        "structured_output": True},
            extra_create_args={"extra_body": common.EXTRA_BODY},
        )
        orig = self.client._client.chat.completions.create

        async def _create(*a, **kw):  # AutoGen drops per-request extra_body: force non-thinking mode here
            kw["extra_body"] = {**(kw.get("extra_body") or {}), **common.EXTRA_BODY}
            return await orig(*a, **kw)

        self.client._client.chat.completions.create = _create  # type: ignore[method-assign]
        self.usage = [0, 0, 0]
        self.final = ""

    def agent(self, key: str, role: str, handoffs: list[str] | None = None) -> AssistantAgent:
        tools = [make_fn(self.rt, key, self.sc.tools[n]) for n in common.tools_of(self.sc, role)]
        sys_msg = f"{self.system}\n{common.ROLE_TEXT[role]}"
        if role in ("R", "D") and self.rt.reader_suffix:
            sys_msg += self.rt.reader_suffix
        if role in ("A", "AW", "S", "S2"):
            sys_msg += f" When all required actions are done, end your message with {DONE}."
        return AssistantAgent(key, model_client=self.client, tools=tools or None, system_message=sys_msg,
                              reflect_on_tool_use=bool(tools), handoffs=handoffs,
                              description=common.ROLE_TEXT[role], max_tool_iterations=3)

    async def run(self, task: str) -> str:
        t = self.topology
        term = TextMentionTermination(DONE) | MaxMessageTermination(12)
        R, W, A = self.agent("R", "R"), self.agent("W", "W"), self.agent("A", "A")
        if t == "roundrobin":
            team = RoundRobinGroupChat([R, W, A], termination_condition=term)
        elif t == "selector":
            team = SelectorGroupChat([R, W, A], model_client=self.client, termination_condition=term,
                                     allow_repeated_speaker=False)
        elif t == "swarm":
            R, W, A = self.agent("R", "R", ["W"]), self.agent("W", "W", ["A"]), self.agent("A", "A", ["R"])
            team = Swarm([R, W, A], termination_condition=term)
        elif t == "graphflow_seq":
            b = DiGraphBuilder()
            b.add_node(R).add_node(W).add_node(A)
            b.add_edge(R, W).add_edge(W, A)
            team = GraphFlow([R, W, A], graph=b.build(), termination_condition=term)
        elif t == "graphflow_par":
            N, A = self.agent("N", "N"), self.agent("A", "AW")
            b = DiGraphBuilder()
            b.add_node(R).add_node(N).add_node(A)
            b.add_edge(R, A).add_edge(N, A)
            team = GraphFlow([R, N, A], graph=b.build(), termination_condition=term)
        else:
            raise ValueError(t)
        res = await team.run(task=task)
        for m in res.messages:
            u = getattr(m, "models_usage", None)
            if u:
                self.usage[0] += u.prompt_tokens
                self.usage[1] += u.completion_tokens
        self.final = "\n".join(str(getattr(m, "content", ""))[:300] for m in res.messages[-3:])
        return self.final


TOPOLOGIES = ("roundrobin", "selector", "swarm", "graphflow_seq", "graphflow_par")
