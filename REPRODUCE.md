# Reproduction guide

This document provides exact reproduction instructions for every table, figure, and empirical result. Commands use the project virtual environment via `uv run` or directly executable modules within `src`.

All zero-cost commands execute locally without external model APIs and incur zero monetary cost.

---

## Environment setup

Clone the repository and install all dependencies:

```bash
# Clone repository
git clone https://github.com/shafin0id/guide.git
cd guide

# Checkout the main release branch
git checkout main

# Sync dependencies using uv
uv sync --all-extras
```

The framework applications (Table 14, Protocol v9b) use a separate virtual environment because LangGraph, CrewAI, and AutoGen pin dependencies that conflict with AgentDojo:

```bash
uv venv .venv-rw --python 3.12
uv pip install --python .venv-rw/bin/python langgraph==1.2.21 crewai==1.15.41 \
  autogen-agentchat==0.7.5 "autogen-ext[openai]==0.7.5" langchain-openai openai python-dotenv cryptography
```

System requirements:
- Python 3.10 to 3.12
- `uv` package manager
- Live model runs require API keys in `.env` (copy `.env.example` to `.env`).

---

## Quick validation

To verify the test suite, package boundaries, and Protocol v9 result completeness without re-running model calls:

```bash
# Run test suite (0 failed expected)
uv run pytest -q

# Verify core <- research <- bench import boundary
uv run python scripts/check_boundaries.py

# Verify Protocol v9 result completeness across all blocks (0 missing expected)
PYTHONPATH=src uv run python scripts/v9/verify_complete.py

# Recompute Protocol v9 summary tables from raw JSONL logs
PYTHONPATH=src uv run python scripts/v9/analyze.py
```

---

## Reproduction by table

### Table 1. Comparison of security mechanisms
- **Protocol**: Systematic literature review (`review-protocol-v1`)
- **Inputs**: Literature review corpus and extraction data in `docs/lit-review/`
- **Outputs**: `docs/lit-review/literature-review.md` (§6)
- **Expected key number**: 721 included studies (607 database + 114 snowball); comparative matrix across single-agent monitors and multi-agent frameworks
- **API cost**: $0.00 (zero-cost)
- **Git tag**: `review-protocol-v1`

---

### Table 2. Research questions, objectives, hypotheses, and evidence
- **Protocol**: Pre-registered evaluation design (`protocol-v1`, extended in `protocol-v3` to `protocol-v9a-frozen`)
- **Inputs**: `docs/evaluation.md`, `docs/experiments.md`, `docs/results-v9.md`
- **Outputs**: Summary against hypotheses in `docs/experiments.md`
- **Expected key number**: 5 research questions and pre-registered hypotheses mapped to recorded artifacts
- **API cost**: $0.00 (zero-cost)
- **Git tag**: `protocol-v1`

---

### Table 3. Evaluation metrics and operational definitions
- **Protocol**: Metric definitions (`protocol-v1`)
- **Inputs**: Benchmark scoring framework in `src/guide_bench/scoring.py` and `docs/evaluation.md`
- **Outputs**: `docs/evaluation.md` (§3)
- **Expected key number**: 8 operational metric definitions
- **API cost**: $0.00 (zero-cost)
- **Git tag**: `protocol-v1`

---

### Table 4. Deviations from the proposal
- **Protocol**: Auditing and compliance (`protocol-v1` to `protocol-v9a-frozen`)
- **Inputs**: Disclosed amendments and limitations in `docs/experiments.md`, `docs/limitations.md`, `docs/results/protocol-v7.md`, and `docs/results-v9.md`
- **Outputs**: `docs/experiments.md`, `docs/limitations.md`
- **Expected key number**: All protocol amendments and scope disclosures documented alongside frozen tags
- **API cost**: $0.00 (zero-cost)
- **Git tag**: `paper-v1`

---

### Table 5. Violation rate under assumed compromise, K1 to K4
- **Protocols**: Protocol v2, Protocol v5
- **Commands**:
  ```bash
  # Protocol v2: DeepSeek assumed compromise (N=140)
  uv run guide-bench --suite compromised --conditions B1,B2,P,GPLUS --reps 5 --out experiments/results/v2-compromised

  # Protocol v5: Gemini 3.5 Flash-Lite (N=46)
  uv run python -m guide_bench.run --suite compromised --conditions B1,B2,P,GPLUS --reps 2 --base-url https://generativelanguage.googleapis.com/v1beta/openai --key-env GEMINI_API_KEY --model gemini-3.5-flash-lite --model-seed none --out experiments/results/v5-compromised-gemini

  # Protocol v5: Groq GPT-OSS 120B (N=38)
  uv run python -m guide_bench.run --suite compromised --conditions B1,B2,P,GPLUS --reps 2 --base-url https://api.groq.com/openai/v1 --key-env GROQ_API_KEY --model openai/gpt-oss-120b --model-seed none --out experiments/results/v5-compromised-groq-gptoss120b
  ```
- **Inputs**: Adversarial test tasks K1 to K4 (`src/guide_bench/adversarial.py`)
- **Outputs**: `experiments/results/v2-compromised/summary.md`, `experiments/results/v5-compromised-*/summary.md`
- **Expected key numbers**:
  - K1 (Direct read of restricted context): 0% leakage into final deliverable across all models (restricted exposure 1.0 in ungated B1/B2 vs 0.0 in P/GPLUS)
  - K2 (Unauthorized email to external domain): 100% violation in B1 and B2, and 0% violation in P and GPLUS across all models
  - K3 (Unauthorized email to in-domain recipient from untrusted tool data): 100% violation in B1, B2, and P, and 0% violation in GPLUS across all models
  - K4 (Destructive record deletion): 100% violation in B1 and B2, and 0% violation in P and GPLUS across all models
- **API cost**: External model API calls (completed during historical protocol runs)
- **Git tags**: `protocol-v2`, `protocol-v5`

---

### Table 6. Assumed-compromise replay on AgentDojo
- **Protocol**: Protocol v8 (M1)
- **Command**:
  ```bash
  PYTHONPATH=src uv run python -m guide_agentdojo.compromise_replay
  ```
- **Inputs**: AgentDojo benchmark suite (`agentdojo==0.1.35`), 949 task-injection pairs across Banking, Slack, Travel, Workspace
- **Outputs**: `experiments/results/compromise-replay-v8/summary.json`, `experiments/results/compromise-replay-v8/summary.md` (full replay also writes `pairs.jsonl` and `calls.jsonl`)
- **Expected key numbers**:
  - Full grid pairs: 949 total, 588 in-scope
  - Contained pairs (`strict`): 543/588 (92.3% [89.9%, 94.2%])
  - Partial containment: 0/588 (0.0%)
  - Admitted sink invocations: 45/588 (7.7%)
  - Sink-call block rate: 93.6% (657 denied out of 702 malicious sink calls)
  - v6 subset containment: 89.5% [86.1%, 92.1%] (384/429)
  - Undefended baseline containment: 0.0% (0/588)
- **API cost**: $0.00 (zero-cost synthetic replay)
- **Git tag**: `protocol-v8`

---

### Table 7. Bound prediction versus runtime containment on AgentDojo
- **Protocol**: Protocol v8 (M1)
- **Command**:
  ```bash
  PYTHONPATH=src uv run python -m guide_agentdojo.compromise_replay
  ```
- **Inputs**: Pre-computed static bounds from `src/guide_agentdojo/bound.py` and runtime outcomes from M1
- **Outputs**: `experiments/results/compromise-replay-v8/summary.json` (`bound_vs_runtime`)
- **Expected key numbers**:
  - Bound blocked and runtime contained: 657 calls (543 pairs)
  - Bound admitted and runtime executed: 427 calls (45 pairs)
  - Bound blocked and runtime executed (soundness violations): 0
  - Bound admitted and runtime denied (exactness gaps): 0
- **API cost**: $0.00 (zero-cost)
- **Git tag**: `protocol-v8`

---

### Table 8. AgentDojo benchmark performance comparison: defended versus undefended
- **Protocols**: Protocol v6, Protocol v6b
- **Commands**:
  ```bash
  # Protocol v6: Defended run on DeepSeek (run across each suite; model configured via DEEPSEEK_MODEL)
  for suite in banking slack travel workspace; do
    uv run guide-agentdojo --suite "$suite" --attack important_instructions --logdir experiments/results/agentdojo-v6
  done

  # Protocol v6b: Undefended baseline on DeepSeek
  uv run python -m guide_agentdojo.run_baseline --model deepseek-v4-flash --logdir experiments/results/agentdojo-v6b-undefended
  ```
- **Inputs**: 97 benign tasks and 529 attack pairs across Banking, Slack, Travel, Workspace
- **Outputs**: `experiments/results/agentdojo-v6/`, `experiments/results/agentdojo-v6b-undefended/`
- **Expected key numbers**:
  - Benign utility: 91.8% undefended (89/97) versus 61.9% defended (60/97), a 29.9 percentage point cost
  - Slack benign utility: 95.2% undefended (20/21) versus 28.6% defended (6/21), a 66.7 percentage point cost
  - Attack utility: 85.6% undefended (453/529) versus 68.4% defended (362/529)
  - Attack success rate: 2.1% undefended (11/529) versus 2.3% defended (12/529)
  - Tool-sink compromise rate: 0.0% (0/517) on both undefended and defended runs
- **API cost**: ~10.89 CNY (undefended) + ~13.95 CNY (defended) via DeepSeek API (historical runs)
- **Git tags**: `protocol-v6`, `protocol-v6b`

---

### Table 9. Utility-cost prediction confusion matrix
- **Protocol**: Protocol v8 (M1b)
- **Command**:
  ```bash
  PYTHONPATH=src uv run python -m guide_agentdojo.compromise_replay --m1b-only
  ```
- **Inputs**: Empirical task outcomes from `experiments/results/agentdojo-v6/` and `experiments/results/agentdojo-v6b-undefended/`
- **Outputs**: `experiments/results/final-v8/v7a_attributable_loss.json`, `experiments/results/final-v8/v7a_attributable_loss.md`
- **Expected key numbers**:
  - Total lost tasks: 30
  - True positives (predicted block and empirical loss): 29
  - False positives (predicted block and no loss): 2
  - False negatives (predicted pass and empirical loss): 1
  - True negatives (predicted pass and no loss): 65
  - Prediction accuracy: 96.9% [91.3%, 98.9%]
  - Predicted cost: 29.9 percentage points versus observed cost 29.9 percentage points
- **API cost**: $0.00 (zero-cost)
- **Git tag**: `protocol-v8`

---

### Table 10. Structural census of fifty-five acyclic multi-agent configurations
- **Protocol**: Protocol v8 (M2)
- **Command**:
  ```bash
  PYTHONPATH=src uv run python -m guide_bench.topology_v8
  ```
- **Inputs**: 19 self-authored configurations in `experiments/real_world_blast_radius/results.jsonl` and 36 mined configurations in `experiments/mining/results.jsonl`
- **Outputs**: `experiments/results/topology-v8/summary.json`, `experiments/results/topology-v8/summary.md`
- **Expected key numbers**:
  - Total acyclic configurations: 55
  - Linear dependency chains: 49/55 (89.1%)
  - Dominating source agents: 55/55 (100.0%)
  - Configurations with sink floor equal to 1 under signed hand-offs: 21/21 (100.0% of sink-bearing configurations)
  - Proposition 4 property test counterexamples: 0 across 300 tests
  - Absolute reach median reduction via least privilege: 50.0% (from 2.0 to 1.0 sink)
- **API cost**: $0.00 (zero-cost)
- **Git tag**: `protocol-v8`

---

### Table 11. Configuration mining funnel and metrics
- **Protocol**: Protocol v7b
- **Commands**:
  ```bash
  # Repository harvesting and static capability audit
  uv run python -m guide_bench.mining.audit
  ```
- **Inputs**: Public GitHub repositories matching frozen queries for CrewAI, LangGraph, and AutoGen
- **Outputs**: `experiments/mining/funnel.json`, `experiments/mining/configs.jsonl`, `experiments/mining/summary.json`
- **Expected key numbers**:
  - Candidate configurations: 37
  - Scored acyclic configurations: 36 (1 cyclic LangGraph configuration excluded with disclosure)
  - Configurations with zero write or external sinks: 34/36 (94.4%)
  - Sequential configurations: 36/36 (100.0%)
  - M1 metric (single agent blast radius contains a sink): 0.056 [0.015, 0.181] (2/36)
  - M2 metric (zero-own-sink agent reaches a downstream sink): 0.028 [0.005, 0.142] (1/36)
  - M5 metric (code execution tools): 0.000 [0.0, 0.096] (0/36)
- **API cost**: $0.00 (zero-cost)
- **Git tag**: `protocol-v7b`

---

### Table 12. Nominal task performance across model families
- **Protocols**: Protocol v1, Protocol v2, Protocol v5
- **Commands**:
  ```bash
  # Protocol v1 and v2: DeepSeek baseline (N=360, reps=5)
  uv run guide-bench --suite main --conditions B1,B2,P,GPLUS --reps 5 --out experiments/results/v2-main

  # Protocol v5: Gemini 3.5 Flash-Lite (N=248)
  uv run python -m guide_bench.run --suite main --conditions B1,B2,P,GPLUS --reps 2 --base-url https://generativelanguage.googleapis.com/v1beta/openai --key-env GEMINI_API_KEY --model gemini-3.5-flash-lite --model-seed none --out experiments/results/v5-main-gemini

  # Protocol v5: Groq GPT-OSS 120B (N=166)
  uv run python -m guide_bench.run --suite main --conditions B1,B2,P,GPLUS --reps 2 --base-url https://api.groq.com/openai/v1 --key-env GROQ_API_KEY --model openai/gpt-oss-120b --model-seed none --out experiments/results/v5-main-groq-gptoss120b

  # Cross-model summary aggregation
  uv run python scripts/aggregate_protocol_v5.py
  ```
- **Inputs**: Multi-agent benchmark tasks 1 to 18 (`src/guide_bench/tasks.py`)
- **Outputs**: `experiments/results/v2-main/summary.md`, `experiments/results/v5-main-*/summary.md`
- **Expected key numbers**:
  - DeepSeek: B1 0.989, B2 1.000, P 0.989, GPLUS 1.000 task success
  - Gemini 3.5 Flash-Lite: B1 0.935, B2 0.969, P 0.967, GPLUS 0.968 task success
  - Groq GPT-OSS 120B: B1 0.409, B2 0.390, P 0.297, GPLUS 0.318 task success
  - Nominal violations: 0 across all conditions and models
- **API cost**: External model API calls (completed during historical protocol runs)
- **Git tags**: `protocol-v1`, `protocol-v2`, `protocol-v5`

---

### Table 13. Defenses on AgentDojo (Protocol v9a, v9c, v9g)
- **Protocols**: Protocol v9a, Protocol v9c, Protocol v9g (`docs/protocols/protocol-v9a.md`)
- **Commands**:
  ```bash
  # Check matrix completeness across all Protocol v9 blocks (zero API cost)
  PYTHONPATH=src uv run python scripts/v9/verify_complete.py

  # Recompute all Protocol v9 summary tables and statistics from raw JSONL logs (zero API cost)
  PYTHONPATH=src uv run python scripts/v9/analyze.py

  # Offline variant evaluation and full-grid replay (zero API cost)
  PYTHONPATH=src uv run python scripts/v9/w2_variants.py
  PYTHONPATH=src uv run python scripts/v9/w2_full.py

  # Live DeepSeek Protocol v9a lanes (requires DEEPSEEK_API_KEY)
  scripts/v9/run_v9a.sh 1
  scripts/v9/run_v9a.sh 2
  scripts/v9/run_v9a.sh 3
  scripts/v9/run_v9a.sh 4
  ```
- **Inputs**:
  - `experiments/results/v9/runs/main/` (97 benign tasks, 200 stratified pairs × 8 conditions/attacks, 30 adaptive attack pairs)
  - `experiments/results/v9/runs/rep2/`, `experiments/results/v9/runs/rep3/` (3-repetition variance checks)
  - `experiments/results/v9/runs/gemini/rows_important_instructions_default.jsonl` (Gemini 3.1 Flash-Lite 20-pair replication under 4 GUIDE conditions)
- **Outputs**: `experiments/results/v9/summary.md`, `experiments/results/v9/summary.json`, `docs/results-v9.md`
- **Expected key numbers**:
  - Full-grid containment: `strict` 92.3% (543/588), `cred` 95.1% (559/588), `flexI_cred` 88.8% (522/588)
  - Pooled benign utility: `none` 95.9% (93/97), `strict` 62.9% (61/97), `cred` 62.9% (61/97), `flexI_cred` 78.4% (76/97; Slack recovery +38.1 pp from 28.6% to 66.7%)
  - `direct` attack (N=200): `none` 9.0% (18/200), `strict` 0.5% (1/200), `tool_filter` 1.0% (2/200), `pi_detector` 1.5% (3/200), `spotlighting` 4.5% (9/200), `repeat_user_prompt` 4.0% (8/200)
  - Gemini 3.1 Flash-Lite replication (first 20 pairs): ASR 75.0% (`15/20`, `none`) -> 5.0% (`1/20`, `strict`/`cred`/`flexI_cred`)
- **API cost**: DeepSeek ~$6.05 + Gemini ~$0.75 (historical live runs); analysis and variant scripts are $0.00
- **Git tags**: `protocol-v9a-frozen`, `protocol-v9c-frozen`, `protocol-v9g-frozen`

---

### Table 14. Framework applications (Protocol v9b)
- **Protocol**: Protocol v9b (`docs/protocols/protocol-v9b.md`, uses `.venv-rw`)
- **Commands**:
  ```bash
  # Run the 15 framework applications (15 apps x 12 tasks x 4 conditions = 720 runs; requires DEEPSEEK_API_KEY)
  PYTHONPATH=src .venv-rw/bin/python -m guide_realworld.run_rw --tag main

  # Analyze and verify all 720 runs (zero API cost)
  PYTHONPATH=src uv run python scripts/v9/analyze.py
  PYTHONPATH=src uv run python scripts/v9/verify_complete.py
  ```
- **Inputs**: `src/guide_realworld/lg_apps.py`, `src/guide_realworld/cr_apps.py`, `src/guide_realworld/ag_apps.py`, `src/guide_realworld/scenarios.py`
- **Outputs**: `experiments/results/v9/realworld/main/rows.jsonl`, `experiments/results/v9/summary.md`
- **Expected key numbers**:
  - 720 completed runs (15 applications × 12 tasks × 4 conditions)
  - Compromised-reader relay attacks (`N=90`): 25.6% (23/90) undefended ASR -> 0.0% (0/90) under `strict` and `cred`, 6.7% (6/90) under `flexI_cred`
  - Static prediction vs live monitor decisions on 69 attacker sink calls: 0 soundness violations, 84.1% agreement
- **API cost**: Included in DeepSeek Protocol v9 ledger above; analysis is $0.00
- **Git tag**: `protocol-v9b-frozen`

---

## Figures

### Figures 1 to 7, S1, and S2
- **Protocol**: Figure generation from verified result summaries
- **Command**:
  ```bash
  uv run python scripts/paper/make_figures.py
  ```
- **Inputs**: Verified result tables from `docs/experiments.md`, `docs/lit-review/prisma-counts.json`, and `experiments/results/`
- **Outputs** (`scripts/paper/figures/`):
  - `fig1_reference_monitor_design.png`
  - `fig4_main_suite_success.png`
  - `fig5_compromise_heatmap.png`
  - `fig6_blast_radius_bound_sizes.png`
  - `fig7_overhead.png`
  - `fig8_degraded_agent_sequence.png`
  - `fig9_agentdojo_utility_containment.png`
  - `figS1_prisma_flow.png`
  - `figS2_routing_regret.png`
- **API cost**: $0.00 (zero-cost)
- **Git tag**: `paper-v1`

---

## Model-free and auxiliary experiments

### 1. Hand-off integrity verification
- **Protocol**: Protocol v1
- **Command**:
  ```bash
  uv run python -m guide_bench.integrity --n 500 --out experiments/results/integrity
  ```
- **Outputs**: `experiments/results/integrity/`
- **Expected key numbers**: 100% detection rate across 10 mutation classes with per-principal keys, and 0% sender spoofing detection with shared key.
- **API cost**: $0.00 (zero-cost)
- **Git tag**: `protocol-v1`

---

### 2. Adaptive routing simulation
- **Protocol**: Protocol v1
- **Command**:
  ```bash
  uv run python -m guide_bench.routing_sim --seeds 100 --horizon 1000 --out experiments/results/routing
  ```
- **Outputs**: `experiments/results/routing/`
- **Expected key numbers**: Cumulative regret reduction from 150.0 (static) to 18.3 (Bayes-UCB) and 12.5 (Bayes-UCB with penalty).
- **API cost**: $0.00 (zero-cost)
- **Git tag**: `protocol-v1`

---

### 3. Framework runtime overhead
- **Protocol**: Protocol v2
- **Command**:
  ```bash
  PYTHONPATH=src:tests uv run python tests/performance/test_overhead.py
  ```
- **Expected key numbers**: Framework governance latency of 1.68 ms (P) and 1.69 ms (GPLUS) per 3-step run, compared to baseline overhead of 0.16 ms (B1) and 0.23 ms (B2).
- **API cost**: $0.00 (zero-cost)
- **Git tag**: `protocol-v2`

---

### 4. Static blast-radius offline soundness
- **Protocol**: Protocol v3
- **Command** (requires local `transcripts.jsonl` in each run directory from executing `guide-bench`; raw `transcripts.jsonl` files are gitignored):
  ```bash
  uv run python -m guide_bench.validate_bound offline experiments/results/v2-compromised experiments/results/v2-main experiments/results/v2-adversarial experiments/results/main experiments/results/adversarial --out experiments/results/v3-offline
  ```
- **Outputs**: `experiments/results/v3-offline/offline.json`
- **Expected key numbers**: 0 step-containment violations and 0 blast-radius violations across 1,575 recorded runs and 2,051 executed tool calls.
- **API cost**: $0.00 (zero-cost)
- **Git tag**: `protocol-v3`

---

### 5. Topology refinement property test
- **Protocol**: Protocol v7c
- **Command**:
  ```bash
  uv run pytest tests/unit/test_topology.py -q
  ```
- **Expected key numbers**: 0 counterexamples across 200 Hypothesis trials validating Proposition 3.
- **API cost**: $0.00 (zero-cost)
- **Git tag**: `protocol-v7c`

---

### 6. Bounded exhaustive verification of the blast-radius model
- **Protocol**: Protocol v9
- **Commands**:
  ```bash
  PYTHONPATH=src uv run python scripts/v9/exhaustive_bound.py A
  PYTHONPATH=src uv run python scripts/v9/exhaustive_bound.py B
  ```
- **Outputs**: `experiments/results/v9/exhaustive/part_A.json`, `experiments/results/v9/exhaustive/part_B.json`
- **Expected key numbers**: 0 oracle mismatches and 0 monotonicity violations across 594,516 influence cases (Part A); 0 soundness violations and 0 exactness violations across 1,966,080 gate evaluations (Part B).
- **API cost**: $0.00 (zero-cost)
- **Git tag**: `protocol-v9a-frozen`
