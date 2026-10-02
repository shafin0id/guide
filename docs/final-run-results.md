# Final Run Results — M1 to M6 (Protocol v8 + publication readiness)

Spec: `docs/final-run-plan.md`. Fill this file in **as each step finishes**. Every number
must trace to a file under `experiments/` (give the path next to it). Where a list is
empty, write "none found" explicitly.

Executor / model: ___ · Run date: ___ · Branch: `research/evidence-based-rebuild`

---

## Run log
- Live log: `experiments/results/final-v8/run.log`
- Progress ledger: `experiments/results/final-v8/progress.json`
- Final overall %: ___

## M3 — flaky test fix
- Final `max_examples`: 4000 · executed (ALLOW+BOUND) count: 294 (threshold 200, kept)
- 6 verification runs: 6/6 passed
- Full suite after fix: 132 passed / 0 failed
- Commit: `8a33d2b`

## Freeze
- `protocol-v8` tag → commit ___
- Targeted tests before tag: `test_compromise_replay.py` ___ passed; `test_topology_theory.py` ___ passed

## M1 — Assumed-compromise replay on AgentDojo
Outputs: `experiments/results/compromise-replay-v8/`

| suite | pairs (full) | in scope | CONTAINED | PARTIAL | EXECUTED | containment [95% CI] | v6-subset containment | undefended containment |
|---|---|---|---|---|---|---|---|---|
| banking | 144 | | | | | | | 0% |
| slack | 105 | | | | | | | 0% |
| travel | 140 | | | | | | | 0% |
| workspace | 560 | | | | | | (10-task subset) | 0% |
| **overall** | 949 | | | | | | | 0% |

- Sink-call block rate: ___ (denied / total attacker sink calls)
- Out-of-scope pairs (`no_tool_calls` / `no_sink_calls`), by injection task: ___

**Admitted sink calls by reason**

| reason | count | injection tasks |
|---|---|---|
| no_control_params | | |
| control_value_in_trusted_prompt | | |
| other (explain each) | | |

**Bound vs runtime (all attacker calls)**

| | runtime executed | runtime denied |
|---|---|---|
| static admitted | | exactness gaps: ___ |
| static blocked | **soundness violations: ___ (must be 0)** | |

Per-injection-task table: `experiments/results/compromise-replay-v8/summary.md`

## M1b — GUIDE-attributable utility loss
Outputs: `experiments/results/final-v8/v7a_attributable_loss.{json,md}`

| | lost (v6b ✓, v6 ✗) | not lost |
|---|---|---|
| predicted_block | | |
| not predicted | | |

- Accuracy ___ [CI ___] · precision ___ · recall ___ · lost count ___
- Predicted cost ___ vs observed cost ___ pp

## M2 — Proposition 4 and absolute reach
Outputs: `experiments/results/topology-v8/`

- Prop 4a property test: ___ examples, counterexamples: ___ (must be 0)
- Prop 4b/4c checks: ___ · Real configs, brute force = closed form: ___/76
- Proposition 4 added to `docs/formal_model.md`: yes/no

**Absolute reach, median across 19 own configs**

| condition | median abs WBR₁ | median nom-normalised WBR₁ | reduction from (i) |
|---|---|---|---|
| (i) nominal, TRANSCRIPT | | | — |
| (ii) least privilege | | | |
| (iii) + SIGNED | | | |
| (iv) + best partition | | | |

**Structural census (acyclic configs; the 1 cyclic config is listed and not analysed)**

| set | n | is_chain | dominating source (all steps) | floor = 1 under SIGNED (Prop 4) |
|---|---|---|---|---|
| own | 19 | | | |
| mined (scored) | 36 | | | |
| total | 55 | | | |

## M5 — References and competitor check
- Venue entries fixed: ___/19 (DOI ___, proceedings URL ___); manual list: ___ (with links)
- `anon2025make` authors: found / still [VERIFY]
- Preprints upgraded to peer-reviewed: ___ (list)
- Comparators added: ARM, Cordon, 2606.26479, 2603.28013 — yes/no each
- Preprints dropped to keep ≤ 20% (with reason): ___
- Final bibliography: ___ total, ___ peer-reviewed / ___ preprint (___%)
- Competitor search: ___ hits; `NOVELTY-CRITICAL`: ___ (list, or "none found")
  — details in `docs/lit-review/final-competitor-check.md`
- Lookup log: `experiments/results/final-v8/ref_lookup.jsonl`
- Citation/reference cross-check mismatches: ___

## M4 — Documents and manuscript
- [ ] 4.1 experiments.md corrected (v6 pooled utility; Key Finding 1 rewritten; v6b + v8 sections)
- [ ] 4.2 submission-alignment.md A34–A36
- [ ] 4.3 differences-from-submitted.md
- [ ] 4.4 title / abstract (word count ___) / keywords
- [ ] 4.5 introduction, C1–C4, RQs reordered
- [ ] 4.6 related work + comparison table (cells sourced)
- [ ] 4.7 methods 3.10–3.13
- [ ] 4.8 results
- [ ] 4.9 discussion
- [ ] 4.10 limitations (all listed items present)
- [ ] 4.11 conclusion + new figure
- [ ] 4.12 voice pass; wording greps clean; `check_numbers` missing = 0

## M6 — Release preparation
- Secret scan on result dirs: clean / redacted (details)
- REPRODUCE.md, README section, CITATION.cff written: yes/no
- LICENSE present: yes/no (owner decision if no)
- Full suite: ___ passed / ___ failed
- Docx built: media entries ___ = image refs ___
- `paper-v1` tag → commit ___ (not pushed)

## Soundness-critical items
- M1 soundness violations: ___
- Prop 4 counterexamples: ___
- Any test weakened: no (must stay no)

## Deviations
(none yet)

## Owner decisions pending
- CITATION.cff full name / ORCID
- LICENSE choice
- Manual reference checks (list)
- Confirm the title and the GUIDE expansion ("Intent-pinned Delegation Enforcer")
