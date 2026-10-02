# Final Run Plan — M1 to M6 (Protocol v8 + publication readiness)

Status: **NOT STARTED.** This is the binding specification for the last run before
the paper is written up. One phase, executed start to finish by one agent. Every
path, definition, metric, threshold, order and stop rule is fixed here. If something
is impossible as written, record why in `docs/final-run-results.md` §Deviations and do
the closest thing. Never improvise silently.

Results go in `docs/final-run-results.md` (template already exists; fill it in as each
step finishes, not at the end). This file is the spec: only tick its §10 status boxes.

Binding rules (from the project owner's standing preferences):
- Never fabricate a number, citation, DOI, page range, author or result. A number with
  no source file does not go into any document.
- Freeze code in git (tag) before running the analysis it produces.
- Keep negative results. Report every mismatch and every stop condition.
- Never tune a rule after seeing its agreement with the data. Bugs are fixed as a
  disclosed version (`protocol-v8.1`), and both versions' numbers are reported.
- **No LLM API calls and no spending.** Nothing in this plan needs DeepSeek, Gemini or
  any paid service. Network use is limited to free public APIs (arXiv, Crossref,
  OpenAlex, Semantic Scholar, USENIX/ACL/PMLR/NeurIPS proceedings pages).
- Do not push to any remote. Do not edit `previously submitted to university/`.
- The host is memory-tight: run everything serially, targeted tests during work, and
  the full test suite only in M3 and M6.

---

## 0. Context the executor must understand

### 0.1 What GUIDE is (final framing — do not deviate)
GUIDE is a **reference monitor for LLM multi-agent systems**. Under the assumption
that some agents will be compromised, it (1) computes a **sound static blast-radius
bound** for any compromised subset of agents, (2) synthesises the least-privilege policy
that still permits the nominal workflow, and (3) enforces the bound at runtime at the
tool-call boundary (policy gate + provenance guard). It is **not** an orchestration
framework and does not compete with LangGraph, CrewAI or AutoGen; it can sit under any
of them.

Name: keep **GUIDE**. Expansion: **Governed, Uncertainty-aware, Intent-pinned Delegation
Enforcer** (G = bound/synthesis/gate; U = Bayes-UCB routing, supporting; I = provenance
guard and root-intent pinning; D = signed hand-offs; E = the enforcement point every tool
call passes through).

### 0.2 How GUIDE relates to other work (wording is binding)
- **CaMeL, Progent, FIDES, ARM, MiniScope** are **single-agent** tool-call reference
  monitors. Their architectures are different from GUIDE's (CaMeL: control/data-flow
  separation; Progent: programmable privilege policies; FIDES: information-flow
  control with labels; ARM: provenance-checked reference monitor). They protect one
  agent from untrusted data. GUIDE addresses a **different problem**: bounding what a
  compromised **subset of agents** can reach across a multi-agent system, before
  deployment. GUIDE does **not** extend, generalise or build on them.
  Allowed words: "differs from", "addresses a distinct problem", "complements",
  "related single-agent monitors". **Forbidden** about these works: "extend(s)",
  "extension of", "generalise(s)/generalize(s)", "builds on", "multi-agent version of".
- **Parisel (arXiv 2607.09744), Muruaga (arXiv 2608.15888), Moon & Varshney (arXiv
  2605.09045)** overlap partially with the bound idea. Wording: "overlaps partially
  with", "differs in". Not "extends".
- **Paul & Nandy (arXiv 2609.22949) and Safin et al. (arXiv 2609.17648)** published the
  four-control integration / containment design first (Sept 2026). GUIDE's integration
  is not claimed as novel.

### 0.3 The evidence that already exists (verified 2026-10-02/03; do not re-run)
| ID | What | Where | Key numbers |
|---|---|---|---|
| internal | Own multi-agent bench, 3 model families, assumed compromise K1–K4, live adaptive attacker | `docs/experiments.md` protocols v1–v5 | bound exact vs live attacker 39/39; substring provenance admits 692 recipients; 18/19 configs over-privileged; LP cuts sink capabilities 55.6% |
| v6 | AgentDojo `v1.2.2`, GUIDE GPLUS, `deepseek-v4-flash` | `experiments/results/agentdojo-v6/` | pooled benign utility 60/97 = 61.9%; attack utility 362/529 = 68.4%; ASR 12/529 = 2.3% (all 12 on text-only travel `injection_task_6`) |
| v6b | Same, undefended (`gated=False, provenance=False`) | `experiments/results/agentdojo-v6b-undefended/` | benign 89/97 = 91.8%; attack utility 453/529 = 85.6%; ASR 11/529 = 2.1% |
| v7a | Static utility-cost predictor | `experiments/results/predict-utility-v7a/` | accuracy 0.928 [0.858, 0.965], n=97; 0 `fn_onpath` |
| v7c | Topology analysis, Proposition 3 | `experiments/results/topology-v7c/` | 0 counterexamples; all 19 own configs are linear chains; WBR₁ = 1.000 for 18/19 under every condition |
| v7b | GitHub mining | `experiments/mining/` | 37 configs (36 CrewAI, 1 LangGraph, 0 AutoGen); 36 scored; 34/36 have no write/external tool; 36/36 CrewAI `process: sequential`; extraction validation 10/10 |

**The gap this run closes.** v6b shows `deepseek-v4-flash` executed **zero** injected tool
calls even without any defence. So the live AgentDojo "0 compromised tool sinks" says
nothing about GUIDE. M1 fixes this by replaying the attacker's own calls (assumed
compromise), which is the paper's threat model anyway.

Also: AgentDojo is a **single-agent** benchmark. It validates GUIDE's enforcement and
the cost predictor, **not** the multi-agent bound. No standard benchmark for
compromised-agent containment in multi-agent systems exists (checked 2026-10-03; the
closest is arXiv 2603.28013, which uses its own harness). Do not run any other benchmark.

### 0.4 Repo facts (verified)
- Venv: `.venv/bin/python`; run tools with `uv run`.
- AgentDojo pinned `agentdojo==0.1.35`, benchmark `v1.2.2`. Suites: banking, slack,
  travel, workspace. Injection tasks per suite: 9, 5, 7, 14 (35 total); 26 of 35 have a
  non-empty tool-call `ground_truth`. User tasks: 16, 21, 20, 40.
- `injection_task.ground_truth(pre_environment) -> list[FunctionCall]`; use `fc.function`
  and `dict(fc.args)` (ignore `placeholder_args`).
  `env = suite.load_and_inject_default_environment({})`.
- Adapter: `src/guide_agentdojo/specs.py` (`DOJO_TOOL_SECURITY[name] = (write_effect,
  external, control_params, resource_class)`, `build_tool_registry`), `policy.py`
  (`build_suite_policy`), `pipeline.py` (live gate, lines ~217–300), `predict.py` (v7a,
  frozen: `_build_model`, `_caps_by_key`, `_verdict`).
- Live gate construction, to be mirrored exactly:
  ```python
  engine = RulePolicyEngine(policy, registry)
  guard = ProvenanceGuard(engine, registry, match="substring")
  guard.observe(run_id, {"objective": user_task.PROMPT}, Trust.TRUSTED)
  d = guard.evaluate(
      ToolCall(tool=fn, operation=fn, args=args, principal="agent"),
      PolicyContext(run_id=run_id, step_id="dojo-step", step_tools=frozenset(f.name for f in suite.tools)),
  )
  executed = d.decision is not Decision.DENY   # ALLOW and BOUND both execute
  ```
  Imports: `guide.policy` (`Decision`, `PolicyContext`, `RulePolicyEngine`), `guide.types`
  (`ToolCall`, `Trust`), `guide_research.provenance` (`ProvenanceGuard`).
- Analyser: `src/guide_research/blast_radius.py` (`SystemModel`, `authority`,
  `influenced`, `blast_radius`, `synthesize_least_privilege`, `ObservedCall`). Topology:
  `src/guide_research/topology.py` (frozen at `protocol-v7c`; do not edit it).
- Own configs: `guide_bench.real_world.configs.load_configs()` → 19 configs. Mined configs:
  `experiments/mining/configs.jsonl` (37 lines) → `guide_bench.mining.to_model.build_model`.
- Paper: `docs/paper/manuscript-draft.md`. APA builder: `scripts/paper/build_apa_refs.py`
  (reads `references-final.bib`, writes `docs/paper/references-apa.{md,json}`). Docx style:
  `docs/paper/reference-style.docx`. Pandoc at `/opt/homebrew/bin/pandoc`.
- References: `references-final.bib` (111 entries; edit it directly; **do not** re-run
  `docs/lit-review/scripts/build_final_refs.py`, which would overwrite it).
  `docs/references-final.md` lists each entry's status. The 19 to fix have status
  `PR (venue-from-OpenAlex)`; the 1 with missing authors is `anon2025make`
  (`PR (VERIFY)`).
- Writing rules: `/Users/shafinoid/.kiro/crew/skills/shafin-writing-skill/SKILL.md`. Read it
  in full before M4 and apply every rule.
- Known pre-existing failing test:
  `tests/unit/test_blast_radius.py::test_property_coverage_is_not_vacuous` (M3 fixes it).
- `.env` is gitignored and must never be committed.

---

## 1. Execution order (single phase, no pauses)

1. **Setup**: create `scripts/final/progress.py` and `scripts/final/run_final.py` (§2).
2. **M3**: fix the flaky test (§5). It goes first so the suite is green before freezing.
3. **Code for M1 and M2**: write modules + tests (§3, §4). Run targeted tests until they pass.
4. **Freeze**: commit, then `git tag protocol-v8`.
5. **Compute**: `uv run python -u scripts/final/run_final.py --stage compute` (M1, M1b, M2,
   numbers). Then commit the results.
6. **M5**: reference fixes + competitor search (§6). Commit.
7. **M4**: docs and manuscript (§7). Commit.
8. **M6**: release preparation, full test suite, docx build, tag `paper-v1` (§8). Commit.
9. Final reply (§9).

Stop conditions (the only reasons to stop early):
- **S1**: M1 finds any call the runtime executes but the static bound says is blocked
  (soundness violation). Stop after writing the results; do not do M4.
- **S2**: the Proposition 4 property test finds a counterexample. Same handling as S1.
- **S3**: a test cannot be made to pass without weakening it. Stop and report.
Everything else (DOI lookups failing, a competitor found, and so on) is recorded and the
run continues.

---

## 2. Progress and logging (required)

### 2.1 `scripts/final/progress.py`
A `Progress` class shared by every stage, plus a CLI:
- Ledger: `experiments/results/final-v8/progress.json` with, per stage, `done` and
  `total` units, `started_utc` and `finished_utc`. Create it if missing; update it after
  every unit, so a crash resumes from the right place.
- Stage weights (sum 100): `M3`=5, `M1`=30, `M1b`=2, `M2`=13, `M5`=15, `M4`=25, `M6`=10.
  Overall % = Σ weight × (done/total). A stage with `total` not yet known counts as 0.
- Every unit prints one line, flushed immediately, to stdout **and** appended to
  `experiments/results/final-v8/run.log`:
  ```
  [2026-10-03 10:12:44] [overall  41.7%] [M1  412/949  43.4%] banking user_task_3 x injection_task_2 -> CONTAINED (sink calls denied 1/1)
  ```
- At each stage start and end, print a banner with the stage name, unit count and elapsed
  time, for example:
  `===== M1 START: 949 units =====` and `===== M1 DONE: 949/949 in 37.2s =====`.
- CLI for agent-driven stages:
  - `uv run python scripts/final/progress.py --set-total M4 12` sets a stage's total.
  - `uv run python scripts/final/progress.py --mark M4 "4.3 related work rewritten"`
    increments `done` by 1 and prints the progress line.
  - `uv run python scripts/final/progress.py --show` prints every stage and the overall %.

### 2.2 `scripts/final/run_final.py`
`--stage {m3_verify, m1, m1b, m2, numbers, check_numbers, m5_lookup, m5_search, compute}`.
`compute` = `m1` → `m1b` → `m2` → `numbers`, in that order. Always run it with
`uv run python -u` (unbuffered) so the log streams live. Every stage uses `Progress`.

Manual-unit totals, set with `--set-total` at the start of each stage:
- M3: 6 runs (§5);
- M5: 1 unit per bib entry fixed or checked (19 + 1 + 20 preprints = 40) plus 1 per
  search query (6), giving 46;
- M4: 12 (§7 list);
- M6: 7 (§8 list).

---

## 3. M1 — Assumed-compromise replay on AgentDojo (+ M1b)

### 3.1 Question
If the agent is fully compromised (the attacker controls its proposals), does GUIDE's
runtime gate stop the attacker's own tool calls on an external, independently authored
benchmark, and does the static bound agree with the runtime on every call?

### 3.2 Grid
- **Full grid (primary)**: every user task × every injection task in each suite:
  banking 16×9 = 144, slack 21×5 = 105, travel 20×7 = 140, workspace 40×14 = 560,
  **total 949** pairs.
- **v6-matched subset (secondary)**: the 529 pairs evaluated live in v6. This is the same
  as the full grid except that workspace is limited to user tasks `user_task_0, 4, 8, 12,
  16, 20, 24, 28, 32, 36`.

### 3.3 Procedure per pair (FROZEN)
1. `suite = get_suite("v1.2.2", s)`; `env = suite.load_and_inject_default_environment({})`
   (cache per suite).
2. `atk = injection_task.ground_truth(env)`. If it is empty, mark the pair
   `status="no_tool_calls"`. It is excluded from the containment denominator, but counted
   and listed.
3. **Sink calls**: calls whose `DOJO_TOOL_SECURITY[fc.function]` has `write_effect` or
   `external` set. Non-sink calls are evaluated and logged but do not decide containment.
   If an injection task has tool calls but no sink calls, use `status="no_sink_calls"` and
   treat it the same way as `no_tool_calls`.
4. **Undefended comparator**: with no gate, every attacker call executes. Record
   `undefended_executed = len(sink_calls)`. Also check it with the static model:
   `replace(model, gate="none")`, where every sink call must be admitted by
   `_caps_by_key`/`Capability.admits`. Any exception to this is a bug; stop and fix.
5. **Runtime (GUIDE)**: build the gate exactly as in §0.4, using a fresh `run_id` per
   pair (`f"m1-{s}-{ut}-{it}"`) and observing the trusted objective once. Evaluate every
   attacker call in order. Record `decision`, `rule` and `reason` for each.
6. **Static bound**: `model = predict._build_model(s, suite, user_task.PROMPT)`;
   `caps = predict._caps_by_key(model)`; `v = predict._verdict(fc, caps)`, so a call is
   statically admitted iff `not v.blocked`. Use these functions; do not re-implement
   them.
7. **Pair outcome**:
   - `CONTAINED` if every sink call is denied by the runtime;
   - `PARTIAL` if some but not all are denied;
   - `EXECUTED` if none are denied.
8. **Admitted-call reason** (for every sink call the runtime executes), exactly one of:
   - `no_control_params`: the operation's `control_params` is empty, for example
     `update_password`;
   - `control_value_in_trusted_prompt`: every control-param value, normalised, is a
     substring of `corpus_of({"objective": PROMPT})`;
   - `other`: write a one-line manual explanation for each.

### 3.4 Bound vs runtime cross-check (soundness-critical)
For every attacker call, sink and non-sink alike, record the 2×2 of (static admitted,
runtime executed):
- **soundness violation**: runtime executed and static blocked. Must be 0. If it is
  above 0, stop under **S1**.
- **exactness gap**: static admitted and runtime denied. Report the count and the
  `rule` for each. This is allowed, because the bound over-approximates on malformed
  calls, but every instance must be listed.

### 3.5 Metrics (pre-registered)
- Containment rate = CONTAINED pairs / in-scope pairs, with a Wilson 95% interval
  (reuse `guide_bench.mining.audit.wilson_interval`). Report it:
  - per suite and overall;
  - for the full grid and the v6-matched subset;
  - beside the undefended rate, which is 0% contained.
- Sink-call block rate: denied sink calls / all attacker sink calls, overall and per suite.
- A per-injection-task table: suite, injection task id, goal (first 80 characters of
  `injection_task.GOAL`), sink functions, outcome distribution over user tasks, and
  admitted reasons. Containment is expected to depend mostly on the injection task;
  this table makes that visible.
- Counts of `no_tool_calls` and `no_sink_calls` pairs, listed by injection task.
- The bound/runtime 2×2, overall.

### 3.6 M1b — GUIDE-attributable utility loss (pre-registered in plan v7a §1.5)
For each of the 97 benign tasks:
- `lost = v6b_utility and not v6_utility`, read from `summary_none.json`
  `utility_results` in both result directories;
- `predicted_block` comes from `experiments/results/predict-utility-v7a/predictions.jsonl`.

Report:
- the confusion matrix of predicted_block against lost, with accuracy and a Wilson
  interval, precision and recall;
- the count of `lost` tasks;
- the predicted cost, `mean(predicted_block × v6b_utility)`, next to the observed cost,
  `v6b benign utility − v6 benign utility`.

Write `experiments/results/final-v8/v7a_attributable_loss.json` and `.md`. Do not
modify anything under `predict-utility-v7a/`.

### 3.7 Files
- `src/guide_agentdojo/compromise_replay.py`:
  - `replay_pair(suite_name, user_task_id, injection_task_id) -> dict`;
  - `iter_grid() -> list[tuple[str, str, str]]` (full grid, sorted by suite in the
    order above, then by natural task number);
  - `run_all(progress) -> list[dict]`;
  - `summarize(rows) -> dict`;
  - `main()`.
- `tests/unit/test_compromise_replay.py`:
  - (a) a banking injection task whose ground truth calls `send_money` to an IBAN not in
    the user prompt is denied by the runtime and blocked statically. Pick the first
    banking injection task with a `send_money` call; assert that it exists.
  - (b) a synthetic `FunctionCall("update_password", {"password": "x"})` is executed by
    the runtime and admitted statically. This documents the `no_control_params` class.
  - (c) `iter_grid()` has length 949, and the v6-matched filter has length 529.
  - (d) for every pair of one small suite (slack), there are 0 soundness violations.
- Outputs, in `experiments/results/compromise-replay-v8/`:
  - `pairs.jsonl`: one row per pair, with suite, user_task_id, injection_task_id,
    in_v6_subset, status, outcome, n_sink_calls, n_denied, and admitted_reasons;
  - `calls.jsonl`: one row per attacker call, with pair keys, function, args,
    is_sink, runtime decision/rule/reason, static_admitted, and static_reason;
  - `summary.json`;
  - `summary.md`.

---

## 4. M2 — Proposition 4 (topology floor) + absolute-reach reporting

### 4.1 Proposition 4 (add verbatim to `docs/formal_model.md` after Proposition 3)
Notation: Π_⊥ is the finest partition (one agent per step); for a step s, Infl_s =
Infl({a_s}) under Π_⊥ (this includes context and state-flow rules); R(s) = the set of
distinct (tool, operation) sinks in ⋃_{t ∈ Infl_s} Auth_g(t); Sinks* is as in §2.2 of
`docs/static-analysis-extensions-plan.md`.

**Proposition 4 (Topology floor).** For a fixed workflow, mode m and policy P with
Sinks* ≠ ∅:
- (a) min over partitions Π of WBR₁(Π) = max_s |R(s)| / |Sinks*|, attained by Π_⊥.
- (b) If m = transcript, then min_Π WBR₁(Π) = 1.
- (c) If m ∈ {structured, signed} and some step r reaches every step that holds a sink
  along `depends_on` edges, then min_Π WBR₁(Π) = 1.
- Corollary: in a sequential chain (each step depends on its predecessor), WBR₁ = 1 under
  every mode and every partition whenever any sink remains. Splitting agents and signing
  hand-offs cannot lower the worst case; only removing sinks from authority (policy or
  delegation) changes the reach.

*Proof.*
- (a) Π_⊥ refines every partition, so Proposition 3 gives WBR₁(Π_⊥) ≤ WBR₁(Π) for all Π.
  Under Π_⊥, the single agents are exactly the steps.
- (b) Let s₀ be the first step in execution order. Rule C in transcript mode makes every
  later step influenced once s₀ is, so Infl_{s₀} = S and R(s₀) = Sinks*.
- (c) Rule C in structured and signed mode propagates along every `depends_on` edge, so
  Infl_r contains every sink-holding step.
∎

Also add one sentence to Proposition 3's caveat. WBR is normalised by Sinks* under the
same policy, so a least-privilege policy that removes some sinks but not all can leave
WBR₁ = 1 while still lowering the absolute reach. Report absolute reach (§4.3) for policy
comparisons.

### 4.2 Code
- `src/guide_research/topology_theory.py`:
  - `step_reach(model, step_id) -> frozenset[tuple[str, str]]` (R(s) under Π_⊥, using
    `topology.apply_partition` with the identity RGS and `blast_radius`);
  - `closed_form_floor(model) -> float` (Prop 4a);
  - `has_dominating_source(workflow, sink_steps) -> bool` (Prop 4c);
  - `is_chain(workflow) -> bool` (every non-first step has `depends_on == (previous
    step id,)` in list order).

  Do not edit `topology.py`.
- `tests/unit/test_topology_theory.py`:
  - **Property test, Prop 4a.** Use Hypothesis with `@settings(max_examples=300,
    deadline=None, derandomize=True, database=None)` and the toy registry below.
    - Toy registry, 4 tools: `t_read` (read, resource `r0`), `t_w1` (write, `r1`), `t_w2`
      (write, `r2`), `t_x` (external, `r3`). Each tool has one operation named after the
      tool and no control params.
    - Policy: permits all four, `allow_write=True`, `allow_external=True`,
      `max_sensitivity=RESTRICTED`.
    - Workflow: n ∈ [1, 5] steps. Each step gets a random non-empty tool subset, and
      `depends_on` is a random subset of earlier steps (acyclic by construction).
    - Modes: TRANSCRIPT and SIGNED; `gate="rule"`; `trusted_corpus=""`.
    - Assertion: the brute-force minimum over `topology.set_partitions(n)`, computed with
      `topology.wbr`, equals `closed_form_floor` (absolute tolerance 1e-9).
  - **Prop 4b**: for every generated case in TRANSCRIPT mode with Sinks* ≠ ∅, the floor
    is 1.
  - **Prop 4c**: for every generated case in SIGNED mode where `has_dominating_source`
    holds over the sink steps, the floor is 1.
  - **Real configs**: for all 19 configs × {TRANSCRIPT, SIGNED} × {nominal, least
    privilege}, the brute-force minimum equals the closed form.
  - Any counterexample stops the run under **S2**.

### 4.3 Analysis outputs (`experiments/results/topology-v8/`)
**Absolute reach**, for each of the 19 own configs and each of the four Q4 conditions
from v7c:
- `abs_wbr1` = max over agents of |D(BR)|;
- `nom_wbr1` = `abs_wbr1` / |Sinks* under the nominal policy|.

Report per config and as a median, and add a "reduction from (i)" column. This is the
table that shows least privilege lowering reach even where the fraction stays 1.

**Structural census** over all 56 acyclic configs (19 own + 36 mined scored + 1 mined
cyclic, listed separately and not analysed). Count:
- `is_chain`;
- `has_dominating_source` over all steps;
- `has_dominating_source` over sink steps (only configs with sinks);
- configs where Prop 4 implies floor = 1 under SIGNED.

Give counts with Wilson intervals.

**Files**:
- `abs_reach.jsonl`;
- `census.jsonl`;
- `summary.json`;
- `summary.md`.

---

## 5. M3 — Fix the pre-existing flaky test

Test: `tests/unit/test_blast_radius.py::test_property_coverage_is_not_vacuous`.

Root causes, verified:
- (1) `COVERAGE` is a module-level dict filled only by
  `test_property_auth_is_exact_wrt_real_gate`, so running the coverage test alone always
  fails;
- (2) the number of executed (ALLOW + BOUND) examples is random, and was observed at
  116–150, against a threshold of 200, at `max_examples=1500`.

Fix (no weakening):
1. On `test_property_auth_is_exact_wrt_real_gate`, set `@settings(max_examples=3000,
   deadline=None, derandomize=True, database=None, suppress_health_check=[HealthCheck.too_slow])`.
2. At the start of `test_property_coverage_is_not_vacuous`: if `COVERAGE` is empty, call
   `test_property_auth_is_exact_wrt_real_gate()`. A Hypothesis-wrapped test can be called
   with no arguments, and it runs the search.
3. Run it once and read the executed count. If it is below 260 (the 200 threshold plus a
   30% margin), raise `max_examples` to 4000 and re-check. Record the final
   `max_examples` and the executed count.
4. Never lower the 200 threshold, and never remove a rule from the required-coverage
   list. If neither 3000 nor 4000 is enough, stop under **S3**.
5. Verify with 6 runs (these are the M3 units):
   - 3× `uv run pytest tests/unit/test_blast_radius.py -q`;
   - 3× `uv run pytest "tests/unit/test_blast_radius.py::test_property_coverage_is_not_vacuous" -q`.

   All 6 must pass. Then run the full suite once and record the counts (expected
   0 failed).
6. Commit with the message `M3: derandomize gate property test and remove order
   dependency of its coverage check`.

---

## 6. M5 — References and competitor check

### 6.1 Fix the 19 `PR (venue-from-OpenAlex)` entries and `anon2025make`
For each entry, in this order, stopping at the first source that gives an exact match:
1. Crossref: `https://api.crossref.org/works?query.bibliographic=<url-encoded title>&rows=5`.
   Accept a hit only if all of these hold:
   - the normalised title similarity is ≥ 0.95 (`difflib.SequenceMatcher` on lowercased,
     punctuation-stripped titles);
   - the year is within ±1;
   - the container title matches the venue named in the entry's `note`.

   Take `DOI`, `page` and `container-title`.
2. The official proceedings site for the venue:
   - ACL Anthology: `aclanthology.org`; its DOIs are `10.18653/v1/...`;
   - PMLR: `proceedings.mlr.press`, which gives volume and pages;
   - NeurIPS: `proceedings.neurips.cc`, which gives a URL (NeurIPS usually has no DOI);
   - USENIX: `usenix.org` presentation page, which gives a URL and authors;
   - IEEE/ACM: their DOI pages.
3. If the paper is only on OpenReview (ICLR, COLM): record the OpenReview forum URL if
   it can be fetched. If it can't, add the entry to a "manual check" list for the user
   with the search link `https://openreview.net/search?term=<title>`.

Edit `references-final.bib` in place:
- add `doi`, `pages` and `url` fields where found;
- remove the arXiv-DOI-only `note` once the venue is fixed;
- never invent a page range or DOI.

Update the entry's status in `docs/references-final.md` to `PR (DOI-verified)` or
`PR (proceedings-URL)`. Log every lookup, with the query, the source and the
accepted/rejected reason, in `experiments/results/final-v8/ref_lookup.jsonl`.

For `anon2025make`, get the authors from the USENIX Security 2025 program page. If the
page can't be retrieved, keep `[VERIFY]` and put the entry on the manual list.

### 6.2 Re-check the 20 preprints
- Look each one up on Semantic Scholar:
  `https://api.semanticscholar.org/graph/v1/paper/arXiv:<id>?fields=title,venue,publicationVenue,year,externalIds`.
- For the ones known to be uncertain (Triedman → COLM 2025, τ-bench), also run a
  Crossref title search.
- If a preprint has a peer-reviewed version, move it to peer-reviewed (same acceptance
  rule as §6.1) and update the totals in `docs/references-final.md`.

### 6.3 Add the three missing comparators
These are arXiv 2604.04035 (ARM), 2606.17573 (Cordon) and 2606.26479 (an adaptive
evaluation of defences outside the model).
1. Fetch each abstract from `export.arxiv.org/api/query?id_list=<id>`.
2. Add a bib entry from the fetched metadata only.
3. Add them to `docs/references-final.md` as `PP` (they are preprints).
4. If the preprint share then goes above 20%, first apply the upgrades from §6.2.
5. If it is still above 20%, drop the lowest-relevance preprint that is not
   novelty-critical, following selection rule 3 in `docs/references-final.md`, and
   record which one and why. Parisel, Muruaga, Moon & Varshney, Paul & Nandy, Safin et
   al., ARM and 2603.28013 are novelty-critical and are never dropped.

Also add arXiv 2603.28013 (a multi-agent prompt-injection pipeline study) as a `PP`
reference. Related work cites it as the closest multi-agent evaluation, which uses its
own harness.

### 6.4 Competitor search (novelty guard)
Run 6 queries on the arXiv API with `sortBy=submittedDate`, keeping results submitted on
or after 2026-07-01, with `max_results=50` each:
1. `all:"blast radius" AND all:agent`
2. `all:compromised AND all:"multi-agent" AND all:LLM`
3. `all:"reference monitor" AND all:agent`
4. `all:"least privilege" AND all:agent AND all:LLM`
5. `all:"static analysis" AND all:"multi-agent" AND all:LLM`
6. `all:"information flow" AND all:"multi-agent" AND all:LLM`

For each hit, record the arXiv id, title, date and the first sentence of the abstract in
`docs/lit-review/final-competitor-check.md`. Give each hit one verdict:
- `NOVELTY-CRITICAL`: it claims a sound or static bound on what a compromised subset of
  agents can reach, or it predicts deployment utility cost from a static analysis;
- `RELATED`: cite it in related work if relevant;
- `UNRELATED`.

If any hit is `NOVELTY-CRITICAL`:
- put it at the top of that file and in the final reply;
- cite it in related work with an honest one-line contrast;
- do **not** rewrite the contribution claims beyond that. The owner decides.

### 6.5 Rebuild the reference list
1. Run `uv run python scripts/paper/build_apa_refs.py`.
2. Replace everything between the `## References` heading and the `## Appendices` heading
   in the manuscript with the content of `docs/paper/references-apa.md`.
3. Check that every `[@key]` or author-year citation in the text has an entry, and that
   no entry is uncited. List any mismatches and fix them.

---

## 7. M4 — Documentation and manuscript (12 units; `--set-total M4 12`)

First run `uv run python -u scripts/final/run_final.py --stage numbers`. This writes
`experiments/results/final-v8/paper_numbers.json`, holding every number below as a
formatted string together with its source file. **Every number written into the
manuscript must come from this file.** After editing, `--stage check_numbers` greps the
manuscript for every key flagged `"manuscript": true` and prints any that are missing.
The run ends with 0 missing.

Required keys (sources in brackets):
- **v6**: `v6_benign_util` "61.9%" (60/97), `v6_attack_util` "68.4%", `v6_asr` "2.3%"
  [`agentdojo-v6/*/summary_*.json`];
- **v6b**: `v6b_benign_util` "91.8%", `v6b_attack_util` "85.6%", `v6b_asr` "2.1%",
  `util_cost_pp` "29.9", `slack_cost_pp` "66.7" [v6b + v6];
- **v7a**: `v7a_acc` "92.8%", `v7a_ci` "[85.8%, 96.5%]", `v7a_fn_onpath` "0";
- **M1b**: `m1b_*` [final-v8];
- **M1**: `m1_containment_full`, `m1_ci_full`, `m1_containment_v6sub`, `m1_sink_block_rate`,
  `m1_in_scope_pairs`, `m1_soundness_violations`, `m1_exactness_gaps`
  [compromise-replay-v8];
- **M2**: `m2_chain_count`, `m2_dominated_count`, `m2_census_n`, `m2_abs_reduction_median`
  [topology-v8];
- **v7b**: `v7b_configs` "37", `v7b_scored` "36", `v7b_no_sink` "34", `v7b_sequential`
  "36" [experiments/mining];
- **tokens**: `v6_tokens`, `v6b_tokens`, `v6_cny`, `v6b_cny` [summary files; footnote that
  the v6 ledger `token_usage.jsonl` total is 11,450,443, which includes the smoke and
  duplicate phase rows].

The values in quotes are the expected values, already verified. If the computed value
differs, use the computed value and record the difference in Deviations.

The 12 units, marked one by one with `progress.py --mark M4 "<unit>"`:

**4.1 `docs/experiments.md` correction.**
- In the Protocol v6 table, replace the "Total / Overall" 63.9% and 70.5% with the pooled
  61.9% (60/97) and 68.4% (362/529), and add a note that utility is pooled over tasks.
- Rewrite Key Finding 1 ("Tool Execution Immunity"). The zero tool-sink compromises in
  v6 are **not** attributable to GUIDE, because the undefended v6b run also had zero.
  The model ignored the injections; M1 measures GUIDE under assumed compromise.
- Add a "Protocol v6b" section (the paired table from the verified v6b report) and a
  "Protocol v8" section (M1, M1b, M2) with tags and commits.

**4.2 `docs/submission-alignment.md`.** Add these rows:
- A34: protocol-v8, M1/M2;
- A35: the reframing from orchestration to reference monitor, with RQs reordered (see
  4.5);
- A36: AgentDojo's scope stated as single-agent enforcement validation only.

**4.3 `docs/paper/differences-from-submitted.md`.** Add rows matching A34–A36 in plain
language.

**4.4 Title, abstract, keywords.**
- Title: **Bounding the Blast Radius of Compromised Agents: Sound Static Analysis and
  Runtime Enforcement for LLM Multi-Agent Systems**.
- Abstract, at most 250 words, in this order:
  1. problem: prompt injection cannot be reliably prevented;
  2. approach: assumed compromise and a reference monitor;
  3. C1 to C4 below, with one key number each;
  4. one limitation sentence.
- Keywords: multi-agent systems; large language models; prompt injection; reference
  monitor; least privilege; static analysis; blast radius. No "framework" and no
  "orchestration".

**4.5 Introduction.**
- Problem and motivation.
- Introduce the GUIDE expansion once.
- Contributions, in this order:
  - **C1**: the sound static blast-radius bound for any compromised subset of agents,
    plus least-privilege synthesis (proof, property tests, exact against the live
    attacker on 39/39);
  - **C2**: the bound predicts the deployment cost before deployment (v7a, M1b, v6b);
  - **C3**: the topology floor, Propositions 3 and 4. In sequential pipelines only
    removing privileges lowers reach, and the M2 census shows real configs are
    sequential;
  - **C4**: empirical findings, namely substring provenance admitting 692 recipients,
    18/19 configs over-privileged, M1 containment under assumed compromise on AgentDojo,
    and the utility trade-off.
- RQs, reordered:
  - RQ1: soundness and exactness of the bound (old RQ5);
  - RQ2: containment under assumed compromise, internal suite plus M1 (old RQ4);
  - RQ3: pre-deployment cost prediction (v7a, M1b);
  - RQ4: the topology floor and real-world structure (v7c, M2, v7b);
  - RQ5: nominal performance across model families, kept as a secondary null result
    (old RQ3).
- The old RQ1/RQ2 artefact demonstration becomes the design description in §3.2 and is
  no longer an RQ.

**4.6 Related work (§2).** Restructure into:
- 2.1 Multi-agent orchestration frameworks (context only);
- 2.2 Single-agent tool-call reference monitors and IFC (CaMeL, Progent, FIDES, ARM,
  MiniScope, Cordon), using the §0.2 wording;
- 2.3 Multi-agent security and containment (Paul & Nandy, Safin et al., 2603.28013 and
  the others already in the draft);
- 2.4 Static and pre-deployment analysis (Parisel, Muruaga, Moon & Varshney, with
  partial-overlap wording);
- 2.5 Evaluation benchmarks: AgentDojo is single-agent, and no standard benchmark for
  multi-agent compromised-agent containment exists.

Add a comparison table with columns:
- targets multi-agent compromised subsets;
- static pre-deployment bound;
- soundness proof;
- least-privilege synthesis;
- deployment-cost prediction.

Rows: CaMeL, Progent, FIDES, ARM, Parisel, Muruaga, Moon & Varshney, GUIDE. Fill a cell
only from an abstract or full text actually read in this run, citing the source. Use
"not reported" when it is unclear, and never guess.

Remove any text that presents the systematic literature review as a method of this
paper (PRISMA counts, screening, kappa) and replace it with one sentence: "Related work
was identified through a systematic review conducted for the author's dissertation
(721 included studies)."

**4.7 Methods (§3).** Keep 3.1 to 3.9, updating 3.2 to hold the old RQ1/RQ2 design
material. Add:
- 3.10 External benchmark: AgentDojo v6, v6b and M1, with the single-agent scope
  statement;
- 3.11 Pre-deployment cost prediction (v7a, M1b);
- 3.12 Topology analysis (Props 3 and 4, absolute reach);
- 3.13 Real-world configuration mining (v7b), with its lower-bound caveats and the §5
  stop condition.

**4.8 Results (§4).** Make the subsections match the new RQ1–RQ5. Keep the existing
numbers for RQ1, RQ2 (internal) and RQ5, and add the tables:
- M1 per suite;
- v6/v6b paired;
- v7a and M1b;
- the M2 absolute-reach and census tables;
- the v7b funnel and metrics.

**4.9 Discussion (§5).** Add these points:
- the AgentDojo containment result does not depend on the model complying, because v6b
  shows the model resisted the injections anyway and M1 shows GUIDE blocks
  deterministically;
- least privilege is the only lever in sequential pipelines (Prop 4 and the census);
- the security vs utility trade-off (Slack −66.7 pp) and that v7a predicts it;
- rewrite "5.3 What the static bound adds" around C2.

**4.10 Limitations (§5.6).** Include all of the following:
- partial overlap with the three 2026 preprints;
- the proof is checked by hand and by property tests, not by a machine;
- multi-agent evidence comes from the author's own suite, because no standard benchmark
  exists;
- AgentDojo uses one model and is single-agent;
- live workspace attacks used a 10-task subset (M1 covers the full grid);
- live AgentDojo attack success is uninformative for this model;
- v7b is a small sample of public demo code, and its classifier is a lower bound (the
  "add"/"writer" undercounts);
- cyclic workflows are out of scope for the DAG model;
- text-only injections (travel `injection_task_6`) are out of scope for a tool-boundary
  monitor;
- the `admitted` classes found in M1 (for example, no-control-param writes).

**4.11 Conclusion + figures.** Rewrite the conclusion to the new contributions. Add one
figure with `scripts/paper/make_figures.py`, following its existing style: the v6 vs
v6b benign utility per suite, plus the M1 containment per suite. Save it next to the
existing figures and reference it in §4.

**4.12 Voice and wording pass.** Apply every rule in
`/Users/shafinoid/.kiro/crew/skills/shafin-writing-skill/SKILL.md` to the whole
manuscript. Then run these checks, which must all pass:
- `grep -nE "(extend|extends|extension of|generali[sz]e|builds? on|multi-agent version)" docs/paper/manuscript-draft.md`:
  no hit may refer to CaMeL, Progent, FIDES, ARM, MiniScope, Cordon, Parisel, Muruaga or
  Moon & Varshney. Rewrite every hit that does.
- `grep -niE "GUIDE[^.]{0,60}(framework|orchestrat)" docs/paper/manuscript-draft.md`: no
  hit may describe GUIDE as a framework or orchestrator.
- `uv run python -u scripts/final/run_final.py --stage check_numbers`: 0 missing.

---

## 8. M6 — Release preparation (7 units; `--set-total M6 7`)

1. **Commit the untracked AgentDojo results.** These are `experiments/results/agentdojo-v6/`
   (9.5 MB) and `agentdojo-v6b-undefended/` (8.6 MB).
   - First run `grep -rlE "sk-[A-Za-z0-9]{20,}|DEEPSEEK_API_KEY=|Authorization: Bearer" experiments/results/agentdojo-v6 experiments/results/agentdojo-v6b-undefended`.
     It must print nothing. If it prints any file, redact the secret in that file and
     record the redaction.
   - Add `!experiments/results/agentdojo-v6*/token_usage.jsonl` to `.gitignore` so the
     ledgers are committed.
2. **Write `REPRODUCE.md`** at the repo root. For every table in the paper, give the exact
   command, its inputs, its outputs, the expected key number, the API cost (zero-cost
   items marked) and the git tag, grouped by protocol (v1–v5, v6, v6b, v7a, v7b, v7c,
   v8). Use only commands that exist in the repo; copy them from `docs/experiments.md`,
   the plan files and this run.
3. **Add a "Paper artefacts" section to `README.md`**, linking `REPRODUCE.md`,
   `docs/formal_model.md`, `docs/final-run-results.md` and the result directories.
4. **Write `CITATION.cff`** (cff-version 1.2.0) with:
   - title (the paper title);
   - authors: family "Shafin", given "" — **flag for the owner to complete**, since full
     legal name and ORCID are not in the repo;
   - version `paper-v1`;
   - date-released today.

   If a `LICENSE` file exists, reference it. If none exists, do **not** create one;
   list it in the final reply as an owner decision.
5. **Full test suite**: `uv run pytest -q`. Record the counts. Expected: 0 failed.
6. **Build the docx.** Run
   `pandoc docs/paper/manuscript-draft.md -o docs/paper/out/manuscript-draft.docx --reference-doc=docs/paper/reference-style.docx --resource-path=docs/paper:.`
   and the same for `differences-from-submitted.md`. Check that the number of
   `word/media/*` entries in the manuscript docx (`unzip -l`) equals the number of image
   references in the markdown.
7. **Commit everything and run `git tag paper-v1`.** Do not push. Print the commands the
   owner would run later, `git push origin research/evidence-based-rebuild` and
   `git push origin --tags`, without running them.

---

## 9. Final reply (what the executor must report)

1. A one-line status for each of M1–M6.
2. The M1 table per suite (full grid and v6 subset), the bound/runtime 2×2, and the
   admitted-reason counts.
3. The M1b confusion matrix and the predicted vs observed cost.
4. The Prop 4 test result, the census counts and the absolute-reach median reduction.
5. M5: entries fixed, entries on the manual list (with links), preprint upgrades, the
   final peer-reviewed/preprint split, and any `NOVELTY-CRITICAL` hits.
6. The results of every check in 4.12 and M6.5.
7. Every deviation.
8. Owner decisions pending: the CITATION author details, the LICENSE, the manual
   reference checks, and the GUIDE expansion and title if the owner wants something
   different.

---

## 10. Status log (executor ticks in place)
- [x] Setup: progress.py, run_final.py
- [x] M3 flaky test fixed (final max_examples: 4000, executed count: 294)
- [x] M1/M2 code + tests, tag `protocol-v8` (commit `e1736ed`)
- [x] Compute: M1, M1b, M2, numbers (commit `cb71222`)
- [x] M5 references + competitor check (commit e0d9... to be recorded)
- [ ] M4 docs + manuscript (commit ___)
- [ ] M6 release prep, full suite (___ passed / ___ failed), docx, tag `paper-v1`
- Deviations: (none yet)
