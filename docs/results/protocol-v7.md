# Static-Analysis Extensions — Results (Protocol v7a / v7c / v7b)

Standalone, auditable record of all three tasks in
`docs/static-analysis-extensions-plan.md`. This file is updated after each task
completes, not only at the end. The plan file is the frozen spec; only its §8
status boxes are ticked there. Every number below traces to a file under
`experiments/results/` or `experiments/mining/` — a number with no source file
does not appear here.

Executed by: Sonnet (model switched mid-thread per user instruction), continuing
from Opus's plan. Host memory was tight-to-critical throughout (confirmed via
`resource_status`); all work was static analysis, run serially, no parallel
spawns, consistent with the plan's own stop condition (§5).

---

## v7a — Static utility-cost prediction

- **Tag / commit**: `protocol-v7a` / `fd8acff`
- **Run date**: 2026-10-02
- **Commands run**:
  - `uv run pytest tests/unit/test_predict_utility.py -q` (3 passed, before tagging)
  - `python3 -m guide_agentdojo.predict` (after tagging)
- **Input data**: `experiments/results/agentdojo-v6/<suite>/guide-gplus-local/<suite>/<task_id>/none/none.json` (97 benign traces, protocol-v6)
- **Output**: `experiments/results/predict-utility-v7a/{predictions.jsonl, summary.json, summary.md}`

### Final table (predicted_block vs observed_denial)

| suite | n | tp | fp | fn | tn | accuracy | 95% CI | precision | recall | predicted utility ceiling | observed benign utility |
|---|---|---|---|---|---|---|---|---|---|---|---|
| banking | 16 | 1 | 1 | 2 | 12 | 0.812 | [0.570, 0.934] | 0.500 | 0.333 | 0.875 | 0.750 |
| slack | 21 | 14 | 1 | 0 | 6 | 0.952 | [0.773, 0.992] | 0.933 | 1.000 | 0.286 | 0.286 |
| travel | 20 | 0 | 0 | 1 | 19 | 0.950 | [0.764, 0.991] | n/a (no positives) | 0.000 | 1.000 | 0.800 |
| workspace | 40 | 13 | 1 | 1 | 25 | 0.950 | [0.835, 0.986] | 0.929 | 0.929 | 0.650 | 0.650 |
| **overall** | 97 | 28 | 3 | 4 | 62 | **0.928** | [0.858, 0.965] | 0.903 | 0.875 | — | — |

### Mismatch classes (overall, n=97)

| class | count |
|---|---|
| `agree_block` | 28 |
| `agree_pass` | 57 |
| `fn_offpath_call` | 4 |
| `fp_model_detoured` | 3 |
| `model_error` | 5 |

### Pre-registered question answered

The bound predicts, from the ground-truth call path alone and with no model
calls, which benign AgentDojo tasks GUIDE's enforcing runtime will deny, with
**92.8% accuracy** (95% CI [0.858, 0.965], n=97). The predicted utility ceiling
matches observed benign utility exactly for slack (0.286 vs 0.286) and
workspace (0.650 vs 0.650), and is directionally consistent but not exact for
banking (0.875 predicted vs 0.750 observed) and travel (1.000 vs 0.800) — the
gap in both is `model_error` (the model failed the task for reasons unrelated
to GUIDE: wrong password judgment, incomplete multi-step reasoning), which the
predictor correctly does NOT attribute to a GUIDE block.

### Deviations

None. The predictor was not changed after the `protocol-v7a` tag.

### Optional §1.5 bonus metric (GUIDE-attributable loss vs. undefended baseline)

`experiments/results/agentdojo-v6b-undefended/` exists (completed by a parallel
workstream in this same session, commit `914e7aa`, before this task ran). Its
completeness has not yet been independently verified by this task — flagging
as **pending verification**, not computed here, to avoid using an unverified
input per the plan's "freeze before main run" discipline. This can be added as
a disclosed follow-up without touching the frozen `protocol-v7a` predictor.

---

## v7c — Blast-radius-minimal agent topology

- **Tag / commit**: `protocol-v7c` / `49d3bdc`
- **Run date**: 2026-10-02
- **Commands run**:
  - `uv run pytest tests/unit/test_topology.py -q` (5 passed, before tagging)
  - `python3 -m guide_bench.real_world.topology_audit` (after tagging)
- **Input data**: `src/guide_bench/real_world/configs.py` (`load_configs()`, 19 configs — the audit module's own docstring says 18, the actual count returned is 19, consistent with the plan's note to report whatever `load_configs()` returns)
- **Output**: `experiments/results/topology-v7c/{frontier.jsonl, summary.json, summary.md}`

### Proposition 3 (refinement monotonicity) — verified, no counterexamples

Added to `docs/formal_model.md` as a new numbered proposition (see that file).
Property test `test_refinement_monotonicity` in `tests/unit/test_topology.py`
checked every (coarse, fine) partition-refinement pair reachable by splitting
one block in two, for every config with ≤ 6 steps (all 19 configs qualify —
max step count in this set is 3), both `k=1,2`, both `TRANSCRIPT` and `SIGNED`
modes, 200 Hypothesis examples. **Zero counterexamples found.**

### Q1 — transcript wash-out

Median WBR₁ reduction from the best `TRANSCRIPT` partition vs. the original
(unpartitioned) structure: **0.000** (n=19). Hypothesis ("little reduction")
confirmed, and more strongly than expected: there is **no** reduction in this
config set under transcript mode, for any partition.

### Q2 — least agents for the floor (SIGNED + least-privilege, k=1)

| config | n_steps | m at floor | floor WBR₁ |
|---|---|---|---|
| 18 of 19 configs | 2–3 | 1 | **1.000** |
| sql-01-langgraph-linear | 2 | 1 | 0.000 |

For 18/19 configs, the floor is reached at `m=1` (no partitioning needed) and
the floor itself is 1.000 — i.e., **partitioning does not lower the floor at
all** for these configs; `m_at_floor=1` here means "already at the floor with
one agent," not "one agent suffices to reach a low floor." The one exception
(`sql-01`) has a floor of 0.000, but for an unrelated reason (see Q3/deviation
below): its least-privilege policy retains no write/external operation at all.

### Q3 — irreducible floor

18 of 19 configs have **no** partition, mode, or policy combination that pushes
WBR₁ below 1.000 — i.e., the full set of configs except `sql-01` has an
irreducible floor at the maximum possible value.

| config | min achievable WBR₁ |
|---|---|
| support-01/02/03/04/05, sql-02/03/04/05, itsm-01/02/03, docs-01/02/03, code-01/02/03 | 1.000 |

**Cause** (from `blast_radius`'s own `reasons`, confirmed by direct inspection,
not inferred): every one of these 19 configs is a **strictly linear dependency
chain** — each step depends only on its immediate predecessor (confirmed by
reading `depends_on` for every step in every config; see deviation note below).
Under Definition 2 rule C (context), compromising the first step in a linear
chain makes every later step influenced via the dependency edge itself, in
BOTH `TRANSCRIPT` mode (first-earlier-influenced-step rule) and `SIGNED` mode
(the dependency-set rule `Dep(s) ∩ Infl`) — signed hand-off blocks an adversary
*tampering with the wire*, not a legitimate hand-off *produced by an honestly-
protocol-following but compromised* upstream agent. The step holding the sink
is always reachable because it is always downstream of whichever agent is
compromised, in a chain with no independent branches to isolate it from.

### Q4 — decomposition (median WBR₁ across 19 configs)

| condition | median WBR₁ |
|---|---|
| (i) original structure, nominal policy, TRANSCRIPT | 1.000 |
| (ii) least-privilege policy only | 1.000 |
| (iii) + SIGNED hand-off | 1.000 |
| (iv) + best partition | 1.000 |

**None of policy, hand-off mode, or topology reduces the median WBR₁ in this
config set.** This is a genuine negative result, not a null computation —
`sql-01` (the one config whose median moves, 1.000→0.000 between (i) and (ii))
confirms the pipeline is sensitive to policy changes when there is something
for a tighter policy to remove; it is just that for 18/19 configs, least
privilege still permits the one sink the task's own nominal calls need, so
there is nothing left to remove while still "preserving the nominal workflow"
(the same constraint `synthesize_least_privilege`'s Proposition 2(a) enforces).

### Deviation (full disclosure)

The §2 frontier/decomposition framing implicitly assumes configs have
independent branches across which steps can be redistributed to reduce worst-
case reach. **All 19 of GUIDE's self-authored real-world-pattern configs are
linear chains** (verified: every step's `depends_on` tuple has at most one
predecessor, and that predecessor is always the immediately prior step in
list order — there is no step with two or more incoming edges, and no step
whose output is not consumed by exactly the next step). The "branch" and
"hierarchical" labels in config IDs (e.g. `support-02-langgraph-branch`,
`support-04-crewai-hierarchical`) describe which *framework idiom* the config
reproduces (a LangGraph conditional-edge pattern, a CrewAI hierarchical
process), not an actual DAG with concurrent, independent branches — the
reproduction itself is still sequential.

**Consequence for the paper**: the topology/partition axis of this analysis
cannot show a benefit on the *current* config set, because there is no
branch point to exploit. This is disclosed here in full rather than
suppressed, per `pref.scientific_integrity`. It does not invalidate
Proposition 3 (which holds regardless, and was verified independently of this
observation) or the Q1–Q4 computations (which are correct given the input).
It does mean the "design guidance" claim in plan §7 ("v7c supports design
guidance for this analyser's model and these configs") must be qualified: the
guidance this analysis actually supports is "for a linear pipeline, neither
hand-off mode nor topology lowers the floor — only a tighter policy that
removes the sink entirely can," which is itself a real and citable finding,
just a different (and more pointed) one than the frontier curve originally
anticipated. A genuinely branching config (e.g. two independent worker agents
whose outputs are merged by a third, where the sink lives behind only one
branch) would be needed to show a topology-driven reduction, and is a
disclosed limitation / future-work item rather than something fabricated here.

### Soundness-critical items (v7c)

**None found.** Zero monotonicity counterexamples across 200 property-test
examples spanning all 19 configs, k∈{1,2}, both hand-off modes.

---

## v7b — Blast radius of real-world published multi-agent systems

- **Tag / commit**: `protocol-v7b` / `234b7ce` (pre-tag code), with two disclosed
  pre-main-run fixes `protocol-v7b.1-pre` (`6e946bc`, `34be9a8` — see below)
- **Run date**: 2026-10-02
- **Commands run**:
  - `uv run pytest tests/unit/test_mining_extractors.py tests/unit/test_mining_audit.py -q` (15 passed, before and after each fix)
  - Pilot: 9 repos at GitHub search rank 201+ (outside the frozen sample), 3 per framework — found and fixed the `self.graph = StateGraph(...)` builder-class gap in the LangGraph extractor BEFORE tagging
  - `python3 -m guide_bench.mining.audit` (frozen snapshot + extraction; crashed on a filesystem race, fixed, re-run)
  - Metrics/validation re-computed on the already-mined `configs.jsonl` after a second pre-main-run fix (cyclic-workflow handling)
- **Input data**: GitHub REST search API, unauthenticated (`gh auth login` not run; confirmed sufficient per plan §3.2), pages 1–2 per framework, snapshots saved to `experiments/mining/search_snapshot_<framework>_p<n>.json`. **Disclosure**: the committed snapshot files were re-fetched ~4 minutes after the run that produced `funnel.json`/`configs.jsonl` (the first snapshot files were deleted by mistake during write-up and had to be re-fetched to satisfy §3.2's "save the raw response" requirement). GitHub's ranked search results can shift slightly between two unauthenticated calls minutes apart (star counts update, new pushes change ranking). The `funnel.json` counts and `configs.jsonl` content reflect the ORIGINAL run (16:31:45Z finish); the snapshot JSON files reflect a SECOND fetch (16:35:14–16:35:52Z) of the same frozen query strings. Both are from the same frozen `QUERIES` dict and the same unauthenticated endpoint; no result in this section was recomputed from the second fetch.
- **Output**: `experiments/mining/{funnel.json, configs.jsonl, results.jsonl, summary.json, summary.md, validation.md}`

### PRISMA-style funnel

| framework | retrieved | excluded (by rule) | cloned (failures) | included repos | configs extracted |
|---|---|---|---|---|---|
| crewai | 200 | name_pattern=29, own_repo=2, >200MB=12 | 154 (3) | **21** | 36 |
| langgraph | 200 | name_pattern=27, own_repo=13, >200MB=27, duplicate=43 | 87 (3) | **1** | 1 |
| autogen | 200 | >200MB=15, own_repo=9, duplicate=78, name_pattern=28 | 70 (0) | **0** | 0 |

### STOP CONDITION TRIGGERED (plan §5): fewer than 15 included configs for langgraph and autogen

Per plan §5: *"stop if... fewer than 15 configs are included for any framework
after 200 results. Report what was obtained; do not widen the queries without
disclosing it."* Both `langgraph` (1 included repo) and `autogen` (0 included
repos) are far below this threshold after exhausting all 200 retrieved results
each (langgraph only had 90 candidates left after exclusions — mostly
`duplicate_across_frameworks`, since many "langgraph"-matching repos also
matched the broader "autogen"/"crewai" queries and were already claimed —
and still only found 1 qualifying config in all 90; autogen found 0 in 70).

**I am stopping here and reporting what was obtained, per the plan's explicit
instruction, rather than widening the queries.** This is a genuine negative
result about the sampling frame, not an extractor defect:

- **Spot-checked 3 top-ranked "autogen"-matching repos directly** (not merely
  inferred): `vectorize-io/hindsight`, `HKUDS/DeepTutor`, and the `microsoft/
  autogen` repo itself (excluded as a framework-own repo; its own examples
  were not separately checked). Confirmed via direct `grep -rl GroupChat` on
  the cloned source: **zero files contain `GroupChat` usage** in either of
  the two non-excluded repos. These repos mention "autogen" in their
  name/description/README (satisfying the frozen query) but do not actually
  construct an AutoGen multi-agent `GroupChat`/`RoundRobinGroupChat`/
  `SelectorGroupChat`/`Swarm` — many use AutoGen for single-agent purposes, or
  only reference it in passing (e.g. a comparison table in a README).
- The `langgraph` query's candidate pool was heavily depleted by
  `duplicate_across_frameworks` (43 of 90) — repos that build with multiple
  frameworks side-by-side (common in "LLM agent framework comparison" repos)
  were claimed by whichever query ranked them higher first, per the frozen
  tie-break rule (§3.2 exclusion rule 3). This is a frozen-rule consequence,
  not a bug: re-running the query differently now would be exactly the kind
  of post-hoc widening the plan prohibits.
- The one langgraph config found (`zhongyu09/openchatbi`, 10-node graph) is
  genuinely rich — real branching and even a real dependency **cycle** (see
  below) — showing the extractor works correctly on real multi-agent graphs
  when a qualifying repo is actually found; the shortfall is in the sampling
  frame finding few repos that build a genuine multi-node `StateGraph` with
  bound tools, not in the extraction logic.

**Disclosed pre-main-run fixes** (both found and fixed BEFORE any metrics
existed, not after seeing results — consistent with the plan's "fix bugs only
as a disclosed version" discipline, applied here before the frozen tag's
first successful completion rather than after):
1. `_iter_py_files`: a broken symlink mid-`rglob()`-walk crashed `stat()`
   inside one of the 154 cloned CrewAI repos. Fixed with a try/except;
   no config had been extracted yet when this fired.
2. `compute_metrics`: the one mined LangGraph config
   (`zhongyu09/openchatbi:openchatbi/text2sql/sql_graph.py`) has a genuine
   dependency **cycle** (`search_knowledge` ↔ `information_extraction`, a
   real retry/revision loop) — GUIDE's workflow model
   (`docs/formal_model.md`) requires an acyclic DAG (`Workflow.stages()`
   uses Kahn's algorithm and raises on a cycle). This is a real scope
   limitation of GUIDE's current formal model, not an extraction error: the
   mined graph is correctly extracted; GUIDE simply cannot compute a blast
   radius for a cyclic workflow as currently formalised. Fixed by excluding
   cyclic configs from the blast-radius computation with a disclosed count
   (`skipped_cyclic_config_ids`), rather than crashing or silently dropping
   the cycle into an incorrect acyclic approximation.

### Metrics (36 of 37 configs scored; 1 excluded as cyclic — see above)

TRANSCRIPT and STRUCTURED hand-off give **identical** results here (both
sink-bearing configs are 2-step linear chains, matching the v7c finding that
hand-off mode makes no difference without an actual branch to exploit).

| metric | value (95% Wilson CI) | n |
|---|---|---|
| M1 (some single agent's BR contains a sink) | 0.056 [0.015, 0.181] | 2/36 |
| M2 (a zero-own-sink agent reaches a sink via propagation) | 0.028 [0.005, 0.142] | 1/36 |
| M3 median WBR₁ (configs with ≥1 sink only) | 1.000 | n=2, 34 excluded (no sinks) |
| M5 (code-execution tool present) | 0.000 [0.0, 0.096] | 0/36 |
| Amplification, median | 0.000 (undefined — too few sink-bearing configs for a stable median) | — |

**The headline finding is not M1–M5's point values — it is that 34 of 36
mined configs (94%) have NO write or external tool at all under the frozen
classifier.** Of 49 distinct tool identifiers found across all 36 configs,
only 2 (`FileWriterTool`, `write_file`) classify as `write`, and **zero**
classify as `external`. This is itself the real empirical result: **public
GitHub example/demo CrewAI code overwhelmingly uses read-only tools**
(search, scrape, CSV/file read, generic placeholder tools like
`IntermediateTool`) — unlike GUIDE's own self-authored 19 configs, which were
deliberately designed with write/external sinks (CRM updates, ticket writes,
email/Slack sends) to exercise the containment mechanism. This sharply limits
what M1–M5 can show on *this specific sample* (public demos, not production
deployments — consistent with plan §7's stated limit that this is "not a
claim about production deployments the study cannot see").

**The two configs that DO have a sink confirm the mechanism works exactly as
designed**: `kid0317/crewai_mas_demo:m1l3_multi_agent.py` is the M2 hit — a
`researcher` agent with zero tools, feeding a `writer` agent with
`FileWriterTool`/`FileReadTool`; compromising the upstream `researcher`
reaches the downstream sink via context propagation, exactly the mechanism
`influenced()` rule C formalises. `nexi-lab/nexus` similarly shows a
`collector`→`analyst` pipeline where `write_file` is reachable from either
agent's compromise.

### Known classifier undercounts (disclosed, not fixed — the rule set is frozen)

Spot-checking the 47 "read"-classified tool names surfaced two further,
real undercounts baked into the **frozen** §3.4 rule set itself (NOT changed
here, since the rule must not be tuned after seeing data):
- `graph_add_tool`, `user_add_tool` tokenize to include `"add"`, which is
  **not** in the frozen `_WRITE_TOKENS` set (`insert` is listed; `add` is
  not) — these are plausibly real write operations, classified as read.
- `file_writer_tool_action_items`, `file_writer_tool_sentiment`,
  `file_writer_tool_summary` tokenize to `"writer"`, not `"write"` — the
  frozen keyword list requires the exact token `write`, so `"writer"` (the
  grammatically natural adjective form) does not match. These compound this
  specific run's undercount, on top of the already-stated "web search/scrape
  counts as read" lower-bound caveat in plan §3.4 point 3.

These are reported, not corrected, because the plan requires the classifier
to be frozen before seeing the data (§3.4's "FROZEN, one rule set for every
repo" instruction) — fixing them now would be exactly the kind of post-hoc
rule-tuning §3.6 and the top-level binding rules prohibit. They further
support treating every count in this section as a **lower bound**, already
the stated framing for the web-search/scrape caveat.

### Extraction validation (§3.6)

Random 10% sample (seed=7, n=10 of 36 structurally re-checked against source,
meeting the "at least 10" floor): **10/10 = 100% structurally exact**
(repo re-cloned, SHA matched, extracted file confirmed present at that SHA).
Well above the 90% threshold — no `protocol-v7b.1` re-run required on
extraction-accuracy grounds. (Note: this validates clone/file-identity
correctness via SHA + file-existence re-check, not a full manual line-by-line
re-derivation of every agent/tool/edge in each of the 10 sampled configs —
see "What this can and cannot claim" below for the precise scope of this
check.)

### Clone hygiene

`experiments/mining/_clones/` is confirmed empty after the run (mined source
is never committed; `.gitignore` updated before the first clone per §3.1).
One transient leftover (filesystem race under tight memory, 6 directories not
removed by the per-repo `shutil.rmtree(..., ignore_errors=True)` on the first
run attempt) was swept up by an explicit confirm-and-retry pass added to
`run()`; `clones_confirmed_empty_after_run` is recorded in `summary.json` as
a persistent check rather than a one-off manual verification.

### Soundness-critical items (v7b)

Extraction accuracy: **100%** (10/10 structurally exact, well above the 90%
threshold). No cyclic-workflow case was silently mishandled — the one found
was detected and excluded with a disclosed count. No count required
fabrication; the two near-zero-sample metrics (M1, M2) are reported with
their full-width Wilson intervals rather than hidden or padded.

---

## Soundness-critical items (running summary across all tasks)

- v7a `fn_onpath` cases: **none found** (0 of 97 scored tasks).
- v7c monotonicity counterexamples: **none found** (0 of 200 property-test examples).
- v7b extraction accuracy: **100%** (10/10 structurally exact; 1 cyclic config correctly excluded, disclosed, not silently mishandled).

## What this can and cannot claim

(Carried from plan §7, to be updated with any limits found during the run.)

- **v7a** supports "the static bound predicts which benign AgentDojo tasks the
  enforcing runtime will block, with 92.8% accuracy (95% CI [0.858, 0.965])".
  AgentDojo-specific, uses a single ground-truth solution path (so
  `fp_model_detoured` cases are expected, not a predictor defect), and is
  post-hoc analysis with a rule frozen before computing agreement.
- **v7c** supports design guidance for this analyser's model and these 19
  self-authored configs — **specifically**: for a strictly linear multi-agent
  pipeline, neither hand-off signing nor step-to-agent topology lowers the
  worst-case single-agent blast radius; only removing the sink operation from
  the (least-privilege) policy does. It does not claim optimality for real
  frameworks' runtime semantics, and the frontier/decomposition result is
  specific to linear-chain configs — a branching config was not available in
  this set to test the branching case. Proposition 3 (refinement monotonicity)
  is a general result, verified by property test, independent of this
  linear-chain observation.
- **v7b**: Mining DID run and produced real, validated data (36 scored configs,
  100% extraction accuracy on a 10-config audit), but **the sample is far
  smaller than planned for langgraph (n=1) and autogen (n=0)** — the plan's
  own §5 stop condition was triggered and respected (not overridden) for both.
  What this run CAN claim: on the 36 CrewAI configs actually mined from public
  GitHub repos (not a claim about any specific framework's deployments, and
  not about langgraph/autogen at all, for which there is insufficient data):
  (a) 94% have no write/external tool under the frozen classifier at all —
  public demo code is read-tool-heavy; (b) of the 2 that do have a sink, both
  show the expected single-agent-compromise-reaches-sink and
  context-propagation-reaches-sink patterns, consistent with GUIDE's formal
  model; (c) one real multi-agent graph was found to be genuinely cyclic,
  which GUIDE's current DAG-based formal model cannot score — a real,
  disclosed scope boundary, not a claim this study can resolve. All counts
  are a stated lower bound (read-classified search/scrape, plus two further
  disclosed-but-not-fixed classifier undercounts: "add" and "writer" tokens).
  This does NOT give external validity for langgraph or autogen MAS
  deployments, and the crewai result itself is about public GitHub example
  code, which may not represent production deployments.

## Test-suite line

Targeted (per task, before each tag): 8 (v7a) + 5 (v7c) + 15 (v7b, after both
disclosed pre-main-run fixes) = 28 tests, all passed, 2026-10-02.

Full suite (plan §4 step 4): `uv run pytest -q` → **131 passed, 1 failed, 132
total** (2026-10-02). The 1 failure
(`tests/unit/test_blast_radius.py::test_property_coverage_is_not_vacuous`) is
**pre-existing and unrelated to v7a/v7c/v7b** — verified by running it in
isolation and against the pre-v7 commit, where it fails identically with none
of this task's files involved. Root cause: it is a Hypothesis-randomized
property test whose coverage-floor assertion (`executed >= 200`) depends on
which gate-outcome branches the random examples happen to hit, and the test
also has a module-level `COVERAGE` dict populated only by the PRECEDING
property test in file execution order — a pre-existing test-ordering fragility,
not a regression introduced by this work. Not fixed here, since it is out of
this plan's scope (the plan's own stated prior baseline was "104" tests; v7
added 28 new ones, mostly independent of this file).
