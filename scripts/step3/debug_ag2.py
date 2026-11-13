"""Debug helper: raw AutoGen client check (is thinking disabled?) and GraphFlow message sources."""

import asyncio

from autogen_core.models import UserMessage

from guide_realworld.ag_apps import AutoGenApp
from guide_realworld.core import SYSTEM_DEFAULT, Runtime
from guide_realworld.scenarios import SCENARIOS

sc = SCENARIOS["finance"]
rt = Runtime(sc, "none", None, sc.benign[0].prompt, "")
app = AutoGenApp(sc, rt, SYSTEM_DEFAULT, "graphflow_par")


async def main() -> None:
    r = await app.client.create([UserMessage(content="Say hi in one word.", source="user")])
    print("thought:", repr(r.thought), "usage", r.usage, "content", r.content)
    from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
    from autogen_agentchat.teams import DiGraphBuilder, GraphFlow

    R, N, A = app.agent("R", "R"), app.agent("N", "N"), app.agent("A", "A")
    b = DiGraphBuilder()
    b.add_node(R).add_node(N).add_node(A)
    b.add_edge(R, A).add_edge(N, A)
    team = GraphFlow([R, N, A], graph=b.build(), termination_condition=TextMentionTermination("TASK_DONE") | MaxMessageTermination(12))
    res = await team.run(task=sc.benign[0].prompt)
    for m in res.messages:
        print(type(m).__name__, getattr(m, "source", ""), str(getattr(m, "content", ""))[:100].replace("\n", " "))
    print("stop:", res.stop_reason)


asyncio.run(main())
