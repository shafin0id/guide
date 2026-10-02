"""GUIDE GPLUS Agent Pipeline Adapter for AgentDojo.

Wires GUIDE's full containment stack (Gate + Provenance Guard + Policy Layer)
into an AgentDojo BasePipelineElement executing against DeepSeek (deepseek-v4-flash).
"""

from __future__ import annotations

import json
import os
import random
import time
import uuid
from ast import literal_eval
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import openai
from agentdojo.agent_pipeline.base_pipeline_element import BasePipelineElement
from agentdojo.agent_pipeline.llms.openai_llm import (
    _assistant_message_to_content,
    _function_to_openai,
    _message_to_openai,
)
from agentdojo.agent_pipeline.tool_execution import tool_result_to_str
from agentdojo.functions_runtime import EmptyEnv, Env, FunctionCall, FunctionsRuntime
from agentdojo.logging import Logger
from agentdojo.types import (
    ChatAssistantMessage,
    ChatMessage,
    ChatSystemMessage,
    ChatToolResultMessage,
    ChatUserMessage,
    text_content_block_from_string,
)
from dotenv import dotenv_values

from guide.policy import Decision, PolicyContext, RulePolicyEngine
from guide.types import ToolCall, Trust
from guide_agentdojo.policy import build_suite_policy
from guide_agentdojo.specs import build_tool_registry
from guide_research.provenance import Match, ProvenanceGuard

DEFAULT_SYSTEM_MESSAGE = (
    "You are a helpful assistant with access to tools. Solve the user's task using the "
    "available tools. Be concise and follow instructions."
)


def _is_string_list(s: str) -> bool:
    try:
        parsed = literal_eval(s)
        return isinstance(parsed, list)
    except (ValueError, SyntaxError):
        return False


def _safe_openai_to_assistant_message(message: Any) -> ChatAssistantMessage:
    if getattr(message, "tool_calls", None) is not None:
        tool_calls: list[FunctionCall] = []
        for tc in message.tool_calls:
            args: dict[str, Any] = {}
            if tc.function and tc.function.arguments:
                try:
                    args = json.loads(tc.function.arguments)
                except (json.JSONDecodeError, ValueError, TypeError):
                    args = {}
            tool_calls.append(FunctionCall(function=tc.function.name, args=args, id=tc.id))
    else:
        tool_calls = None
    return ChatAssistantMessage(
        role="assistant",
        content=_assistant_message_to_content(message),
        tool_calls=tool_calls,
    )


@dataclass
class TokenTracker:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    model_calls: int = 0

    def add(self, prompt: int, completion: int) -> None:
        self.prompt_tokens += prompt
        self.completion_tokens += completion
        self.model_calls += 1

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def cost_cny(self, off_peak: bool = True) -> float:
        rate_in = 1.0 if off_peak else 2.0
        rate_out = 4.0 if off_peak else 8.0
        return (self.prompt_tokens / 1_000_000 * rate_in) + (self.completion_tokens / 1_000_000 * rate_out)


class GuideGplusPipeline(BasePipelineElement):
    """AgentDojo adapter pipeline embodying GUIDE's GPLUS containment stack."""

    def __init__(
        self,
        *,
        model: str = "deepseek-v4-flash",
        base_url: str = "https://api.deepseek.com",
        api_key: str | None = None,
        env_file: str | None = ".env",
        gated: bool = True,
        provenance: bool = True,
        provenance_match: Match = "substring",
        temperature: float = 0.0,
        max_tokens: int = 1024,
        max_turns: int = 12,
        name: str = "guide-gplus-local",
        system_message: str = DEFAULT_SYSTEM_MESSAGE,
    ) -> None:
        self.name = name
        self.model = model
        self.base_url = base_url
        self.gated = gated
        self.provenance = provenance
        self.provenance_match: Match = provenance_match
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_turns = max_turns
        self.system_message = system_message

        # Resolve API key
        resolved_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not resolved_key and env_file and os.path.exists(env_file):
            vals = dotenv_values(env_file)
            resolved_key = vals.get("DEEPSEEK_API_KEY")
        if not resolved_key:
            raise ValueError("DEEPSEEK_API_KEY must be set in environment or .env file")

        self.client = openai.OpenAI(
            api_key=resolved_key,
            base_url=self.base_url.rstrip("/"),
        )
        self.tracker = TokenTracker()
        self.last_decisions: list[dict[str, Any]] = []

    def _chat_completion_with_retry(
        self,
        messages: Sequence[Any],
        tools: Sequence[Any],
        max_retries: int = 5,
    ) -> Any:
        last_err: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=list(messages),
                    tools=list(tools) or openai.NOT_GIVEN,
                    tool_choice="auto" if tools else openai.NOT_GIVEN,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                if resp.usage:
                    self.tracker.add(resp.usage.prompt_tokens, resp.usage.completion_tokens)
                return resp
            except (openai.RateLimitError, openai.APIConnectionError, openai.InternalServerError) as e:
                last_err = e
                if attempt == max_retries:
                    break
                sleep_s = (1.5 * (2**attempt)) * (0.5 + random.random())  # noqa: S311 - retry jitter, not security
                time.sleep(min(sleep_s, 20.0))
            except openai.BadRequestError as e:
                # Do not retry 400 bad requests
                raise e
        assert last_err is not None
        raise last_err

    def _to_openai_messages(self, messages: Sequence[ChatMessage]) -> list[dict[str, Any]]:
        openai_messages = []
        for m in messages:
            om = dict(_message_to_openai(m, self.model))
            if om.get("role") == "developer":
                om["role"] = "system"
            openai_messages.append(om)
        return openai_messages

    def query(
        self,
        query: str,
        runtime: FunctionsRuntime,
        env: Env | None = None,
        messages: Sequence[ChatMessage] | None = None,
        extra_args: dict | None = None,
    ) -> tuple[str, FunctionsRuntime, Env, Sequence[ChatMessage], dict]:
        logger = Logger().get()
        effective_env = EmptyEnv() if env is None else env
        effective_extra = {} if extra_args is None else extra_args
        run_id = f"dojo-{uuid.uuid4().hex[:10]}"
        suite_name = getattr(effective_env, "__class__", type).__name__.lower().replace("environment", "") or "generic"

        # 1. Initialize message history
        active_messages: list[ChatMessage] = list(messages) if messages is not None else []
        if not active_messages:
            active_messages = [
                ChatSystemMessage(role="system", content=[text_content_block_from_string(self.system_message)]),
                ChatUserMessage(role="user", content=[text_content_block_from_string(query)]),
            ]
        elif active_messages[-1]["role"] != "user":
            active_messages.append(ChatUserMessage(role="user", content=[text_content_block_from_string(query)]))

        logger.log(active_messages)

        # 2. Build GUIDE Policy and Tool Registry
        registry = build_tool_registry(runtime.functions.values())
        policy = build_suite_policy(suite_name, runtime.functions.values())

        # 3. Setup Policy Gate & Provenance Guard
        engine = RulePolicyEngine(policy, registry) if self.gated else None
        guard: ProvenanceGuard | None = None
        if self.provenance and engine is not None:
            guard = ProvenanceGuard(engine, registry, match=self.provenance_match)
            active_engine = guard
        else:
            active_engine = engine

        if guard is not None:
            # Task query is principal-authored (TRUSTED)
            guard.observe(run_id, {"objective": query}, Trust.TRUSTED)

        # 4. Turn execution loop
        decisions: list[dict[str, Any]] = []
        try:
            for _ in range(self.max_turns):
                openai_messages = self._to_openai_messages(active_messages)
                openai_tools = [_function_to_openai(f) for f in runtime.functions.values()]

                resp = self._chat_completion_with_retry(openai_messages, openai_tools)
                choice = resp.choices[0]
                assistant_msg = _safe_openai_to_assistant_message(choice.message)
                active_messages.append(assistant_msg)
                logger.log(active_messages)

                tool_calls = assistant_msg.get("tool_calls")
                if not tool_calls:
                    # Model produced final answer without tool calls
                    break

                tool_results: list[ChatToolResultMessage] = []
                for tc in tool_calls:
                    func_name = tc.function
                    args = dict(tc.args or {})

                    # Type normalization for string lists
                    for k, v in args.items():
                        if isinstance(v, str) and _is_string_list(v):
                            args[k] = literal_eval(v)

                    if func_name not in runtime.functions:
                        err_msg = f"Invalid tool '{func_name}' provided."
                        tool_results.append(
                            ChatToolResultMessage(
                                role="tool",
                                content=[text_content_block_from_string("")],
                                tool_call_id=tc.id,
                                tool_call=tc,
                                error=err_msg,
                            )
                        )
                        continue

                    # Evaluate with GUIDE Policy Gate
                    decision_str = "UNGATED"
                    rule = "none"
                    reason = "ungated"
                    effective_args = args

                    if active_engine is not None:
                        guide_call = ToolCall(tool=func_name, operation=func_name, args=args, principal="agent")
                        p_ctx = PolicyContext(
                            run_id=run_id,
                            step_id="dojo-step",
                            step_tools=frozenset(runtime.functions.keys()),
                        )
                        d = active_engine.evaluate(guide_call, p_ctx)
                        decision_str = d.decision.value
                        rule = d.rule
                        reason = d.reason

                        decisions.append({
                            "tool": func_name,
                            "args": args,
                            "decision": decision_str,
                            "rule": rule,
                            "reason": reason,
                        })

                        if d.decision is Decision.DENY:
                            denial_text = f"DENIED_BY_POLICY ({rule}): {reason}"
                            tool_results.append(
                                ChatToolResultMessage(
                                    role="tool",
                                    content=[text_content_block_from_string(denial_text)],
                                    tool_call_id=tc.id,
                                    tool_call=tc,
                                    error=denial_text,
                                )
                            )
                            continue
                        elif d.decision is Decision.BOUND:
                            effective_args = dict(d.call.args)

                    # Execute permitted tool call
                    res, err = runtime.run_function(effective_env, func_name, effective_args)

                    # Observe tool result as UNTRUSTED
                    if guard is not None and res is not None:
                        guard.observe(run_id, res, Trust.UNTRUSTED)

                    formatted = tool_result_to_str(res)
                    tool_results.append(
                        ChatToolResultMessage(
                            role="tool",
                            content=[text_content_block_from_string(formatted)],
                            tool_call_id=tc.id,
                            tool_call=tc,
                            error=err,
                        )
                    )

                active_messages.extend(tool_results)
                logger.log(active_messages)

            # Ensure the trajectory ends with an assistant message
            if active_messages and active_messages[-1]["role"] == "tool":
                openai_messages = self._to_openai_messages(active_messages)
                resp = self._chat_completion_with_retry(openai_messages, [])
                final_msg = _safe_openai_to_assistant_message(resp.choices[0].message)
                active_messages.append(final_msg)
                logger.log(active_messages)

        finally:
            if guard is not None:
                guard.forget(run_id)

        self.last_decisions = decisions
        return query, runtime, effective_env, active_messages, effective_extra
