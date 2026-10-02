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

Not started yet. Will be filled in after the pilot (§3.2) and the frozen-tag
extraction run, per plan §3.7.

---

## Soundness-critical items (running summary across all tasks)

- v7a `fn_onpath` cases: **none found** (0 of 97 scored tasks).
- v7c monotonicity counterexamples: **none found** (0 of 200 property-test examples).
- v7b extraction accuracy: pending.

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
- **v7b**: not yet run.

## Test-suite line

Targeted: `uv run pytest tests/unit/test_predict_utility.py tests/unit/test_topology.py -q` → 8 passed (2026-10-02). Full suite run deferred to end of all three tasks per plan §4 step 4.
