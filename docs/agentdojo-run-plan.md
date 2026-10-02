# AgentDojo External Benchmark Run -- Plan & Handoff

Status: **Phase 0 & Phase 1 complete**. Phase 2 (Slack) ready to initiate. This file is the single source of truth for this run:
decisions made, why they were made, and the exact 4-phase execution plan. A fresh
agent session (or a future you) should be able to pick this up with zero other
context.

This is the project's last planned data-collection piece before the paper draft
is finalized. Treat the integrity rules in `pref.scientific_integrity` (frozen
protocol before runs, no fabrication, disclose deviations) as binding here too.

---

## 1. Why AgentDojo, and why only one more benchmark run

- GUIDE's own suite (`src/guide_bench`) is author-authored: every task, checker,
  and the 19 structural configs were written by this project, not drawn from an
  external benchmark. That is the single biggest gap standing between this paper
  and a confidently Q1/Q2-level submission (see 2026-10-02 session discussion).
- Confirmed via web research (2026-10-02): AgentDojo is the canonical, widely-cited
  benchmark for indirect prompt injection / agent-security research. It is the
  shared external baseline that comparator papers in this project's own
  related-work table (Muruaga/APC-style work, Safin et al.) report against. It is
  not a wasted pick -- it is the standard move for this exact gap.
- The user can only afford one more external benchmark run (time and attention,
  not money -- see cost section below). AgentDojo was confirmed as worth that
  single shot before committing.
- Decision: run the **full official AgentDojo suite** (all 4 of its own task
  suites: banking, Slack, travel, workspace; all built-in attacks), on **one
  model only** (DeepSeek, off-peak pricing -- see below), not three.
  - Why one model is defensible to a reviewer: GUIDE's own 3-model
    cross-model-generalization claim is already fully supported by the internal
    suite (Protocol v5, `docs/experiments.md`). AgentDojo's job here is different
    -- it answers "does containment hold on an independently authored external
    benchmark," not "does it hold across models." That is a different axis of
    external validity, and every close comparator cited in this project's
    literature review (Muruaga/APC, Safin et al.) validated against an external
    benchmark on one model too. Running three models on AgentDojo would be ~3x
    the cost for a claim this paper doesn't need to make.
- Scope: run against GUIDE's full containment configuration (the gate + the
  provenance guard + the policy layer + routing, i.e. GPLUS in this project's
  own naming) so the result is "does GUIDE's full containment hold against an
  independent benchmark's attacks," plus compute the static blast-radius bound
  for AgentDojo's task/tool graph. If time/token budget allows, add the B1/B2/P
  conditions for direct comparability with the internal suite's table shape --
  this is a nice-to-have, not required to close the gap.

## 2. Pricing, budget, and why that budget

Source: DeepSeek API pricing docs, confirmed 2026-10-02, user's account is
recharged in CNY.

| | Off-peak (cache miss) | Peak (cache miss) |
|---|---|---|
| Input, per 1M tokens | 1 CNY | 2 CNY |
| Output, per 1M tokens | 4 CNY | 8 CNY |
| Concurrency limit | 2500 | 500 |

- **Peak hours** (avoid): 9:00-12:00 and 14:00-18:00, Beijing time, Monday-Friday,
  excluding Chinese statutory holidays.
- **Off-peak hours** (run only during these): everything else -- before 9:00,
  12:00-14:00, after 18:00 Beijing time on weekdays, plus all of Saturday and
  Sunday, plus all day on Chinese statutory holidays.
- User's local time is UTC+8, same offset as Beijing, so Beijing peak/off-peak
  clock times map directly to the user's own wall clock: off-peak windows are
  **before 09:00, 12:00-14:00, after 18:00** on weekdays, and **all weekend**.
- Decision: **cap the run at 10,000,000 tokens total**, not a dollar/CNY figure.
  - Estimated actual usage for the full official 4-suite run: 3-5M tokens
    (derived from AgentDojo's ~40 base tasks per suite x 4 suites x its full
    attack matrix, ~1,800 total LLM calls, averaging 1,500-2,500 tokens/call --
    the same order of magnitude as GUIDE's own internal suite).
  - 10M is roughly 2-3x that estimate, which covers retries, repaired/failed
    calls, and reruns of any suite that errors out mid-run, without needing a
    second approval mid-task.
  - At off-peak rates, 10M tokens costs on the order of **~20 CNY worst case**
    (3-5M estimated actual usage is nearer **~6-10 CNY**). This confirms the
    token cap, not the CNY cost, is the real constraint to manage here --
    money was never the binding limit; wall-clock time and the concurrency cap
    are.
- The concurrency limit (2500 req/s off-peak vs 500 peak) is the more operationally
  real constraint than price: it determines how fast a suite can actually run,
  not whether it's affordable.

## 3. Why phase-by-phase (suite-by-suite), and the off-peak constraint

AgentDojo ships 4 independent task suites: **banking, Slack, travel, workspace**.
Each is a self-contained module (its own tools, environment, and attack
injections) and can be run as a separate process/invocation.

Running all 4 in one long unbroken session risks the run crossing from an
off-peak window into a peak window mid-flight (e.g. starting at 18:30 and still
running at 09:00 the next weekday) -- which would silently 2x the per-token cost
for whatever portion ran during peak hours, undisclosed unless caught.

Decision: split the run into **4 phases, one AgentDojo suite per phase**, each
phase short enough to start and finish inside a single off-peak window (evenings
after 18:00, early mornings before 09:00, the 12:00-14:00 weekday gap, or any
time on a weekend). This also means:
- A phase that fails or needs a retry doesn't require re-running the other 3.
- Token usage is checked and logged against the 10M cap after every phase, not
  only at the end -- so a runaway phase is caught before it burns the whole
  budget on one suite.
- Each phase's logs and results are self-contained and auditable independently.

## 4. Terminal logging requirement

Whoever runs each phase **must** see live progress in the terminal while it
runs -- not just a final summary after the process exits. This project has
already been burned twice by processes that silently died mid-run with no
visible signal until a `pgrep` found nothing (the Groq relaunch, 2026-10-01/02).
For AgentDojo:
- Do not pipe output to a log file only -- run with stdout visible in the
  terminal (tee to a log file in addition, don't redirect-only).
- Each phase's runner script must print, as it happens: which suite is running,
  which task/attack pair is currently executing (a running counter like
  `[task 7/40] [attack 3/9]`), running token-usage tally so far this phase, and
  a clear `PHASE COMPLETE` / `PHASE FAILED` line at the end.
- If AgentDojo's own CLI buffers or suppresses this by default, wrap it (e.g.
  `python -u`, or a thin progress-reporting wrapper around its task loop) rather
  than accept a silent run.

## 5. The 4 phases

Each phase = one AgentDojo suite, run against GUIDE's full containment stack
(GPLUS), on **`deepseek-v4-flash` strictly -- no other DeepSeek model**, started
only inside a confirmed off-peak window (check current Beijing time before
starting; see §2), capped against the shared 10M token budget tracked
cumulatively across all 4 phases.

| Phase | AgentDojo suite | Depends on | Approx. task/attack volume | Status & Outcome |
|---|---|---|---|---|
| 0 | **Adapter / Bounds / Smoke** | Prerequisites | Static bounds + 1 task smoke | **COMPLETE** (smoke util=100%, sec=100%, bounds proven 100%) |
| 1 | **Banking** | Phase 0 complete | 16 base tasks + 144 attack pairs | **COMPLETE** (benign util=75.0%, attack util=79.2%, containment=100.0%, 1.25M tokens, ~1.78 CNY) |
| 2 | **Slack** | Phase 1 adapter proven working | 21 base tasks + 105 attack pairs | **Pending** (ready to start in off-peak window) |
| 3 | **Travel** | Phase 1 adapter proven working | 20 base tasks + 140 attack pairs | **Pending** |
| 4 | **Workspace** | Phase 1 adapter proven working | 40 base tasks + 560 attack pairs | **Pending** |

Phase 0 (prerequisite, not one of the 4 data-collection phases): build and smoke-test
the GUIDE<->AgentDojo adapter (pin `agentdojo` to an exact version in the project
venv via `uv add`; wire GUIDE's pipeline as an AgentDojo custom agent; map
AgentDojo's tool/task metadata into whatever shape GUIDE's gate/provenance
guard/policy layer needs to evaluate it; compute the static blast-radius bound
for AgentDojo's tool graph). Phase 0 should itself be smoke-tested on a tiny
slice (1-2 tasks) before Phase 1 commits real budget to a full suite run.

Order rationale: Banking first because it is typically the smallest/simplest
AgentDojo suite, so it is the cheapest place to catch an adapter bug before the
other 3 (larger) suites consume real budget on the same mistake.

## 6. What must be true before Phase 1 starts

- [x] `agentdojo` package added to the project venv, pinned to an exact version
  (`agentdojo==0.1.35`), via `uv add agentdojo==0.1.35`.
- [x] A `protocol-v6` tag committed in git, freezing the adapter code and run
  config before any task/attack is executed against it -- same discipline as
  `protocol-v1` through `v5`.
- [x] Adapter smoke-tested on a tiny slice (1-2 tasks, no attacks) to confirm it
  runs end-to-end and produces a parseable result row, before any full-suite run.
- [x] Current Beijing time checked and confirmed off-peak before every phase
  start (not just Phase 1) -- see §2 windows.
- [x] A running cumulative token-usage ledger file started (e.g.
  `experiments/results/agentdojo-v6/token_usage.jsonl`), updated after every
  phase, checked against the 10M cap before starting the next phase.

## 7. Results and transparency tracking

All raw run output, logs, and a running tally belong under
`experiments/results/agentdojo-v6/`, one subfolder per phase/suite
(`banking/`, `slack/`, `travel/`, `workspace/`), each with:
- the raw AgentDojo result file(s) for that suite, untouched;
- the full terminal log captured via `tee` (not reconstructed after the fact);
- a token-usage line appended to the shared `token_usage.jsonl` ledger at phase
  completion.

This document (`docs/agentdojo-run-plan.md`) should be updated in place as each
phase completes -- mark phases done in §5's table, log actual token usage vs.
estimate, and note any deviation from this plan (per `pref.scientific_integrity`,
deviations get disclosed, not hidden).

Once all 4 phases are done, the results need to be integrated into
`docs/experiments.md` (a new "Protocol v6: external benchmark (AgentDojo)"
section, same style as the existing Protocol v5 section) and into the paper
draft at `docs/paper/manuscript-draft.md` (Results section), with the honest
caveats this project has consistently kept in: reduced scope vs. the internal
suite is fine, but it must be stated, not implied otherwise.
