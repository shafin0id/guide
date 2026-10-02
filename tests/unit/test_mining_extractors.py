"""Tests for guide_bench.mining extractors (protocol-v7b). Inline source strings only --
never cloned code, per docs/static-analysis-extensions-plan.md §3.7 step 1.
"""

from __future__ import annotations

from guide_bench.mining.classify import classify_tool
from guide_bench.mining.extract_autogen import extract_autogen
from guide_bench.mining.extract_crewai import extract_crewai_python
from guide_bench.mining.extract_langgraph import extract_langgraph


# ----------------------------------------------------------------------------- classify.py


def test_classify_known_tool_exact_match() -> None:
    assert classify_tool("PythonREPLTool") == ("external", "known_tool:PythonREPLTool")
    assert classify_tool("FileWriterTool") == ("write", "known_tool:FileWriterTool")
    assert classify_tool("SerperDevTool") == ("read", "known_tool:SerperDevTool")


def test_classify_send_email_prefix() -> None:
    cls, rule = classify_tool("SendEmailViaSMTP")
    assert cls == "external"
    assert rule.startswith("known_tool_prefix")


def test_classify_keyword_external_over_write() -> None:
    # "send" (external) must win over any write-token false positive
    cls, rule = classify_tool("send_slack_notification")
    assert cls == "external"


def test_classify_keyword_write() -> None:
    cls, rule = classify_tool("DeleteRecordTool")
    assert cls == "write"


def test_classify_default_read() -> None:
    cls, rule = classify_tool("get_weather_forecast")
    assert cls == "read"
    assert rule == "default_read"


# ----------------------------------------------------------------------------- crewai


CREWAI_SOURCE = """
from crewai import Agent, Task, Crew, Process

researcher = Agent(role="Researcher", tools=[SerperDevTool()])
writer = Agent(role="Writer", tools=[FileWriterTool()])

research_task = Task(description="research", agent=researcher)
write_task = Task(description="write", agent=writer, context=[research_task])

crew = Crew(agents=[researcher, writer], tasks=[research_task, write_task], process=Process.sequential)
"""


def test_extract_crewai_python_basic() -> None:
    configs = extract_crewai_python(CREWAI_SOURCE, "crew.py")
    assert len(configs) == 1
    cfg = configs[0]
    assert cfg.n_agents() == 2
    assert cfg.qualifies()
    step_ids = {s.step_id for s in cfg.steps}
    assert step_ids == {"research_task", "write_task"}
    write_step = next(s for s in cfg.steps if s.step_id == "write_task")
    assert write_step.depends_on == ["research_task"]


# ----------------------------------------------------------------------------- langgraph


LANGGRAPH_SOURCE = """
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent

researcher = create_react_agent(model, tools=[TavilySearchResults()])
writer_tools = ToolNode([FileWriterTool()])

def research_node(state):
    return researcher.invoke(state)

def write_node(state):
    return writer_tools.invoke(state)

graph = StateGraph(AgentState)
graph.add_node("research", research_node)
graph.add_node("write", write_node)
graph.add_edge("research", "write")
graph.set_entry_point("research")
"""


def test_extract_langgraph_basic() -> None:
    configs = extract_langgraph(LANGGRAPH_SOURCE, "graph.py")
    assert len(configs) == 1
    cfg = configs[0]
    assert cfg.n_agents() == 2
    write_step = next(s for s in cfg.steps if s.step_id == "write")
    assert write_step.depends_on == ["research"]


LANGGRAPH_SELF_ATTR_SOURCE = """
from langgraph.graph import StateGraph, END

class Builder:
    def __init__(self):
        self.graph = StateGraph(State)

    def build(self):
        self.graph.add_node("plan", PlanNode())
        self.graph.add_node("execute", execute_fn)
        self.graph.add_conditional_edges("plan", route, {"go": "execute", "stop": END})
        return self.graph.compile()

def execute_fn(state):
    return state
"""


def test_extract_langgraph_self_attribute_builder_pattern() -> None:
    """A common builder-class idiom: `self.graph = StateGraph(...)` then
    `self.graph.add_node(...)` inside instance methods, not a bare module-level variable."""
    configs = extract_langgraph(LANGGRAPH_SELF_ATTR_SOURCE, "builder.py")
    assert len(configs) == 1
    cfg = configs[0]
    assert {a.name for a in cfg.agents} == {"plan", "execute"}
    execute_step = next(s for s in cfg.steps if s.step_id == "execute")
    assert execute_step.depends_on == ["plan"]


# ----------------------------------------------------------------------------- autogen


AUTOGEN_SOURCE = """
from autogen import AssistantAgent, UserProxyAgent, GroupChat

assistant = AssistantAgent("assistant", tools=[search_tool])
executor = UserProxyAgent("executor", code_execution_config={"work_dir": "coding"})

chat = GroupChat(agents=[assistant, executor])
"""


def test_extract_autogen_basic() -> None:
    configs = extract_autogen(AUTOGEN_SOURCE, "chat.py")
    assert len(configs) == 1
    cfg = configs[0]
    assert cfg.n_agents() == 2
    executor_step = next(s for s in cfg.steps if s.agent == "executor")
    assert "code_executor" in executor_step.tools
