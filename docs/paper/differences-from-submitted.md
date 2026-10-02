# Differences: paper draft vs. previously submitted reports

Purpose: a single reference for explaining to the supervisor what changed between the two submitted
reports and the paper draft at `docs/paper/manuscript-draft.md`, and why. Source of truth for "what was
submitted" is `previously submitted to university/RMCE - Assignment 2 (Proposal).docx` (submitted
2026-08-01) and `RMCE - Assignment 1 (Liturature Review).docx`. Neither file is edited by this project.
This file does not replace `docs/submission-alignment.md` (the full A1-A30 engineering/scope log) or
`docs/lit-review/literature-review.md` §10 (the L1-L13 literature-specific log); it is a compressed,
paper-facing view of both, organised the way a supervisor conversation will actually go.

Status key: **KEPT** = unchanged in substance. **CHANGED** = same topic, different content, with reason.
**ADDED** = new in the paper, not in the proposal/Assignment 1. **DROPPED** = planned or claimed in the
submitted reports, not in the paper.

---

## 1. Scope and research questions

| Item | Submitted (Assignment 2) | Paper draft | Status | Reason |
|---|---|---|---|---|
| Title | "Policy-Aware Orchestration Framework for Enterprise LLM Multi-Agent Workflows" | "Policy-Aware Orchestration with Static Blast-Radius Bounds for Multi-Agent Large Language Model Workflows" | CHANGED | The static blast-radius bound (RQ5) did not exist at proposal time; it is now the paper's most defensible novel contribution, so the title foregrounds it. The proposal's own title remains available as a fallback if the supervisor judges RQ5 too large a departure for the title. |
| RQ1-RQ4 | As written in Assignment 2 §4 | Reproduced with identical meaning | KEPT | No reason to change; the approved scope is still the scope that was executed. |
| RQ5 | Not present | "Can the effects of compromised agents be bounded soundly before deployment?" | ADDED | The four-control integration (RQ1-RQ4's object of study) was independently published by two other groups in September 2026 (see §3 below), which removed it as a novelty claim. RQ5 and the static analysis behind it is what remains as a defensible original contribution, and it is explicitly labelled in the paper as beyond the approved proposal, not folded in silently. |
| Aim | As written in Assignment 2 §5.1 | Reproduced with identical meaning, extended to mention cross-model generalisation | KEPT (extended) | Same aim; the paper adds the question of whether the finding is model-specific, which the proposal could not have anticipated needing before any evaluation ran. |
| Objectives O1-O4 | As written | Reproduced; O5 implied by RQ5 but not separately numbered in the current draft | KEPT, minor gap | The draft states RQ5 but does not yet add a matching O5 line to a Table 1-style RQ/objective/evidence table. Fix before submission: add O5 explicitly to Appendix Table 2. |

## 2. Baselines, framework and conditions

| Item | Submitted | Paper draft | Status | Reason |
|---|---|---|---|---|
| B1 / B2 / P definitions | Assignment 2 §8.2 | Identical in meaning | KEPT | Core experimental design unchanged. |
| GPLUS | Not in Assignment 2 | Added as an explicit fourth condition (P + provenance guard + re-dispatch) | ADDED | Needed to isolate the provenance guard's effect from the gate's effect under assumed compromise (RQ4); without it, Section 4.3's finding that the gate alone cannot stop K3 would not be attributable to a specific mechanism. |
| Six ablations (GPLUS minus one mechanism each) | Not in Assignment 2 | Added | ADDED | Required to attribute containment to a specific mechanism rather than to "the framework" as a bundle; this is what lets the paper say the provenance guard, specifically, depends on the gate underneath it. |
| Comparison with real CrewAI, LangGraph, AutoGen code | An earlier internal README (not the submitted proposal) implied this had been done | Explicitly stated as never executed; the structural-pattern study (§4.4) is labelled as not an execution of any external framework's code | DROPPED (claim), ADDED (honest replacement) | The claim was never true and was never in the approved proposal either; it existed only in an interim engineering document that this project's own audit (`docs/submission-alignment.md` A1, A21, A27) flagged and withdrew before any paper text was written. The paper never repeats it. |
| Policy gate "Euclidean projection over the action tuple" | Assignment 2 Appendix B, item 4 | Corrected to interval projection for numeric arguments and subset projection for column lists | CHANGED | The appendix's formula described an idealised mechanism that was never implemented this way; the paper reports the mechanism that was actually built and tested (deviation A10 in `docs/submission-alignment.md`). |
| Hand-off serialisation "RFC 8785" / "canonical JSON" | Assignment 2 Appendix B, item 3 implies RFC 8785 | Corrected to canonical JSON over a restricted value domain, RFC 8785 not claimed | CHANGED | Accuracy correction; the implementation never claimed full RFC 8785 conformance (deviation A11). |
| Routing regret guarantee | Appendix B implies a closed-form guarantee for the UCB routing algorithm | No closed-form guarantee claimed for the deployed system; regret is studied only in a separate Bernoulli-agent simulation, reported as simulation | DROPPED (claim), CHANGED (what is reported) | The closed-form regret bound is a property of the underlying bandit algorithm in isolation, not of the deployed multi-agent system with LLM agents, which do not satisfy the algorithm's assumptions. The paper reports simulation results and labels them as simulation (deviation A15). |

## 3. Novelty claim

| Item | Submitted | Paper draft | Status | Reason |
|---|---|---|---|---|
| "No study was identified that experimentally integrates and evaluates all four controls" | Assignment 2 §7, flagged in the proposal itself as "to be revalidated during the final systematic literature review" | Not repeated. The paper states the four-control integration was independently published in September 2026 (Paul and Nandy, 2026; Safin et al., 2026) and presents the artefact as a design science contribution, not a novel integration | CHANGED | This is exactly the revalidation the proposal itself called for, and it came back negative for novelty. Repeating the original claim in the paper would be a false statement the author already has evidence against; the proposal anticipated this exact possibility and asked for the check, so acting on the check's result is not a deviation from the research plan, it is the plan completing itself. |
| Static blast-radius bound as a contribution | Not present (RQ5 did not exist) | Presented as an extension of three concurrent 2026 preprints (Parisel; Muruaga; Moon and Varshney), not as a first | ADDED, with a specific framing constraint | A systematic review (`docs/lit-review/literature-review.md` §5.5, §7) found genuine partial overlap with all three works, each published within months of this project's own development of the bound. Overclaiming this as "first" would be the kind of fabricated-novelty claim this project's own integrity rule (`pref.scientific_integrity`) forbids, and a reviewer who finds any of the three preprints would read an unqualified "first" claim as either careless or dishonest. |
| K1-K4 assumed-compromise design | Not present (the proposal's RQ4 plan was "simulated perturbation" of inputs, not agent compromise) | Presented as a three-model-family replication of a design shared with Muruaga (2026) and Safin et al. (2026), not as an original evaluation design | ADDED, with the same honesty framing | The assumed-compromise suite itself (ground-truth attacker call replacing an agent's first proposal) was built independently of these two papers, which appeared later in 2026, but the systematic review found the same design in both, so the paper does not claim the design itself as novel. What is retained as a genuine contribution is the three-model-family replication, which neither of those two papers reports. |

## 4. Evaluation scale and models

| Item | Submitted | Paper draft | Status | Reason |
|---|---|---|---|---|
| Model | "selected LLM service or local model" (Assignment 2 §9, deliberately unspecified) | Three named model families: DeepSeek (`deepseek-flash`, requested as `deepseek-chat`), Google `gemini-3.5-flash-lite`, and Groq-served `openai/gpt-oss-120b`, each with exact settings and dates | CHANGED (specified), ADDED (two extra families) | The proposal deliberately left this open pending availability. One model family was flagged in this project's own limitations document as an external-validity threat before the paper was drafted; two more families were added specifically to answer that threat, which is RQ3/RQ4's generalisation rather than a new question. |
| Run counts | 270 main-suite runs + 12 robustness cases = 294 planned formal runs, one model | 360-run main suite and compromised/adversarial suites on DeepSeek (protocol v1-v4), plus 248 and 166 main-suite runs and 46 and 38 compromised-suite runs on Gemini and Groq respectively (protocol v5, reduced to 2 reps/cell on the two added models) | CHANGED | The DeepSeek-only run counts already exceeded the proposal's 294-run plan because the formal protocol used 18 tasks x 4 conditions x 5 reps = 360 for the main suite alone, before the two added model families existed. The two added families use fewer repetitions per cell (2, not 5) than DeepSeek, a disclosed trade-off made for free-tier quota reasons, not a quality shortcut applied selectively. |
| Repetitions | 5 reps per condition, all suites | 5 reps for DeepSeek (protocol v1-v4); 2 reps for Gemini and Groq (protocol v5) | CHANGED | Free-tier daily and per-minute quotas on both added providers could not support 5 reps of a 360-run suite inside the project timeline; disclosed in the paper's Methods (§3.5, §3.8) with the exact reduced count, not silently run at a smaller scale and reported as if it were the planned size. |
| Semantic scoring | Two blinded human assessors, stratified 20% sample, Cohen's kappa | Deterministic substring/field checks only; no human assessors | CHANGED | No ethics approval for human assessors was in place when the formal runs executed. This remains an open item (not resolved) rather than a silent substitution: the paper's limitations section states plainly that the originally planned kappa measure did not run, and a 20% sample is held in case a future assessor (the supervisor, or another approved rater) wants to score it. |
| Resumed/pruned failed runs | Proposal's evaluation design implies every run stands as recorded, nothing re-run | Protocol v5 explicitly re-runs failed attempts, but only those with zero model calls (pure infrastructure rejection before the model saw the request); a model-generated failure is never re-run | CHANGED, with a narrow and disclosed rule | This is the one place the project's own frozen "nothing is re-run" rule needed an exception, because two free-tier providers can reject a request before the model ever runs, which is a different failure class from a model producing a bad output. The paper's Methods section (§3.8) states the exact rule and the exact count of pruned rows per model and suite, specifically so a reviewer can tell this apart from result-shopping. |

## 5. Literature review

| Item | Submitted | Paper draft / review | Status | Reason |
|---|---|---|---|---|
| Databases searched | Assignment 2 §8.1: ACM Digital Library, IEEE Xplore, Scopus, ACL Anthology, Google Scholar, 2022-2026 | OpenAlex, arXiv, Semantic Scholar (open APIs); DBLP attempted and blocked | CHANGED | Subscription databases have no reproducible open query API suited to a PRISMA-documented, scriptable search; the substitute sources are disclosed by name in the Methods section rather than silently presented as if the originally named databases were searched. |
| Review scale and method | Assignment 1: narrative review of 16 sources across three themes | Systematic review, PRISMA 2020, 3,600 records retrieved, 721 included after screening and snowballing, five themes | CHANGED | A full systematic review was undertaken as part of closing item A22 in the submission-alignment log, well beyond Assignment 1's narrative scope; Related Work in the paper is rebuilt from this review rather than reused from Assignment 1's text, which also avoids any similarity match against a document already in APU's Turnitin index. |
| Framework comparison tables (CrewAI, LangGraph, AutoGen, OpenAI Agents, Microsoft Agent Framework) | Assignment 1 Tables 1-2 | Cited only as structural patterns informing the nineteen-configuration study (§4.4), not as empirical evidence | CHANGED | Assignment 1's tables are literature-based judgements, not measurements; no study in the systematic review ran these frameworks under this project's own protocol, so the paper does not present Assignment 1's tables as if they were measured results. |
| Kaufmann et al. (2012) authors | "Kaufmann, Korda & Munos" | Corrected to "Kaufmann, Cappé & Garivier" | CHANGED | The AISTATS 2012 Bayesian-UCB paper's actual authors are Kaufmann, Cappé and Garivier; Korda and Munos co-authored a different 2012 Kaufmann paper on Thompson sampling. Verified against the publisher page during the systematic review; this is a factual correction, not a stylistic one. |
| "No study integrates all four controls" (literature claim, Assignment 1 framing) | Implicit in Assignment 1's gap statements (decoupled runtime policy layer, adaptive allocation under uncertainty, structural intent-preserving protocols, a formally verifiable integrated system) | Each of these four stated gaps is now reported as substantially populated by 2025-2026 work found in the systematic review | CHANGED | Same underlying issue as §3 above: the gaps Assignment 1 identified in 2026 have since been addressed by other groups' 2025-2026 publications. The paper states this plainly rather than repeating gap language that no longer holds. |

## 6. What stayed exactly the same

- The unit of analysis: the orchestration framework, not any one model's intelligence.
- The use of design science research (Hevner et al., 2004; Peffers et al., 2007) as the methodology.
- The core measures: task success, intent fidelity, violation rate, trace completeness, time, cost.
- The practical-significance threshold (10 percentage points, or 50% fewer violations, within 30% extra time), even though no condition meets it on the main suite.
- The ethics position: synthetic or public data only, no human participants, no personal data.
- The explicit refusal to claim universal security, carried from the proposal's abstract into the paper's own abstract and conclusion.

## 7. Items still open, not yet resolved in either direction

1. Second-screener inter-rater kappa for the systematic review (A5 in the literature review's own open-items list). Candidate rater: the supervisor, per the user's own suggestion in this project's working thread.
2. Nineteen venue DOIs and one missing author list in `references-final.bib`, before the References section of the paper draft can be generated from it.
3. A similarity check against Turnitin/iThenticate has not yet been run on the paper draft; both submitted assignments are already in APU's repository, so this is a required check, not an optional one.
4. Author list, order, and target venue need the supervisor's confirmation (plan gate G6); the paper draft currently lists only the student and the supervisor as placeholders.
