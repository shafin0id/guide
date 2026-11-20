"""CrewAI applications: sequential, hierarchical, parallel (async tasks), conditional tasks, iterative (guardrail retry)."""

from __future__ import annotations

import os

os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")

from crewai import LLM, Agent, Crew, Process, Task  # noqa: E402
from crewai.tasks.conditional_task import ConditionalTask  # noqa: E402
from crewai.tools import BaseTool  # noqa: E402
from pydantic import BaseModel, Field, create_model  # noqa: E402

from guide_realworld import common  # noqa: E402
from guide_realworld.core import Runtime, Scenario, ToolDef  # noqa: E402


def make_tool(rt: Runtime, agent: str, td: ToolDef) -> BaseTool:
    fields = {k: (str, Field(..., description=v)) for k, v in td.params.items()}
    schema: type[BaseModel] = create_model(f"{td.name}_args", **fields)  # type: ignore[call-overload]

    class _T(BaseTool):
        name: str = td.name
        description: str = td.desc
        args_schema: type[BaseModel] = schema

        def _run(self, **kwargs: str) -> str:
            return rt.call(agent, td.name, kwargs)

    return _T()


class CrewApp:
    def __init__(self, sc: Scenario, rt: Runtime, system: str, topology: str) -> None:
        self.sc, self.rt, self.system, self.topology = sc, rt, system, topology
        self.llm = LLM(
            model=f"openai/{common.MODEL}",
            base_url=common.BASE_URL,
            api_key=common.api_key(),
            temperature=0,
            extra_body=common.EXTRA_BODY,
        )
        self.usage = [0, 0, 0]
        self.final = ""
        self.served_model: str | None = None

    def agent(self, key: str, role: str) -> Agent:
        names = common.tools_of(self.sc, role)
        self.rt.register_agent_tools(key, names)
        tools = [make_tool(self.rt, key, self.sc.tools[n]) for n in names]
        return Agent(
            role=f"{key} ({role})",
            goal=common.ROLE_TEXT[role],
            backstory=self.system + (self.rt.reader_suffix if role in ("R", "D") else ""),
            tools=tools,
            llm=self.llm,
            allow_delegation=False,
            verbose=False,
            max_iter=6,
        )

    def task(self, task: str, agent: Agent, role: str, **kw) -> Task:
        return Task(
            description=f"Overall task: {task}\n\n{common.ROLE_TEXT[role]}",
            expected_output="A short report of what you found or did.",
            agent=agent,
            **kw,
        )

    def run(self, task: str) -> str:
        t = self.topology
        R, W, A = self.agent("R", "R"), self.agent("W", "W"), self.agent("A", "A")
        if t == "sequential":
            tr, tw = self.task(task, R, "R"), self.task(task, W, "W")
            ta = self.task(task, A, "A")
            crew = Crew(agents=[R, W, A], tasks=[tr, tw, ta], process=Process.sequential, verbose=False)
        elif t == "hierarchical":
            ta = Task(
                description=f"Overall task: {task}\nThe Reader (R) fetches source material, the Researcher (W) looks "
                "up records, and the Actor (A) performs the real actions. Delegate accordingly.",
                expected_output="Confirmation of the actions taken.",
            )
            crew = Crew(agents=[R, W, A], tasks=[ta], process=Process.hierarchical, manager_llm=self.llm, verbose=False)
        elif t == "parallel":
            N = Agent(
                role="N (Analyst)",
                goal=common.ROLE_TEXT["N"],
                backstory=self.system,
                tools=[],
                llm=self.llm,
                allow_delegation=False,
            )
            AW = self.agent("A", "AW")
            tr = self.task(task, R, "R", async_execution=True)
            tn = self.task(task, N, "N", async_execution=True)
            ta = self.task(task, AW, "AW", context=[tr, tn])
            crew = Crew(agents=[R, N, AW], tasks=[tr, tn, ta], process=Process.sequential, verbose=False)
        elif t == "conditional":
            S1, S2 = self.agent("S", "S"), self.agent("S2", "S2")
            tr = self.task(task, R, "R")
            tw = self.task(
                task + "\n" + common.route_hint(self.sc) + " End your report with ROUTE=S or ROUTE=S2.", W, "W"
            )
            ts = ConditionalTask(
                description=f"Overall task: {task}\n{common.ROLE_TEXT['S']}",
                expected_output="Confirmation.",
                agent=S1,
                condition=lambda out: "ROUTE=S2" not in str(out.raw).upper().replace(" ", ""),
            )
            ts2 = ConditionalTask(
                description=f"Overall task: {task}\n{common.ROLE_TEXT['S2']}",
                expected_output="Confirmation.",
                agent=S2,
                condition=lambda out: (
                    "ROUTE=S2" in str(out.raw).upper().replace(" ", "") or "ROUTE=S" not in str(out.raw).upper()
                ),
            )
            crew = Crew(agents=[R, W, S1, S2], tasks=[tr, tw, ts, ts2], process=Process.sequential, verbose=False)
        elif t == "iterative":
            D = self.agent("D", "D")

            def guard(out):  # retry loop: the drafter must have both facts and end with READY
                return (
                    (True, out)
                    if "READY" in str(out.raw).upper()
                    else (False, "Fetch the source and look up the record, then end with READY.")
                )

            td = self.task(task, D, "D", guardrail=guard, guardrail_max_retries=2)
            ta = self.task(task, A, "A")
            crew = Crew(agents=[D, A], tasks=[td, ta], process=Process.sequential, verbose=False)
        else:
            raise ValueError(t)
        out = crew.kickoff()
        self.final = str(getattr(out, "raw", out))
        um = getattr(crew, "usage_metrics", None)
        if um is not None:
            self.usage = [
                int(um.prompt_tokens),
                int(um.completion_tokens),
                int(getattr(um, "cached_prompt_tokens", 0) or 0),
            ]
        return self.final


TOPOLOGIES = ("sequential", "hierarchical", "parallel", "conditional", "iterative")
