"""Debug helper: run one AutoGen app and print every message (S4 smoke diagnosis)."""

import asyncio
import sys

from guide_realworld.ag_apps import AutoGenApp
from guide_realworld.core import SYSTEM_DEFAULT, Runtime
from guide_realworld.scenarios import SCENARIOS

topo, sid = sys.argv[1], sys.argv[2]
sc = SCENARIOS[sid]
rt = Runtime(sc, "none", None, sc.benign[0].prompt, "")
app = AutoGenApp(sc, rt, SYSTEM_DEFAULT, topo)


async def main() -> None:
    try:
        await app.run(sc.benign[0].prompt)
    except Exception as e:  # noqa: BLE001
        print("ERR", type(e).__name__, str(e)[:1500])
    print("events", [(e["agent"], e["tool"]) for e in rt.events])
    print("final", app.final[:600])


asyncio.run(main())
