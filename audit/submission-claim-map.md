# Submission claim-to-evidence map

**Current scope correction:** Universal synthesis preservation and least-element optimality are not established; numeric authority is not exact at argument level, and sensitivity/input robustness gaps remain. See [claim-scope-corrections.md](claim-scope-corrections.md). These are disclosed limitations, not code fixes.


Current claims supersede broader wording in historical audit records. All paths below are relative to the repository root.

| Claim in revised manuscript | Evidence | Permitted interpretation |
|---|---|---|
| Conditional static reachability bound, Sections 3.7/4.1 | docs/formal_model.md; src/guide_research/; results/verification/exhaustive/part_A.json | 594,516 finite cases; fixed topological order and documented assumptions |
| Gate correspondence, Section 4.1 | src/guide/policy.py; scripts/v9/exhaustive_bound.py; results/verification/exhaustive/part_B.json | 1,966,080 enumerated evaluations; not unrestricted proof by testing |
| Current replay executes revised arguments | src/guide_agentdojo/replay_execution.py; tests/unit/test_replay_execution.py | BOUND arguments reach the backend; DENY does not |
| Bounding cannot change an authorized recipient | src/guide/policy.py; tests/unit/test_core.py, test_numeric_bounding_cannot_change_authorized_recipient | Specific gate regression; not comprehensive deployment safety |
| 12-arm containment/admissibility, Table 15 | results/offline/component_audit.json, component_ablations_agentdojo; scripts/run_offline_ablations.py | Retrospective supplied-call replay; 588 attack pairs and 97 benign tasks |
| Prompt-only heuristic, Section 5.3 | results/offline/component_audit.json | Exploratory 70/97 versus 67/97 majority; not validated general prediction |
| Mining corrections, Table 11 | results/offline/mining_audit.json; audit/mining-provenance-audit.md; experiments/ | Descriptive source audit; no production-prevalence inference |
| Historical baseline and framework comparisons, Tables 13–14 | experiments/results/; results/reproduction/v9_matrix_audit.json; results/sensitivity/stage5_stats_audit.json | Historical live measurements; current adapter fixes not rerun live |
| Historical utility-loss prediction, Table 9 | experiments/results/predict-utility-v7a/; experiments/results/final-v8/ | Requires known required calls and existing live outcomes |
| Recipient enumeration, Figure 2 | paper/figures/fig2_recipient_audit.csv; tests/; experiments/results/ | Finite recipient surface, not live attack success |
| Missing 1,575-run aggregate | audit/evidence-availability.md; manuscript Section 4.1 | Historical report only; underlying five transcripts missing |
| Related-work distinctions, Table 1 | audit/table1-evidence.md; audit/reference-ledger.csv; results/offline/reference_verification.json | Qualitative comparisons, no official head-to-head experiment; old reference IDs mapped separately |

The release manifest fixes the exact supplied file bytes. It does not authenticate external historical provenance or repair missing records.
