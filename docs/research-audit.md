# GUIDE / RMCE — Baseline Research & Engineering Audit

Audit date: 2026-09-29. Audited commits: `guide@fc1d4b4`, `guide-bench@f5642d8`.
Scope source of truth: `previously submitted to university/` (Proposal = Assignment 2, Literature Review = Assignment 1).
Status legend: **VERIFIED** (read code / ran it), **INFERRED** (strong evidence, not executed), **TO VERIFY**.

---

## 0. Executive verdict

- The **mechanisms** (Bayes-UCB routing, Ed25519-signed hash-linked hand-offs, pre-execution policy gate, hash-linked trace, DAG scheduler, content-addressed store) are real, small, and mostly correct. 61/61 unit tests pass (VERIFIED).
- The **evidence** does not exist yet. Every headline number in `README.md` is either (a) an analytic formula evaluated with assumed parameters, (b) assigned per condition by the evaluation code, or (c) produced by a harness that fills GUIDE's output from the answer key. None of it may be reported as an experimental result.
- The **approved proposal is sound and modest** (four controls, B1/B2 baselines, 294 runs, Wilcoxon, kappa, "does not claim universal security"). The README/spec drifted far past it. The fastest route to a defensible paper is to return to the proposal's protocol and execute it honestly.
- Timeline: per Proposal Table 4, October 2026 is baselines + pilot + frozen protocol. Nothing academically required has been lost yet.

---

## 1. What the system is supposed to do (Proposal)

Aim: a policy-aware, traceable orchestration framework that preserves mandatory task constraints across hand-offs and blocks unauthorised tool actions **before** execution.

| RQ | Question | Required evidence |
|---|---|---|
| RQ1 | Requirements for a policy-aware traceable MAS framework | Requirement catalogue + spec |
| RQ2 | How to combine routing, structured hand-offs, policy validation, trace capture | Component contracts + run records |
| RQ3 | P vs B1 (fixed-role sequential, plain-text) vs B2 (static graph, structured state) on success, intent fidelity, policy compliance, trace completeness, time, cost | 18 tasks × 3 conditions × 5 reps = 270 runs |
| RQ4 | Preservation/rejection under ambiguous, conflicting, adversarial inputs | 12 held-out robustness cases × {P, B2} = 24 runs |

Claimed contribution (Proposal §7): the **integration** of four controls under a common evaluation protocol — explicitly *not* each control individually.

---

## 2. Current architecture (as implemented)

```
guide_mas/
  core/coordinator.py    BayesUCBCoordinator: Beta(α,β) per (agent,domain), argmax Beta.ppf(1-1/t), warm-up, "trust freeze" (β+=5 on confident failure)
  core/handoff.py        IntentPackage (pydantic) → canonical JSON → SHA-256(prev‖P_k) → Ed25519 sign/verify, expiry, parent link; 3 "tiers"
  core/policy_gate.py    CAMCOPolicyGate: allow-list tool/op, sensitivity ceiling, write-effect deny, clamp `limit` to [1,max]
  core/trace_ledger.py   Hash-linked event list, genesis hash, integrity verification, JSONL export
  core/topology.py       Kahn topological sort → parallel stages
  core/model_client.py   LiteLLM wrapper + keyword-matching offline stub
  storage/content_store  sha256-addressed blob store (input_refs)
  prompts/               static-prefix system prompts + templates
  tools/synthetic_tools  Mock ProcurementDB / IncidentLogStore / EmailService
  baselines/b1,b2        B1 sequential, B2 static graph
  evaluation/            18 tasks, 12 robustness cases, runner, Wilcoxon/bootstrap
```

Control flow (P): task → DAG stages → `route()` → sign hand-off → agent LLM call → action record → `validate_and_project()` → mock tool → `append_event()` → rubric scoring.

Current safeguards that genuinely work at unit level (VERIFIED via tests/robustness.py calling real components): signature mismatch rejection, parent-hash discontinuity, expiry, ledger tamper detection, tool allow-list, write-effect deny, sensitivity ceiling, limit clamp.

---

## 3. Evaluation integrity findings (blocking — must be fixed before any result is reported)

| # | Finding | Evidence | Severity |
|---|---|---|---|
| E1 | Intent fidelity is **assigned by condition**, not measured: P = 0.85+0.15·0.85^h, B2 = max(0.6, 0.88−0.02h), B1 = 0.85^h. The hypothesis is hard-coded as the result. | `guide_mas/evaluation/runner.py:110-121` | Critical |
| E2 | Baseline success is capped by hard-coded thresholds (B2 fails if constraints > 6, B1 if > 4) independent of output. | `runner.py:113-120` | Critical |
| E3 | Baseline latency padded (`+ n_hops*0.4`) and tokens synthesised by formula when absent. | `runner.py:184-197` | Critical |
| E4 | Model client defaults to an offline stub when no API key is present and **silently** falls back on API errors; the stub returns the ground-truth records by keyword match. Runs are indistinguishable from live runs in output. | `core/model_client.py` (`offline_mode = not has_api_key`; except-branch fallback unless `GUIDE_STRICT_LIVE`) | Critical |
| E5 | B2 robustness baseline returns `passed=False` by construction. | `evaluation/robustness.py:467-475` | High |
| E6 | guide-bench GUIDE adapter **writes the expected rubric properties into GUIDE's output** based on keys in `expected_schema` (`tampering_detected=True`, `tests_passed=5`, `coverage_pct=100.0`, `sublinear_regret=True`, …). Competitors get no such fill. | `guide-bench/adapters/guide_adapter.py:470-528` | Critical |
| E7 | "CrewAI / LangGraph / AutoGen" are **not used**. None are installed; `HAS_CREWAI` etc. are set and never read; adapters are hand-written LiteLLM prompt chains labelled with framework names. | `guide-bench/adapters/*_adapter.py:18-30`; `import crewai/langgraph/autogen` → ModuleNotFoundError | Critical (claim) |
| E8 | Bench intent fidelity = keyword overlap ≥ 0.35 × decay^(hops−1); penalises hop count, not information loss, and hop counts differ per adapter by design. | `guide-bench/metrics/scorers.py:186-212` | High |
| E9 | "SWE-bench Lite / GAIA / HotpotQA / ToolBench / InjecAgent / MultiAgentBench" are hand-authored imitations (5–12 tasks each), not the official datasets/harnesses; SWE "tests passed" are never executed (see E6). | `guide-bench/datasets/*.py`, E6 | High (claim) |
| E10 | 1 repetition, no randomised order, no pilot exclusion, no blinded assessors / Cohen's kappa, despite the proposal requiring them. | `guide-bench/output/full_60_matrix/benchmark_manifest.json` (`repetitions: 1`) | High |
| E11 | README analytic claims (96.01% regret reduction, 91.66% IPS, 50% speedup) are closed-form numbers derived from assumed µ, r, w, T_node — not measurements. The regret "bound" is also misapplied (Lai–Robbins is a lower bound; the static-regret comparison assumes the static choice is always the wrong arm). | `README.md §2`, spec §2 | High |

What *is* genuine in guide-bench (VERIFIED): the 240 runs made real DeepSeek calls (non-zero tokens, no simulation markers). The raw LLM transcripts may be reusable for qualitative analysis; the scores are not.

**Consequence:** the README leaderboard, Wilcoxon table, and 6-dimension table must be withdrawn. If they have been shown to the supervisor, the supervisor should be told they came from a non-neutral harness.

---

## 4. Mechanism-level technical findings

| Component | Status | Issues |
|---|---|---|
| Bayes-UCB routing | Correct Beta-quantile rule (Kaufmann 2012) | Reward is a rubric pass that, in the stub, is always 1 → router never learns anything. "Trust freeze" (β+=5, κ≥0.8) is an ad-hoc heuristic with no justification or ablation. With 2 agents per domain and 18 tasks, T is far too small for asymptotic regret to mean anything; regret claims must be empirical curves on a controlled bandit simulation, not asymptotics. Uses LLM **self-reported** confidence as a signal (known to be poorly calibrated). |
| Signed hand-offs | Ed25519 + SHA-256 chain correct | **One keypair per run shared by all agents** (`runner.py:293`, `robustness.py:170`), in-process → signature attests nothing about *which* agent produced a package; no key custody, rotation, or trust boundary. "RFC 8785 JCS" is `json.dumps(sort_keys, separators)`: not JCS (number formatting, UTF-16 key order differ). Signatures give tamper-evidence only — correctly stated in the proposal, overstated in README ("prevents diff escaping", "defeats DPI decay"). |
| Intent anchor S₀ | S₀ is re-injected each hop | Re-injecting the objective is a standard pattern; nothing measures whether downstream agents *honour* constraints. The DPI framing is not an information-theoretic result about this system — r=0.85 is assumed. |
| Policy gate ("CAMCO") | Real deny/allow rules | The "Euclidean convex projection" is a 1-D clamp of `limit` to [1, max] (`policy_gate.py:103-117`); categorical fields (tool, op, sensitivity) are not in ℝ^d in any meaningful sense. Must be described as a rule-based pre-execution gate with parameter bounding. The gate sees only the action record, not *why* the action was proposed (no provenance/taint) — so an injection that stays inside permissions passes (e.g. a permitted read that exfiltrates via final answer). "Out-of-process" is claimed but it runs in-process. |
| Trace ledger | Hash chain correct | In-memory, same process, no external anchoring/signing → tamper-evident only against a third party who cannot rewrite the whole chain. Adequate for the proposal's "trace completeness" metric. |
| DAG topology | Correct Kahn's algorithm | "50% speedup" is arithmetic on assumed durations; parallel execution not measured. Not part of the proposal's four controls. |
| Content store / pointer refs | Works | Reduces tokens only if agents don't need the content; content must still be dereferenced into a prompt somewhere. Token claims unmeasured. |
| Model client | LiteLLM wrapper | Silent fallback (E4); broad `except Exception`. |
| Tools | Mock, deterministic | Fine for the proposal's sandbox scope; too easy to separate architectures (4 records). |

---

## 5. Engineering weaknesses

- Package is `guide_mas` in a flat layout; no `src/`, no public API contract, no Protocols for provider/tool/policy/store/observer; research code (runner, formulas, stub) lives inside the framework package.
- Coupling: runner hard-wires agents, domains, tools, formulas; baselines share code paths with scoring.
- Error handling: broad `except Exception` in model client and bench adapters (`except (ImportError, PermissionError, Exception)`), silent degradation.
- No structured observability (events exist only in the ledger), no redaction policy, no cost/token accounting independent of provider response.
- No CI, no type checking, no lint config visible; `setup.py` + `pyproject.toml` + `requirements.txt` + `uv.lock` coexist (dependency source of truth unclear).
- Reproducibility: no pinned model version in results, no commit hash in manifests of `guide`, seeds not meaningful for most hosted LLMs, offline stub makes "reproducible" results trivially reproducible because they are fixed.
- guide-bench hard-codes an absolute local path in `requirements.txt` comment; mutates `appdirs.user_data_dir` globally (monkey patch).

## 6. Security weaknesses (for enterprise claims)

- No trust boundary between agents: shared key, shared process, shared memory.
- Gate is not provenance-aware: cannot distinguish an action motivated by the user's S₀ from one motivated by untrusted retrieved content.
- Untrusted tool output is passed back into prompts without labelling/quarantine.
- No human-escalation path, no rollback semantics for write-effect tools (only deny).
- No authN/authZ model for principals (user, agent, tool); policy is a dict.

## 7. Novelty assessment (preliminary — full literature verification pending in `docs/novelty.md`)

| Element | Prior art (TO VERIFY exact citations) | Novel? |
|---|---|---|
| Beta-Bernoulli / Bayes-UCB routing | Kaufmann et al. 2012; bandit-based LLM/model routing literature | No |
| Signed, hash-chained logs / hand-offs | Tamper-evident logging (Crosby & Wallach 2009), Certificate Transparency, provenance literature | No |
| Pre-execution tool-policy enforcement | Progent (2025), AgentSpec (2025), GuardAgent/ShieldAgent (2025), CaMeL (Debenedetti et al., 2025), Invariant-style guardrails | No |
| Structured state hand-offs | MetaGPT SOPs, LangGraph typed state | No |
| Objective re-injection (S₀ anchor) | Common prompting practice | No |
| **Integration of all four under one protocol with ablation evidence** (Proposal §7) | Pasupuleti et al. 2026 (policy projection), others separately | **Possibly** — modest, DSR-appropriate, defensible only with ablations |

Candidate directions that could turn this into a stronger (Q1/Q2-plausible) contribution — each is a hypothesis to test, not a claim:

1. **Provenance-carrying hand-offs + provenance-aware gate.** Signed packages carry per-field provenance labels (user/S₀, trusted tool, untrusted content, agent-derived); the gate decides on the action *and* on the provenance of the data that motivated it. Directly tests the proposal's thesis that controls must be connected across stages. Closest prior art: CaMeL, FIDES-style information-flow control (TO VERIFY) — the MAS hand-off setting is the potential delta.
2. **Measured constraint-level intent fidelity.** Every S₀ constraint gets an ID; agents must emit constraint-satisfaction claims; a deterministic checker verifies them. Converts "intent fidelity" from an assumed curve into a measurable per-constraint outcome.
3. **Cross-stage failure injection + ablation.** Faults that start at routing or hand-off and manifest at tool use; show which controls catch which fault class. This is the empirical core of the proposal's "integration" claim.
4. **Per-agent identity keys** so a signature attributes each package/action to a principal — needed for "who did what, under which policy".

## 8. Claims currently unsupported (remove or weaken)

"100% task success", "0% policy violations", "intercepts 100% of prompt injections", "provable O(ln T)" for this system, "96.01% regret reduction", "91.66% IPS", "50% speedup", "60.3% token reduction", "80–90% cache savings", "≥95% hand-off rejection" (as a result rather than a criterion), "Production-Grade", "outperforms CrewAI/LangGraph/AutoGen", "Euclidean convex projection" (overstated), "RFC 8785" (not implemented), "out-of-process" gate, Wilcoxon p-values, target venue badges.

## 9. What a strong reviewer would raise

1. Results derived from the evaluation code, not the system (E1–E6).
2. Baselines are straw men built by the author with handicaps.
3. Tiny, author-written tasks with 4 DB rows; no standard benchmark.
4. Each component is known; where is the contribution beyond integration?
5. No ablations; no cost/latency overhead analysis vs benefit (the proposal's own thresholds are unreported).
6. Asymptotic bandit math applied to T≈18.
7. LLM self-confidence used as a trust signal.
8. Security claims without an adaptive attacker (e.g. AgentDojo-style attacks).

## 10. Recommended evaluation direction (detail in `docs/evaluation.md`, pending)

- **Primary (proposal-conformant):** 18 tasks × {B1, B2, P} × 5 reps, live model, randomised order, measured fidelity, Wilcoxon + bootstrap CI + practical thresholds; 12 robustness cases × {P, B2}; blinded 20% semantic sample with kappa.
- **Ablations:** P, P−routing, P−signed hand-off, P−gate, P−trace (and P−provenance if direction 1 is adopted).
- **External validity (TO VERIFY suitability):** AgentDojo (utility + attack success rate under prompt injection, pluggable agent pipelines) and τ-bench (policy-following tool use with pass^k consistency). Use official harnesses only.
- Framework comparisons (CrewAI/LangGraph/AutoGen) only if run through the real libraries with the same model; otherwise drop them. They are not required by the proposal.

## 11. Proposed phase plan (each phase gated on the previous one)

| Phase | Goal | Exit criterion |
|---|---|---|
| P0 | This audit + submission alignment | Done |
| P1 | Evaluation integrity: fail-closed live mode, stub isolated to unit tests, measured metrics, neutral scoring, remove answer-key fill, honest README; tag `baseline-v0` | A run cannot produce a score not derived from system output |
| P2 | Three-boundary restructure: `guide` (Core), `guide_research` (RMCE mechanisms), `guide-bench` (evaluation); typed Protocols; per-agent keys; fail-loud errors | Existing behaviour preserved, tests green, public API documented |
| P3 | Pilot (6 tasks, excluded) → freeze protocol → formal 294 runs of baseline GUIDE | Frozen, reproducible baseline dataset |
| P4 | Improvements with pre-registered hypotheses (provenance-aware gate, constraint-ID fidelity) + ablations + adversarial suite | Baseline vs improved with stats; negative results kept |
| P5 | Docs set, ADRs, CI, packaging extras | Another researcher can reproduce from README |

## 12. Resolution status (2026-09-29, branch `research/evidence-based-rebuild`)

E1–E6, E8, E10, E11 are fixed and regression-tested (`tests/regression/`). E7/E9 are resolved by withdrawal: no
third-party framework or named-benchmark claim remains. All §4–§6 mechanism issues were addressed, except those listed as
explicit limitations (in-process keys, no rollback, no human escalation, sequential execution). Results:
`docs/experiments.md`. Scope deviations: `docs/submission-alignment.md`.
