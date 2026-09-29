# Architecture Decision Records

Short-form ADRs. Status: Accepted unless stated.

## ADR-0001 — Rebuild on a clean `src/` layout; retire `guide_mas`

* **Problem.** The `guide_mas` package mixed framework code with an evaluation that assigned results per
  condition (audit E1–E6), and its layout made research code part of the importable framework.
* **Alternatives.** (a) Patch `guide_mas` in place; (b) new package, port the correct mechanisms.
* **Decision.** (b). Correct mechanisms (Beta routing, Ed25519 chain, ledger, Kahn DAG, CAS) were re-implemented
  in `src/guide` with typed contracts; `guide_mas` is preserved unmodified at tag `baseline-v0`.
* **Consequences.** Old import paths break (pre-1.0, acceptable). History and the audited baseline remain reproducible.

## ADR-0002 — Three packages with one-way dependencies (Core ← Research ← Bench)

* **Problem.** Research mechanisms and experiments must not destabilise a framework API meant for users.
* **Alternatives.** One package with sub-modules; three repositories; one repository with three packages.
* **Decision.** One repository, three top-level packages in one distribution for now; boundary enforced by
  `scripts/check_boundaries.py` in CI. The external `guide-bench` repository is superseded (its adapters did not
  run the frameworks they named, audit E7) and is not used for any reported result.
* **Consequences.** Can split into separate distributions later without code moves. A research mechanism
  graduates into Core only with supporting evidence in `docs/experiments.md`.

## ADR-0003 — Per-principal signing keys

* **Problem.** baseline-v0 signed every hand-off in a run with one shared key, so a signature proved integrity
  but not *which agent* produced a package.
* **Decision.** `KeyRing` enrolls one Ed25519 key per principal; `open_sealed` verifies against the claimed sender.
* **Evidence.** Integrity experiment: sender spoofing rejected 100 % with per-principal keys, 0 % with a shared key.
* **Consequences.** Key custody becomes a deployment concern (subclass `KeyRing` for KMS).

## ADR-0004 — One runtime for every experimental condition

* **Problem.** Separate baseline implementations let incidental differences (prompts, tool wiring, retries)
  masquerade as architectural effects.
* **Decision.** B1, B2, P, GPLUS and all ablations are configurations of the same `Runtime`; only hand-off mode,
  router, policy engine, observers, re-dispatch and trace differ.
* **Trade-off.** A reviewer may call B1/B2 "GUIDE with features off". That is intentional: it is exactly the
  independent variable defined in the proposal (§8.2). Comparisons with third-party frameworks would need the real
  libraries and are listed as future work.

## ADR-0005 — Fail closed; no silent fallbacks

* **Problem.** baseline-v0 silently replaced failed or missing model calls with a stub that returned correct answers.
* **Decision.** Providers raise `ProviderError`; the only non-network provider is the explicitly-constructed
  `ScriptedProvider`. Integrity failure halts the run. Malformed output gets a bounded number of repairs.
* **Consequences.** Some runs fail that previously "succeeded"; those failures are reported.

## ADR-0006 — Policy decisions derive from tool metadata, not proposer claims

* **Problem.** baseline-v0's action record carried a `data_sensitivity` chosen by the proposing agent.
* **Decision.** Sensitivity is derived from `ToolSpec.column_sensitivity`; requested columns above clearance are
  removed (BOUND) or the call is denied; unknown columns are denied with the valid list (pilot finding #1).

## ADR-0007 — Minimal core dependencies

* **Decision.** Core requires only `cryptography`. HTTP (`httpx`) is the `openai` extra; statistics (`scipy`,
  `numpy`) are bench/dev extras; the Beta quantile has a pure-Python implementation (scipy used when present,
  equality tested). LiteLLM is not a dependency; any OpenAI-compatible endpoint works through one small adapter.

## ADR-0008 — Provenance guard stays in Research

* **Status.** Proposed for graduation pending external-benchmark evidence (see docs/experiments.md H1).
* **Reason.** Value-level substring provenance is a heuristic with known bypasses (paraphrase, attacker text that
  also appears in trusted content); it should not be presented as a stable guarantee.
