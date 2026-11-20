"""Protocol v7b: common config record shape + helpers shared by the three per-framework
extractors. See docs/static-analysis-extensions-plan.md §3.3.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ExtractedAgent:
    name: str
    role: str = ""
    tools: list[str] = field(default_factory=list)


@dataclass
class ExtractedStep:
    step_id: str
    agent: str
    tools: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)


@dataclass
class ExtractedConfig:
    framework: str
    repo: str
    sha: str
    file: str
    agents: list[ExtractedAgent]
    steps: list[ExtractedStep]
    process: str = ""
    unresolved: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "framework": self.framework,
            "repo": self.repo,
            "sha": self.sha,
            "file": self.file,
            "agents": [{"name": a.name, "role": a.role, "tools": a.tools} for a in self.agents],
            "steps": [
                {"id": s.step_id, "agent": s.agent, "tools": s.tools, "depends_on": s.depends_on} for s in self.steps
            ],
            "process": self.process,
            "unresolved": self.unresolved,
        }

    def n_agents(self) -> int:
        return len(self.agents)

    def n_tools_bound(self) -> int:
        return sum(len(a.tools) for a in self.agents) + sum(len(s.tools) for s in self.steps)

    def qualifies(self) -> bool:
        """§3.2 inclusion rule: >= 2 agents AND >= 1 tool bound to an agent."""
        return self.n_agents() >= 2 and self.n_tools_bound() >= 1
