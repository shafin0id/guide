"""GUIDE: policy-aware orchestration for LLM multi-agent workflows.

Stable public API. Anything not re-exported here is internal and may change without notice.
"""

from guide.agent import AgentSpec
from guide.errors import (
    ConfigurationError,
    GuideError,
    IntegrityError,
    MalformedOutputError,
    ProviderError,
    ToolError,
    WorkflowError,
)
from guide.handoff import ContentStore, IntentPackage, KeyRing, open_sealed, seal
from guide.policy import Decision, Policy, PolicyContext, PolicyDecision, PolicyEngine, RulePolicyEngine
from guide.providers import ModelProvider, ModelResponse, ModelSettings, OpenAICompatibleProvider, ScriptedProvider
from guide.routing import BayesUCBRouter, Router, RoutingDecision, StaticRouter
from guide.runtime import (
    CallRecord,
    ContentObserver,
    HandoffMode,
    RunRecord,
    Runtime,
    RuntimeConfig,
    Transport,
)
from guide.tools import OperationSpec, Tool, ToolRegistry, ToolSpec
from guide.trace import EventSink, JsonlSink, TraceEvent, TraceLedger
from guide.types import ChatMessage, Sensitivity, ToolCall, ToolResult, Trust, Usage
from guide.workflow import Step, TaskSpec, Workflow

__version__ = "0.3.0"

__all__ = [
    "AgentSpec",
    "BayesUCBRouter",
    "CallRecord",
    "ChatMessage",
    "ConfigurationError",
    "ContentObserver",
    "ContentStore",
    "Decision",
    "EventSink",
    "GuideError",
    "HandoffMode",
    "IntegrityError",
    "IntentPackage",
    "JsonlSink",
    "KeyRing",
    "MalformedOutputError",
    "ModelProvider",
    "ModelResponse",
    "ModelSettings",
    "OpenAICompatibleProvider",
    "OperationSpec",
    "Policy",
    "PolicyContext",
    "PolicyDecision",
    "PolicyEngine",
    "ProviderError",
    "Router",
    "RoutingDecision",
    "RulePolicyEngine",
    "RunRecord",
    "Runtime",
    "RuntimeConfig",
    "ScriptedProvider",
    "Sensitivity",
    "StaticRouter",
    "Step",
    "TaskSpec",
    "Tool",
    "ToolCall",
    "ToolError",
    "ToolRegistry",
    "ToolResult",
    "ToolSpec",
    "TraceEvent",
    "TraceLedger",
    "Transport",
    "Trust",
    "Usage",
    "Workflow",
    "WorkflowError",
    "open_sealed",
    "seal",
    "__version__",
]
