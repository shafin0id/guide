# Systematic literature review protocol (closes A22)

Version: `review-protocol-v1`, frozen in git before any search was run (2026-10-01).
Reviewer: the author, with tool assistance disclosed in §7. Reporting standard: PRISMA 2020
(Page et al., 2021). Process: Kitchenham & Charters (2007) guidelines for SLRs in software engineering;
snowballing per Wohlin (2014).

## 1. Review questions
- **SQ1** Which mechanisms control routing, hand-off integrity, tool authorisation and traceability in
  LLM multi-agent systems, and how were they evaluated?
- **SQ2** Which works evaluate containment of a *compromised* agent (not only injected text)?
- **SQ3** Which works compute, before deployment, a bound on what a compromised agent can cause, and is
  that bound tied to the enforcing runtime (soundness)? *(decides the novelty claim, §6)*
- **SQ4** Which benchmarks and metrics exist for policy compliance, intent fidelity and agent security?

## 2. Sources
Planned in the proposal (§8.1): ACM DL, IEEE Xplore, Scopus, ACL Anthology, Google Scholar.
Executed (deviation, disclosed in the paper's method section and in `differences-vs-submitted.md`):

| Source | Access | Covers |
|---|---|---|
| OpenAlex (`api.openalex.org/works`, title+abstract search) | open API | ACM, IEEE, Springer, Elsevier, ACL, USENIX, NeurIPS/ICLR/ICML proceedings, arXiv |
| arXiv API (`export.arxiv.org/api/query`, `ti`/`abs` fields) | open API | cs.CR, cs.AI, cs.MA, cs.SE, cs.CL, cs.LG preprints |
| DBLP (`dblp.org/search/publ/api`, title search) | open API | bibliographic coverage check for CS venues (USENIX Sec, S&P, CCS, NDSS, ACL, NeurIPS, ICLR) |

ACM DL, IEEE Xplore, Scopus and Google Scholar have no open, reproducible query API; their content is
reached through OpenAlex (which ingests publisher and Crossref metadata) and checked by DBLP. Every
query is logged with date, exact string and hit count in `search-log.csv`, and re-runnable with
`scripts/search.py`.

## 3. Search strings
Each string is translated to the source's syntax (translations in `scripts/search.py`, verbatim in the log).
- **S1** `("multi-agent" OR "multi agent" OR agentic) AND ("large language model" OR LLM) AND (orchestration OR routing OR delegation OR "hand-off" OR handoff)`
- **S2** `(LLM OR "language model") AND agent AND ("prompt injection" OR "tool misuse" OR privilege OR "confused deputy" OR "compromised agent")`
- **S3** `(LLM OR agent) AND ("information flow" OR taint OR capability OR "least privilege" OR "access control" OR "policy enforcement")`
- **S4** `(LLM OR agent) AND ("static analysis" OR reachability OR "blast radius" OR "formal verification" OR soundness)`
- **S5** `("LLM agent" OR "tool use") AND (benchmark OR evaluation) AND (security OR "policy compliance" OR safety)`
- **S6** `(LLM OR agent) AND (provenance OR "audit trail" OR traceability OR "tamper-evident" OR signature)`

Window: 2022-01-01 to the search date. Cap: the first 200 records per string per source in the
source's relevance order (the plan's Google Scholar rule, applied uniformly so the retrieval set is
reproducible). Foundational pre-2022 works (Saltzer & Schroeder 1975; Denning 1976; Hevner 2004;
Peffers 2007; Auer 2002; Kaufmann 2012; Bernstein 2012; Cheney 2009; Backes 2018) are background,
outside the counts.

## 4. Eligibility
- **I1** Peer-reviewed paper or arXiv preprint, in English.
- **I2** Concerns LLM-based agents (single or multi-agent) that call tools or exchange messages.
- **I3** Proposes or evaluates a control, an attack/threat analysis, or a benchmark relevant to SQ1–SQ4.
- **E1** Single-turn chatbot safety without tools or agents (jailbreak-only, toxicity, alignment).
- **E2** Multi-agent RL / robotics / classical MAS without LLMs.
- **E3** Position, vision or survey piece with no mechanism and no evaluation (surveys may be used as
  pointers for snowballing but are not included as primary studies).
- **E4** Duplicate (the peer-reviewed version is kept; arXiv id recorded).
- **E5** Full text or abstract not accessible.
- **E6** Off-topic (term collision: e.g. "agent" in chemistry, "provenance" in art history, LLM used as a
  tool for an unrelated task such as code generation quality without agent security).

Preprints are included and flagged `peer_reviewed=no`; their claims are reported as "reported".

## 5. Screening, snowballing, extraction, appraisal
1. Deduplicate by DOI, then arXiv id, then normalised title.
2. **Rule pre-filter (tool-assisted, deterministic):** a record passes only if title+abstract contains a
   language-model term (`LLM`, `language model`, `GPT`, `foundation model`) AND an agent term (`agent`,
   `agentic`, `tool`, `multi-agent`). Fails are coded E1/E2/E6 automatically. Validation: a uniform
   random sample of 100 failed records (seed 2026) is read by hand; false negatives are reported and, if
   any, the rule is widened and re-applied.
3. **Title/abstract screening** of every pre-filter pass by the author against I1–I3/E1–E6, reason code
   recorded in `screening.csv`.
4. **Second screener:** a uniform random 20 % sample (seed 2026) of title/abstract decisions is screened
   independently and blind by a second screener; Cohen's kappa is reported. The second screener is an
   LLM instance with no access to the first decisions (disclosed as a limitation; a human second
   screener, e.g. the supervisor, may replace it before submission).
5. **Full-text assessment** of title/abstract includes whose relevance to SQ2/SQ3 is high (closest
   works); others are coded from abstract + full-text skim, recorded as `extraction_basis`.
6. **Snowballing:** one round backward and forward on the included set via OpenAlex
   `referenced_works`/`cited_by`, screened with the same criteria.
7. **Extraction** into `extraction.csv` with the columns of the plan (L1), plus `extraction_basis`.
8. **Quality appraisal** 0–2 on each of: explicit threat model; released artefact; live-LLM evaluation;
   baselines/ablations; variance or statistics reported (total 0–10).

## 6. Novelty decision rule (SQ3)
For each included work coded `static_bound = yes|partial`, record (a) what is bounded, (b) whether the
bound is sound w.r.t. an enforcing runtime, (c) whether it is parametric in a compromised agent set K,
(d) whether policy synthesis is provided.
- No work with (a)+(b)+(c): contribution C3 stays "to our knowledge, first".
- Partial overlap: C3 is reworded "extends X by ...", naming X.
- Full overlap: C3 is downgraded to an independent implementation/replication.

## 7. Tool use and threats to validity (declared in advance)
- Queries, deduplication, pre-filter and counts are scripted (`scripts/`), so they are reproducible.
- Screening and extraction decisions were made with LLM assistance (the author's AI assistant read
  titles/abstracts and full texts and proposed codes); every include decision and every SQ3 coding must
  be confirmed by the author before the paper cites it. This is disclosed in the paper's AI-use statement.
- Single primary screener; mitigated by the blind second screener (§5.4) and snowballing.
- Relevance-ordered cap of 200 per string/source may miss low-ranked relevant work; mitigated by
  snowballing and by the mandatory must-check list (plan L3).
- The field moves weekly; the search date bounds every "no prior work found" statement.
