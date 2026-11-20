# Current release assessment — 20 November 2026

**Current scope correction:** Universal synthesis preservation and least-element optimality are not established; numeric authority is not exact at argument level, and sensitivity/input robustness gaps remain. See [claim-scope-corrections.md](claim-scope-corrections.md). These are disclosed limitations, not code fixes.


This assessment governs the revised package. Imported ledgers and closure records describe earlier work; their completion labels do not override the limits below.

## What changed

The manuscript preserves the previous final document's structure and much of its prose. Necessary replacements narrow claims to available evidence, distinguish historical live results from current offline checks, correct the mining and failure analyses, and add the complete 12-arm security–admissibility trade-off. Figure 2 is regenerated from the recorded recipient enumeration. The manuscript has 15 tables, seven figures and 109 references; the supplement retains the original routing simulation and adds evidence-scope notes.

Revised core, research and framework-adapter packages are integrated directly, with no separate development workspace required. Existing hardening includes recipient/input validation, provenance handling, metadata checks and provider-identification recording. Additional final-review fixes ensure the offline runner executes the gate's transformed arguments and reject numeric bounding that changes a previously authorized recipient. Regression tests cover both cases. The formal-model document now states the corresponding parser and bounding behavior explicitly.

## Checks completed on this package

- Full test suite: 166 passed. See results/verification/pytest-final.log.
- Ruff: all checks passed. Mypy: no issues in 18 source files. Package-boundary check passed.
- Influence enumeration: 594,516 cases; zero independent-oracle mismatches and zero compromised-set monotonicity violations.
- Gate enumeration: 1,966,080 evaluations, including 250,880 admitted and 1,715,200 denied calls; zero soundness/exactness violations within that finite grid.
- Fresh offline component audit matches the imported stage7d JSON exactly, including the component, prompt-heuristic and external-DAG outputs. This is not independent data or a fresh live evaluation.
- Native DOCX rendering was inspected page by page. PDFs preserve the inspected layout; Microsoft Word and Google Docs may paginate differently. Numeric citations were renumbered after removing seven unrelated references.

The tests ran using the bundled Python runtime plus compatible dependencies and pure-Python packages from the supplied environment. Some copied native packages could not load under company-laptop restrictions and were replaced with freshly installed compatible builds. See verification-environment.json. A fresh installation from uv.lock was not verified; its presence is a recorded resolution, not certification of environment reproducibility.

## Evidence limits that remain

The five transcripts underlying the 1,575-run aggregate are absent. The paper discloses this and does not use that aggregate as independently reproducible soundness evidence. No substitute records were fabricated.

Historical provider runs predate current hardening. Their model aliases do not uniformly identify immutable model snapshots. No current live security or utility improvement is claimed. The framework studies test guard adapters, not all controls of the signed core runtime or the DAG theorem on cycles.

The 12-arm audit uses supplied calls and inspected tasks. Benign admission is not completed-task utility; its historical 30/67 split is descriptive, not untouched evaluation. The prompt-only heuristic remains exploratory. Missing attack-call metadata excludes some exfiltration tasks from the 588-pair denominator.

Mining records are a convenience sample with duplicates, unresolved bindings and omitted effects. The manuscript retracts general prevalence claims. Four AgentDojo baselines provide limited comparisons; there is no official CaMeL/Progent/FIDES head-to-head result and no demonstrated superiority over all defenses.

Formal guarantees remain conditional on accurate metadata, complete mediation, a trusted monitor and fixed acyclic workflows. Finite tests are not a machine-checked proof or a production security audit. Authorized malicious content and untyped numeric collisions remain limitations.

Reference metadata and local audit records were reviewed; a fresh full-text, source-by-source verification of every citation was not completed. The literature review is narrative, without an independent-screening claim.

## Author handoff

Review NEW_AND_REVISED_TEXT.md outside the repository, retaining its IDs and numerical qualifications when paraphrasing. Select the destination journal before applying its template, page limit, anonymization and declarations. This is an improved, scoped research manuscript, not a guarantee of acceptance or a claim that reviewers cannot request revisions. Nothing has been pushed to GitHub. Original source documents and the separate development workspace remain intact outside this replacement package.
