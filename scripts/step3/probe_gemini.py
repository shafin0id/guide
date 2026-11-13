"""S0 probe: which Gemini models support the multi-turn tool loop through the OpenAI-compatible endpoint."""

import json
import sys

import openai

from guide_agentdojo import spend

key = spend.resolve_key("GEMINI_API_KEY")
c = openai.OpenAI(api_key=key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
tools = [{"type": "function", "function": {"name": "get_balance", "description": "Get the account balance",
          "parameters": {"type": "object", "properties": {}}}}]
for model in sys.argv[1:]:
    for effort in (None, "none", "minimal"):
        kw = {"reasoning_effort": effort} if effort else {}
        try:
            r = c.chat.completions.create(model=model, messages=[{"role": "user", "content": "What is my balance? Use the tool."}],
                                          tools=tools, max_tokens=300, **kw)
            m = r.choices[0].message
            u = r.usage
            line = f"{model} effort={effort}: ok1 calls={bool(m.tool_calls)} in={u.prompt_tokens} out={u.completion_tokens}"
            if m.tool_calls:
                tc = m.tool_calls[0]
                msgs = [{"role": "user", "content": "What is my balance? Use the tool."},
                        {"role": "assistant", "content": m.content or "", "tool_calls": [
                            {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}]},
                        {"role": "tool", "tool_call_id": tc.id, "content": "balance: 100"}]
                try:
                    r2 = c.chat.completions.create(model=model, messages=msgs, tools=tools, max_tokens=300, **kw)
                    line += f" | turn2 OK in={r2.usage.prompt_tokens} out={r2.usage.completion_tokens} '{(r2.choices[0].message.content or '')[:40]}'"
                except Exception as e:  # noqa: BLE001
                    line += f" | turn2 FAIL {str(e)[:140]}"
            print(line, flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"{model} effort={effort}: FAIL {str(e)[:160]}", flush=True)
