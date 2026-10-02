# Systematic literature review — GUIDE (closes A22)

Search date: 2026-10-01. Protocol: `docs/lit-review/protocol.md` (frozen as git tag `review-protocol-v1`
before any search; amendments A1–A6 are dated and listed there). This file is the single summary of
the review: method, numbers, synthesis, the novelty decision, what changes in the paper, and how the
result differs from the two submitted reports. Every number below is reproduced by the scripts in
`docs/lit-review/scripts/` from the files in `docs/lit-review/data/`.

**Status of decisions.** Screening and coding were done by the author's AI assistant under the
protocol and must be confirmed by the author before the paper relies on them (protocol §7). The blind
second-screener check (§5.4) is still open (amendment A5).

---

## 1. Files

| File | Content |
|---|---|
| `protocol.md` | Review questions SQ1–SQ4, sources, strings S1–S6, eligibility I1–I3/E1–E6, procedure, novelty rule, amendments A1–A6 |
| `search-log.csv` | One row per string × source: date, exact query sent, hits reported, records retrieved |
| `screening.csv` | Every unique record (2,766 database + 615 snowball): decision, stage, reason code |
| `extraction.csv` | 721 included studies; keyword-assisted codes for all, hand codes for 26 core works |
| `must-check.csv` | 51 references from the plan's L3 list checked against Crossref / arXiv / OpenAlex, with venue status |
| `prisma.svg`, `prisma-counts.json` | PRISMA 2020 flow |
| `second-screener-sample.csv` | Seeded 20 % sample (342 records) for the inter-rater check; `scripts/kappa.py` scores it |
| `data/` | Raw API records, dedup/pre-filter output, screening batches, snowball candidates |
| `/references.bib` (repo root) | 81 entries generated from verified metadata; each `note` gives verification status |

Re-run order: `search.py` → `dedup_prefilter.py` → `snowball.py` → `snowball.py s2` →
`screening.py` → `extract.py` → `prisma.py` → `verify_refs.py` → `build_bib.py`. Searches return
different hits on a later date; the frozen record set is the one in `data/`.

## 2. Method actually executed (deviations from the plan are in bold)

- Sources: **OpenAlex, arXiv API, Semantic Scholar** (proposal: ACM DL, IEEE Xplore, Scopus, ACL
  Anthology, Google Scholar; plan: same + arXiv and security venues). Subscription databases have no open
  query API; OpenAlex ingests their metadata. **DBLP was planned as a third source but served a bot
  challenge and was replaced by Semantic Scholar (A1).**
- Six frozen strings × three sources, first 200 records each, 2022-01-01 to 2026-10-01.
- Deterministic pre-filter (LLM term AND agent term), audited twice on 100 random failures:
  round 1 found 4/100 false negatives ("AI agent"/"agentic" phrasing) → rule widened; round 2 found
  1/100 (an LLM-integrated-app RCE paper) → admitted by hand. **A recall check against the must-check
  list then found SafeFlow rejected; a rescue pass re-admitted 7 of 33 suspicious failures (A3).**
- Title screening of 1,712 records, abstract screening of 631.
- **Snowballing on a 43-work core set, not on all includes (A4).**
- **Second screener not yet run (A5); extraction keyword-assisted except for 26 core works (A6).**
- Quality appraisal (0–10, protocol §5.8) scored for the 26 core works only.

## 3. PRISMA numbers

| Stage | n | Excluded (reason codes) |
|---|---|---|
| Records identified (18 queries) | 3,600 | — |
| After de-duplication | 2,766 | 834 duplicates |
| Rule pre-filter | 1,712 pass | 1,054 (E6 917, E3 99, E1 31, E2 7) |
| Title screening | 631 pass | 1,081 (E6 894, E3 135, E1 33, E2 19) |
| Abstract screening | 607 included | 24 (E3 18, E6 5, E5 1) |
| Snowballing (new records) | 615 identified | 353 pre-filter, 148 title |
| **Included** | **721** (607 database + 114 snowball) | |

Of the 721: 149 have a peer-reviewed venue in their metadata, 572 are preprints (flagged; reported as
"reported", not "established"). Publication year: 2022: 1, 2023: 11, 2024: 49, 2025: 224, 2026: 436.
The field is very young and preprint-dominated, which is itself a threat to validity to state.

## 4. Descriptive map (keyword-assisted, multi-label; approximate)

Mechanism codes over the 721 includes: attack studies 403, access/privilege control 337, benchmarks
319, policy gates/guardrails 254, provenance/audit 240, monitors/detectors 217, routing/orchestration
163, sandboxing 103, information-flow control 76, training-time defences 51, formal verification 39,
static analysis 32. Threat codes: prompt injection 334, compromised or malicious agent 90, tool/skill
poisoning 75, tampering 55, memory poisoning 16. Titles naming MCP or agent "skills": 63; naming
multi-agent systems: 122. These counts are for orientation only and must not be quoted as precise.

## 5. Thematic synthesis

Each theme ends with the gap that remains after this review; the gaps lead to RQ1–RQ5.

### 5.1 Orchestration, routing and delegation (SQ1)
Adaptive routing among LLM agents is now an active line: learned routers (MasRouter, ACL 2025),
evolving or difficulty-aware orchestration (Dang et al., NeurIPS 2025; difficulty-aware agentic
orchestration, arXiv), confidence- and
uncertainty-aware routing, topology search (GPTSwarm, DyTopo) and selective delegation
(Uno-Orchestra). They optimise accuracy and cost; none of the reviewed routing works treats policy
denials or integrity failures as routing signals, and routing is evaluated on reasoning benchmarks,
not under compromise. GUIDE's Beta-posterior Bayes-UCB router is a standard algorithm (novelty.md) and
its contribution is only as one control of the artefact.
**Gap:** routing is studied for capability and cost, separately from authorisation and integrity.

### 5.2 Intent and hand-off integrity (SQ1, SQ4)
Recent measurement studies confirm the proposal's core problem. Fiducia-bench (arXiv:2608.16055)
shows policy-relevant facts attenuated at hand-off boundaries: 0 % in a single loop, 56 % in a fixed
pipeline and 85 % in an orchestrator–sub-agent design with a 32B model, but only 3–6 % with a stronger
model. Related work reports boundary metadata collapse in hand-off artefacts, constraint decay over
long horizons ("omission constraints decay", "governance decay" under context compaction) and agent
drift. Integrity mechanisms exist (signed or Macaroon-style delegation tokens in CAPMAS, Agentic JWT,
hash-chained evidence in APC and NovaFabric, W3C PROV-O agent provenance). The capability dependence
in Fiducia-bench matches GUIDE's own result: ceiling on DeepSeek and Gemini, much lower success on
GPT-OSS-120B with no condition effect.
**Gap:** structured, signed hand-offs are proposed, but whether they preserve constraints better
than conversational hand-offs on capable models is rarely tested against baselines; GUIDE's null RQ3
result is relevant evidence, not a failure to hide.

### 5.3 Tool authorisation and information flow (SQ1, SQ2)
This is the densest theme. Deterministic privilege control (Progent; MiniScope with automatic least
privilege; AgentSpec; formal Datalog policy enforcement with a reference monitor; SMT-checked tool
calls), information-flow control with security proofs or guarantees (CaMeL, IEEE SaTML 2026; FIDES;
the LLMbda calculus; GIF) and isolation (IsolateGPT, NDSS 2025; privilege-separated agents). For
multi-agent systems specifically: SafeFlow propagates semantic taints over the collaboration graph;
CAPMAS attenuates privileges monotonically with Macaroons; Paul & Nandy (ICML 2026 AIWILD workshop)
combine signed messages, provenance tracking and privilege-scoped tools and test 14 attack vectors;
Safin et al. (IEEE CARS 2026) show a compromised low-privilege agent reaching execution in every
undefended trial and contained by signed task-bound tokens plus a policy oracle, with a component
ablation. Muruaga (Bounded Agents, arXiv:2608.15888) evaluates enforcement *independently of the
model* by injecting the ground-truth attack call after the first legitimate call — the same design as
GUIDE's assumed-compromise suite K1–K4 — and reports AgentDojo exfiltration falling from 75–100 % to 0 %.
**Gap:** runtime enforcement is well covered; what is missing is a way to know, before deployment and
for a given workflow configuration, what a compromised subset of agents could still cause.

### 5.4 Evaluation of agent security (SQ4)
Standard benchmarks: AgentDojo (NeurIPS 2024 D&B), InjecAgent (ACL Findings 2024), ASB, τ-bench,
MCP-specific suites (MCPSecBench, MCPTox, MSB), multi-agent suites (TAMAS, 10 backbone models;
ContainmentBench, 17,640 trace records with stage-scoped containment metrics) and a privilege metric
that is orthogonal to attack success (Ajar measures "open privilege" left by Progent, CaMeL and
others). Methodological exemplars: pre-registered ablations with exact tests and Holm correction
(arXiv:2609.15887). Most evaluations use one to a few model families; injection success varies widely
by model, which matches GUIDE's v1 finding that the capable model ignored every textual injection.
**Gap:** few evaluations separate *model* robustness from *architecture* containment; those that do
(APC, Safin et al., GUIDE) converge on the same compromised-model protocol.

### 5.5 Static and pre-deployment analysis (SQ3) — decides the novelty claim
Full table in §6. The closest works:
- **Parisel, "A Theory of Least Autonomy in AI" (arXiv:2607.09744, July 2026; full text read).** A
  static, design-time influence graph over agents (arcs from shared-resource write-to-read meetings and
  conservatively undirected agent-to-agent channels); an agent's "effective autonomy" is the union of
  the actions of every agent it can reach; a "compositional blast radius" metric over an enterprise
  resource hierarchy; a collusion predicate. It explicitly claims **no** enforcement or noninterference
  theorem, has no runtime, no synthesis and only an illustrative example.
- **Muruaga, "Bounded Agents" (arXiv:2608.15888, Aug 2026; full text read).** Proves Blast Radius
  Monotonicity (the reachable blast radius never grows along a delegation chain) and Composition
  Soundness for a runtime authorisation model, with 3,154 evaluation instances. The bound is a runtime
  scope/budget property, not a pre-deployment computation of effects.
- **Moon & Varshney, "Containment Verification" (arXiv:2605.09045).** Models the AI as an unconstrained
  ("havoc") oracle and mechanises in Dafny that a containment layer enforces its boundary policy for
  every action the model can emit, on one minimalist framework. Sound w.r.t. the implementation and
  stronger than GUIDE's paper proof; not parametric in a subset of agents; no multi-agent influence; no
  synthesis.
- CaMeLoT (static model checking of each generated *plan* against CTL policies), AgentFlow (static
  dependency graphs of agent *source code*, 5,399 programs), Agent Audit (static code and configuration
  scanning), ATAG and MATRA (attack graphs / attack trees for agent applications; no guarantee).
- Least-privilege synthesis: MiniScope (automatic, from permission hierarchies), Aethelgard (learned
  minimum capability set from audit logs with PPO), task-conditioned least-privilege post-training
  (arXiv:2608.18351). None claims minimality in a policy lattice or proves that the synthesised policy
  shrinks a compromise bound.
- Terminology: "blast radius" is used in at least four unrelated senses (Parisel's metric; APC's
  budget; MATRA's risk; an unrelated memory-management system called "Blast Radius"). The paper must
  define BR(K) formally at first use.

**Gap that remains:** no reviewed work computes, before deployment, a set of effects reachable by an
arbitrary compromised subset K of agents (tool, operation, admissible destinations, exposed data)
through context, shared state, tools and transport, *and* proves that set sound against the gate and
runtime that enforce it, *and* checks it live (exactness on direct effects), *and* synthesises a
least-privilege policy that provably shrinks it. Each ingredient has prior art; the combination does not.

## 6. Related-work matrix (Table 1 draft)

✓ = present; p = partial (footnote in the paper); – = absent; n/c = not coded from what was read
(must be checked in the full text before the table is published).
Columns: Rout = adaptive routing; HO = signed/integrity-protected hand-off or delegation; Gate =
deterministic pre-execution gate; Trace = audit/evidence trail; IFC = provenance/information-flow;
Comp = evaluates a compromised agent; Stat = pre-deployment bound or verification; Snd = soundness w.r.t.
the enforcing runtime; Syn = least-privilege synthesis; MM = >1 model family evaluated.

| Work | Rout | HO | Gate | Trace | IFC | Comp | Stat | Snd | Syn | MM |
|---|---|---|---|---|---|---|---|---|---|---|
| CaMeL (SaTML 2026) | – | – | ✓ | n/c | ✓ | – | – | p¹ | – | n/c |
| FIDES (arXiv 2025) | – | – | ✓ | n/c | ✓ | – | – | p¹ | – | n/c |
| Progent (arXiv 2025) | – | – | ✓ | n/c | – | – | – | – | p² | n/c |
| AgentSpec (ICSE 2026) | – | – | ✓ | n/c | – | – | – | – | – | n/c |
| MiniScope (arXiv 2025) | – | – | ✓ | n/c | – | – | – | – | ✓ | n/c |
| Aethelgard (arXiv 2026) | – | – | ✓ | ✓ | – | – | – | – | p³ | n/c |
| Agent Audit (arXiv 2026) | – | – | – | – | p | – | p⁴ | – | – | – |
| AgentFlow ADG (arXiv 2026) | – | – | – | – | p | – | p⁴ | – | – | – |
| CaMeLoT (arXiv 2026) | – | – | ✓ | n/c | ✓ | – | p⁵ | p | – | n/c |
| Containment Verification (arXiv 2026) | – | – | ✓ | n/c | – | p⁶ | ✓ | ✓ | – | – |
| Least Autonomy, Parisel (arXiv 2026) | – | – | – | – | – | p⁷ | ✓ | – | – | – |
| Bounded Agents / APC (arXiv 2026) | p | ✓ | ✓ | ✓ | – | ✓ | p⁸ | ✓⁹ | – | – (one vendor) |
| Paul & Nandy (ICML 2026 workshop) | – | ✓ | ✓ | n/c | ✓ | ✓ | – | – | – | n/c |
| Safin et al. (IEEE CARS 2026) | – | ✓ | ✓ | n/c | – | ✓ | – | – | – | n/c |
| CAPMAS (arXiv 2026) | – | ✓ | ✓ | n/c | – | n/c | – | – | p³ | n/c |
| SafeFlow (arXiv 2026) | – | – | ✓ | n/c | ✓ | ✓ | – | – | – | n/c |
| ContainmentBench (arXiv 2026) | – | – | ✓ | ✓ | ✓ | p | – | – | – | – (one main model) |
| TAMAS (arXiv 2025) | – | – | – | – | – | ✓ | – | – | – | ✓ (10) |
| **GUIDE (this work)** | ✓ | ✓ | ✓ | ✓ | p¹⁰ | ✓ | ✓ | p¹¹ | ✓ | ✓ (3) |

¹ provable security per query/planner, not a deployment bound. ² LLM-generated policies. ³ learned or
semantic scoping, no minimality claim. ⁴ static analysis of code/configuration, no compromise model.
⁵ per-plan model checking. ⁶ all model outputs adversarial (havoc oracle), not a subset K.
⁷ conservative reachability screening; collusion predicate. ⁸ runtime scope/budget monotonicity along
delegation chains. ⁹ paper proofs, not machine-checked. ¹⁰ heuristic substring/token provenance guard,
weaker than CaMeL/FIDES. ¹¹ paper proof plus property tests and 0 violations on 1,575 recorded runs; not
mechanised (Containment Verification is stronger on this axis).

## 7. Novelty decision (protocol §6; plan L4) — **partial overlap**

Recorded decision: **contribution C3 is reworded "extends … by …"; it is not "to our knowledge,
first".** Proposed wording for the Introduction (author to rewrite in own voice):

> Parisel (2026) screens multi-agent configurations statically for influence and collusion but states
> no enforcement guarantee; Muruaga (2026) proves that a runtime authorisation scope cannot grow along a
> delegation chain; Moon and Varshney (2026) mechanise containment of an arbitrary model output in one
> framework. We extend these by computing, before deployment, the effects reachable by any compromised
> subset of agents, proving the bound sound against the gate and runtime that enforce it, checking it
> against live adaptive attacks (exact on direct effects, 39/39), and synthesising a lattice-minimal
> least-privilege policy that provably shrinks it without denying nominal calls.

Consequences:
- Title option 1 in the plan ("…Static Blast-Radius Bounds…") remains defensible only with this
  framing; option 3 (closest to the proposal) is the safer default if the supervisor prefers.
- C2's assumed-compromise protocol is **not** novel (same design as APC; same finding as Safin et al.).
  Present K1–K4 as a replication across three model families, which is itself useful evidence.
- Add as limitations: the soundness proof is not mechanised; the provenance guard is heuristic; the
  real-world configuration study (protocol v4) is synthetic.
- Must cite in Related Work: Parisel 2026, Muruaga 2026, Moon & Varshney 2026, CaMeLoT, AgentFlow,
  MiniScope, Aethelgard, Ajar, Fiducia-bench, Safin 2026, Paul & Nandy 2026, CAPMAS, SafeFlow,
  ContainmentBench, TAMAS, CaMeL, FIDES, Progent, AgentDojo, InjecAgent.
- Re-run the SQ3 search immediately before submission: two of the three closest works appeared in
  July–August 2026.

## 8. Answers to the review questions

- **SQ1** All four GUIDE controls exist individually and in combination (Paul & Nandy; APC; Safin
  et al.). Evaluation is mostly on single-agent injection benchmarks; multi-agent and compromised-agent
  evaluations are recent (2026) and few.
- **SQ2** About 90 includes code a compromised/malicious agent; the closest controlled designs are APC
  and Safin et al.; benchmarks: TAMAS, ContainmentBench.
- **SQ3** Static/formal work exists at the plan level (CaMeLoT), code level (AgentFlow, Agent Audit),
  framework level (Containment Verification) and configuration level without guarantees (Least
  Autonomy, attack graphs). None meets all of: effect-level, compromise-parametric, runtime-sound,
  live-validated, with synthesis (§5.5).
- **SQ4** AgentDojo, InjecAgent, ASB, τ-bench, MCP suites, TAMAS, ContainmentBench, Ajar's open-privilege
  metric, Fiducia-bench's governability metric. GUIDE's internal suite remains justified (A14) but the
  paper should name AgentDojo/TAMAS as the external validation route (future work).

## 9. Reference verification findings (from `must-check.csv`)

- Verified against a live source: 50 of 51. Not indexed: Kitchenham & Charters 2007 (technical report;
  open the PDF before citing). La Malfa et al. 2025: verified as NeurIPS 2025 (DOI 10.52202/085713-4663).
- **Error in Assignment 2's reference list:** "Kaufmann, E., Korda, N., & Munos, R. (2012). Bayesian
  upper confidence bounds for bandit problems. AISTATS" — the AISTATS 2012 paper is *On Bayesian Upper
  Confidence Bounds for Bandit Problems* by Kaufmann, Cappé and Garivier (PMLR 22:592–600). Korda and
  Munos co-authored a different 2012 Kaufmann paper (Thompson sampling, ALT). Use the corrected entry in
  the paper. (`docs/novelty.md` already cites the correct authors.)
- Venue still unverified by API (OpenReview blocks scripted access): Triedman et al. as COLM 2025;
  WebArena as ICLR 2024; τ-bench venue; AutoGen venue. Open the pages before citing those venues;
  otherwise cite as arXiv.
- Assignment 1 cites Maloyan & Namiot (2026) in *Int. J. Open Information Technologies* 14(2); only
  the arXiv version was verified.
- Peer-reviewed status confirmed for: AgentDojo (NeurIPS 2024 D&B), InjecAgent (ACL Findings 2024),
  Greshake et al. (AISec 2023), Liu et al. (USENIX Security 2024), CaMeL (IEEE SaTML 2026), AgentSpec
  (ICSE 2026), IsolateGPT (NDSS 2025), Dang et al. (NeurIPS 2025), Backes et al. (FMCAD 2018), Zhang
  et al. (ICRA 2025), MACCA (TMLR 2025), Safin et al. (IEEE CARS 2026, accepted), Paul & Nandy (ICML 2026
  workshop).
- Excluded by the SLR criteria but cited in the submissions: Collini et al. (MARVEL: LLMs for RTL
  vulnerability detection, E6), Zhang et al. ICRA 2025 and MACCA (no LLM agents, E2). They may stay as
  background citations but are not evidence for agent-governance claims.

## 10. Differences from the submitted reports

Compared with `previously submitted to university/RMCE - Assignment 1 (Liturature Review).docx` (A1)
and `RMCE - Assignment 2 (Proposal).docx` (A2). The submitted files are not edited; each difference must
be stated in the paper (Table 9 / §3.8 in the plan) and is mirrored in `docs/submission-alignment.md`.

| # | Submitted report says | This review found | Effect on the paper |
|---|---|---|---|
| L1 | A2 §8.1: search ACM DL, IEEE Xplore, Scopus, ACL Anthology, Google Scholar, 2022–2026; code by problem, mechanism, evidence, limitation, implication | Executed on OpenAlex, arXiv and Semantic Scholar (open APIs; DBLP blocked), same window, PRISMA 2020; coding scheme kept and extended (threat model, static bound, soundness, synthesis, quality) | Disclose source substitution and amendments A1–A6 in Methods |
| L2 | A1: narrative review of 16 sources in three themes | 721 included studies (3,600 records screened plus 615 by snowballing); five themes | Related Work is rebuilt from the review, not from A1's text (also avoids self-similarity) |
| L3 | A2 §7: "no study was identified that experimentally integrates and evaluates all four controls"; claim to be revalidated | Superseded: Paul & Nandy 2026 combine signed messages, provenance and privilege-scoped tools; APC and Safin et al. evaluate integrated authorisation under compromise | Do not repeat the claim; state it held at proposal time (June 2026) and was superseded (A22, confirmed) |
| L4 | A1 §5.4 gap: "a decoupled run-time policy projection layer" for agent graphs | Now heavily populated (Progent, AgentSpec, formal Datalog enforcement, APC, CaMeL, FIDES) | Present GUIDE's gate as an instance of an established class, simpler than Progent |
| L5 | A1 §3.4 gap: adaptive allocation that models agent competence under uncertainty | Many 2025–2026 routing/orchestration works (MasRouter, evolving orchestration, confidence-aware routing) | Routing is a component of the artefact, not a contribution |
| L6 | A1 §4.4 gap: structural intent-preserving protocols | Problem confirmed by new measurement work (Fiducia-bench, boundary-metadata collapse, constraint decay); integrity mechanisms emerging | Keep RQ1/RQ3 framing; cite the new evidence; report GUIDE's null RQ3 result alongside Fiducia's capability dependence |
| L7 | A1 §7 gap: "a single system that is … formally verifiable" | Formal work now exists at plan, code and framework level (CaMeLoT, AgentFlow, Containment Verification) and as static screening (Least Autonomy) | Motivates RQ5 precisely: the remaining gap is a sound, compromise-parametric, effect-level bound with synthesis (§5.5) |
| L8 | A1 Tables 1–2 compare CrewAI, LangGraph, AutoGen, OpenAI Agents, Microsoft Agent Framework | Those tables are literature-based judgements, not measurements; no reviewed study ran these frameworks under GUIDE's protocol | Cite as structural patterns only (A1, A21, A27 unchanged) |
| L9 | A2 assumes the evaluation design (B1/B2/P under adversarial inputs) is the paper's empirical contribution | The compromised-model evaluation design is shared with APC (Aug 2026) and Safin et al. (Sept 2026) | Present K1–K4 results as a three-model-family replication |
| L10 | A2 reference: Kaufmann, Korda & Munos (2012) | Correct authors: Kaufmann, Cappé & Garivier (2012) | Fix in the paper |
| L11 | A1/A2 cite Triedman et al. (COLM 2025), Zhou et al. WebArena (ICLR 2024), La Malfa et al. (NeurIPS 2025) | La Malfa verified; COLM and ICLR venues not yet verified | Verify before citing venues |
| L12 | A1 includes MARVEL, a CBF deadlock paper (ICRA) and MACCA as governance/orchestration evidence | Outside this review's scope (not LLM-agent control) | Use only as background, if at all |
| L13 | A2 scope: RQ1–RQ4 | RQ5 (pre-deployment bound) is an extension (A23); this review supports keeping it, with the partial-overlap wording of §7 | RQ5 labelled as extension; C3 reworded |

## 11. Open items before the paper cites this review

1. Author confirms every include used in the paper and every SQ3 coding in §6 (protocol §7).
2. Second screener fills `second-screener-sample.csv`; run `scripts/kappa.py`; report kappa (A5).
3. Fill the n/c cells of Table 1 from full texts; read the full texts of CaMeLoT, Containment
   Verification, MiniScope and Aethelgard before writing §2.5 of the paper.
4. Verify the venues listed as unverified in §9; complete given names in `references.bib`.
5. Re-run S4 (static/formal string) in the week of submission and update §5.5 if new work appears.
