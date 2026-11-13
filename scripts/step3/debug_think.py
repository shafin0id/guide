"""Debug helper: confirm non-thinking mode in each framework by completion-token count for a one-word answer."""

import asyncio
import os

from autogen_core.models import UserMessage

from guide_realworld import common
from guide_realworld.ag_apps import AutoGenApp
from guide_realworld.core import SYSTEM_DEFAULT, Runtime
from guide_realworld.scenarios import SCENARIOS

sc = SCENARIOS["finance"]
rt = Runtime(sc, "none", None, "x", "")


async def ag() -> None:
    app = AutoGenApp(sc, rt, SYSTEM_DEFAULT, "roundrobin")
    r = await app.client.create([UserMessage(content="Say hi in one word.", source="user")])
    print("autogen thought:", repr(r.thought), "completion_tokens", r.usage.completion_tokens)


asyncio.run(ag())

os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
from crewai import LLM  # noqa: E402

llm = LLM(model=f"openai/{common.MODEL}", base_url=common.BASE_URL, api_key=common.api_key(), temperature=0,
          extra_body=common.EXTRA_BODY)
out = llm.call("Say hi in one word.")
print("crewai out:", out, "usage", llm.get_token_usage_summary())

from langchain_openai import ChatOpenAI  # noqa: E402

m = ChatOpenAI(model=common.MODEL, base_url=common.BASE_URL, api_key=common.api_key(), temperature=0,
               extra_body=common.EXTRA_BODY)
r = m.invoke("Say hi in one word.")
print("langgraph out:", r.content, r.usage_metadata)
