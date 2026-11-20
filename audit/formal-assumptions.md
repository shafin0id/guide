> Historical audit record imported from the separate development workspace. Its paths identify that workspace, and its completion labels are not independent certification. See current-assessment.md for the submitted release.

# Stage 4 — Formal Model Assumptions, Proof Review & Boundary Audit

Recorded: 2026-11-19 UTC  
Audited sources: `docs/formal_model.md`, `src/guide/`, `src/guide_research/`, `src/guide_agentdojo/`, `src/guide_realworld/`, and manuscript Section 3.2 & 3.7 (Eqs. 1–5).

## 1. Assumption-by-Assumption Audit (A1–A5 & Implicit Assumptions)

| ID | Formal Statement (`docs/formal_model.md`) | Implementation Reality | Scope / Exclusions & Gaps Found |
|---|---|---|---|
| **A1** | Complete mediation: agents invoke tools only via `Runtime._execute`. | Holds in core `guide.runtime.Runtime` (all calls parsed by `parse_reply`, executed via `_execute`) and in `guide_agentdojo.pipeline` & `guide_realworld.{lg,cr,ag}_apps` (all sandbox tools route through monitor). | Does **not** hold if a tool or third-party framework invokes side effects outside the wrapper, or if a process-level adversary bypasses Python wrappers. In `guide_realworld.core.Runtime.call:165`, `Decision.BOUND` revised arguments (`d.call.args`) are ignored and original `args` are executed (`ISS-024`)! |
| **A2** | Ed25519 EUF-CMA security; private keys live only in runtime's `KeyRing`. | Implemented in `guide.handoff.KeyRing` (`cryptography` Ed25519). Keys are generated in-process per `Runtime` instance. | Keys are in-process memory (no KMS/HSM isolation); arbitrary host/process compromise defeats A2. `open_sealed` checks `expected_parent`, `expected_receiver`, `link_hash`, `signature`, `expiry_ms`, but does not check `expected_sender` or `expected_run_id` (harmless when runtime exclusively holds all keys, weak defense-in-depth if any enrolled key leaks). Signing authenticates origin, **not truth**. |
| **A3** | Honest same-role agents have identical output distributions given identical views. | Needed only because influenced steps may alter shared `Router` state, causing non-influenced steps to select a different honest candidate. | Holds in homogeneous pools (same model/persona); fails if heterogeneous models share a role. |
| **A4** | `ToolSpec` fidelity: only `write_effect` ops mutate state (and only `res(t)`), only `external` ops egress data, reads return only `args[cp(t)]` when `cp(t) != None`. | Trusted operator metadata. `guide_agentdojo/specs.py` classifies 74 functions manually; `guide_realworld/scenarios.py` classifies sandbox tools manually. | **Violated/weakened in practice**: (1) `update_password`/`update_user_info` had `control_params=()` in v8 (`ISS-027`); (2) `create_calendar_event` has optional `control_params=('participants',)`, allowing vacuous bypass when omitted (`ISS-013`, `ISS-021`); (3) **F2 design gap**: tools with `column_sensitivity` but `columns_param=None` check only `default_sensitivity`, allowing RESTRICTED columns under INTERNAL clearance (modeled soundly by `blast_radius`, still a gate gap). |
| **A5** | TCB = runtime, gate, policy, registry, keyring; single run on fresh environment (no cross-run persistence, acyclic DAG only). | `Workflow.stages()` enforces acyclicity via Kahn's algorithm. Fresh `Environment()` per run in bench. | **Excludes**: cyclic workflows (e.g., LangGraph supervisor/cyclic, AutoGen round-robin/swarm, mined `openchatbi`), concurrent step execution (parallel LangGraph/CrewAI/AutoGen apps), persistent databases/memory across sessions, and side channels (denial-feedback causality laundering, timing). |
| **Implicit A6 (DISCOVERED)** | **Tool results always observed as `Trust.UNTRUSTED`**. | `docs/formal_model.md:27` asserts tool results are observed only as UNTRUSTED, **but `Runtime._execute:455` passes `result.trust` instead of hardcoded `Trust.UNTRUSTED`!** (`ISS-023`). | Any tool returning `ToolResult(..., trust=Trust.TRUSTED)` injects tool output into the trusted corpus, invalidating Lemma 1's assumption that trusted text equals `T`. Fix in V2: enforce `Trust.UNTRUSTED` (or require explicit trusted-source policy). |
| **Implicit A7 (DISCOVERED)** | **Header corpus excludes structural JSON keys**. | `Runtime.run:167` observes `{"objective": ..., "constraints": ...}`, and `provenance._strings(dict)` yields dict **keys**! (`ISS-021`). | Every run's trusted corpus silently contains `"objective"` and `"constraints"`, authorizing control values matching those words/substrings! |

## 2. Step-by-Step Proof Review

### Lemma 1 (Gate correspondence: soundness & exactness)
- **Claim**: For all `c` and `s`: (a) `delta_g(c, s) = c_hat != DENY => exists kappa in Auth_g(s)` admitting `(c_hat.args, X(c_hat))`; (b) `kappa in Auth_g(s)` admitting `c.args` and `c` well-formed `=> delta_g(c, s) != DENY`.
- **Audit result**:
  - **Core branches 1–6**: Soundness holds on normal inputs, **EXCEPT**:
    1. **Malformed `columns` type (`ISS-019`)**: If `args[columns_param]` is a non-empty non-list (e.g. a string `"unit_price"`), `RulePolicyEngine:127` falls back to `all_cols`, and if `removed` is empty, line 146 leaves the unvalidated string in `args[columns_param]` instead of denying or normalizing!
    2. **`NaN` numeric argument (`ISS-020`)**: `float("nan")` passes `numeric_bounds` clamping (`min(max(nan, lo), hi) == nan`) and produces `Decision.BOUND` with `args[name] = nan`!
    3. **Recipient domain whitespace/multi-address (`ISS-018`)**: `recipient_domains` checks `str(call.args.get("recipient", "")).rsplit("@", 1)[-1].lower()` without stripping whitespace (`"a@corp.example "` -> denied despite `allowed_recipients` stripping it; `"evil@bad.com, ok@corp.example"` -> domain `"corp.example"` -> ALLOWED!). Also hardcoded to param `"recipient"` (ignores `"recipients"` or `"to"`).
    4. **Falsy numeric `0` bypass in `ProvenanceGuard` (`ISS-021`)**: `str(value or "").strip().lower()` converts `value = 0` to `""`, skipping provenance check completely (`file_id=0` admitted even if `"0"` is absent from trusted text)!
    5. **Omitted/empty optional control parameter (`ISS-013`, `ISS-021`)**: `args.get(param)` returning `None`, `""`, or `[]` is skipped via `if not v: continue`, causing vacuous admission on sinks with optional control parameters (`create_calendar_event` without `participants` -> 20/20 AgentDojo bypasses).
    6. **Dict-key corpus pollution (`ISS-021`)**: `_strings(dict)` yields `"objective"` and `"constraints"` as trusted text.
- **Verdict**: Lemma 1 holds for well-typed string/list inputs on the benchmark tools, **fails on edge-case inputs** (`value=0`, `NaN`, non-list `columns`, multi-recipient strings), and **vacuously admits omitted optional control parameters** by construction. Defects `ISS-018`–`ISS-023` will be fixed and regression-tested in Stage 7A!

### Lemma 2 (Delegation integrity) & Theorem 1 (Step containment)
- **Audit result**: Valid for core `guide.runtime.Runtime` under A1–A2 (modulo the Lemma 1 edge cases above).
- **Critical scope boundary**: Lemma 2 does **NOT** apply to `guide_agentdojo` (single-agent loop, no hand-offs) or `guide_realworld` (framework adapters omit signed hand-offs AND pass `step_tools = frozenset(sc.tools)` for every agent).

### Theorem 2 (Soundness of blast-radius bound) & Corollary 1
- **Audit result**: The coupling/induction argument over Kahn topological order `≺` is logically sound under A1–A5 + Implicit A6 (tool results untrusted). No circularity found in the core coupling proof.
- **Exactness distinction**:
  - **Direct compromise (`Proposition 1`)**: Exact (every capability in `Auth_g(s)` for `s in Direct(K)` is realisable via a well-formed proposal), confirmed empirically (`39/39` on T15).
  - **Transitive influence (`Infl \ Direct`)**: Conservative over-approximation (`0/6` realised on T15).
  - **Table 7 (`compromise-replay-v8`)**: `0` soundness / `0` exactness gaps across 1,084 calls verifies **implementation agreement** between `blast_radius.authority()` and `ProvenanceGuard.evaluate()` (both call `supported()` over the same `corpus_of`), NOT independent end-to-end runtime soundness!

### Proposition 2 (Least-privilege synthesis)
- **Audit result**:
  - **Manuscript Eq. (4) is wrong (`ISS-028`)**: Manuscript writes `Policy*(s) = ⋂ {P | NominalExec(s) ⊆ P}` (a per-step policy), whereas `synthesize_least_privilege` actually outputs a pair `(P*, W*)` with a **single workflow-wide policy `P*`** and **per-step tool delegations `Tools*(s)`**.
  - **Implementation bug on non-`recipient` external tools (`ISS-022`)**: `synthesize_least_privilege:374` hardcodes `c.args.get("recipient", "")`. If an observed external tool uses `"to"` or `"url"` (or a recipient without `@`), `domains` becomes `frozenset()` (lattice TOP = unrestricted!) and `allowed_recipients` becomes `{""}` (denying all real recipients while allowing empty ones!).
  - **Numeric bounds partial minimality**: Unused numeric-bound parameters keep original `(lo, hi)` rather than shrinking to bottom; minimality holds over the active synthesized dimensions and observed calls `O`, not unseen benign tasks.

### Proposition 3 (Refinement monotonicity) & Proposition 4 (Topology floor)
- **Audit result**:
  - **Proposition 3**: Proof is mathematically sound for fixed workflow, policy, mode, and feasible `1 <= k <= |Pi|`, because `Sinks*` is partition-invariant and any `k` refined blocks are covered by at most `k` coarse blocks (padded to `k` since `k <= |Pi|`).
  - **Proposition 4**: Proof is mathematically sound for acyclic workflows with `Sinks* != empty`.
  - **Manuscript Eq. (5) is imprecise (`ISS-028`)**: Writes `Reach(s_k) = Union_{j=k}^N Sinks(s_j)` without specifying that `Sinks(s_j)` are the sinks admitted by `Auth_g(s_j)` under policy `P` and gate `g` (and ignores state-flow edges in non-chain DAGs).
  - **Manuscript Eq. (3) is imprecise (`ISS-028`)**: Writes `Reach(C) = Union_{s in Inf(C)} Auth(s)` using `C` (compromised steps) instead of adversary `A = <K, J, tau_adv>` (compromised agents `K`, injectable tools `J`, transport adversary `tau_adv`), and omits gate subscript `g`.
  - **Manuscript Eq. (2) is slightly imprecise**: `Bayes-UCB(i,d) = Q(1 - 1/t, Beta(alpha, beta))` omits the `max(t, 2)` guard in `routing.py:145` (so at `t=1`, `1 - 1/1 = 0`, though warm-up prevents `t=1` before `>=2` pulls when `len(candidates)>=2`; with 1 candidate `max(t, 2)` matters).

## 3. Control-Coverage Matrix Across Experimental Harnesses

| Control | Core `guide.runtime` (`guide_bench` v1–v5) | `guide_agentdojo` (v6, v6b, v8, v9a/c/g) | `guide_realworld` (v9b 15 apps) |
|---|---|---|---|
| Bayes-UCB routing | Active (`P`, `GPLUS`) | **Not used** (single-agent loop) | **Not used** (framework orchestrates) |
| Per-principal Ed25519 signed hand-offs | Active (`P`, `GPLUS`) | **Not used** | **Not used** |
| Hash-linked `TraceLedger` | Active (`P`, `GPLUS`) | **Not used** (custom decision list) | **Not used** (custom event list) |
| `RulePolicyEngine` allow-list / write / external / sensitivity / delegation | Active (`P`, `GPLUS`) | Permissive policy (`allow_write=True`, `allow_external=True`, `RESTRICTED`, all suite tools); only `limit` bound possible | Permissive policy (`allow_write=True`, `allow_external=True`, `RESTRICTED`, `step_tools=ALL`); `BOUND` args ignored (`ISS-024`) |
| `ProvenanceGuard` / `DirectoryGuard` | Active (`GPLUS`) | **Sole active containment control** | **Sole active containment control** |
| Static blast-radius bound `BR(A)` | Directly applies (DAGs, A1–A5) | Single-step degenerate DAG (`Auth_g`) | **Does NOT apply to cyclic/concurrent apps**; v9b checks single-call guard rule only |
