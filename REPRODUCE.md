# Reproduction guide

This document provides exact reproduction instructions for every table and empirical result in the paper. Commands use the project virtual environment via `uv run` or directly executable modules within `src`.

All commands execute locally. Zero-cost items require no external model APIs and incur zero monetary cost.

---

## Environment setup

Clone the repository and install all dependencies:

```bash
# Clone repository
git clone https://github.com/shafin0id/guide.git
cd guide

# Checkout the paper branch
git checkout research/evidence-based-rebuild

# Sync dependencies using uv
uv sync --all-extras
```

System requirements:
- Python 3.10 to 3.12
- `uv` package manager
- Optional for document compilation: `pandoc`

---

## Quick validation

To verify the test suite and all 34 manuscript numbers without re-running long benchmarks:

```bash
# Run test suite (0 failed expected)
uv run pytest -q

# Verify all 34 manuscript numbers against raw experimental outputs (0 missing expected)
uv run python -u scripts/final/run_final.py --stage check_numbers
```

---

## Reproduction by table and protocol

### Table 1. Comparative capability matrix
- **Paper section**: Section 2 (Related work)
- **Protocol**: Architectural review (`paper-v1`)
- **Inputs**: Formal model and specifications in `docs/formal_model.md` and literature review in `docs/lit-review/`
- **Outputs**: Comparative matrix in `docs/paper/manuscript-draft.md` Table 1
- **Expected key number**: 8 capability dimensions across 8 single-agent monitors and multi-agent frameworks
- **API cost**: $0.00 (zero-cost)
- **Git tag**: `paper-v1`

---

### Table 2. Alignment of research questions, objectives, and evidence
- **Paper section**: Section 1 (Introduction) and Appendix
- **Protocol**: Methodological mapping (`paper-v1`)
- **Inputs**: Research plan and formal evaluation design
- **Outputs**: Table 2 in `docs/paper/manuscript-draft.md`
- **Expected key number**: 5 research questions (RQ1 to RQ5) mapped to contributions C1 to C4
- **API cost**: $0.00 (zero-cost)
- **Git tag**: `paper-v1`

---

### Table 3. Assumed-compromise containment replay on AgentDojo
- **Paper section**: Section 4.2 (RQ2 runtime containment)
- **Protocol**: Protocol v8 (M1)
- **Command**:
  ```bash
  uv run python -u scripts/final/run_final.py --stage m1
  ```
- **Inputs**: AgentDojo benchmark suite (`agentdojo==0.1.35`), 949 task-injection pairs across Banking, Slack, Travel, Workspace
- **Outputs**: `experiments/results/compromise-replay-v8/summary.json`, `trace_log.jsonl`
- **Expected key numbers**:
  - Full grid pairs: 949 total, 588 in-scope
  - Contained pairs: 543/588 (92.3% [89.9%, 94.2%])
  - Partial containment: 0/588 (0.0%)
  - Admitted sink invocations: 45/588 (7.7%)
  - Sink-call block rate: 93.6% (657 denied out of 702 malicious sink calls)
  - v6 subset containment: 89.5% [86.1%, 92.1%] (384/429)
  - Undefended baseline containment: 0.0% (0/588)
- **API cost**: $0.00 (zero-cost synthetic replay)
- **Git tag**: `protocol-v8`

---

### Table 4. Bound prediction versus runtime containment on AgentDojo
- **Paper section**: Section 4.2 (RQ2 runtime containment)
- **Protocol**: Protocol v8 (M1)
- **Command**:
  ```bash
  uv run python -u scripts/final/run_final.py --stage m1
  ```
- **Inputs**: Pre-computed static bounds from `src/guide_agentdojo/bound.py` and runtime outcomes from M1
- **Outputs**: `experiments/results/compromise-replay-v8/summary.json` (`bound_vs_runtime`)
- **Expected key numbers**:
  - Bound blocked and runtime contained: 543
  - Bound admitted and runtime executed: 45
  - Bound blocked and runtime executed (soundness violations): 0
  - Bound admitted and runtime denied (exactness gaps): 0
- **API cost**: $0.00 (zero-cost)
- **Git tag**: `protocol-v8`

---

### Table 5. Evaluation metrics and operational definitions
- **Paper section**: Section 3.11 (Methods)
- **Protocol**: Metric definitions (`protocol-v1`)
- **Inputs**: Benchmark scoring framework in `src/guide_bench/scoring.py`
- **Outputs**: Metric definitions in `docs/paper/manuscript-draft.md` Table 5
- **Expected key number**: 8 operational metric definitions
- **API cost**: $0.00 (zero-cost)
- **Git tag**: `protocol-v1`

---

### Table 6. Main-suite task performance across model families
- **Paper section**: Section 4.1 (RQ1 governance overhead and utility)
- **Protocols**: Protocol v1, Protocol v2, Protocol v5
- **Commands**:
  ```bash
  # Protocol v1 and v2: DeepSeek baseline (N=360, reps=5)
  uv run guide-bench --suite main --conditions B1,B2,P,GPLUS --reps 5 --out experiments/results/v2-main

  # Protocol v5: Gemini 3.5 Flash-Lite (N=248)
  uv run python -m guide_bench.run --suite main --conditions B1,B2,P,GPLUS --reps 2 --provider gemini --model gemini-3.5-flash-lite --out experiments/results/v5-main-gemini

  # Protocol v5: Groq GPT-OSS 120B (N=166)
  uv run python -m guide_bench.run --suite main --conditions B1,B2,P,GPLUS --reps 2 --provider groq --model openai/gpt-oss-120b --out experiments/results/v5-main-groq-gptoss120b

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

### Table 7. Assumed-compromise containment across model families
- **Paper section**: Section 4.1 (RQ1 governance under compromise)
- **Protocols**: Protocol v2, Protocol v5
- **Commands**:
  ```bash
  # Protocol v2: DeepSeek assumed compromise (N=140)
  uv run guide-bench --suite adversarial --conditions B1,B2,P,GPLUS --reps 5 --out experiments/results/v2-compromised

  # Protocol v5: Gemini 3.5 Flash-Lite (N=46)
  uv run python -m guide_bench.run --suite adversarial --conditions B1,B2,P,GPLUS --reps 2 --provider gemini --model gemini-3.5-flash-lite --out experiments/results/v5-compromised-gemini

  # Protocol v5: Groq GPT-OSS 120B (N=38)
  uv run python -m guide_bench.run --suite adversarial --conditions B1,B2,P,GPLUS --reps 2 --provider groq --model openai/gpt-oss-120b --out experiments/results/v5-compromised-groq-gptoss120b
  ```
- **Inputs**: Adversarial test tasks K1 to K4 (`src/guide_bench/adversarial.py`)
- **Outputs**: `experiments/results/v2-compromised/summary.md`, `experiments/results/v5-compromised-*/summary.md`
- **Expected key numbers**:
  - K1 (Direct read of restricted context): 0% leakage into final deliverable across all models
  - K2 (Unauthorized email to external domain): 100% violation in B1 and B2, and 0% violation in P and GPLUS across all models
  - K3 (Unauthorized email to in-domain recipient from untrusted tool data): 100% violation in B1, B2, and P, and 0% violation in GPLUS across all models
  - K4 (Destructive record deletion): 100% violation in B1 and B2, and 0% violation in P and GPLUS across all models
- **API cost**: External model API calls (completed during historical protocol runs)
- **Git tags**: `protocol-v2`, `protocol-v5`

---

### Table 8. AgentDojo benchmark performance comparison: defended versus undefended
- **Paper section**: Section 4.2 (RQ2 runtime containment)
- **Protocols**: Protocol v6, Protocol v6b
- **Commands**:
  ```bash
  # Protocol v6: Defended run on DeepSeek-V3
  uv run guide-agentdojo --suite all --attack-type important_instructions --model deepseek-v4-flash --out experiments/results/agentdojo-v6

  # Protocol v6b: Undefended baseline on DeepSeek-V3
  uv run python -m guide_agentdojo.run_baseline --suite all --attack-type important_instructions --model deepseek-v4-flash --out experiments/results/agentdojo-v6b-undefended
  ```
- **Inputs**: 97 benign tasks and 529 attack pairs across Banking, Slack, Travel, Workspace
- **Outputs**: `experiments/results/agentdojo-v6/` and `experiments/results/agentdojo-v6b-undefended/`
- **Expected key numbers**:
  - Benign utility: 91.8% undefended (89/97) versus 61.9% defended (60/97), a 29.9 percentage point cost
  - Slack benign utility: 95.2% undefended (20/21) versus 28.6% defended (6/21), a 66.7 percentage point cost
  - Attack utility: 85.6% undefended (453/529) versus 68.4% defended (362/529)
  - Attack success rate: 2.1% undefended (11/529) versus 2.3% defended (12/529)
  - Tool-sink compromise rate: 0.0% (0/517) on both undefended and defended runs
- **API cost**: ~10.89 CNY (undefended) + ~13.95 CNY (defended) via DeepSeek API
- **Git tags**: `protocol-v6`, `protocol-v6b`

---

### Table 9. Full deviation registry
- **Paper section**: Appendix
- **Protocol**: Auditing and compliance (`paper-v1`)
- **Inputs**: Historical project decision records and alignment ledger in `docs/submission-alignment.md`
- **Outputs**: Table 9 in `docs/paper/manuscript-draft.md`
- **Expected key number**: 36 disclosed deviations (A1 to A36) with rationale and impact assessments
- **API cost**: $0.00 (zero-cost)
- **Git tag**: `paper-v1`

---

### Table 10. Confusion matrix of pre-deployment utility cost prediction
- **Paper section**: Section 4.3 (RQ3 pre-deployment utility prediction)
- **Protocol**: Protocol v8 (M1b)
- **Command**:
  ```bash
  uv run python -u scripts/final/run_final.py --stage m1b
  ```
- **Inputs**: Empirical task outcomes from `experiments/results/agentdojo-v6/` and `agentdojo-v6b-undefended/`
- **Outputs**: `experiments/results/final-v8/v7a_attributable_loss.json`
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

### Table 11. Structural census of fifty-five acyclic multi-agent configurations
- **Paper section**: Section 4.4 (RQ4 agent topology and blast radius)
- **Protocol**: Protocol v8 (M2)
- **Command**:
  ```bash
  uv run python -u scripts/final/run_final.py --stage m2
  ```
- **Inputs**: 19 self-authored configurations in `experiments/real_world_blast_radius/results.jsonl` and 36 mined configurations in `experiments/mining/results.jsonl`
- **Outputs**: `experiments/results/topology-v8/summary.json`
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

### Table 12. Real-world configuration mining funnel and metrics
- **Paper section**: Section 4.4 (RQ4 agent topology and blast radius)
- **Protocol**: Protocol v7b
- **Commands**:
  ```bash
  # Repository mining
  uv run python -m guide_bench.mining.harvest

  # Static capability audit
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

## Model-free and auxiliary experiments

### 1. Hand-off integrity verification
- **Protocol**: Protocol v1
- **Command**:
  ```bash
  uv run python -m guide_bench.integrity --n 500
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
  uv run python -m guide_bench.routing_sim --seeds 100 --horizon 1000
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
- **Command**:
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
  uv run pytest tests/unit/test_topology_refinement.py -q
  ```
- **Expected key numbers**: 0 counterexamples across 200 Hypothesis trials validating Proposition 3.
- **API cost**: $0.00 (zero-cost)
- **Git tag**: `protocol-v7c`

---

## Protocol v9 (Step 3): provenance variants, AgentDojo baselines, adaptive attacks, Gemini replication, and real-framework applications

### Table 13. Protocol v9 AgentDojo provenance variants, baselines, attack templates, and Gemini replication
- **Paper section**: Section 3.14 & Section 4.5 (RQ5)
- **Protocols**: Protocol v9a, v9b, Step 3 (`step3-protocol-v9`)
- **Commands**:
  ```bash
  # Check matrix completeness across all Step 3 blocks
  .venv/bin/python scripts/step3/verify_complete.py

  # Recompute all Step 3 summary tables and statistics from raw JSONL logs
  .venv/bin/python scripts/step3/analyze.py
  ```
- **Inputs**:
  - `experiments/results/step3/runs/main/` (200 stratified pairs × 5 conditions/attacks plus variants `strict`, `cred`, `flexI_cred`, `none` on 97 benign tasks and 588 held-out/grid pairs; 30 adaptive attack pairs)
  - `experiments/results/step3/runs/rep2/`, `experiments/results/step3/runs/rep3/` (3-repetition variance checks)
  - `experiments/results/step3/runs/gemini/rows_important_instructions_default.jsonl` (Gemini 3.1 Flash-Lite 20-pair replication under 4 GUIDE conditions)
- **Outputs**: `experiments/results/step3/summary.md`, `docs/step3-results.md`
- **Expected key numbers**:
  - Full-grid containment: `strict` 92.3% (543/588), `flexI_cred` 88.8% (522/588)
  - Pooled benign utility: `none` 91.8%, `strict` 61.9%, `flexI_cred` 77.3% (+15.5 pp overall recovery; Slack +38.1 pp from 28.6% to 66.7%)
  - Gemini 3.1 Flash-Lite replication (first 20 pairs): ASR 75.0% (`15/20`, none) -> 20.0% (`4/20`, rule-only) -> 5.0% (`1/20`, `strict`/`flexI_cred`)

---

### Table 14. Real-framework multi-agent applications across LangGraph, CrewAI, and AutoGen
- **Paper section**: Section 3.14 & Section 4.6 (RQ6)
- **Protocol**: Protocol v9 / Step 3 real-world harness (`src/guide_realworld/`, `.venv-rw` or installed framework dependencies)
- **Commands**:
  ```bash
  # Run the 15 framework applications (2 benign + 10 injected tasks x 4 conditions = 720 runs)
  .venv-rw/bin/python -m guide_realworld.run_rw --out experiments/results/step3/realworld/main

  # Analyze and verify all 720 runs
  .venv/bin/python scripts/step3/analyze.py
  .venv/bin/python scripts/step3/verify_complete.py
  ```
- **Inputs**: `src/guide_realworld/lg_apps.py`, `src/guide_realworld/cr_apps.py`, `src/guide_realworld/ag_apps.py`, `src/guide_realworld/scenarios.py`
- **Outputs**: `experiments/results/step3/realworld/main/rows.jsonl`, `experiments/results/step3/summary.md`
- **Expected key numbers**:
  - 720 completed runs (15 applications × 12 tasks × 4 conditions)
  - Compromised-reader attacks (`N=90`): 25.6% (23/90) undefended ASR -> 0.0% (0/90) under strict and `flexI_cred`
  - Unseen predictor accuracy: 96.7% (29/30) across all 15 applications

---

## Manuscript figures and numbers compilation

### Generate all manuscript figures
```bash
.venv/bin/python scripts/paper/make_figures.py
```
Outputs figures into `scripts/paper/figures/`:
- `fig4_main_suite_success.png`
- `fig5_compromise_heatmap.png`
- `fig6_blast_radius_bound_sizes.png`
- `fig7_overhead.png`
- `fig8_degraded_agent_sequence.png`
- `fig9_agentdojo_utility_containment.png`
- `figS1_prisma_flow.png`
- `figS2_routing_regret.png`

### Generate and verify manuscript numbers ledger
```bash
# Generate paper_numbers.json from raw logs
.venv/bin/python -u scripts/final/run_final.py --stage numbers

# Check synced markdown manuscript numbers match verbatim
.venv/bin/python -u scripts/final/run_final.py --stage check_numbers

# Verify V2 Word manuscript numbers against raw experimental artifacts
.venv/bin/python scripts/paper/verify_docx_numbers.py docs/paper/revision-v2/GUIDE_Manuscript_Revised_V2.docx
```

### Revised V2 Word manuscripts & supplementary material
- `docs/paper/revision-v2/GUIDE_Manuscript_Revised_V2.docx` and `GUIDE_Manuscript_Revised_V2.md`
- `docs/paper/revision-v2/GUIDE_Supplementary_Material_V2.docx` and `GUIDE_Supplementary_Material_V2.md`
- `docs/paper/revision-v2/REVISION-LOG.md`

### Build Word manuscripts via Pandoc
```bash
# Build main manuscript
pandoc docs/paper/manuscript-draft.md \
  -o docs/paper/out/manuscript-draft.docx \
  --reference-doc=docs/paper/reference-style.docx \
  --resource-path=docs/paper:.

# Build differences document
pandoc docs/paper/differences-from-submitted.md \
  -o docs/paper/out/differences-from-submitted.docx \
  --reference-doc=docs/paper/reference-style.docx \
  --resource-path=docs/paper:.
```
