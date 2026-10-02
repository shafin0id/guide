# Limitations and threats to validity

## Internal validity
* **Researcher-authored tasks and checkers.** All 18 main tasks, 12 robustness cases and their deterministic checks
  were written by the project author. The pilot found two harness defects (tool/gate silently dropping misspelled columns;
  output truncation at 1024 tokens) and the formal run found one checker defect (T17.7 exact match). Checker corrections
  are reported as a separate sensitivity analysis, never merged into primary results.
* **Ceiling effects.** The model solved ≈97 % of nominal tasks in every condition, so the main suite cannot detect
  improvements in task quality. The tasks are too easy for a 2026 frontier-class model; harder tasks (longer horizons,
  larger data, conflicting evidence) are needed.
* **Baselines are configurations of the same runtime** (ADR-0004). That controls confounds but does not measure third-party
  frameworks (LangGraph, CrewAI, AutoGen).
* **Ungated baselines still bind tools per step.** This is realistic, and it makes B1/B2 stronger than "no controls at all".
* **Router state is shared across concurrent runs within a condition**, so run order affects routing decisions.
* **Temperature-0 nondeterminism.** The hosted model is not bit-reproducible, so repetitions measure provider variance.
* **Semantic scoring.** The proposal's two blinded assessors with Cohen's kappa were replaced by deterministic checks
  (substring/field checks). This is stricter to reproduce but coarse for free-text quality.

## External validity
* **Model families.** Protocol v1-v4 used one model family (DeepSeek, served as `deepseek-flash`,
  requested as `deepseek-chat`). Protocol v5 (docs/adr/0005-multi-model-evaluation.md,
  docs/experiments.md "Protocol v5") adds `qwen/qwen3.8-27b` (Groq) and `gemini-3.8-flash` (Google AI
  Studio) on the same tasks/policies/conditions -- still only 3 families, all mid-sized-or-larger
  2026-era models; no small/weak model has been tested, so the ceiling effect's dependence on model
  strength remains open.
* **Synthetic sandbox** with 4 vendor rows and 4 incidents; no real enterprise systems (by design, proposal §6).
* **Injection attacks are fixed, not adaptive.** A single phrasing per case; no optimisation against the defences.
  Attack success rates are therefore upper bounds on robustness only for these attacks.
* **No standard benchmark yet** (AgentDojo, τ-bench, InjecAgent). The results are internal-suite results.

## Construct validity
* **Violation** covers leaks of specific restricted values, write side effects and unauthorised e-mail recipients. It does
  not cover subtler harms (misleading summaries, partial leaks in paraphrase).
* **Intent fidelity** = satisfied atomic constraints / total. It does not weight constraints by importance.
* **Trace completeness** is 0 for B1/B2 by construction (they have no trace). It is reported to follow the proposal,
  not as a finding.

## Mechanism limitations
* **Provenance guard:** substring matching over string leaves. Bypassed by paraphrase or encoding of destinations, and by
  attacker-controlled text that also appears in trusted content. It is blind to data arguments (e.g. an e-mail body that
  summarises restricted data), and it may deny legitimate destinations that the task expects to be looked up in data.
* **Signing:** in-process keys; attests origin and integrity, not truth. A compromised agent can sign false content (A07).
* **Rule gate:** only as good as the tool metadata; it cannot see semantic misuse of an allowed call.
* **Routing:** no regret guarantee for non-stationary, non-Bernoulli LLM agents; with homogeneous agents routing is pure
  overhead.
* **No concurrency, no human escalation, no rollback** (see architecture.md).

## Blast-radius analysis (protocol-v3)
* The guarantee is conditional on A1–A5 (formal_model.md §4): complete mediation, unforgeable signatures, honest agents
  in a role being interchangeable, tools that honour their `ToolSpec`, and a single run on a fresh environment.
* It bounds *which effects and destinations* are reachable. It does not bound *content*: an exfiltrating body sent to a
  permitted recipient is inside every bound (F3).
* The bound is exact only for directly compromised steps. Beyond that it is conservative (transitive tightness 0/6).
* The proof is on paper and checked by property tests, not machine-checked.
* Least privilege is minimal with respect to the *observed* nominal traces; unseen legitimate behaviour may be denied.
  Held-out replay found 0/44 denials, but that is only 18 tasks.
* Validation used one task (T15) for the adaptive attacker and one model family.

## What was not done (scope honesty)
Standard-benchmark evaluation, more than 3 model families, a small/weak model, formal protocol verification (beyond
protocol-v3's paper proof), human assessors, LangGraph/CrewAI/AutoGen comparisons through their real libraries.
