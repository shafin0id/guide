# Handoff Prompt — AgentDojo Undefended-Baseline Run (Protocol v6b)

Copy everything below this line into a fresh agent session.

---

I need you to run the **undefended baseline** for GUIDE's AgentDojo external
benchmark campaign. This is a single, bounded, well-specified task. Full
context, budget rationale, and every decision behind this run are written
down in **`docs/agentdojo-baseline-run-plan.md`** in this repository — read
that file in full before doing anything else. It is the source of truth; this
prompt is a pointer to it plus the hard constraints repeated here so they
can't be missed.

## What this is and why

GUIDE is a research artefact from an MSc dissertation project, now being
reframed for journal submission as a **reference monitor**: a deterministic,
out-of-band enforcement layer that bounds and contains what a compromised
agent (or subset of agents) can do, rather than a multi-agent orchestration
framework. (It is explicitly *not* positioned as competing with
LangChain/CrewAI/AutoGen.)

A prior run (**Protocol v6**, already complete — see
`docs/agentdojo-run-plan.md`) evaluated GUIDE's full containment stack
(policy gate + provenance guard + policy layer, called "GPLUS" in this
project) against all 4 AgentDojo suites (banking, slack, travel, workspace),
on `deepseek-v4-flash`, and found 0 of 517 tool-calling attacks succeeded,
with benign task utility of 63.9% overall.

That result is **not yet comparable to anything** because there is no
undefended baseline on the same tasks, same model. Without it, nobody can
tell whether GUIDE's 63.9% utility is a real cost (undefended might score
~95%) or no cost at all (undefended might also score ~65%), and whether 0%
attack success is impressive (undefended might be ~40%+) or trivial
(undefended might also be near-0% because this particular model happens to
ignore these particular injection styles — which is exactly what happened in
this project's own earlier internal benchmark suite). The three closest
published comparator systems (CaMeL, Progent, FIDES — all AgentDojo-based)
each report exactly this defended-vs-undefended pair, so GUIDE's paper needs
it too to be reviewed on equal footing.

This is the project's **last planned data-collection task** before the paper
is finalized.

## Hard constraints — do not deviate from these

1. **Model: `deepseek-v4-flash` strictly.** Not `deepseek-v4`, not `-pro`,
   not any other variant or alias. Must match the model used in Protocol v6
   exactly, or the comparison is invalid.
2. **No new adapter code needed.** `src/guide_agentdojo/pipeline.py`'s
   `GuideGplusPipeline` already accepts `gated=False, provenance=False`
   constructor arguments — this run is that pipeline with both flags off,
   nothing else changed (same `base_url`, `temperature=0.0`, `max_tokens`,
   `max_turns`, `system_message` as the v6 defended runs).
3. **Same task sets as Protocol v6, suite for suite** — this matters for a
   valid paired comparison:
   - banking: 16 benign tasks, 144 attack pairs (`important_instructions`)
   - slack: 21 benign tasks, 105 attack pairs
   - travel: 20 benign tasks, 140 attack pairs
   - workspace: **40 benign tasks** (full), but the **attack condition must
     use the identical 10-task stratified subset v6 used**
     (`user_task_0,4,8,12,16,20,24,28,32,36` × 14 injection goals = 140
     pairs) — read `docs/agentdojo-run-plan.md` §8's footnote on this before
     you start; running the full 40 under attack here while v6 only ran 10
     breaks the paired comparison.
4. **Off-peak only.** DeepSeek pricing: off-peak (1 CNY/1M input, 4 CNY/1M
   output) is half of peak (2 CNY/1M input, 8 CNY/1M output). Off-peak
   windows (Beijing time = user's local time, both UTC+8): before 09:00,
   12:00–14:00, after 18:00 on weekdays, plus all weekend. **Check the clock
   before starting, and re-check before every suite transition within the
   run** — if you cross into a peak window mid-run, pause and wait for the
   next off-peak window rather than silently continuing at 2x cost.
5. **Token budget: 12,000,000 tokens, tracked as a token cap, not a CNY
   figure.** (Expected actual usage: similar order to v6's 11.45M, likely
   somewhat higher since undefended runs tend to make more tool calls, not
   fewer, with nothing blocking them early. At off-peak rates 12M tokens is
   roughly ~24 CNY worst case, likely ~14–18 CNY actual — money is not the
   real constraint, the token cap and the concurrency limit are.) Log
   cumulative usage after every suite and stop if you approach the cap.
6. **Run as ONE phase** covering all 4 suites sequentially, not 4 separate
   phases like v6 — but only if you're confident the full run fits inside a
   single off-peak window (v6's largest single suite took ~23 minutes; all 4
   suites × 2 conditions should comfortably fit after an 18:00 start). If you
   have any doubt it fits, say so and fall back to per-suite invocations
   instead of risking a silent peak-rate overrun. Do not force the one-phase
   shape through if the clock math doesn't support it.
7. **Terminal logging must show live progress AND a running completion
   percentage, start to end**, not just a final summary:
   - `python -u` or equivalent — never buffered/silent, always `tee`'d to a
     log file in addition to stdout.
   - Compute the total planned (suite, condition, task) unit count up front
     (97 benign + 529 attack-pair units = 626 total units across all 4
     suites) so you can report a percentage against a known denominator from
     line one.
   - Print per unit: suite, condition, task/injection identifier, a running
     counter and percentage (e.g.
     `[suite:slack] [attack:important_instructions] [unit 212/626] (33.9%)`),
     cumulative tokens so far, estimated CNY so far.
   - Print `PHASE COMPLETE`/`PHASE FAILED` per suite×condition block and a
     final `RUN COMPLETE — 100%` summary line.
8. **No fabrication, ever.** This project has a standing zero-fabrication
   rule (`pref.scientific_integrity`). If something fails, times out, or a
   process dies silently (this has happened twice before in this project —
   check with `pgrep`/process status, don't assume success from a log file
   existing), report it plainly. Verify completeness by **parsing result
   keys and counting completed cells against the full task×condition grid**
   — never trust a raw line count or a self-reported "100%/N-of-N" summary;
   this exact mistake produced a false completeness claim earlier in this
   project (see `docs/agentdojo-run-plan.md` and the project's own learned
   corrections for the pattern).

## What to do, in order

1. Read `docs/agentdojo-baseline-run-plan.md` in full.
2. Read `docs/agentdojo-run-plan.md` §8 (the v6 results table and footnote)
   so you know the exact task sets and the workspace subset to match.
3. Check current Beijing/local time; confirm off-peak before starting.
4. Confirm `GuideGplusPipeline(gated=False, provenance=False, ...)` runs a
   clean smoke test (1 task, no attack) before committing the full run's
   budget — same discipline as v6's Phase 0.
5. Run all 4 suites, both conditions, matching the task sets in constraint
   #3, with live percentage logging per constraint #7.
6. Save all raw results, logs, and a `token_usage.jsonl` ledger under
   `experiments/results/agentdojo-v6b-undefended/`, mirroring v6's folder
   layout exactly (see `docs/agentdojo-baseline-run-plan.md` §6).
7. Verify completeness by cell-count against the full grid, not line-count.
8. Update `docs/agentdojo-baseline-run-plan.md` §7's checklist in place with
   actual results and any deviations.
9. Report back: a results table (suite × benign-utility × attack-utility ×
   ASR, defended-vs-undefended side by side), total tokens used, total CNY
   cost, and explicit confirmation that the workspace attack subset matched
   v6's 10 tasks.

Do not integrate into `docs/experiments.md` or the manuscript draft yourself
unless asked — report the results back first for review.
