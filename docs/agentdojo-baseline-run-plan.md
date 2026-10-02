# AgentDojo Undefended-Baseline Run — Plan & Transparency Record

Status: **NOT STARTED.** This file is the single source of truth for this run:
why it is needed, the exact numbers behind the budget, and the one-phase
execution plan. A fresh agent session should be able to pick this up with zero
other context beyond this file plus `docs/agentdojo-run-plan.md`.

This is `protocol-v6b` — a direct extension of the completed `protocol-v6`
AgentDojo campaign (see `docs/agentdojo-run-plan.md`), not a new benchmark
choice. Treat `pref.scientific_integrity` (frozen protocol before runs, no
fabrication, disclose deviations) as binding here too.

---

## 1. Why this run exists — the gap it closes

Protocol v6 (completed 2026-10-02) ran AgentDojo's 4 suites **only with GUIDE's
full GPLUS containment stack enabled** (gate + provenance guard + policy
layer). Result: 0 of 517 tool-calling attacks succeeded, benign utility
63.9% overall (varying 28.6%–80.0% per suite).

That result has a hole a reviewer will find immediately: **there is no
undefended run on the same tasks, same model, same seed data.** Without it,
two numbers in the v6 report are unverifiable:

1. **GUIDE's utility *cost*.** 63.9% benign utility means nothing on its own —
   we don't know what the same model (`deepseek-v4-flash`) scores on the same
   AgentDojo tasks with no gate, no provenance guard, nothing. If undefended
   utility is also ~65%, GUIDE costs ~0% utility. If undefended utility is
   ~95%, GUIDE costs ~30 points. These are very different stories and the
   paper currently can't tell them apart.
2. **GUIDE's attack-success *reduction*, not just its absolute rate.** 0% ASR
   under GUIDE is unimpressive if the undefended model also scores ~0% ASR on
   these specific attacks (DeepSeek-Flash may simply ignore some injection
   styles, as happened in this project's own internal suite — see
   `docs/experiments.md`, "injection resistance could not be measured" note).
   CaMeL, Progent and FIDES — the three closest comparator systems — all
   report their undefended baseline alongside their defended numbers for
   exactly this reason. GUIDE's paper needs the same pair to be comparable.

This is the project's **last planned data-collection task** before the paper's
Results section is finalized. No new adapter code is required: `GuideGplusPipeline`
(`src/guide_agentdojo/pipeline.py`) already accepts `gated=False, provenance=False`
constructor flags — the undefended condition is a config flip, not new
engineering.

### Framing context this run supports (do not re-derive, just carry forward)

The project reframed GUIDE this session: it is **not** a multi-agent
orchestration framework and is **not** positioned as competing with
LangChain/CrewAI/AutoGen. GUIDE is a **reference monitor** — a deterministic,
out-of-band enforcement layer that computes a sound static blast-radius bound
for any compromised subset of agents and enforces it at the tool-call
boundary. AgentDojo (a single-agent benchmark) validates the *enforcement*
half of that claim (does the gate/provenance guard actually stop attacks on an
independent benchmark); it does not and cannot validate the *multi-agent
bound* half (AgentDojo has no multi-agent task graph). State this scope limit
explicitly in the paper — do not let the AgentDojo result imply a multi-agent
validation it didn't do.

The closest comparator systems (CaMeL, Progent, FIDES — all AgentDojo-based,
all published 2025–2026) each report an undefended-vs-defended utility/ASR
pair. GUIDE's paper needs the same pair to be reviewed on equal footing. A
preliminary comparison table pulled from these papers' abstracts was found to
be partially unverifiable (ASR figures were not in the abstracts for Progent
and FIDES) — do not cite that table's ASR numbers without checking each
paper's actual results tables first; that is separate follow-up work, not part
of this run.

---

## 2. Scope — what runs, what doesn't

- **Model**: `deepseek-v4-flash` — strictly this model. Not `deepseek-v4`,
  not `-pro`, not any other variant. Same model as protocol-v6, so the
  defended/undefended comparison is apples-to-apples.
- **Suites**: all 4 AgentDojo suites — banking, slack, travel, workspace —
  same `benchmark_version="v1.2.2"` as protocol-v6.
- **Tasks**: the **same task sets** actually run under protocol-v6:
  - banking: all 16 benign tasks, all 144 attack pairs (`important_instructions`)
  - slack: all 21 benign tasks, all 105 attack pairs
  - travel: all 20 benign tasks, all 140 attack pairs
  - workspace: **all 40 benign tasks** (full, unlike v6's attack phase), but
    for the attack condition use the **same 10-task stratified subset** v6
    used (`user_task_0,4,8,12,16,20,24,28,32,36` × 14 injection goals = 140
    pairs) — matching subsets is required for a valid paired comparison; do
    not silently run the full 40 under attack here while v6 only ran 10, or
    the two numbers aren't comparable and the asymmetry needs its own
    disclosure if introduced.
- **Pipeline config**: `GuideGplusPipeline(gated=False, provenance=False, ...)`
  — everything else (model, base_url, temperature=0.0, max_tokens, max_turns,
  system_message) identical to the v6 defended runs, so the only variable
  that changes between v6 and this run is containment on/off.
- **Attacks**: `none` (benign) and `important_instructions` (attack) — same
  two conditions used throughout protocol-v6. Do not add new attack types.
- **This is ONE phase**, not four. Rationale in §4.

---

## 3. Pricing, budget, and why that budget

Same DeepSeek pricing table as protocol-v6 (source: DeepSeek API docs,
confirmed 2026-10-02, account recharged in CNY):

| | Off-peak (cache miss) | Peak (cache miss) |
|---|---|---|
| Input, per 1M tokens | 1 CNY | 2 CNY |
| Output, per 1M tokens | 4 CNY | 8 CNY |
| Concurrency limit | 2500 req/s | 500 req/s |

- **Off-peak hours (run only during these)**: before 09:00, 12:00–14:00, after
  18:00 Beijing time on weekdays, plus all of Saturday and Sunday, plus
  Chinese statutory holidays. User's local time is UTC+8, same offset as
  Beijing, so these clock times map directly to local wall clock.
- **Token budget: cap at 12,000,000 tokens for this single run**, tracked as a
  *token* cap, not a CNY cap (CNY cost is incidental given how cheap
  DeepSeek-Flash off-peak is — see below).
  - Why 12M, not 10M like v6: this run has to cover **all 4 suites' full
    benign task sets (97 tasks) plus the same 529 attack pairs v6 covered**,
    under the *undefended* condition. Undefended runs typically use **more**
    tokens than defended runs, not fewer — with no policy gate blocking a
    tool call early, the model is free to make additional tool calls per
    task (retries, exploration, multi-step chains it wasn't denied out of),
    and conversation histories run longer before termination. Protocol v6's
    defended run consumed 11,450,443 tokens; budget this one at roughly
    **1.0–1.3× that figure** to be safe = ~12M.
  - At off-peak rates, 12M tokens costs on the order of **~24 CNY worst
    case** (proportionally similar to v6's actual ~14 CNY for ~11.45M tokens
    — expect actual usage near **~14–18 CNY**). Confirms, same as v6, that
    the token cap is the operative constraint, not CNY cost — money was never
    the binding limit here.
- **Concurrency** (2500 req/s off-peak) is the real throughput constraint,
  same as v6 — it determines how fast the suite can run, not whether it's
  affordable.

---

## 4. Why ONE phase, not four — and why that's safe here

Protocol v6 split into 4 phases (one per suite) specifically to avoid any
single run crossing from an off-peak window into a peak window mid-flight.
That risk is being accepted deliberately here, in one phase, because:

- v6's actual largest single suite (workspace) took ~23 minutes of wall-clock
  for its attack phase (see `experiments/results/agentdojo-v6/workspace/run.log`
  timestamps). All 4 suites' benign + attack conditions together, run
  sequentially, should fit inside one off-peak window if started with enough
  margin (e.g. right after 18:00 Beijing / local time, which gives a 15-hour
  window before the next 09:00 peak start).
- The runner (§5) **must check the Beijing clock before starting and must
  re-check before each suite transition inside the single run** — if a
  suite boundary is reached and the clock has moved into a peak window, the
  runner must pause and wait for the next off-peak window rather than
  silently continuing at 2x cost. This substitutes for v6's phase-boundary
  safety with an in-run clock check instead of a hard stop between manual
  invocations.
- If the agent executing this doubts the full run fits in one window, it
  should say so and split back into per-suite invocations rather than risk a
  silent peak-rate overrun — the one-phase shape is a convenience, not a
  requirement to force through regardless.

---

## 5. Terminal logging requirement — including completion percentage

Same discipline as v6, with one addition: **a live completion percentage**,
not just a task counter. This project has been burned twice by processes that
silently died mid-run with no visible signal (the Groq relaunch, 2026-10-01/02)
and the open requirement is for the user to be able to see, at a glance in the
terminal, start to end, how far through the full run they are.

Requirements for the runner script:
- Run with stdout visible in the terminal, `tee`'d to a log file in addition —
  never redirect-only, never buffered silently (`python -u` or equivalent).
- Compute total planned (suite, condition, task) units up front across all 4
  suites × 2 conditions, so a percentage can be reported against a known
  denominator from the very first line.
- Print, as it happens, for every unit: which suite, which condition
  (benign/attack), which task/injection pair, a running counter
  (`[suite:slack] [attack:important_instructions] [task 42/805] (5.2%)`),
  running cumulative token tally this run, and estimated CNY so far.
- Print a clear `PHASE COMPLETE` or `PHASE FAILED` line per suite×condition
  block, and a final `RUN COMPLETE — 100%` line with the full summary at the
  very end.
- If AgentDojo's own CLI buffers or suppresses step-level output, wrap it
  (thin progress-reporting wrapper around its task loop) rather than accept a
  silent run — same requirement as v6 §4.

---

## 6. Results and transparency tracking

All raw run output, logs, and ledger entries go under
`experiments/results/agentdojo-v6b-undefended/`, mirroring v6's layout: one
subfolder per suite (`banking/`, `slack/`, `travel/`, `workspace/`), each
with the raw AgentDojo result file(s), the full `tee`'d terminal log, and a
token-usage line appended to a `token_usage.jsonl` ledger in that directory
(same schema as v6's ledger — see `experiments/results/agentdojo-v6/token_usage.jsonl`
for the exact fields: `timestamp_utc`, `phase`, `suite`, `model`,
`prompt_tokens`, `completion_tokens`, `total_tokens`,
`estimated_cny_cost_offpeak`, `utility_rate`, `security_rate`).

This document should be updated in place as the run progresses — mark it done
in §7 below with actual token usage vs. the 12M estimate, and disclose any
deviation from this plan per `pref.scientific_integrity`.

Before this run is considered complete, verify completeness the same way this
project has learned to (the hard way, repeatedly): **parse result keys, filter
to the actual task/condition grid, and count completed cells — never trust a
raw line count or a self-reported "100%" summary.** Confirm the undefended
workspace attack condition used the exact same 10-task subset as v6 (listed in
§2), not all 40, or the paired comparison is invalid.

Once complete, integrate into:
- `docs/experiments.md` — add an undefended-baseline column/row next to each
  existing Protocol v6 suite row (not a new separate section) so the
  defended-vs-undefended comparison is visually paired.
- `docs/paper/manuscript-draft.md` Results section — the AgentDojo subsection
  needs the undefended numbers added before this paper can state a utility
  *cost* or an ASR *reduction* figure (currently it can only state an absolute
  rate, which is a weaker and less reviewable claim).

---

## 7. Status (update this section as the run progresses)

- [ ] Clock checked, off-peak window confirmed before start.
- [ ] Banking: benign (16 tasks) + attack (144 pairs) — undefended.
- [ ] Slack: benign (21 tasks) + attack (105 pairs) — undefended.
- [ ] Travel: benign (20 tasks) + attack (140 pairs) — undefended.
- [ ] Workspace: benign (40 tasks) + attack (10-task subset, 140 pairs) — undefended.
- [ ] Token ledger reconciled against 12M cap.
- [ ] Completeness verified by cell-count, not line-count or self-report.
- [ ] `docs/experiments.md` updated with paired defended/undefended table.
- [ ] `docs/paper/manuscript-draft.md` Results section updated with utility-cost
  and ASR-reduction framing.
