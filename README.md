# GUIDE: an external reference monitor for LLM multi-agent workflows

GUIDE is an external reference monitor for LLM multi-agent workflows (MSc AI dissertation, APU/DMU, CT095-6-M-RMCE; author Shafin Ahmad;
supervisors Ts. Dr. Maythem Kamal and Dr. R Logeswaran). It sits outside the model and the agents and applies four connected controls to every proposed tool call and delegation:

1. **Outcome-based routing:** Bayes-UCB over per-agent success evidence, with optional re-dispatch on step failure.
2. **Signed, hash-linked hand-offs:** each agent has its own Ed25519 key; packages are checked for lineage, receiver and expiry.
3. **Pre-execution policy gate:** calls are allowed, bounded (e.g. restricted columns removed, limits clamped) or denied before any tool runs.
4. **Hash-linked trace** of routing, hand-off, policy, tool and output events.

> **Status: alpha, research code.** No security certification is implied. An earlier README (v2.4) reported benchmark
> results that were produced by the evaluation code rather than by the system. Those results are withdrawn; see
> [`docs/research-audit.md`](docs/research-audit.md). The audited code is preserved at tag `baseline-v0`.

## What the evidence shows (single model family, synthetic sandbox; details in [`docs/experiments.md`](docs/experiments.md))

* **Nominal tasks (18 tasks × 4 conditions × 5 reps):** no measurable quality benefit. Every condition solved about 97 % of
  tasks (ceiling effect). Overhead was small: median wall time was about +3 % versus the static-graph baseline.
* **Degraded agent:** a static assignment failed 20/20 runs. Adaptive routing failed once (warm-up), and routing plus
  re-dispatch failed 0/20.
* **Hand-off integrity:** 10 mutation classes were detected at 100 % with 0 false rejections. Per-principal keys detect
  sender spoofing, which the earlier shared-key design could not (0 %).
* **Prompt injection:** this model ignored every textual injection in the suite in every condition, so injection
  resistance could not be measured.
* **Assumed compromise** (an agent's proposal replaced by the attacker's call, 5 runs per cell): ungated baselines
  violated in 30/30 runs (external e-mail, in-domain e-mail, deletion). Baseline GUIDE (P) contained external e-mail and
  deletion, but not in-domain e-mail (5/15 violations). Improved GUIDE contained all of them (0/15). The provenance guard
  alone accounts for the in-domain case; it is a heuristic with known bypasses ([limitations](docs/limitations.md)).
* **Negative result:** with protocol-v1, signed hand-offs *lowered* task success on adversarial tasks (0.86 vs 1.00).
  The cause was an implementation confound (agents saw sorted-key JSON). It was fixed and confirmed under protocol-v2.

## Install

```bash
pip install -e ".[openai]"      # core + OpenAI-compatible HTTP provider
pip install -e ".[dev]"         # + tests, lint, type checking, statistics
```

The core depends only on `cryptography`.

## Quick start

```python
from guide import (AgentSpec, BayesUCBRouter, HandoffMode, OpenAICompatibleProvider, Policy, RulePolicyEngine,
                   Runtime, RuntimeConfig, Step, TaskSpec, ToolRegistry, Workflow)
from guide_bench.env import Environment  # sandbox tools used in the experiments; use your own Tool implementations

env = Environment()
registry = ToolRegistry(env.tools)
policy = Policy("read-only", {"procurement_db": frozenset({"query"})})
provider = OpenAICompatibleProvider(model="deepseek-chat", base_url="https://api.deepseek.com",
                                    api_key_env="DEEPSEEK_API_KEY")
agents = [AgentSpec("retriever-a", "retriever", "You retrieve records."),
          AgentSpec("reporter-a", "reporter", "You write the final JSON deliverable.")]
runtime = Runtime(provider, registry, agents, policy,
                  RuntimeConfig(handoff_mode=HandoffMode.SIGNED, router=BayesUCBRouter(),
                                policy_engine=RulePolicyEngine(policy, registry)))
task = TaskSpec("demo", "procurement", "Summarise SLA terms of vendor V-001.",
                ("Report delivery_sla_days.", "Do not disclose unit prices."),
                {"vendor_id": "string", "delivery_sla_days": "number"},
                Workflow((Step("retrieve", "retriever", "Retrieve the vendor record.", tools=("procurement_db",)),
                          Step("report", "reporter", "Write the deliverable.", depends_on=("retrieve",)))))
record = runtime.run(task)
print(record.status, record.final_output, record.trace_intact)
```

## Repository layout (three boundaries)

| Layer | Package | Purpose |
|---|---|---|
| GUIDE Core | `src/guide` | stable primitives: providers, tools, policy, hand-off, trace, routing, runtime (public API = `guide/__init__.py`) |
| GUIDE Research | `src/guide_research` | experimental mechanisms under evaluation (`provenance`, `provenance_v9`, `blast_radius`, `topology`, `topology_theory`) |
| GUIDE Bench & Real-World | `src/guide_bench`, `src/guide_agentdojo`, `src/guide_realworld` | tasks, sandbox, AgentDojo harness, real LangGraph/CrewAI/AutoGen applications, condition-blind scoring, runner, statistics |

Dependencies point one way only (Core ← Research ← Bench), enforced by `scripts/check_boundaries.py` in CI.

## Reproduce

See [REPRODUCE.md](REPRODUCE.md) for complete instructions to reproduce every table and metric in the paper (Protocols v1 to v9).

Quick check:

```bash
.venv/bin/python -m pytest -q                                                   # Unit test suite, no network
.venv/bin/python scripts/step3/verify_complete.py                                # Verify Step 3 (Protocol v9) completeness
.venv/bin/python -u scripts/final/run_final.py --stage check_numbers             # Verify paper_numbers.json against manuscript
.venv/bin/python scripts/paper/verify_docx_numbers.py docs/paper/revision-v2/GUIDE_Manuscript_Revised_V2.docx
```

## Paper artefacts

The research paper evaluates GUIDE as an external reference monitor for LLM multi-agent systems across formal proofs, synthetic benchmarks, AgentDojo, and real-framework applications:

- [Revised V2 manuscript](docs/paper/revision-v2/GUIDE_Manuscript_Revised_V2.md) and [supplementary material](docs/paper/revision-v2/GUIDE_Supplementary_Material_V2.md) (`.docx` companions and revision log in `docs/paper/revision-v2/`).
- [Reproduction guide](REPRODUCE.md): step-by-step commands and verification for every table and empirical finding across protocols v1 to v9.
- [Formal model and proofs](docs/formal_model.md): complete definitions, Theorem 1 and Theorem 2 blast-radius containment, Proposition 3 topology monotonicity, and Proposition 4 linear chain closed-form bounds.
- [Final run results](docs/final-run-results.md) & [Step 3 results](docs/step3-results.md): execution logs and metric summaries for Protocols v8 and v9.
- [Benchmark experiment logs](docs/experiments.md): detailed records covering protocols v1 to v8.

### Experimental result directories

- `experiments/results/step3/`: Protocol v9 (Step 3) variants (`strict`, `cred`, `flexI_cred`), AgentDojo baselines, adaptive/GUIDE-aware/direct attacks, Gemini 3.1 Flash-Lite replication (`runs/`), and 15 real-framework applications (`realworld/main/rows.jsonl`, summary in `summary.md`).
- `experiments/results/compromise-replay-v8/`: Protocol v8 (M1) assumed-compromise replay logs across 949 AgentDojo pairs.
- `experiments/results/final-v8/`: Protocol v8 (M1b) attributable utility loss evaluation and verified paper numbers ledger.
- `experiments/results/topology-v8/`: Protocol v8 (M2) structural census and Proposition 4 evaluation over 55 acyclic workflows.
- `experiments/results/agentdojo-v6/`: Protocol v6 defended benchmark execution traces on DeepSeek-V3.
- `experiments/results/agentdojo-v6b-undefended/`: Protocol v6b paired undefended benchmark execution traces on DeepSeek-V3.
- `experiments/results/predict-utility-v7a/`: Protocol v7a static utility loss prediction against benign traces.
- `experiments/results/topology-v7c/`: Protocol v7c topology refinement property tests.
- `experiments/mining/`: Protocol v7b public multi-agent configuration mining funnel and capability audits.
- `experiments/real_world_blast_radius/`: Protocol v4 static capability audit across 19 real-world configurations.
- `experiments/results/v2-main/`, `v2-compromised/`: Protocol v2 multi-agent benchmark traces on DeepSeek-V3.
- `experiments/results/v5-main-*/`, `v5-compromised-*/`: Protocol v5 multi-model evaluation traces across Gemini and Groq.

## Documentation

[architecture](docs/architecture.md) · [evaluation protocol](docs/evaluation.md) · [experiments](docs/experiments.md) ·
[formal model](docs/formal_model.md) · [novelty](docs/novelty.md) · [limitations](docs/limitations.md) · [security](docs/security.md) · [ADRs](docs/adr/README.md) ·
[research audit](docs/research-audit.md) · [submission alignment](docs/submission-alignment.md)

## License

Apache-2.0.

