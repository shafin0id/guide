# Supplementary Material: GUIDE

Supplement to GUIDE: An External Reference Monitor That Bounds the Blast Radius of Compromised Agents in LLM Multi-Agent Systems.

## S1. Systematic Literature Review Protocol and PRISMA 2020 Selection

Searches were executed on 2026-10-01 across OpenAlex, arXiv, and Semantic Scholar (which replaced DBLP under protocol Amendment A1 after DBLP returned a bot-challenge page) for records published from 2022-01-01 to the search date, capped at the first 200 records per search string and source. Snowballing followed Wohlin (2014) for one backward and forward round on a 43-work core set.

Figure S1. PRISMA 2020 study selection flow diagram (`scripts/paper/figures/figS1_prisma_flow.png`).

| Stage | Count | Details / Exclusion Reasons |
|---|---|---|
| Records identified (18 queries) | 3,600 | 6 search strings x 3 sources (OpenAlex, arXiv, Semantic Scholar), cap 200 |
| After deduplication | 2,766 | 834 duplicates removed (DOI, arXiv ID, normalized title) |
| Rule pre-filter passed | 1,712 | 1,054 excluded (E6: 917, E3: 99, E1: 31, E2: 7; 7 rescued in audit) |
| Title screening passed | 631 | 1,081 excluded (E6: 894, E3: 135, E1: 33, E2: 19) |
| Database studies included | 607 | 24 excluded at abstract stage (E3: 18, E6: 5, E5: 1) |
| Snowballing additions | 114 | 615 identified from 43 core works (353 pre-filter, 148 title excluded) |
| Total included studies | 721 | 607 database + 114 snowballing (26 core works hand-coded) |

Search strings S1 to S6:

- S1: ("multi-agent" OR "multi agent" OR agentic) AND ("large language model" OR LLM) AND (orchestration OR routing OR delegation OR "hand-off" OR handoff)
- S2: (LLM OR "language model") AND agent AND ("prompt injection" OR "tool misuse" OR privilege OR "confused deputy" OR "compromised agent")
- S3: (LLM OR agent) AND ("information flow" OR taint OR capability OR "least privilege" OR "access control" OR "policy enforcement")
- S4: (LLM OR agent) AND ("static analysis" OR reachability OR "blast radius" OR "formal verification" OR soundness)
- S5: ("LLM agent" OR "tool use") AND (benchmark OR evaluation) AND (security OR "policy compliance" OR safety)
- S6: (LLM OR agent) AND (provenance OR "audit trail" OR traceability OR "tamper-evident" OR signature)

## S2. Prior Routing Policy Simulation (Figure S2)

Before running live LLM evaluations, the Bayes-UCB routing policy (Control 1) was simulated over 100 random seeds with horizon T = 1,000 steps under two regimes: a mis-assigned stationary regime and a non-stationary drift regime where the best agent's success probability drops from 0.9 to 0.2 at step T/2.

Figure S2. Mean routing regret across 100 seeds (horizon T = 1,000) under stationary and post-drift regimes (`scripts/paper/figures/figS2_routing_regret.png`).

| Routing Policy | Stationary Mean Regret | Drift Overall Regret | Post-Drift Regret |
|---|---|---|---|
| Static assignment | 150.0 | 275.0 | - |
| Bayes-UCB (Control 1) | 18.3 [15.7, 21.0] | 54.5 | 39.8 |
| Discounted (0.99) | 61.2 | 41.8 | 12.2 |
| Bayes-UCB + penalty | 12.5 [9.6, 15.4] | 61.0 | 49.4 |
