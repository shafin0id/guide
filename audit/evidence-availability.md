> Historical audit record imported from the separate development workspace. Its paths identify that workspace, and its completion labels are not independent certification. See current-assessment.md for the submitted release.

# Stage 3 — Evidence Availability & Reproduction Audit

Recorded: 2026-11-19 UTC  
Scope: Complete verification of raw inputs, reproducible model-free runs, aggregate-only artifacts, and missing evidence across Protocols v1–v9.

## 1. CI & Test Suite Baseline (Inside `version-2/workspace` Before Any Code Edits)

| Check | Command | Exit Code | Result | Notes |
|---|---|---|---|---|
| Unit/Integration/Security/Regression tests | `pytest -q` | 0 | **138 passed** (24.9s) | Clean pass in locked Python 3.12.16 venv. |
| Import layer boundaries | `python scripts/check_boundaries.py` | 0 | **PASS** | Core <- Research <- Bench holds. |
| Type checking (core + research) | `mypy` | 0 | **PASS** | Strict typing clean for `guide` & `guide_research`. |
| Linting (`src tests`) | `ruff check src tests` | **1 (FAIL)** | **FAIL** | E501, B007, F841, BLE001, S310, S311, S603, S607, UP031 (`ISS-011`). |
| Linting CI (`src tests scripts`) | `ruff check src tests scripts` | **1 (FAIL)** | **FAIL** | Additional E501, B007, B023, I001, S311 in `scripts/` (`ISS-011`). |

## 2. Model-Free Reproduction Matrix

| Study / Artifact | Historical Source | Re-run Status | Comparison vs Historical Summary | Discrepancies / Findings |
|---|---|---|---|---|
| Exhaustive bound Part A (`exhaustive_bound.py A`) | `v9/exhaustive/part_A.json` | **PASS** (22.8s) | **EXACT MATCH** (`594,516` cases, `0` oracle mismatches, `0` monotonicity violations) | Does not test `J` (injectable tools), `tau_adv`, or multi-agent roles. |
| Exhaustive bound Part B (`exhaustive_bound.py B`) | `v9/exhaustive/part_B.json` | **PASS** (4.4s) | **EXACT MATCH** (`1,966,080` evals, `250,880` exec, `1,715,200` denied, `0` unsound, `0` inexact) | Narrow call grid (only 3 recipients; no substring collisions or clamping). |
| AgentDojo M1 replay (`compromise_replay`) | `compromise-replay-v8/summary.json` | **PARTIAL FAIL -> PASS** | M1 **EXACT MATCH** (`543/588 = 92.3%`, `657/702 = 93.6%`), **CRASHED in M1b** on first run because `predictions.jsonl` was missing (`ISS-009`). Re-ran `--m1b-only` after `predict` -> **EXACT MATCH** (`29, 2, 1, 65`, `96.9%`). | **3 critical findings**: (1) `workspace:injection_task_6..13` (320 pairs) have empty `ground_truth(env)`, NOT read-only goals (`ISS-012`); (2) `travel:injection_task_2` (20 pairs) is vacuous omitted-param admission, NOT trusted prompt value, and `workspace:injection_task_1` (3 pairs) is `'13'` in `'June 13'` collision (`ISS-013`); (3) `REPRODUCE.md:141` wrong v6-subset fraction (`384/429` vs actual `365/408`), `protocol-v8.md:36-37` wrong task IDs (`ISS-015`). |
| Static cost prediction v7a (`guide_agentdojo.predict`) | `predict-utility-v7a/summary.json` | **PASS** (6.7s) | **EXACT MATCH** (`90/97 = 92.8%`, `TP=28, FP=3, FN=4, TN=62`, `0 fn_onpath`) | Creates `predictions.jsonl` required by M1b. |
| Real-world 19-config audit (`guide_bench.real_world.audit`) | `real_world_blast_radius/summary.json` | **PASS** (0.3s) | **EXACT SCIENTIFIC MATCH** (`18/19 = 94.7%`, `144 -> 64` = `55.6%`, `19/19` preserved); only commit/timestamp differed. | Self-authored configs with whole-tool grants. |
| Topology v8 census (`guide_bench.topology_v8`) | `topology-v8/summary.json` | **CRASH (`exit=1`)** | **FAILED TO RUN**: `WorkflowError: workflow contains a dependency cycle` (`topology_v8.py:232` catches `ValueError` instead of `WorkflowError`, `ISS-010`). | Also manuscript `P0220` states `"mean reduction of 0.945 sink"` whereas actual `abs_reach.jsonl` mean is **`1.263` sinks** (`24/19`, `ISS-016`). |
| Topology property tests (`test_topology*.py`) | `tests/unit/test_topology*.py` | **PASS** (2.4s) | **0 counterexamples** (Prop 3 & Prop 4) | Verified in Stage 3; independently challenged in Stage 4 & 7A. |
| Offline variant selection (`w2_variants.py` & `w2_full.py`) | `v9/w2/{variants,full_grid}.json` | **PASS** (30.0s / 10.4s) | **EXACT MATCH** (`strict 543/588`, `cred 559/588`, `flexI_cred 522/588`) | **CRITICAL (`ISS-014`)**: `variants.json` shows `_selection.chosen == "strict"` (`eligible: ["strict", "cred", "hard"]`); `flexI_cred` FAILED the `-2 pp` dev containment floor (`88.4%` vs `92.3%`, `-3.9 pp`), contradicting manuscript `P0149`! |
| Hand-off integrity (`guide_bench.integrity --n 500`) | `integrity/integrity.json` | **PASS** (4.6s) | **EXACT MATCH** (`1.000` all 10 classes per-principal; `0.000` spoofing shared-key; `0.000` false rejections) | Deterministic seed=11. |
| Routing simulation (`guide_bench.routing_sim --seeds 100 --horizon 1000`) | `routing/routing.json` | **PASS** (9.9s) | **EXACT MATCH** (stationary `150.0, 18.3, 61.2, 12.5`; drift `275.0, 54.5/39.8, 41.8/12.2, 61.0/49.4`) | Note `docs/evaluation.md:39` says `200 seeds` while actual run/Table S1 used `100 seeds`. |
| Protocol v9 analysis (`scripts/v9/analyze.py`) | `v9/summary.{json,md}` | **PASS** (0.7s) | All scientific metrics **EXACT MATCH**; Gemini spend updated `$0.22 -> $0.75` (committed summary was stale before final Gemini rows). | Independent strict validator (`validate_v9_matrix.py`) confirmed 0 missing, 0 conflicting completed rows, 0 failed-after-completed erasures across all blocks; audited 466 discarded `tool_filter` v1 rows, 16 aborted v9g-2 Gemini rows, 4 main retries, 21 adaptive YAML-parse retries. |
| Protocol v5 aggregator (`scripts/aggregate_protocol_v5.py`) | `v5-*/results.jsonl` | **PASS** (0.5s) | **EXACT MATCH** with Table 12 | Hardcodes `1.000` completion column after filtering to completed rows; 33 Gemini + 53 Groq failed attempts were pruned prior to completion. |
| Overhead microbenchmark (`tests/performance/test_overhead.py`) | `docs/experiments.md:143` | **PASS** (1.7s) | Current hardware (Apple Silicon macOS 27.2): **B1 0.15 ms, B2 0.22 ms, P 1.63 ms, GPLUS 1.65 ms** (historical: 0.16, 0.23, 1.68, 1.69 ms). | Hardware-dependent timing; reported separately from historical measurements. |

## 3. Raw Evidence Availability Audit (What Exists vs Missing)

| Evidence Class | Status | Exact Files | Implication |
|---|---|---|---|
| Protocol v1–v2 `results.jsonl` & `manifest.json` | **PRESENT** | `experiments/results/{main,adversarial,sequence,v2-main,v2-compromised,v2-adversarial}/` | Per-run scores, tokens, latencies reproducible from raw JSONL. |
| Protocol v1–v2 `transcripts.jsonl` (for v3 offline soundness) | **MISSING (gitignored)** | Required by `validate_bound offline` (`1,575 runs / 2,051 tool calls`); only aggregate `v3-offline/offline.json` exists. | **Cannot be labeled reproduced (`ISS-001`)**; must classify as historical aggregate-only. Also 0/80 textual injection attempt count in adversarial transcripts is aggregate-only. |
| Protocol v3 `v3-bound`, `v3-lp`, `v3-nominal` | **PRESENT** | `experiments/results/v3-{bound,lp,nominal}/results.jsonl` | Exact counts reproduced (`0/120` soundness violations, `75/75` blocked, `39/39` direct, `0/6` transitive, `36/36` LP live). |
| Protocol v5 `v5-main-*`, `v5-compromised-*` | **PRESENT (completed only)** | `results.jsonl` present; pruned failed attempts only in `temp/` (partial) and git tag `paper-v1`. | Uneven repetition counts per task (2–5 reps) due to free-tier resumptions. |
| Protocol v6 & v6b AgentDojo per-task JSONs | **PRESENT** | `experiments/results/agentdojo-v6*/<suite>/.../*.json` & `token_usage.jsonl` | Re-aggregated independently from all 97 benign + 529 attack per-task JSONs; exact match to Table 8 (`89/97` vs `60/97`, `30 lost`, `1 gained` = `workspace|user_task_3`, net drop `29`). |
| Protocol v7b mining `configs.jsonl` & `results.jsonl` | **PRESENT (clones deleted)** | `experiments/mining/{configs.jsonl,results.jsonl,funnel.json,search_snapshot_*.json}` | Clones deleted (except leftover `_clones/nexi-lab__nexus_validate`); snapshots re-fetched 4 min after original run (disclosed). Re-fetching public commits audited in Stage 6. |
| Protocol v9 raw JSONL rows & ledger | **PRESENT** | `experiments/results/v9/{runs/,realworld/main/rows.jsonl,ledger.jsonl}` | All 8 blocks complete (`validate_v9_matrix.py`: `all_clean=True`), but rows omit provider-returned `response.model` (`ISS-007`). |
| Original SLR CSVs (`screening.csv`, `extraction.csv`, `search-log.csv`) | **MISSING** | Absent from repo and `temp/`. | Related work must stay a narrative review with newly logged Stage 6 search update (`ISS-003`). |
