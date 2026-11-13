"""Debug helper: show what the tool-filter LLM call returns for a few banking tasks."""

from agentdojo.benchmark import get_suite
from agentdojo.functions_runtime import FunctionsRuntime
from agentdojo.types import ChatSystemMessage, ChatUserMessage, text_content_block_from_string

from guide_agentdojo import run_v9

suite = get_suite("v1.2.2", "banking")
pipe = run_v9.make_pipeline("deepseek", "tool_filter", "default")
orig = pipe.client.chat.completions.create


def spy(**kw):
    r = orig(**kw)
    m = r.choices[0].message
    print("FILTER REPLY content=", repr(m.content)[:300], "| tool_calls=", [t.function.name for t in (m.tool_calls or [])])
    return r


pipe.client.chat.completions.create = spy
for tid in ("user_task_0", "user_task_1", "user_task_3"):
    rt = FunctionsRuntime(suite.tools)
    q = suite.user_tasks[tid].PROMPT
    msgs = [ChatSystemMessage(role="system", content=[text_content_block_from_string(pipe.system_message)]),
            ChatUserMessage(role="user", content=[text_content_block_from_string(q)])]
    pipe._apply_tool_filter(msgs, rt)
    print(tid, "kept", sorted(rt.functions))
