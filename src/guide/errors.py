"""Structured exception hierarchy for GUIDE.

Every error raised by the framework derives from :class:`GuideError`, so callers can
catch framework failures without catching unrelated bugs. Errors carry a stable
``code`` for audit logs; messages must never contain secrets or restricted data.
"""

from __future__ import annotations


class GuideError(Exception):
    """Base class for all framework errors."""

    code = "GUIDE_ERROR"


class ConfigurationError(GuideError):
    """Invalid or missing configuration (never raised lazily at run time if avoidable)."""

    code = "CONFIGURATION_ERROR"


class ProviderError(GuideError):
    """A model provider call failed.

    ``retryable`` distinguishes transient failures (timeouts, 429, 5xx) from permanent ones.
    """

    code = "PROVIDER_ERROR"

    def __init__(self, message: str, *, retryable: bool = False, status: int | None = None):
        super().__init__(message)
        self.retryable = retryable
        self.status = status


class MalformedOutputError(GuideError):
    """A model response could not be parsed into the required structure."""

    code = "MALFORMED_OUTPUT"


class ToolError(GuideError):
    """A tool invocation failed."""

    code = "TOOL_ERROR"


class ToolNotFoundError(ToolError):
    code = "TOOL_NOT_FOUND"


class IntegrityError(GuideError):
    """A hand-off package or trace failed verification (proposal: REJECTED_INTEGRITY)."""

    code = "REJECTED_INTEGRITY"

    def __init__(self, reason: str):
        super().__init__(f"REJECTED_INTEGRITY: {reason}")
        self.reason = reason


class BudgetExceededError(GuideError):
    """A run exceeded its model-call, token or wall-clock budget."""

    code = "BUDGET_EXCEEDED"


class WorkflowError(GuideError):
    """A workflow definition is invalid (e.g. cyclic dependencies)."""

    code = "WORKFLOW_ERROR"
