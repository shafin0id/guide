# GUIDE — policy-aware, traceable orchestration for LLM multi-agent workflows

GUIDE is a research prototype (MSc AI dissertation artefact, APU/DMU, CT095-6-M-RMCE; author Shafin Ahmad;
supervisors Ts. Dr. Maythem Kamal and Dr. R Logeswaran). It adds four connected controls around an existing LLM:

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
| GUIDE Research | `src/guide_research` | experimental mechanisms under evaluation (provenance guard) |
| GUIDE Bench | `src/guide_bench` | tasks, sandbox, conditions, condition-blind scoring, runner, statistics |

Dependencies point one way only (Core ← Research ← Bench), enforced by `scripts/check_boundaries.py` in CI.

## Reproduce

```bash
pytest -q                                                   # 72 tests, no network
python -m guide_bench.integrity --n 500 --out experiments/results/integrity
python -m guide_bench.routing_sim --seeds 100 --horizon 1000 --out experiments/results/routing
guide-bench --suite main --conditions B1,B2,P,GPLUS --reps 5 --out experiments/results/main --env-file .env
python -m guide_bench.stats experiments/results/main
```

Each run directory contains `manifest.json` (git commit, model requested/observed, settings, task digests, seed),
`results.jsonl` (one scored row per run) and `transcripts.jsonl` (model I/O, not committed).

## Documentation

[architecture](docs/architecture.md) · [evaluation protocol](docs/evaluation.md) · [experiments](docs/experiments.md) ·
[novelty](docs/novelty.md) · [limitations](docs/limitations.md) · [security](docs/security.md) · [ADRs](docs/adr/README.md) ·
[research audit](docs/research-audit.md) · [submission alignment](docs/submission-alignment.md)

## License

Apache-2.0.
