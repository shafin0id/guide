# GUIDE paper plan: systematic literature review + manuscript writing

Status: plan only. Written 2026-10-01 on branch `research/evidence-based-rebuild`.
Audience: the author, and any AI tool helping to draft. Every instruction below is binding unless the
author overrides it in writing in this file.

---

## 0. Ground rules (read before any step)

### 0.1 Sources of truth, in priority order
1. `previously submitted to university/RMCE - Assignment 2 (Proposal).docx` (approved scope: title, aim,
   RQ1–RQ4, O1–O4, B1/B2/P, metrics, DSR method). Never edit. Never contradict silently.
2. `previously submitted to university/RMCE - Assignment 1 (Liturature Review).docx` (prior themes:
   orchestration, semantic drift, governance). Never edit.
3. `docs/submission-alignment.md` (A1–A28): every place the delivered work differs from the proposal.
   **Each deviation that touches the paper must be stated in the paper** (Section 3.8 / Table 9 below).
4. `docs/experiments.md`, `docs/evaluation.md`, `docs/limitations.md`, `docs/novelty.md`,
   `docs/formal_model.md`, `docs/architecture.md`, `docs/adr/0005-multi-model-evaluation.md`.
5. Raw data: `experiments/results/**/results.jsonl`, `manifest.json`, `summary.md`.
6. Supervisor guidance: `supporting documents from supervisor/` (template + 3 PDFs). Format and section
   logic come from here.

If two sources disagree, the higher one wins and the conflict is logged in §9 of this file.

### 0.2 Integrity rules (non-negotiable)
- No number enters the manuscript unless it is reproduced by a script from a results file. Each table and
  figure records the script, input path and git commit in a comment in the LaTeX/Word source.
- No reference enters the manuscript unless its DOI/URL was opened and the title, authors, year and venue
  were checked against the publisher page. AI-suggested references are treated as unverified until then.
  A fabricated or wrong citation is a desk-reject offence; zero tolerance.
- Negative and null results stay in (H-RQ3a not supported, injection resistance not measurable,
  heuristic provenance guard bypassable). They are part of the contribution.
- Novelty is stated exactly as `docs/novelty.md` and A22/A23 allow: the four-control integration is
  **not** novel (independently published Sept 2026, arXiv:2609.22949; containment finding also in
  arXiv:2609.17648 — both re-verified in the review: ICML 2026 AIWILD workshop and IEEE CARS 2026). The
  systematic review (`docs/lit-review/literature-review.md` §5.5, §7) found **partial overlap** for the
  blast-radius bound (Parisel 2026, arXiv:2607.09744; Muruaga 2026, arXiv:2608.15888; Moon & Varshney
  2026, arXiv:2605.09045). C3 is therefore stated as an extension of those works, never as "first".
- No claim that GUIDE was compared with real CrewAI/LangGraph/AutoGen code (A1, A21, A27). Those names
  appear only as cited structural patterns.

### 0.3 Originality, similarity and AI use
- Similarity target (Turnitin/iThenticate, excluding the reference list only): overall < 10 %, no single
  source > 1 %. Assignments 1 and 2 are already in the APU Turnitin repository, so **any sentence copied
  from them will match**. Rule: no sentence is copied from either assignment; ideas carry over, wording is
  new. Re-draw Figure 2 of the proposal rather than reusing the image.
- The supervisor's prompt starters (doc 6) are sentence *patterns*, used verbatim by many students.
  Adapt them; never paste them unchanged.
- AI-detection scores: this plan deliberately contains **no techniques for disguising AI-generated text
  or defeating detectors**. Detectors are unreliable, and the real requirement from APU and from Q1/Q2
  publishers (Elsevier, Springer, IEEE, ACM) is disclosure plus author accountability. The workflow is:
  AI tools may build outlines, check consistency, suggest structure and proof-read; the author writes or
  substantively rewrites every paragraph in their own voice, checks every claim against the data, and
  declares AI assistance in the statement the target journal requires (Section 5, item S6). Confirm the
  APU MSc policy on generative-AI use with the supervisor before drafting.
- Good human academic style (also what reviewers reward): one idea per paragraph; concrete nouns and
  numbers instead of generic claims; sentence length that follows the content; first-person plural
  ("we measured") where the journal allows it; no stock filler ("in today's rapidly evolving landscape",
  "delve", "pivotal", "seamlessly", "it is worth noting", "a testament to"); no triple-adjective lists;
  no summary sentence repeating the paragraph; hedge only where the evidence is actually uncertain.

### 0.4 What this plan cannot promise
Acceptance without revision is not something any plan can guarantee; editors almost always ask for at
least minor revision. The plan minimises reviewer objections by closing every known gap in advance (§6).

---

## Part A — Systematic literature review: DONE (2026-10-01)

Completed and removed from this plan. Everything is in `docs/lit-review/literature-review.md`
(method, PRISMA numbers, synthesis, Table 1 draft, novelty decision, reference checks, and the
differences from the submitted reports); protocol in `docs/lit-review/protocol.md` (tag
`review-protocol-v1`). Outcome used below: **L4 = partial overlap** — C3 is worded "extends Parisel
(2026), Muruaga (2026) and Moon & Varshney (2026) by …", not "first". Open review items (second
screener kappa, n/c cells of Table 1, unverified venues) are listed in §11 of that file and must close
before submission.

---

## Part B — Manuscript plan

### B0. Pre-writing gates (all must be ticked)
- [ ] G1 Data freeze: v5 main (144 target, 2 reps) and v5 compromised (32 target) both complete for
      both added models; completed-row counts verified with `status == "completed"` filtered to rep ≤ 2,
      never by line count. Tag `data-freeze-v5`.
- [ ] G2 Fix stale records: A28 and `docs/adr/0005-multi-model-evaluation.md` still name
      `qwen/qwen3.8-27b` for Groq; the runs used `openai/gpt-oss-120b` after Qwen's 200k tokens/day cap
      was exhausted. Record: the 32 Qwen main-suite completions in
      `v5-main-groq-qwen.abandoned-qwen-tpd-exhausted/` are excluded and reported as excluded.
- [ ] G3 Disclose a protocol deviation in v5: `docs/evaluation.md` §5 says provider errors count as run
      failures and nothing is re-run. In v5, rows that failed with provider HTTP 429/transport errors and
      `model_calls == 0` were pruned and re-run. Report: the rule applied (only infrastructure failures with
      zero model calls, never a completed run with a bad outcome), the count of re-run rows per model and
      suite, and a sensitivity table computed with those rows counted as failures. Also disclose the
      reduction from 5 to 2 repetitions, the Gemini seed omission, the flagship-model quota substitution,
      and that runs were spread over several days and API credentials.
- [ ] G4 Aggregation script `scripts/paper/aggregate.py` writes every number used in the paper to
      `docs/paper/numbers.json`; every figure script reads only from that file or raw results.
- [x] G5 Literature-review novelty decision recorded: partial overlap (`docs/lit-review/literature-review.md` §7).
- [ ] G6 Supervisor confirms: target venue, author list/order, AI-use policy, whether a separate
      Related Work section is acceptable in the template.

### B1. Paper identity
- Type: problem–solution paper (supervisor doc 1) in IMRAD form (doc 2), Design Science Research
  (Hevner 2004; Peffers 2007) as in the proposal.
- Title options (≤ 12 words, no abbreviations, no verbs, topic first; picked with the §7 wording of the review in mind):
  1. "Policy-Aware Orchestration with Static Blast-Radius Bounds for Multi-Agent Language Model Workflows"
  2. "Containing Compromised Agents in Policy-Governed Large Language Model Workflows" (if C3 downgraded)
  3. "Policy-Aware Orchestration Framework for Enterprise Multi-Agent Language Model Workflows"
     (closest to the proposal title; safe fallback)
- Keywords (≤ 6, none repeating title words; finalise after title): agentic AI security; prompt
  injection; least privilege; information flow control; design science research; tool authorisation.
- Contributions (state in Introduction, last paragraph before aim; numbered, each tied to evidence):
  - C1 Artefact: an open-source runtime integrating evidence-based routing, signed hash-linked
    hand-offs, an external allow/bound/deny policy gate and a linked trace (RQ1, RQ2). Framed as a DSR
    artefact, **not** as a novel integration (A22).
  - C2 Evaluation: pre-registered, condition-blind comparison against fixed-role and static-graph
    baselines across three model families, with ablations under assumed compromise (RQ3, RQ4).
  - C3 Analysis (extends Parisel 2026, Muruaga 2026, Moon & Varshney 2026 — review §7): a static, compromise-parametric blast-radius bound with a soundness
    argument, least-privilege synthesis, and a 19-configuration structural study (RQ5 extension).
  - C4 Honest negative results: nominal ceiling/null result; textual injection resistance not
    measurable with capable models; heuristic provenance guard bypassable.
- Research questions: keep RQ1–RQ4 **verbatim in meaning** from the proposal; add RQ5 labelled as an
  extension beyond the approved proposal (A23): "Can the effects of compromised agents be bounded soundly
  before deployment?" Objectives O1–O4 as in the proposal, plus O5 for RQ5.
- Hypotheses: H-RQ3a/b/c, H1–H4 exactly as frozen in `docs/evaluation.md` §4 (state that they were
  frozen in git tag `protocol-v1` before runs; v2 amendment D1–D3 disclosed as post-hoc).

### B2. Target venue and length
- Primary format: supervisor's `MKA Papers Writing Template.docm` (sections: Title, Authors and APU
  affiliation, Abstract, Keywords, Introduction, Materials and Methods, Results and Discussion,
  Acknowledgments, References). The template's abstract split is 15 % objectives / 20 % methodology /
  50 % results / 15 % conclusion.
- Journal candidates (check current scope, SJR quartile, APC and AI policy on the journal site and
  scimagojr.com at submission time; quartiles change yearly): Computers & Security; Journal of Systems
  and Software; Information and Software Technology; IEEE Access; Expert Systems with Applications;
  ACM Transactions on Privacy and Security (stretch). After choosing, re-format to the journal's Guide
  for Authors; journal rules override the template where they conflict.
- Length target: 8,000–10,000 words main text (journal) or the venue's page limit; 7–9 figures;
  8–10 tables; appendices/supplement for proofs, task list, full per-task tables.
- Reference style: APA 7 as in both submitted reports, managed in Zotero/BibTeX so the style can be
  switched to the journal's style automatically.

### B3. Section-by-section plan
Word budgets assume ~9,000 words. Tenses follow supervisor doc 2: present for established knowledge and
interpretation, past for methods and results.

#### §0 Title, authors, abstract, keywords (write LAST)
- Authors: Shafin Ahmad (first, corresponding); Ts. Dr. Maythem K. Abbas (supervisor) and others only as
  agreed (G6). Affiliation exactly as the template: Asia Pacific University of Technology and Innovation,
  Technology Park Malaysia, Bukit Jalil, 57000 Kuala Lumpur, Malaysia.
- Abstract: 200–250 words, one paragraph, no citations, no figure/table references, no undefined
  acronyms (spell out "large language model"; avoid "GUIDE" unless defined), no "will be presented".
  Sentence plan (≈ word count): background + problem (35) → objective (25) → method: DSR artefact,
  four conditions, three model families, assumed-compromise suite, static bound (50) → results (110):
  null nominal result with low overhead; containment attributed to gate/provenance/signing; bound
  exactness and least-privilege reduction; cross-model consistency or divergence → conclusion and
  implication (30). Supervisor doc 2 advises few numbers; Q1 abstracts expect some. Compromise: at most
  three headline numbers, each reproduced from `numbers.json`.

#### §1 Introduction (≈ 900 words; supervisor suggests ~500, Q1 venues accept up to ~1,000; 4–5 paragraphs)
1. Topic and significance: enterprise multi-step work delegated across LLM agents; each hand-off is a
   point where a constraint can be lost or an action can be unauthorised. 2–4 recent citations.
2. Problem: a plausible final answer does not show that constraints survived or that tool actions
   followed policy; illustrate with one concrete example (procurement "do not disclose supplier
   pricing"), rewritten from the proposal, not copied.
3. Gap (from the review synthesis, `docs/lit-review/literature-review.md` §5): controls studied separately; containment measured by attacking running
   systems; no pre-deployment, compromise-parametric bound tied to the runtime (worded as the
   review's §5.5 gap). Mention the Sept 2026 independent integration work honestly here.
4. Contributions C1–C4 as a numbered list.
5. Aim, objectives, RQs (template: last paragraph = aim and objectives). Optional one-sentence roadmap.
- Must not: repeat the abstract; claim universal security; claim comparison with framework code.

#### §2 Related Work (≈ 1,300 words) — placed between Introduction and Methods
(The MKA template has no explicit literature section; doc 6 treats literature as its own section.
Default: a separate §2; if the supervisor prefers, merge into §1 as sub-sections. Decide in G6.)
- 2.1 Orchestration, routing and delegation (static roles, graphs, adaptive/bandit routing).
- 2.2 Context and intent preservation across hand-offs (problem drift, hallucination cascades,
  structured state, provenance and signing).
- 2.3 Tool authorisation, prompt injection and information flow (prompt guardrails, privilege control,
  IFC, capability systems, confused-deputy attacks).
- 2.4 Evaluation of agent security and policy compliance (AgentDojo, InjecAgent, τ-bench, WebArena,
  MCP-AgentBench) and why this paper uses its own task suite (A14) with standard benchmarks as future
  work.
- 2.5 Static analysis and pre-deployment bounds (Zelkova as method family; Least Autonomy, Bounded Agents, Containment Verification, CaMeLoT, AgentFlow, Agent Audit, MiniScope, Aethelgard — review §5.5).
- Table 1 related-work matrix; each subsection ends with a one-line gap; the last paragraph synthesises
  the gaps into RQ1–RQ5. Compare and critique (doc 6 §4.2–4.4), never list papers one by one.

#### §3 Materials and Methods (≈ 2,300 words)
- 3.1 Research design: DSR (Peffers 2007 six activities mapped to this study in one short table or
  Figure 2). State the unit of analysis is the framework, not the model.
- 3.2 Artefact: architecture (Figure 1), the four controls plus provenance guard, re-dispatch, DAG
  scheduler (A13). Give precise mechanism definitions: Bayes-UCB routing (Beta posterior, quantile
  1 − 1/t); hash chain h_k = SHA-256(h_{k−1} ‖ canonical(P_k)) with Ed25519 per-principal keys;
  canonical JSON over a restricted value domain (**not** RFC 8785, A11); gate = allow/bound/deny where
  bounding is interval projection for numeric args and subset projection for columns (**not** Euclidean
  projection over the action tuple, A10, A15); in-process gate (novelty.md §3). Note these corrections
  relative to the proposal Appendix B explicitly in Table 9.
- 3.3 Conditions: B1, B2, P, GPLUS (+ ablations) as configurations of one runtime (ADR-0004); Table 3.
- 3.4 Tasks and suites: 18 tasks (3 families × LOW/MEDIUM/HIGH × 2; 4/6/8 atomic constraints), main,
  adversarial A01–A11, assumed-compromise K1–K4, sequence A12, integrity, routing simulation, pilot
  (excluded). Table 4. Explain why the threat model was extended to assumed compromise (A20: textual
  injections produced zero attack attempts).
- 3.5 Models and settings: DeepSeek (requested `deepseek-chat`, reported id as logged, A16) protocol
  v1–v4; protocol v5 adds `openai/gpt-oss-120b` via Groq and `gemini-3.5-flash-lite` via Google AI
  Studio's OpenAI-compatible endpoint; temperature 0, JSON mode, 4,096 max tokens, seed 42 except Gemini
  (seed rejected, disclosed). Why these: free-tier availability, different families; why not others
  (gpt-oss-20b rejected by Groq's tool-call guardrail on prompted JSON; flagship Gemini 20 requests/day).
  Report provider nondeterminism at temperature 0.
- 3.6 Metrics: Table 5 (from `docs/evaluation.md` §3): task success, intent fidelity, violation, ASR,
  trace completeness, integrity detection, cost, time. State scoring is deterministic and condition-blind
  (regression-tested) and that the two-assessor kappa of the proposal was replaced (A7) with reason.
- 3.7 Static blast-radius analysis: definitions, theorem statement, proof sketch (full proof in
  appendix, from `docs/formal_model.md`), least-privilege synthesis, validation procedure (offline over
  all recorded runs, live adaptive attacker), real-world structural configuration study (19 configs,
  hand-authored patterns, A27 scope note verbatim in meaning).
- 3.8 Protocol, statistics and deviations: frozen tags (`protocol-v1` … v5, commit hashes), randomised
  order seed 2026, cluster bootstrap over tasks (10,000 resamples, seed 7), task-level paired Wilcoxon
  signed-rank (Pratt, two-sided) with Holm correction per metric family, "uninformative" rule when nearly
  all differences are zero, practical-significance criterion (≥ 10 pp, ≥ 50 % fewer violations, ≤ 30 %
  time). For v5 with 2 reps: report CIs and effect sizes first, tests second, and state the reduced power.
  Table 9 lists every deviation (A-numbers) with reason and effect.
- 3.9 Ethics and data: synthetic/public data, no participants, sandbox with allow-listed tools, no
  credentials in artefact. Data and code availability statement with archived DOI (Zenodo) of the tagged
  release.

#### §4 Results (≈ 2,000 words; objective, no interpretation — doc 6 §6)
Order mirrors RQs. Every paragraph cites a table/figure number; text highlights only key findings.
- 4.1 RQ1/RQ2 artefact demonstration: requirement catalogue → component mapping (Table 2 alignment:
  RQ–objective–evidence, rewritten from proposal Table 1); unit/integration test count and coverage.
- 4.2 RQ3 nominal performance per model (Table 6, Figure 4): success, fidelity, violations, trace
  completeness per condition × model with 95 % CI; Wilcoxon/Holm; practical-significance verdict.
  Overhead (Figure 7): time and tokens; framework-only time (~1.5 ms).
- 4.3 RQ4 robustness: adversarial A01–A11 (injection attempts count, outcomes), integrity suite
  (100 % detection, 0 false rejections; spoofing 0 → 100 % with per-principal keys), assumed-compromise
  K1–K4 per condition × model (Table 7, Figure 5), sequence A12 (Figure 8: static 0/20, routing 19/20,
  both 20/20), routing simulation (supplement).
- 4.4 RQ5 blast radius: offline soundness over all recorded runs (0 violations of the bound), exactness
  39/39 under adaptive attack, least-privilege reduction with utility retained, findings F1–F4
  (substring provenance admits 692 recipients, realised 3/3), real-world study (94.7 % single-node
  reachability; 55.6 % sink-capability reduction, 0 nominal calls denied) (Figure 6, Table 8).
- 4.5 Cross-model comparison: does each DeepSeek finding replicate on the two added families? A
  three-column replicate / partially / not table. Report Gemini/gpt-oss failures by category (model
  quality vs provider error), separately.
- Numbers above are from the current docs; **re-derive all of them from `numbers.json` before use.**

#### §5 Discussion (≈ 1,500 words; doc 6: interpretation → explanation → comparison → implications → limitations)
- Why the nominal null result: ceiling with capable models; controls cannot raise success that is
  already near 1; the value of controls lies under compromise. Compare with literature that reports
  gains (explain different threat models).
- Why containment worked where it did, and where it needed the provenance guard (in-domain sink
  steering); dependence of the guard on the gate.
- What the bound adds over run-time measurement: pre-deployment guarantees, finding bugs testing missed.
- Cross-model: what changed with weaker/free models (HIGH-tier failures, guardrail behaviour) and what
  that means for model-invariance of the controls.
- Practical implications for practitioners (least-privilege policies from nominal traces; per-principal
  keys; fail-closed halts cost task success but not safety).
- Limitations / threats to validity (from `docs/limitations.md`): synthetic researcher-authored tasks;
  deterministic substring scoring; single-reviewer screening; free-tier models and 2 reps in v5;
  provider nondeterminism; in-process gate; heuristic provenance guard; structural (not executed) external
  framework study; no standard benchmarks yet; no human assessors.
- Do not repeat results numbers; do not introduce new data.

#### §6 Conclusion (≈ 350 words)
Summary → findings per RQ (one sentence each) → contribution summary → limitations (one sentence) →
future work: AgentDojo/τ-bench adapters, more model families incl. a small model, human assessors,
executing real frameworks, out-of-process gate, adaptive textual attacks. No "more research is needed"
without saying what research.

#### Back matter
- Acknowledgments (template): supervisor, lecturer (Dr R. Logeswaran) if appropriate, API providers'
  free tiers if no funding. Funding statement: none, unless stated.
- Statements most Q1/Q2 journals require: S1 data availability; S2 code availability (DOI);
  S3 CRediT author contributions; S4 competing interests; S5 ethics (no human participants);
  S6 generative-AI use declaration (tools, purpose, author responsibility).
- References: only works cited in text, every one verified (L3).
- Appendices/supplement: A proof of the soundness theorem; B full task list with constraints;
  C per-task tables for all suites and models; D policy files; E search strings and PRISMA counts;
  F reproduction commands (from `docs/experiments.md`).

### B4. Figures and tables
Common style for all figures: vector PDF/SVG (raster ≥ 600 dpi for line art, ≥ 300 dpi otherwise);
width 85 mm (single column) or 175 mm (double); sans-serif font ≥ 8 pt after scaling; Okabe–Ito
colour-blind-safe palette with a **fixed colour per condition** (B1 orange, B2 sky blue, P bluish green,
GPLUS vermillion, ablations grey shades) and fixed marker per model (DeepSeek ●, gpt-oss ▲, Gemini ■);
readable in greyscale; no chart junk, no 3-D, no titles inside the image (caption carries it); axes
labelled with units; CIs drawn as error bars and stated in the caption. Each generated by a script in
`scripts/paper/figures/` from `numbers.json`; captions self-contained (what, n, error bars, source).
Do not show the same data in a table and a figure (doc 2).

| # | Section | Content | Form and look |
|---|---|---|---|
| Fig 1 | §3.2 | Architecture and data flow: principal → router → agents; signed hand-off packages with hash chain; policy gate between agent proposal and tool; provenance guard; trace ledger receiving events from every step | Block diagram, left-to-right; controls as rounded boxes in one accent colour; untrusted inputs (tool results, retrieved text) with a dashed red border; trust boundary as a dashed line; numbered arrows matching text. Newly drawn (draw.io or TikZ), not the proposal image |
| Fig 2 | §3.1 | DSR activities (Peffers) mapped to this study's artefacts and protocol tags | Horizontal 6-step process with artefact names under each step and git tags; compact, 85 mm |
| Fig 3 | §3.4 | Threat model: assumed compromise of one agent (K1–K4), what the attacker controls, sinks (external e-mail, restricted columns, destructive write, in-domain recipient) and which control sits on each path | Attack-path diagram; compromised agent in red; each path annotated with the control that blocks it |
| Fig 4 | §4.2 | Task success and intent fidelity by condition, per model | Two-panel dot-and-whisker (mean, 95 % cluster-bootstrap CI), x = condition, colour = condition, panel row = model; y from 0 to 1 |
| Fig 5 | §4.3 | Containment under assumed compromise | Heatmap: rows = conditions (incl. ablations where run), columns = K1–K4, facets = models; cell = violation rate with n printed; sequential palette (white → dark), annotated values |
| Fig 6 | §4.4 | Blast radius: predicted vs realised effects, and least-privilege reduction | Left: scatter or paired bars predicted vs realised (diagonal reference); right: stacked bars of sink capabilities before/after synthesis per configuration domain |
| Fig 7 | §4.2 | Overhead | Box plots (log y) of wall time and total tokens per run by condition, per model; median labelled |
| Fig 8 | §4.3 | Degraded-agent sequence A12 | Step plot of cumulative completed runs over 20 runs for static, routing, re-dispatch, both |
| Fig S1 | Suppl. | PRISMA 2020 flow diagram | Standard PRISMA template boxes with counts |
| Fig S2 | Suppl. | Routing simulation regret (stationary, drift) | Line plot, mean ± CI over 200 seeds |

| # | Section | Content |
|---|---|---|
| Tab 1 | §2 | Related-work matrix (draft in review §6) |
| Tab 2 | §1/§4.1 | RQ–objective–evidence alignment (RQ1–RQ5, O1–O5) |
| Tab 3 | §3.3 | Conditions and which controls each enables |
| Tab 4 | §3.4 | Suites: purpose, tasks/cases, conditions, reps, runs, per model |
| Tab 5 | §3.6 | Metrics: definition, source, preferred direction |
| Tab 6 | §4.2 | Main-suite results per condition × model (mean, 95 % CI) with Holm-adjusted p and effect size |
| Tab 7 | §4.3 | Assumed-compromise and integrity results |
| Tab 8 | §4.4 | Blast-radius validation and analysis findings F1–F4 |
| Tab 9 | §3.8 | Deviations from the approved proposal and from the frozen protocol (A-numbers, reason, effect, where reported) |
| Tab 10 | §4.5/§5 | Hypothesis verdicts across models (supported / not / not testable) |

### B5. Drafting order and procedure
1. Methods (§3) → Results (§4) → Discussion (§5) → Related Work (§2) → Introduction (§1) →
   Conclusion (§6) → Abstract, title, keywords (doc 2: write these last).
2. For each section: outline from this plan → author draft → numbers check against `numbers.json` →
   citation check against `references-final.bib` (list + rules: `docs/references-final.md`; keep non-peer-reviewed ≤ 20 %) → consistency check against proposal/submission-alignment →
   language pass (author) → supervisor review.
3. Keep `docs/paper/claims.csv`: every factual claim in the manuscript, its section, and its evidence
   (file path, figure/table, or citation). Any claim without evidence is deleted.

---

## 5. Consistency checklist against the submitted reports (tick each)
- [ ] Aim and RQ1–RQ4 match the proposal in meaning; RQ5 is marked as an extension.
- [ ] B1/B2/P definitions match the proposal; GPLUS and ablations marked as extensions (A13, A18).
- [ ] Run counts: proposal planned 270 + 12 robustness = 294; the paper reports what was actually run
      (v1 360 main, 550 adversarial, …; v5 reduced) and explains the difference in Table 9.
- [ ] Proposal claim "no study was identified that integrates all four controls" is not repeated; the
      paper states it held at proposal time and was superseded in Sept 2026 (A22).
- [ ] Appendix B corrections (projection, canonicalisation, regret claims) disclosed (A10, A11, A15).
- [ ] Assignment 1's framework comparison table is not presented as empirical evidence; it is a cited
      review of structural limitations.
- [ ] Two-assessor kappa replaced by deterministic checks (A7) — disclosed.
- [ ] Model: proposal said "selected LLM service or local model"; paper lists exact models, ids,
      dates, and substitutions.
- [ ] Ethics: still no participants; if human assessors are added later, ethics approval first.

## 6. Pre-submission reviewer-proofing checklist
- Claims: every number reproducible from `numbers.json`; every claim in `claims.csv` has evidence;
  no overclaiming words ("prove", "guarantee", "secure") unless the soundness theorem's exact scope
  is stated next to them.
- Statistics: n per cell stated; CIs everywhere; multiple-comparison correction; effect sizes;
  uninformative tests labelled; no p-hacking (all pre-registered analyses reported).
- Reproducibility: tagged release, Zenodo DOI, `uv.lock`, exact commands, manifests with model ids,
  dates and settings; README section "Reproducing the paper".
- Threat model explicit and matches what was tested; limitations section not defensive but complete.
- Figures: legible at print size, colour-blind safe, numbered in order of first mention, all referenced.
- Tables: units, n, footnotes for abbreviations; no duplicated data with figures.
- Abbreviations: defined at first use in abstract (avoid) and in text; abbreviation table if the
  journal allows.
- Language: consistent British or American spelling (submissions used British: "authorised",
  "specialised" — keep British); consistent terminology (hand-off, policy gate, blast radius) via a
  glossary in `docs/paper/glossary.md`.
- Citations: every in-text citation in the list and vice versa (scripted check); DOIs present;
  preprints labelled; no citation of a paper for a claim it does not make.
- Similarity report run on the full draft; any match > 1 % rewritten; self-overlap with Assignments 1–2
  rewritten.
- Journal checklist: word/page limits, highlights (3–5 bullets, ≤ 85 characters each, if Elsevier),
  graphical abstract if requested, cover letter stating novelty and fit, suggested reviewers without
  conflicts, all required statements (S1–S6).

## 7. Timeline (fits proposal Table 4: report and submission Nov 2026 weeks 2–4)
| When | Work |
|---|---|
| Oct 2026 wk 1 | G1–G4; review protocol committed; searches run |
| Oct 2026 wk 2 | Review open items (kappa, Table 1 n/c cells, venues; review §11); supervisor check (G6) |
| Oct 2026 wk 3 | Figures/tables from scripts; draft §3–§4 |
| Oct 2026 wk 4 | Draft §5, §2, §1, §6, abstract; claims and citation checks |
| Nov 2026 wk 1 | Supervisor review; revision; similarity check |
| Nov 2026 wk 2 | Journal formatting, statements, cover letter, artefact DOI; submit |

## 8. Instructions for an AI tool executing this plan
- Work one section at a time; read the listed source files first; never invent data, results,
  citations, DOIs, quartiles or page numbers — write `[TODO: verify]` instead.
- Never copy sentences from `previously submitted to university/` or the supervisor documents.
- Output drafts as suggestions for the author to rewrite; mark every number with its `numbers.json` key.
- Stop and ask the author when a source conflict, a missing number, or a novelty question appears.

## 9. Conflict log (append as found)
| Date | Conflict | Resolution |
|---|---|---|
| 2026-10-01 | A28/ADR-0005 name Qwen for Groq; runs used gpt-oss-120b | Update both before drafting (G2) |
| 2026-10-01 | `evaluation.md` §5 "nothing re-run" vs v5 re-runs of zero-call provider errors | Disclose with counts and sensitivity analysis (G3) |
| 2026-10-01 | Template has no literature section; doc 6 has one | Separate §2 by default; supervisor decides (G6) |
| 2026-10-01 | Doc 2 advises few numbers in abstract; Q1 norm expects key numbers | ≤ 3 headline numbers |
| 2026-10-01 | Review: C3 novelty partially overlaps Parisel 2026 / Muruaga 2026 / Moon & Varshney 2026 | C3 worded as an extension (review §7) |
| 2026-10-01 | Review: K1–K4 compromised-model design shared with Muruaga 2026 and Safin 2026 | Present as replication across 3 model families |
| 2026-10-01 | Review: Assignment 2 lists Kaufmann, Korda & Munos (2012); actual authors Kaufmann, Cappé & Garivier | Use corrected reference (review §9) |
