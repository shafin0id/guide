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
* **One model family** (DeepSeek, served as `deepseek-flash`, requested as `deepseek-chat`). Results may differ for
  weaker models, where hand-off format and constraint carrying plausibly matter more.
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

## What was not done (scope honesty)
Standard-benchmark evaluation, multiple model families, adaptive attacks, formal protocol verification, human assessors,
LangGraph/CrewAI/AutoGen comparisons through their real libraries.
