"""S0 probe for the isolated real-world environment: versions and imports of the three frameworks."""

import importlib.metadata as m

for p in ["langgraph", "langchain-openai", "langchain-core", "crewai", "autogen-agentchat", "autogen-ext", "openai", "litellm"]:
    try:
        print(p, m.version(p))
    except Exception:  # noqa: BLE001
        print(p, "MISSING")
from autogen_agentchat.agents import AssistantAgent  # noqa: E402,F401
from autogen_agentchat.teams import (  # noqa: E402,F401
    DiGraphBuilder,
    GraphFlow,
    RoundRobinGroupChat,
    SelectorGroupChat,
    Swarm,
)

print("autogen teams ok")
from crewai import LLM, Agent, Crew, Process, Task  # noqa: E402,F401
from crewai.tools import BaseTool, tool  # noqa: E402,F401

print("crewai ok")
try:
    from crewai.tasks.conditional_task import ConditionalTask  # noqa: F401

    print("conditional ok")
except Exception as e:  # noqa: BLE001
    print("cond", e)
from langgraph.graph import END, START, StateGraph  # noqa: E402,F401
from langgraph.types import Send  # noqa: E402,F401

print("langgraph ok")
