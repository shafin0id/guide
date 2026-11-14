# Revision log: from the V1 submission to the V2 manuscript

This file records why the revision started, what was planned, what was run, what went wrong on the way, what the results were and what changed in the manuscript. Everything here is on the local git branch `step3-protocol-v9`.

## 1. Why this started

The V1 manuscript (`docs/paper/Final Submission [read only for ai]/GUIDE_Manuscript_Draft_Submitted_V1.docx`) went to the supervisor. The supervisor sent back 21 feedback items (`Supervisor Feedback 1.md` in the same folder), grouped into four parts:

- A. Critical research improvements (items 1 to 7): real-world validation on LangGraph, CrewAI and AutoGen, the benign utility drop (91.8% to 61.9%, Slack 66.7 points), stronger live attacks, quantitative comparison with existing defenses, the 588 of 949 scope and the 45 uncontained pairs, the assumptions of the formal model, and more diverse topologies.
- B. Method items (8 to 13): prediction on unseen tasks, statistics and sample sizes, the security-utility trade-off, model documentation, reproducibility and the literature review method.
- C. Reporting items (14 to 17): contradictory workflow statistics, RQ and hypothesis numbering, overclaiming, and the 92.8% versus 96.9% accuracies.
- D. Writing and presentation (18 to 21).

The supervisor could not be contacted again, so every open decision was made in a way that follows the strictest reasonable reading of the feedback. The work was split into four steps. Step 1 is fixing the text, Step 2 is new analysis on existing data, Step 3 is new experiments, and Step 4 is formatting. Step 3 was done first, at the user's request, because the text changes depend on its results.

## 2. Constraints

- Budget: 90.09 CNY of DeepSeek credit and about $10 of Gemini credit.
- Host memory was often critically low, so no sub-agents were used and heavy steps ran one or a few at a time.
- One full run only. Everything was tested in smoke runs first, and each protocol was frozen in git before its main run.
- No result was tuned after it was seen. Negative results are kept.

## 3. Plan

The plan is in `docs/step3-plan.md`. Its main decisions were:

- Real-world validity: build 15 applications with the real frameworks (5 per framework, 5 topologies each), with sandboxed stateful tools. These are framework-built applications, not third-party production systems, and the paper says so.
- Comparison: run the four AgentDojo baseline defenses (tool filter, spotlighting, repeat user prompt, PI detector) inside the same agent loop and model as GUIDE. CaMeL and Progent were not run, which is stated as a limitation.
- Utility: design enforcement variants from the actual Slack failures, choose them on a seeded 30% development split, and report them on all tasks.
- Theory: add an assumptions section and a zero-cost bounded exhaustive check of the formal model.
- Budget fit: use DeepSeek for most cells and a 200-pair stratified attack sample instead of all 949 pairs, because the full-grid containment number already comes from the free replay.

## 4. What was done, in order

### 4.1 Free diagnosis (W1)

- Slack benign failures under GUIDE: 13 of 15 were provenance denials of values that came from a listing tool (channel names, user names, file lists).
- The 45 uncontained pairs in the v8 replay: 16 banking `update_password` calls with no control parameter, 20 travel calendar events and 1 travel email with a legitimate recipient but attacker content, 5 Slack direct messages to a listed user, and 3 workspace `delete_file` calls whose id matched by substring.
- 588 of 949 pairs are in scope because only those injection goals need a write or external call. The other 361 have read-only goals.

### 4.2 Enforcement variants (W2)

Code: `src/guide_research/provenance_v9.py`. Offline study: `experiments/results/step3/w2/variants.json`.

- `strict`: the submitted v8 guard.
- `cred`: credential and profile fields are also treated as control parameters.
- `flexI_cred`: `cred` plus identifiers returned by listing tools are accepted, for internal sinks only.
- Other variants (`hard`, `flexI`, `flexA`) were tested offline and dropped because they were dominated or lost utility.
- Full-grid containment from the replay: strict 543 of 588, cred 559 of 588 (95.1%), flexI_cred 522 of 588 (88.8%).

### 4.3 Engineering and smoke tests

- `src/guide_agentdojo/spend.py`: provider settings, pricing, a per-call spend ledger and hard caps.
- `src/guide_agentdojo/pipeline.py`: provider-neutral, runs the variants and the four baselines, logs cache-hit tokens.
- `src/guide_agentdojo/run_v9.py`: one resumable runner for every live AgentDojo cell.
- `src/guide_agentdojo/adaptive.py`: a 5-round LLM attacker that reads the monitor's denial text and rewrites the injection.
- `src/guide_realworld/`: the 15 LangGraph, CrewAI and AutoGen applications in a separate environment `.venv-rw`.
- `scripts/step3/exhaustive_bound.py`, `scripts/step3/analyze.py`, `scripts/step3/verify_complete.py`.

Problems found during smoke tests and fixed before freezing:

- The model name `deepseek-v4-flash` had been dropped by DeepSeek. Requests now go to `deepseek-flash` (served as DeepSeek-V4.1-Flash-1017). Because of this, the no-defense and GUIDE conditions were all rerun so the comparison is like for like.
- DeepSeek's thinking mode is on by default and breaks multi-turn tool calls, so it is disabled explicitly. AutoGen silently dropped this setting, so it is forced at the client level. Each framework was checked with a 1-token test.
- Gemini 2.5 Flash-Lite was closed to new accounts, so Gemini 3.1 Flash-Lite was used. It needs its thought signatures echoed back on tool calls, which was added.
- The default DeepSeek agent resisted every standard attack (0 of 20 undefended), so attack grids use a "weak" agent prompt that tells it to follow instructions found in tool output.
- In the framework applications, tool-output injection rarely worked, so the main real-world threat is an assumed-compromised reader agent that relays the attacker's request. This matches the threat model of the formal bound.

### 4.4 Protocol freezes

| Tag | Content |
|---|---|
| `protocol-v9a-frozen` | AgentDojo live runs: 8 defenses, benign on all 97 tasks, attacks on 200 pairs (`docs/protocol-v9a.md`) |
| `protocol-v9b-frozen` | 15 framework applications, 4 conditions, 720 runs (`docs/protocol-v9b.md`) |
| `protocol-v9c-frozen` | adaptive attacker on 30 pairs |
| `protocol-v9g-frozen` | Gemini replication, 20 pairs, 4 GUIDE conditions |

### 4.5 Fixes after freezing (disclosed in the paper)

- The first tool filter returned no tools, because the provider ignores tool schemas when tool calling is off. It was rewritten to list the tools in the prompt, and its first rows were discarded.
- Attacker text from the adaptive loop broke AgentDojo's YAML loader, so special characters are now neutralized.
- A final-message edge case in the pipeline was fixed.
- PI detector inputs are truncated to its 512-token window. About 84 benign and 11 cells per attack ran before this change.
- A planned larger Gemini block (v9g-2) was stopped after about 25 cells because the supplied key turned out to be free tier too. The frozen 20-pair block was run instead, with automatic swapping between four keys.

### 4.6 Completeness

`scripts/step3/verify_complete.py` checks every expected cell for a completed row. Final result: 0 missing in every block.

| Block | Cells |
|---|---|
| Benign, 8 conditions | 97 x 8 |
| Benign repetitions 2 and 3, 4 GUIDE conditions | 97 x 4 x 2 |
| Direct attack, 8 conditions | 200 x 8 |
| Important_instructions attack, 8 conditions | 200 x 8 |
| GUIDE-aware attack, 4 conditions | 200 x 4 |
| Adaptive attacker | 30 x 4 |
| Framework applications | 720 |
| Gemini replication | 20 x 4 |

### 4.7 Spend

DeepSeek balance went from 90.09 CNY to 57.18 CNY. The Gemini ledger estimate is $0.75, and the Gemini runs used free-tier keys.

## 5. Results

Full tables: `experiments/results/step3/summary.md` and `docs/step3-results.md`.

AgentDojo, DeepSeek, Protocol v9a:

| Defense | Benign utility | Slack | Direct attack success | Full-grid containment |
|---|---|---|---|---|
| None | 95.9% | 100.0% | 9.0% | 0.0% |
| strict | 62.9% | 28.6% | 0.5% | 92.3% |
| cred | 62.9% | 28.6% | 1.0% | 95.1% |
| flexI_cred | 78.4% | 66.7% | 0.5% | 88.8% |
| Tool filter | 86.6% | 71.4% | 1.0% | n/a |
| Spotlighting | 95.9% | 100.0% | 4.5% | n/a |
| Repeat user prompt | 94.8% | 100.0% | 4.0% | n/a |
| PI detector | 57.7% | 33.3% | 1.5% | n/a |

- flexI_cred beats strict on benign utility (exact McNemar p = 0.0007). Repeated runs changed at most 2 of 97 tasks.
- The important_instructions, GUIDE-aware and adaptive attacks rarely or never succeeded, even with no defense (2.5%, 1.0% and 0 of 30). This is a real limitation of DeepSeek as a test model and is stated in the paper.

Framework applications, Protocol v9b:

- With no defense, the compromised reader reached its goal in 23 of 90 runs (25.6%). strict and cred stopped all of them, and flexI_cred allowed 6, all in one CrewAI application.
- Benign success: 73.3% with no defense, 26.7% under strict, 43.3% under flexI_cred.
- The guard rule predicted the monitor's decision on 84.1% of 69 attacker sink calls in these unseen applications, with no soundness violation.

Gemini 3.1 Flash-Lite, Protocol v9g: attack success 15 of 20 with no defense and 1 of 20 under each GUIDE condition.

Exhaustive check: 594,516 influence cases with no oracle mismatch and no monotonicity violation, and 1,966,080 gate evaluations (250,880 executed, 1,715,200 denied) with no soundness or exactness violation.

## 6. Manuscript changes (V2)

The V1 file was copied and only the copy was edited: `GUIDE_Manuscript_Revised_V2.docx`, with a plain-text export `GUIDE_Manuscript_Revised_V2.md`.

| Feedback item | Change |
|---|---|
| 1, 7 | New Section 3.14 and Section 4.6 with Table 14 (framework applications) |
| 2, 10 | Variants and Table 13 (utility, attack success, containment), trade-off paragraph in the discussion |
| 3 | Direct, GUIDE-aware and adaptive attacks and the Gemini replication, with the low DeepSeek attack success stated plainly |
| 4 | Four baselines under the same conditions, plus a discussion paragraph on where GUIDE fits |
| 5 | Why 588 of 949, the 45 uncontained pairs by cause, and the cred result |
| 6 | Assumptions and limits of the bound, and the exhaustive check |
| 8 | Prediction tested on the unseen framework applications |
| 9 | Wilson intervals, exact McNemar, Cohen's h, sample-size reasoning, repetitions |
| 11 | Exact model ids, snapshot, thinking mode, token limits and package versions |
| 13 | Search strings, sources, criteria and PRISMA counts, single screener stated |
| 14 | "All 55 linear" corrected to 49 of 55, and the mining table now says sequential process type |
| 15 | RQ6 added, hypotheses renumbered H1 to H6 in text and Table 2 |
| 16 | Soundness scoped to the monitor's own enforcement, "model invariance" changed to "model dependence" |
| 17 | The 92.8% and 96.9% now each state their reference |
| 18 | Proofread of the broken paragraphs in related work, methods, results and discussion |

Other updates: the abstract, contributions, deviation table (A35 added), limitations, conclusion and 7 new references (Wilson, McNemar, Cohen, Hines, Protect AI, LangGraph, CrewAI).

### 6.1 Errors found in V1 during the consistency check

The numbers in the V2 docx were checked against the result files with `scripts/paper/verify_docx_numbers.py`, and the leftovers were recomputed from raw data by hand. This found four errors that were already in V1:

- Table 8 per-suite values had been typed into the build script by hand and did not match the raw summaries. For example, Slack is 95.2% to 28.6%, not 90.5% to 23.8%. The overall row was correct.
- Figure 5 used the same wrong undefended values. It was regenerated from the raw data and replaced in the docx.
- The Gemini 3.5 and GPT-OSS run counts were given as 144, but Table 12 was computed on 248 and 166 completed runs.
- Adaptive routing was described as recovering after 19 runs. It failed once in warm-up and then completed 19 of 20.

### 6.2 Second audit pass and polish (Supervisor Feedback 1 completeness check)

After auditing `GUIDE_Manuscript_Revised_V2.docx`, figures, tables, supplementary material, and repository state against all 21 items of `Supervisor Feedback 1.md`, the remaining gaps were closed directly:

- Manuscript prose and tables: fixed §2 `DBLP` to `Semantic Scholar`, added `(Wohlin, 2014)` citation for backward snowballing, added `(Figure S1)` reference, numbered `equation (1)` in §3.2, updated §3.2 `Figure S1` to `Figure S2`, standardized Groq model id in §3.5 to `openai/gpt-oss-120b`, fixed §4.2 degraded-agent sentence (`19 of 20` runs after 1 warm-up failure), added explicit hypothesis confirmations (`This supports H3.` in §4.3, `This supports H4.` in §4.4), clarified §5.5 full-grid drop `(from 543 to 522 of 588 pairs)`, clarified §5.6 DeepSeek utility wording (`kept full or near-full utility`), clarified §6 `90 compromised-reader attack runs`, updated Table 2 RQ2 to `H2a to H2c`, converted Table 12 metrics/CIs to percentages to match the rest of the paper, fixed reference casing/initials (`Lecture Notes in Computer Science`, `Saltzer, J. H., & Schroeder, M. D.`), and formatted all 14 tables with fixed proportional widths (`9072 dxa`), repeating headers (`tblHeader`), and `cantSplit`.
- Figures and supplementary material: regenerated Figures 2 (`fig6`), 4 (`fig8`), and 5 (`fig9`) in `scripts/paper/make_figures.py` to remove text overlaps and legend collisions, re-embedded them in `GUIDE_Manuscript_Revised_V2.docx` with matching aspect ratios, added PRISMA diagram `figS1_prisma_flow.png`, and created `GUIDE_Supplementary_Material_V2.docx` / `GUIDE_Supplementary_Material_V2.md` (Figure S1, PRISMA counts table, search strings S1–S6, Figure S2 routing regret, and routing simulation table).
- Repository and CI: re-synced `GUIDE_Manuscript_Revised_V2.md` and `docs/paper/manuscript-draft.md` with the updated `.docx`, updated `README.md` and `REPRODUCE.md` for Protocol v9 (Tables 13–14, `src/guide_realworld/`, `scripts/step3/`), moved `run_topology_v8` out of `guide_research` into `src/guide_bench/topology_v8.py` to fix boundary/mypy errors, cleaned lint checks, unignored the Step 3 `.jsonl` result files in `.gitignore`, and pushed `step3-protocol-v9`.

## 7. Still open

- Step 4: target-journal formatting (template styling, section/word-limit adjustments, and bibliography style conversion once the target journal is decided).
- Open `GUIDE_Manuscript_Revised_V2.docx` and `GUIDE_Supplementary_Material_V2.docx` in Microsoft Word once on desktop to visually confirm page breaks, figure clarity, and table rendering.
- Acknowledgments mention the free tier for Section 3.5; Section 3.14 also notes its Gemini 3.1 Flash-Lite replication quota was set by the free tier (can be echoed in Acknowledgments during journal formatting if desired).
- Local `.env` and `.env.gemini_keys` remain untracked and gitignored (external API key rotation skipped by user instruction).
