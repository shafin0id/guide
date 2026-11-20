# Stage 6 — Real-World Mined Workflow Provenance, Extractor, and Classifier Audit

Generated: 2026-11-20 UTC  
Audit script: [`version-2/scripts/stage6_audit_mining.py`](../scripts/stage6_audit_mining.py)  
Raw audit ledger: [`version-2/results/offline/mining_audit.json`](../results/offline/mining_audit.json)  
Audited dataset: `version-2/workspace/experiments/mining/configs.jsonl` (all **37** records: 36 CrewAI + 1 LangGraph).

---

## 1. Executive Summary (`ISS-035` — High Severity)

Re-fetching every single one of the 37 mined configurations directly from GitHub at its recorded immutable commit SHA (`raw.githubusercontent.com/<repo>/<sha>/<file>`) and auditing all 37 parsed JSONL structures uncovered **four major validity flaws** in Protocol v7b / Table 11:

1. **Frozen Tool Classifier Has 30.0% Recall (`3/10`) and Undercounts Sinks by 3×–6×:**
   - The frozen keyword rule in `src/guide_bench/mining/classify.py` (`_WRITE_TOKENS` contains `"write"` but NOT `"writer"`, `"add"`, or `"store"`) achieved **100.0% precision (`3/3`)** but only **30.0% recall (`3/10`)** over the 60 unique CrewAI tools!
   - It missed **7 unambiguous write/persistence tools**: `file_writer_tool`, `file_writer_tool_summary`, `file_writer_tool_action_items`, `file_writer_tool_sentiment`, `user_add_tool`, `graph_add_tool`, and `store_memory`.
   - Furthermore, **5 CrewAI configs** write files directly to disk via CrewAI's native task parameter `output_file=...` (which is never modeled as a tool call by the extractor).
2. **Extractor Silently Dropped All Tools in 5 of 36 CrewAI Configs (`13.9%`):**
   - On indices **`12, 13, 15, 23, 32`** (`splx-ai/agentic-radar` ×2, `liangdabiao/easy_investment_Agent_crewai`, `agentcontrol/agent-control`, `brightdata/geo-ai-agent`), `extract_crewai.py` failed to bind tasks in `tasks.yaml` to agents in `agents.yaml`, emitting `"agent": "__unresolved__"` and `"tools": []` on every step.
   - Because `to_model.py` reads tools only from `cfg.steps` (not `cfg.agents`), **all declared agent tools were silently erased** — including `write_report` on `agentcontrol/agent-control` (index 23)!
3. **Exact-File Duplicate Inflation (`36` rows = only `32` unique files across `21` repos):**
   - `apify/apify-sdk-python` (`indices 29, 30, 31`) accounts for **3 byte-identical copies** of the exact same `14_crewai.py` file (`version-3.4`, `version-4.0`, and `docs`).
   - `tylerprogramming/ai` (`indices 10, 11`) has **2 byte-identical** `agents.yaml` files (`day_03` vs `day_05`, differing only by `CustomSerperDevTool` vs `SerperDevTool` in Python code).
   - `getzep/zep` (`indices 4, 5`) extracts 2 distinct Crews from one file (`crewai_tools.py`).
   - `kid0317/crewai_mas_demo/m2l10` (`index 33`) extracted only **1 step** (`task`) despite having 2 declared agents; `m1l3` (`index 35`) extracted only 2 of 4 agents into steps.
4. **Immutable Provenance Check (`36/37` HTTP 200; `1/37` HTTP 404):**
   - All **36/36 CrewAI files** resolved HTTP 200 at their exact recorded commit SHAs on `2026-11-20`.
   - The **1 LangGraph file** (`zhongyu09/openchatbi@79bb4b1da7d1682baabd89d89aeefe7db004121f`, `openchatbi/text2sql/sql_graph.py`) returned **HTTP 404** (commit or path no longer reachable at that SHA on GitHub).
   - **Convenience-sample limitation:** All 36 CrewAI configs come from 21 public tutorial, SDK-example, or course repositories (`500-AI-Agents-Projects`, `crewai_mas_demo`, `openinference`, `apify-sdk-python`, etc.), and **0 AutoGen** and **0 acyclic LangGraph** workflows qualified. These counts **cannot** be generalized to all deployed multi-agent systems!

---

## 2. Reconciled Sink Prevalence: Historical Frozen Count vs Manual Audit

| Definition of Sink-Bearing CrewAI Config | Count (of 36 rows) | % of 36 | Count (of 33 deduplicated workflows\*) | % of 33 |
|---|---:|---:|---:|---:|
| **Historical Table 11 (frozen classifier on extracted steps)** | **2 / 36** | **5.6%** | 2 / 33 | 6.1% |
| Corrected sink classification on extracted steps (`writer`/`add`/`store` fixed) | **6 / 36** | **16.7%** | 6 / 33 | 18.2% |
| Corrected sink classification including dropped `__unresolved__` agent tools (`write_report`) | **7 / 36** | **19.4%** | 7 / 33 | 21.2% |
| Including native CrewAI `output_file` disk-write task parameters in verified source | **12 / 36** | **33.3%** | 12 / 33 | 36.4% |

\* Deduplicated workflows removes the 2 verbatim doc-version duplicates of `apify/apify-sdk-python` (`indices 30, 31`) and the identical `day_03`/`day_05` duplicate (`index 11`), leaving `33` distinct extracted workflows across `21` repos (`5` of which still have unresolved task-to-agent mappings).

### Detailed Sink-Bearing Configs Found by Manual Audit

| Idx | Repo | File | Frozen Sink? | Audit Sink Tools | `output_file` in Source? | Extractor Bug? |
|---:|---|---|---|---|---|---|
| 4 | `getzep/zep` | `integrations/crewai/python/examples/crewai_tools.py` (Crew 1) | No | `user_add_tool`, `graph_add_tool` | No | Classifier FN (`add`) |
| 5 | `getzep/zep` | `integrations/crewai/python/examples/crewai_tools.py` (Crew 2) | No | `user_add_tool` | No | Classifier FN (`add`) |
| 6 | `agentstack-ai/AgentStack` | `examples/stock_market_research/.../agents.yaml` | No | — | **Yes** (`tasks.yaml`) | Unmodeled `output_file` |
| 9 | `tylerprogramming/ai` | `.../meeting_minutes_crew/config/agents.yaml` | No | `file_writer_tool_{summary,action_items,sentiment}` | No | Classifier FN (`writer`) |
| 14 | `kingsidharth/podcaster_crew` | `src/podcaster/config/agents.yaml` | No | `file_writer_tool` | No | Classifier FN (`writer`) |
| 23 | `agentcontrol/agent-control` | `.../secure_research_crew/config/agents.yaml` | No | `write_report` (on agent `writer`) | No | **All steps `__unresolved__` (dropped tool!)** |
| 28 | `nexi-lab/nexus` | `examples/crewai/crewai_nexus_demo.py` | **Yes** (`write_file`) | `write_file`, `store_memory` | No | Missed `store_memory` |
| 35 | `kid0317/crewai_mas_demo` | `m1l3/m1l3_multi_agent.py` | **Yes** (`FileWriterTool`) | `FileWriterTool` | No | Dropped 2 of 4 agents (`searcher`, `editor`) |
| +4 | Other configs with `output_file` in verified source | (`indices 10/11, 21, 32` or sibling `tasks.yaml`) | No | — | **Yes** | Unmodeled `output_file` |

---

## 3. Extractor Bug Check on Topology Structure (`audit.py` + `extract_crewai.py`)

- **Why 100% of extracted CrewAI configs were `"sequential"`:** `extract_crewai.py` defaults to `"sequential"` unless an explicit `Process.hierarchical` AST call is parsed; however, index 2 (`ashishpatel26/500-AI-Agents-Projects/lesson_02/agent.py`) mentions hierarchical in source text while running sequential tasks. More importantly, **CrewAI's tutorial ecosystem itself heavily defaults to `Process.sequential`**, and the AST extractor failed to parse `LangGraph` (`1/1` cyclic) and `AutoGen` (`0` qualified), inducing severe **survivorship bias toward sequential chains**.
- **Consequence for Table 10 & Table 11:**
  1. **Withdraw** the headline prevalence claim `"94.4% of real-world workflows have no write/external sink"` (`Table 11`). Present the mining census strictly as a **small exploratory convenience sample of 36 CrewAI example scripts (32 unique files / 33 deduplicated workflows across 21 repos)**, showing BOTH the frozen lower-bound classifier (`2/36 = 5.6%`) AND the manual-audit correction (`7/36 = 19.4%` explicit sink tools; `12/36 = 33.3%` including `output_file`), plus the `5/36` unresolved-agent extractor failures.
  2. **Qualify Table 10 (`49/55 = 89.1%` linear chains):** Explicitly separate the `19` author-constructed enterprise patterns from the `36` mined CrewAI example scripts (`32` unique files), acknowledge survivorship bias from the AST extractor (which excluded cyclic LangGraph and captured 0 AutoGen workflows), and **never generalize** `89.1%` to all deployed multi-agent systems!
  3. **Add independently sourced branching/non-chain workflows in Stage 7D** to empirically exercise Proposition 3/4 on genuine multi-branch DAGs where partitioning *does* reduce worst-case blast radius.
