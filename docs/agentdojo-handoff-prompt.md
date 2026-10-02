# Handoff Prompt: Build & Run the AgentDojo External Benchmark (4 Phases)

Copy everything below this line into a fresh AI agent session that has access to
this repository (`/Users/shafinoid/Documents/GitHub/guide`).

---

## Context

This is the GUIDE project (an MSc dissertation / paper on multi-agent-system
security containment). All internal data collection (Protocol v5, three model
families: DeepSeek, Gemini, Groq) is complete and documented in
`docs/experiments.md`. The one remaining data-collection gap before the paper
draft is finalized is an **external benchmark run** -- every task and checker in
this project's own suite (`src/guide_bench`) was author-written, and the paper
needs at least one independently-authored benchmark to validate against.

**Full plan and all decisions/rationale already made are written out in
`docs/agentdojo-run-plan.md` -- read that file first, in full, before doing
anything.** It is the single source of truth for this task. Everything below is
a summary; that file is authoritative if anything here is ambiguous or seems to
conflict.

Do not re-derive or re-litigate decisions already made in that file (benchmark
choice, one-model scope, token cap, phase split). If you believe one of them is
wrong, say so and ask -- do not silently change it.

## What you're building and running

1. **An adapter** wiring GUIDE's own agent pipeline (gate + provenance guard +
   policy layer + routing -- the full "GPLUS" containment stack used throughout
   this project) into AgentDojo as a custom agent, so AgentDojo's tasks and
   attacks run against GUIDE instead of a baseline agent.
2. **Four sequential phases**, one per AgentDojo built-in suite (banking, Slack,
   travel, workspace), each run only during a confirmed off-peak pricing window,
   each logged live to the terminal, each checked against a shared token budget
   before the next phase starts.

## Why AgentDojo, why one model, why this scope (full detail in the plan file, §1)

AgentDojo is the confirmed-canonical external benchmark for indirect prompt
injection / agent security research -- the standard baseline this project's own
closest comparator papers (Muruaga/APC-style work, Safin et al.) also validate
against. The user can only justify one more external benchmark run (time cost,
not money), so this was deliberately chosen rather than τ-bench, InjecAgent, or
WebArena. Run on **`deepseek-v4-flash` strictly -- this exact model identifier,
no substitution, no fallback to `deepseek-v4-pro` or any other DeepSeek model.**
The legacy aliases `deepseek-chat` / `deepseek-reasoner` were retired by
DeepSeek on 24 July 2026 and no longer resolve at all -- if you see either name
anywhere in example code, pricing comparisons, or old `.env` files, it is stale
and must not be used. GUIDE's cross-model
generalization claim is already fully supported by its own internal 3-model
suite (Protocol v5); AgentDojo's job is a different axis of validity (external
task/attack authorship), and every comparator paper validated on one model too.
Running 3 models here would ~3x cost for a claim this paper doesn't need.

## Pricing, budget, and why (full detail in the plan file, §2)

DeepSeek API, user's account recharges in CNY. Off-peak (cache miss): 1 CNY/M
input tokens, 4 CNY/M output tokens, 2500 req/s concurrency. Peak (avoid): 2
CNY/M in, 8 CNY/M out, 500 req/s concurrency. Peak hours = 9:00-12:00 and
14:00-18:00 Beijing time, Mon-Fri, excluding Chinese statutory holidays;
everything else (incl. all weekend) is off-peak. User is in UTC+8 (same offset
as Beijing), so these clock times map directly to the user's own wall clock.

**Budget is a token cap, not a currency cap: 10,000,000 tokens total across all
4 phases combined.** Estimated actual usage for the full run is 3-5M tokens
(derived from AgentDojo's own task/attack volume: ~40 base tasks x 4 suites x
full attack matrix, ~1,800 total calls, ~1,500-2,500 tokens/call). The 10M cap
is a ~2-3x safety margin over that estimate, covering retries and reruns without
needing to stop for a second approval mid-task. At off-peak rates this is
roughly 20 CNY worst case, likely 6-10 CNY actual -- money is not the real
constraint here; the token cap and the concurrency limit are. Track cumulative
token usage after every phase against this 10M cap in a shared ledger file (see
plan file §6-7) and stop / ask before continuing if a phase's actual usage
suggests the total will blow past it.

## Why 4 phases, why off-peak only (full detail in the plan file, §3)

AgentDojo ships 4 independent suites (banking, Slack, travel, workspace), each
self-contained. Running all 4 as one long unbroken session risks silently
crossing from an off-peak window into a peak window mid-run, which would 2x the
price for whatever portion ran during peak hours without anyone noticing. So:
**one suite per phase, each phase started only after confirming current Beijing
time is inside an off-peak window, and each phase short enough to plausibly
finish inside that same window.** This also means a failed/retried phase doesn't
require re-running the other 3, and token usage is auditable per-phase.

## Terminal logging -- hard requirement

**The terminal must show live, readable progress for every phase, start to
finish -- not just a final summary.** This project has already lost real time
twice to processes that died silently mid-run with no visible signal (a Groq
API run that exited within a minute of launch with zero output, caught only by
`pgrep` finding nothing). Do not pipe to a log file only. For each phase's run:
- Run with stdout visible in the terminal, `tee`'d to a log file as well
  (not redirected-to-file-only).
- Print, as it happens: current suite name, a running task/attack counter
  (e.g. `[task 7/40] [attack 3/9]`), a running token-usage tally for this phase
  so far, and an unambiguous `PHASE COMPLETE` or `PHASE FAILED` line at the end.
- If AgentDojo's own CLI buffers/suppresses output by default, use `python -u`
  or wrap it with a thin progress reporter rather than accept a silent run.

## The 4 phases (plus Phase 0 prerequisite)

**Phase 0 (prerequisite, not itself one of the 4 data phases):**
- Add `agentdojo` to the project venv pinned to an exact version:
  `uv add agentdojo==<exact version>` (check PyPI for the current stable
  version first; do not use an open range).
- Confirm the run config/`.env` names the model as exactly `deepseek-v4-flash`
  -- not `deepseek-v4-pro`, not a legacy `deepseek-chat`/`deepseek-reasoner`
  alias (retired, non-functional since 24 July 2026). Fix this before the
  smoke test, not after a failed call.
- Build the adapter: wire GUIDE's pipeline as an AgentDojo custom agent; map
  AgentDojo's tool/task metadata into whatever shape GUIDE's gate / provenance
  guard / policy layer needs to evaluate a call; compute the static
  blast-radius bound for AgentDojo's tool graph (reuse
  `src/guide_bench/validate_bound.py`'s approach if it generalizes, otherwise
  extend it).
- Commit a `protocol-v6` git tag freezing the adapter and run config **before**
  any task or attack is executed against it -- same discipline as this
  project's `protocol-v1` through `protocol-v5` tags. No adapter changes after
  this tag without a new tag and a disclosed deviation note in the plan file.
- Smoke-test on a tiny slice (1-2 tasks, no attacks) end-to-end before
  committing real token budget to a full-suite run. Confirm it produces a
  parseable result row.

**Phase 1 -- Banking suite.** Full official AgentDojo banking suite (all base
tasks x full built-in attack set) against GUIDE's GPLUS containment stack, one
model (DeepSeek). Start only in a confirmed off-peak window. Run first because
it is typically AgentDojo's smallest/simplest suite -- cheapest place to catch
an adapter bug before the larger suites spend real budget on the same mistake.

**Phase 2 -- Slack suite.** Same setup, run only after Phase 1 completes and its
results are confirmed sane (adapter is proven working). Start only in a
confirmed off-peak window; it may be a different calendar day/window than
Phase 1.

**Phase 3 -- Travel suite.** Same setup, same preconditions as Phase 2.

**Phase 4 -- Workspace suite.** Same setup, same preconditions. After this phase
completes, do the token-usage reconciliation across all 4 phases against the
10M cap and summarize final total usage and CNY cost (actual, not estimated) in
the plan file and the ledger.

Each phase, on completion, must:
1. Append its actual token usage (input + output, separately) to
   `experiments/results/agentdojo-v6/token_usage.jsonl`.
2. Save its raw, untouched AgentDojo result file(s) under
   `experiments/results/agentdojo-v6/<suite>/`.
3. Save its full tee'd terminal log under the same folder.
4. Update the phase status table in `docs/agentdojo-run-plan.md` §5 (mark done,
   note actual vs. estimated token usage, note any deviation).

## After all 4 phases are done

Integrate results into:
- `docs/experiments.md` -- new "Protocol v6: external benchmark (AgentDojo)"
  section, same style/rigor as the existing Protocol v5 section (per-suite
  table, containment result, honest disclosure of one-model scope and why).
- `docs/paper/manuscript-draft.md` -- Results section, with the same honest
  framing already used throughout this paper (external validity axis, not a
  second cross-model claim; disclose it's one model, by design, not an
  oversight).

## Non-negotiable rules carried over from this project's standing practice

- No fabricated or estimated results -- every number in any doc after this run
  must trace to an actual completed result row on disk.
- Freeze protocol (git tag) before running, same as every prior protocol
  version in this project.
- Disclose every deviation from this plan, don't quietly absorb it.
- Verify completion by **parsing result keys and filtering to actually
  completed rows**, never by trusting a tool's own summary or a raw line count
  -- this project has been burned by exactly that mistake multiple times
  already (padded row counts from retried/leftover rows masking real gaps).
- If a phase's process dies silently (zero output, exits early), do not assume
  it's fine because something ran -- check the actual result file's row count
  and the terminal log before calling a phase complete.
