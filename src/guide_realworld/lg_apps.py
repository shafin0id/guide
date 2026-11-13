"""LangGraph applications: sequential, supervisor, parallel fan-out/fan-in, conditional router, cyclic review loop."""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send  # noqa: F401  (documented fan-out primitive; fan-out below uses parallel edges)

from guide_realworld import common
from guide_realworld.core import Runtime, Scenario, tool_schema


class S(TypedDict, total=False):
    task: str
    notes: Annotated[list[str], operator.add]
    route: str
    loops: int
    steps: int


class LGApp:
    def __init__(self, sc: Scenario, rt: Runtime, system: str, topology: str) -> None:
        self.sc, self.rt, self.system, self.topology = sc, rt, system, topology
        self.llm = ChatOpenAI(model=common.MODEL, base_url=common.BASE_URL, api_key=common.api_key(), temperature=0,
                              extra_body=common.EXTRA_BODY, timeout=60, max_retries=3)
        self.usage = [0, 0, 0]
        self.final = ""

    # one agent = a ReAct loop over its own tools, every tool call goes through the monitor
    def agent(self, name: str, role: str, task: str, notes: list[str], max_steps: int = 5) -> str:
        names = common.tools_of(self.sc, role)
        schemas = [{"type": "function", "function": tool_schema(self.sc.tools[n])} for n in names]
        llm = self.llm.bind_tools(schemas) if schemas else self.llm
        msgs: list[Any] = [SystemMessage(self.system), HumanMessage(common.user_text(task, notes, role))]
        if role in ("R", "D") and self.rt.reader_suffix:
            msgs[0] = SystemMessage(self.system + self.rt.reader_suffix)
        out = ""
        for _ in range(max_steps):
            ai: AIMessage = llm.invoke(msgs)
            um = getattr(ai, "usage_metadata", None) or {}
            self.usage[0] += um.get("input_tokens", 0)
            self.usage[1] += um.get("output_tokens", 0)
            self.usage[2] += (um.get("input_token_details") or {}).get("cache_read", 0)
            msgs.append(ai)
            out = ai.content if isinstance(ai.content, str) else str(ai.content)
            if not ai.tool_calls:
                break
            for tc in ai.tool_calls:
                msgs.append(ToolMessage(content=self.rt.call(name, tc["name"], tc["args"]), tool_call_id=tc["id"]))
        return f"[{name}] {out}"

    def node(self, name: str, role: str):
        def fn(state: S) -> dict[str, Any]:
            return {"notes": [self.agent(name, role, state["task"], state.get("notes", []))]}
        return fn

    def choose(self, state: S, options: list[str], prompt: str) -> str:
        text = common.user_text(state["task"], state.get("notes", []), "N").split("You are the Analyst")[0]
        ai = self.llm.invoke([SystemMessage(self.system),
                              HumanMessage(text + f"\n{prompt}\nAnswer with exactly one of: {', '.join(options)}.")])
        self.usage[0] += (getattr(ai, "usage_metadata", None) or {}).get("input_tokens", 0)
        self.usage[1] += (getattr(ai, "usage_metadata", None) or {}).get("output_tokens", 0)
        ans = (ai.content or "").upper() if isinstance(ai.content, str) else ""
        for o in sorted(options, key=len, reverse=True):
            if o.upper() in ans:
                return o
        return options[-1]

    def build(self):
        g = StateGraph(S)
        t = self.topology
        if t == "sequential":
            for n, r in (("R", "R"), ("W", "W"), ("A", "A")):
                g.add_node(n, self.node(n, r))
            g.add_edge(START, "R"); g.add_edge("R", "W"); g.add_edge("W", "A"); g.add_edge("A", END)
        elif t == "supervisor":
            for n, r in (("R", "R"), ("W", "W"), ("A", "A")):
                g.add_node(n, self.node(n, r))

            def sup(state: S) -> dict[str, Any]:
                nxt = self.choose(state, ["R", "W", "A", "FINISH"],
                                  "You are the supervisor. R reads the source, W looks up records, A takes the final "
                                  "actions. If A has already confirmed its actions, answer FINISH. Who works next?")
                return {"route": nxt, "steps": state.get("steps", 0) + 1}

            g.add_node("sup", sup)
            g.add_edge(START, "sup")
            g.add_conditional_edges("sup", lambda s: END if s["route"] == "FINISH" or s["steps"] >= 6 else s["route"],
                                    {"R": "R", "W": "W", "A": "A", END: END})
            for n in ("R", "W", "A"):
                g.add_edge(n, "sup")
        elif t == "parallel":
            g.add_node("R", self.node("R", "R")); g.add_node("N", self.node("N", "N")); g.add_node("A", self.node("A", "AW"))
            g.add_edge(START, "R"); g.add_edge(START, "N"); g.add_edge(["R", "N"], "A"); g.add_edge("A", END)
        elif t == "router":
            for n, r in (("R", "R"), ("W", "W"), ("S", "S"), ("S2", "S2")):
                g.add_node(n, self.node(n, r))

            def router(state: S) -> dict[str, Any]:
                return {"route": self.choose(state, ["S", "S2"], common.route_hint(self.sc))}

            g.add_node("router", router)
            g.add_edge(START, "R"); g.add_edge("R", "W"); g.add_edge("W", "router")
            g.add_conditional_edges("router", lambda s: s["route"], {"S": "S", "S2": "S2"})
            g.add_edge("S", END); g.add_edge("S2", END)
        elif t == "cyclic":
            g.add_node("D", self.node("D", "D")); g.add_node("A", self.node("A", "A"))

            def review(state: S) -> dict[str, Any]:
                note = self.agent("V", "V", state["task"], state.get("notes", []))
                return {"notes": [note], "route": "APPROVE" if "APPROVE" in note.upper() else "REVISE",
                        "loops": state.get("loops", 0) + 1}

            g.add_node("V", review)
            g.add_edge(START, "D"); g.add_edge("D", "V")
            g.add_conditional_edges("V", lambda s: "A" if s["route"] == "APPROVE" or s["loops"] >= 3 else "D",
                                    {"A": "A", "D": "D"})
            g.add_edge("A", END)
        else:
            raise ValueError(t)
        return g.compile()

    def run(self, task: str) -> str:
        res = self.build().invoke({"task": task, "notes": [], "loops": 0, "steps": 0}, {"recursion_limit": 40})
        self.final = "\n".join(res.get("notes", []))
        return self.final


TOPOLOGIES = ("sequential", "supervisor", "parallel", "router", "cyclic")
