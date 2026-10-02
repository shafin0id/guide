# Final reference list — GUIDE paper

Generated 2026-10-02 by `docs/lit-review/scripts/build_final_refs.py` → `references-final.bib` (cite from this file, not `references.bib`).
This is the paper's bibliography. The 721-study corpus in `docs/lit-review/literature-review.md` is the SLR evidence base and is reported only through PRISMA counts and Table 1.

## Totals

| | n | % |
|---|---|---|
| Peer-reviewed (journal / conference / workshop) | 93 | 80.9% |
| Non-peer-reviewed (arXiv preprints + 1 technical report) | 22 | 19.1% |
| **Total** | **115** | |

## Selection rules
1. Kept all peer-reviewed entries of the 81-entry verified bib (41).
2. Added 50 peer-reviewed corpus studies, chosen per theme for venue tier (USENIX Sec, IEEE S&P, NDSS, SaTML, CCS/AISec, NeurIPS, ICML, ICLR, ACL/EMNLP/NAACL, AAAI, VLDB, IEEE/ACM journals). Preprint servers listed as venues by OpenAlex (Research Square, SSRN, Zenodo, Preprints.org, medRxiv) were treated as non-peer-reviewed and excluded, as were venues that could not be identified.
3. Kept only 20 non-peer-reviewed works: each is novelty-critical or a must-cite in Table 1 with no published version yet. The other 38 bib preprints were dropped, including background papers from Assignment 1 (memory governance, hallucination cascade, coding-assistant injection, authorisation propagation) and collini2025 (excluded by SLR criterion E6). If the paper needs one of them, swap it in for a preprint below so the share stays ≤ 20 %.
4. Every work in Table 1 and in the §7 must-cite list of the review is included.

## Verification status (fix before submission, not before drafting)
- `PR` (41): verified earlier against Crossref/arXiv/OpenAlex (`must-check.csv`).
- `PR (DOI-verified)` (30): metadata fetched from the publisher DOI.
- `PR (venue-from-OpenAlex)` (19): published, but the only DOI found was arXiv's; the entry cites the OpenAlex venue with a `note`. Open the proceedings page and add the venue DOI/pages.
- `PR (VERIFY)` (1): `anon2025make` (USENIX Security 2025) has no DOI or arXiv ID in the metadata; fill in the authors from the USENIX page.
- `PP`: re-check before submission whether any has since been published (Triedman → COLM 2025 and τ-bench → venue are still unconfirmed). Each one that has been published moves to peer-reviewed.
- Before submission, re-run the SQ3 search (protocol §7) for new work related to Parisel, Muruaga or Moon & Varshney.

## List


### Method & foundations

| Key | Title | Year | Venue | Status | Use / reason |
|---|---|---|---|---|---|
| `saltzer1975` | The protection of information in computer systems | 1975 | Proceedings of the IEEE | PR | §3 Method, §4 Design |
| `denning1976` | A lattice model of secure information flow | 1976 | Communications of the ACM | PR | §3 Method, §4 Design |
| `cheney2009` | Provenance in Databases: Why, How, and Where | 2009 | Foundations and Trends in Databases | PR | §3 Method, §4 Design |
| `bernstein2012` | High-speed high-security signatures | 2012 | Journal of Cryptographic Engineering | PR | §3 Method, §4 Design |
| `auer2002` | Finite-time Analysis of the Multiarmed Bandit Problem | 2002 | Machine Learning | PR | §3 Method, §4 Design |
| `kaufmann2012` | On Bayesian Upper Confidence Bounds for Bandit Problems | 2012 | found; venue check: AISTATS 2012 (PMLR v22) -- OpenAlex has  | PR | §3 Method, §4 Design |
| `backes2018` | Semantic-based Automated Reasoning for AWS Access Policies using SMT | 2018 | found; venue check: FMCAD 2018; DOI 10.23919/fmcad.2018.8602 | PR | §3 Method, §4 Design |
| `hevner2004` | Design Science in Information Systems Research1 | 2004 | MIS Quarterly | PR | §3 Method, §4 Design |
| `peffers2007` | A Design Science Research Methodology for Information Systems Research | 2007 | Journal of Management Information Systems | PR | §3 Method, §4 Design |
| `page2021` | The PRISMA 2020 statement: an updated guideline for reporting systematic reviews | 2021 | BMJ | PR | §3 Method, §4 Design |
| `wohlin2014` | Guidelines for snowballing in systematic literature studies and a replication in software  | 2014 | Proceedings of the 18th International Conference on Evaluation and Assessment in Software Engineering | PR | §3 Method, §4 Design |

### LLM agents & multi-agent systems

| Key | Title | Year | Venue | Status | Use / reason |
|---|---|---|---|---|---|
| `park2023` | Generative Agents: Interactive Simulacra of Human Behavior | 2023 | Proceedings of the 36th Annual ACM Symposium on User Interface Software and Technology | PR | §1 Intro, §2.1 |
| `wang2024` | A survey on large language model based autonomous agents | 2024 | Frontiers of Computer Science | PR | §1 Intro, §2.1 |
| `guo2026` | MCP-AgentBench: Evaluating Real-World Language Agent Performance with MCP-Mediated Tools | 2026 | Proceedings of the AAAI Conference on Artificial Intelligence | PR | §1 Intro, §2.1 |
| `dang2025` | Multi-Agent Collaboration via Evolving Orchestration | 2025 | found; venue check: NeurIPS 2025; DOI 10.52202/085713-5502 | PR | §1 Intro, §2.1 |
| `wu2023` | AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation | 2023 | found; venue check: preprint (COLM 2024 version exists per c | PR | §1 Intro, §2.1 |
| `zhou2024` | WebArena: A Realistic Web Environment for Building Autonomous Agents | 2023 | found; venue check: UNVERIFIED: ICLR 2024 claimed; OpenRevie | PR | §1 Intro, §2.1 |
| `lamalfa2025` | Large Language Models Miss the Multi-Agent Mark | 2025 | found (retry; arXiv API transient); venue check: NeurIPS 202 | PR | §1 Intro, §2.1 |
| `mohammadi2025` | Evaluation and Benchmarking of LLM Agents: A Survey | 2025 | Proceedings of the 31st ACM SIGKDD Conference on Knowledge Discovery and Data Mining V.2 | PR | §1 Intro, §2.1 |
| `becker2026` | Stay Focused: Problem Drift in Multi-Agent Debate | 2026 | Findings of the Association for Computational Linguistics: EACL 2026 | PR | §1 Intro, §2.1 |
| `ji2025` | LLM-Based Multi-Agent Systems are Scalable Graph Generative Models | 2025 | Findings of the Association for Computational Linguistics: ACL 2025 | PR | §1 Intro, §2.1 |
| `yu2025` | Tree of Agents: Improving Long-Context Capabilities of Large Language Models through Multi | 2025 | Findings of the Association for Computational Linguistics: EMNLP 2025 | PR | §1 Intro, §2.1 |
| `zhang2025icra` | Adaptive Deadlock Avoidance for Decentralized Multi-agent Systems via CBF-inspired Risk Me | 2025 | found; venue check: ICRA 2025; DOI 10.1109/icra55743.2025.11 | PR | §1 Intro, §2.1 |
| `wang2025macca` | MACCA: Offline Multi-agent Reinforcement Learning with Causal Credit Assignment | 2023 | found; venue check: TMLR 2025 (arXiv journal_ref) | PR | §1 Intro, §2.1 |

### Agent security: attacks, defences, benchmarks

| Key | Title | Year | Venue | Status | Use / reason |
|---|---|---|---|---|---|
| `debenedetti2024` | AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM | 2024 | found; venue check: NeurIPS 2024 D\&B; DOI 10.52202/079017-2 | PR | §2.2-2.4, §5 Evaluation |
| `zhan2024` | InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated Large Language Mode | 2024 | found; venue check: Findings ACL 2024; DOI 10.18653/v1/2024. | PR | §2.2-2.4, §5 Evaluation |
| `greshake2023` | Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with In | 2023 | found; venue check: AISec@CCS 2023; DOI 10.1145/3605764.3623 | PR | §2.2-2.4, §5 Evaluation |
| `liu2024` | Formalizing and Benchmarking Prompt Injection Attacks and Defenses | 2023 | found; venue check: USENIX Security 2024 (arXiv comment + us | PR | §2.2-2.4, §5 Evaluation |
| `debenedetti2025` | Defeating Prompt Injections by Design | 2025 | found; venue check: IEEE SaTML 2026; DOI 10.1109/satml68715. | PR | §2.2-2.4, §5 Evaluation |
| `wu2025isolategpt` | IsolateGPT: An Execution Isolation Architecture for LLM-Based Agentic Systems | 2024 | The Network and Distributed System Security (NDSS) Symposium 2025 | PR | §2.2-2.4, §5 Evaluation |
| `wang2025agentspec` | AgentSpec: Customizable Runtime Enforcement for Safe and Reliable LLM Agents | 2025 | Proc. ICSE'26, pages 2938-2950. ACM, 2026 | PR | §2.2-2.4, §5 Evaluation |
| `asb2024` | Agent Security Bench (ASB): Formalizing and Benchmarking Attacks and Defenses in LLM-based | 2024 | International Conference on Learning Representations | PR | §2.2-2.4, §5 Evaluation |
| `saga2025` | SAGA: A Security Architecture for Governing AI Agentic Systems | 2025 | Network and Distributed System Security Symposium | PR | §2.2-2.4, §5 Evaluation |
| `atag2025` | ATAG: AI-Agent Application Threat Assessment with Attack Graphs | 2025 | ACM Asia Conference on Computer and Communications Security | PR | §2.2-2.4, §5 Evaluation |
| `promptinfection2024` | Prompt Infection: LLM-to-LLM Prompt Injection within Multi-agent Systems | 2026 | Lecture notes in computer science | PR | §2.2-2.4, §5 Evaluation |
| `gsafeguard2025` | G-Safeguard: A Topology-Guided Security Lens and Treatment on LLM-based Multi-agent System | 2025 | Annual Meeting of the Association for Computational Linguistics | PR | §2.2-2.4, §5 Evaluation |
| `blindguard2025` | BlindGuard: Safeguarding LLM-based Multi-Agent Systems under Unknown Attacks | 2025 | Annual Meeting of the Association for Computational Linguistics | PR | §2.2-2.4, §5 Evaluation |
| `tamas2025` | TAMAS: Benchmarking Adversarial Risks in Multi-Agent LLM Systems | 2025 | found; venue check: OpenAlex lists ACL venue but DOI is arXi | PR | §2.2-2.4, §5 Evaluation |
| `paul2026` | Beyond Single-Model Injection: A Threat Model and Defense Architecture for Prompt Injectio | 2026 | found; venue check: ICML 2026 AIWILD workshop, camera-ready  | PR | §2.2-2.4, §5 Evaluation |
| `safin2026` | Trust propagation and structural containment in Multi-agent LLM pipelines | 2026 | found; venue check: IEEE CARS 2026, accepted (arXiv comment) | PR | §2.2-2.4, §5 Evaluation |
| `pasupuleti2026` | Safe and Policy-Compliant Multi-Agent Orchestration for Enterprise AI | 2026 | 2026 International Conference on Artificial Intelligence, Systems, and Emerging Technologies (ICAISET) | PR | §2.2-2.4, §5 Evaluation |

### Preprints kept (novelty-critical)

| Key | Title | Year | Venue | Status | Use / reason |
|---|---|---|---|---|---|
| `parisel2026leastautonomy` | A Theory of Least Autonomy in AI | 2026 | arXiv / grey | PP | closest prior work; decides C3 novelty |
| `muruaga2026boundedagents` | Bounded Agents: Delegation Security for Multi-Agent AI Systems | 2026 | arXiv / grey | PP | closest prior work; same compromise protocol |
| `moon2026containment` | Containment Verification: AI Safety Guarantees Independent of Alignment | 2026 | arXiv / grey | PP | closest prior work; mechanised proof (limitation) |
| `camelot2026` | CaMeLoT: CaMeL orchestrated with Temporal logic for static verification and liveness | 2026 | arXiv / grey | PP | static per-plan checking (Table 1) |
| `agentflow2026adg` | AgentFlow: Building Agent Dependency Graphs for Static Analysis of Agent Programs | 2026 | arXiv / grey | PP | static code-level analysis (Table 1) |
| `agentaudit2026` | Agent Audit: A Security Analysis System for LLM Agent Applications | 2026 | arXiv / grey | PP | static config scanning (Table 1) |
| `matra2026` | MATRA: Modeling the Attack Surface of Agentic AI Systems -- OpenClaw Case Study | 2026 | arXiv / grey | PP | attack-tree modelling (Table 1) |
| `miniscope2025` | MiniScope: A Least Privilege Framework for Authorizing Tool Calling Agents | 2025 | arXiv / grey | PP | least-privilege synthesis (Table 1) |
| `aethelgard2026` | Beyond Static Sandboxing: Learned Capability Governance for Autonomous AI Agents | 2026 | arXiv / grey | PP | learned capability scoping (Table 1) |
| `shi2025` | Progent: Securing AI Agents with Privilege Control | 2025 | arXiv / grey | PP | Progent: privilege control baseline (Table 1) |
| `costa2025` | Securing AI Agents with Information-Flow Control | 2025 | arXiv / grey | PP | FIDES: IFC baseline (Table 1) |
| `capmas2026` | CAPMAS: Capability-Based Delegation of Privileges in Multi-Agent Systems | 2026 | arXiv / grey | PP | attenuating delegation tokens (Table 1) |
| `safeflow2026` | SafeFlow: Semantic Information-Flow Control for Blocking Malicious Propagation in Multi-Ag | 2026 | arXiv / grey | PP | multi-agent taint IFC (Table 1) |
| `containmentbench2026` | ContainmentBench: Trace-Based Evaluation of Post-Exposure Containment in Tool-Using LLM Ag | 2026 | arXiv / grey | PP | multi-agent containment benchmark (Table 1) |
| `ajar2026` | Ajar: Measuring Open Privilege in Agent Defenses | 2026 | arXiv / grey | PP | open-privilege metric (RQ evaluation) |
| `fiducia2026` | Governance at the Boundary: How Agent Decomposition Degrades Policy Compliance | 2026 | arXiv / grey | PP | hand-off attenuation evidence (RQ3 discussion) |
| `proposesdisposes2026` | The Model Proposes, the Code Disposes: A Pre-Registered Ablation of a Verifier-and-Accepta | 2026 | arXiv / grey | PP | pre-registered ablation exemplar (Method) |
| `triedman2025` | Multi-Agent Systems Execute Arbitrary Malicious Code | 2025 | arXiv / grey | PR (proceedings-URL)| MAS arbitrary-code execution (Intro); COLM venue unverified |
| `yao2024` | $τ$-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains | 2024 | arXiv / grey | PR (proceedings-URL)| tau-bench (Evaluation); venue unverified |
| `kitchenham2007` | Guidelines for performing Systematic Literature Reviews in Software Engineering | 2007 | arXiv / grey | PP | SLR guideline (technical report) |

### LLM agents & multi-agent systems

| Key | Title | Year | Venue | Status | Use / reason |
|---|---|---|---|---|---|
| `yue2025masrouter` | MasRouter: Learning to Route LLMs for Multi-Agent Systems | 2025 | Annual Meeting of the Association for Computational Linguist | PR (DOI-verified) | §1 Intro, §2.1 |
| `zhuge2024language` | Language Agents as Optimizable Graphs | 2024 | International Conference on Machine Learning | PR (proceedings-URL)| §1 Intro, §2.1 |
| `yang2025agentnet` | AgentNet: Decentralized Evolutionary Coordination for LLM-based Multi-Agent Systems | 2025 | Neural Information Processing Systems | PR (DOI-verified) | §1 Intro, §2.1 |
| `su2025difficultyaware` | Difficulty-Aware Agentic Orchestration for Query-Specific Multi-Agent Workflows | 2025 | The Web Conference | PR (DOI-verified) | §1 Intro, §2.1 |
| `chang2025sagallm` | SagaLLM: Context Management, Validation, and Transaction Guarantees for Multi-Agent LLM Pl | 2025 | Proceedings of the VLDB Endowment | PR (DOI-verified) | §1 Intro, §2.1 |
| `cemri2025why` | Why Do Multi-Agent LLM Systems Fail? | 2025 | Neural Information Processing Systems | PR (DOI-verified)| §1 Intro, §2.1 |

### Agent security: attacks, defences, benchmarks

| Key | Title | Year | Venue | Status | Use / reason |
|---|---|---|---|---|---|
| `zhan2025adaptive` | Adaptive Attacks Break Defenses Against Indirect Prompt Injection Attacks on LLM Agents | 2025 | North American Chapter of the Association for Computational  | PR (DOI-verified) | §2.2-2.4, §5 Evaluation |
| `jia2025the` | The Task Shield: Enforcing Task Alignment to Defend Against Indirect Prompt Injection in L | 2025 | Annual Meeting of the Association for Computational Linguist | PR (DOI-verified) | §2.2-2.4, §5 Evaluation |
| `shi2026prompt` | Prompt Injection Attack to Tool Selection in LLM Agents | 2026 | Network and Distributed System Security Symposium | PR (DOI-verified) | §2.2-2.4, §5 Evaluation |
| `liu2025datasentinel` | DataSentinel: A Game-Theoretic Detection of Prompt Injection Attacks | 2025 | IEEE Symposium on Security and Privacy | PR (DOI-verified) | §2.2-2.4, §5 Evaluation |
| `an2025ipiguard` | IPIGuard: A Novel Tool Dependency Graph-Based Defense Against Indirect Prompt Injection in | 2025 | Conference on Empirical Methods in Natural Language Processi | PR (DOI-verified) | §2.2-2.4, §5 Evaluation |
| `li2025drift` | DRIFT: Dynamic Rule-Based Defense with Injection Isolation for Securing LLM Agents | 2025 | Neural Information Processing Systems | PR (DOI-verified)| §2.2-2.4, §5 Evaluation |
| `wang2025defending` | Defending Against Prompt Injection with DataFilter | 2025 | 2026 IEEE Conference on Secure and Trustworthy Machine Learn | PR (DOI-verified) | §2.2-2.4, §5 Evaluation |
| `zhu2025melon` | MELON: Provable Defense Against Indirect Prompt Injection Attacks in AI Agents | 2025 | International Conference on Machine Learning | PR (proceedings-URL)| §2.2-2.4, §5 Evaluation |
| `li2025ace` | ACE: A Security Architecture for LLM-Integrated App Systems | 2025 | Network and Distributed System Security Symposium | PR (DOI-verified) | §2.2-2.4, §5 Evaluation |
| `wang2025attntrace` | AttnTrace: Contextual Attribution of Prompt Injection and Knowledge Corruption | 2025 | IEEE Symposium on Security and Privacy | PR (DOI-verified) | §2.2-2.4, §5 Evaluation |
| `abdelnabi2024get` | Get My Drift? Catching LLM Task Drift with Activation Deltas | 2024 | 2025 IEEE Conference on Secure and Trustworthy Machine Learn | PR (DOI-verified) | §2.2-2.4, §5 Evaluation |
| `jia2025a` | A Critical Evaluation of Defenses against Prompt Injection Attacks: [Dataset/Tool Paper] | 2025 | ACM Symposium on Access Control Models and Technologies | PR (DOI-verified) | §2.2-2.4, §5 Evaluation |
| `zhang2026evaluating` | Evaluating Privilege Usage of Agents with Real-World Tools | 2026 | SIGSOFT FSE Companion | PR (DOI-verified) | §2.2-2.4, §5 Evaluation |
| `wu2025towards` | Towards Automating Data Access Permissions in AI Agents | 2025 | IEEE Symposium on Security and Privacy | PR (DOI-verified) | §2.2-2.4, §5 Evaluation |
| `li2025we` | We Urgently Need Privilege Management in MCP: A Measurement of API Usage in MCP Ecosystems | 2025 | IEEE International Conference on Mobile Adhoc and Sensor Sys | PR (DOI-verified) | §2.2-2.4, §5 Evaluation |
| `wang2025mcptox` | MCPTox: A Benchmark for Tool Poisoning Attack on Real-World MCP Servers | 2025 | AAAI Conference on Artificial Intelligence | PR (DOI-verified) | §2.2-2.4, §5 Evaluation |
| `mo2025attractive` | Attractive Metadata Attack: Inducing LLM Agents to Invoke Malicious Tools | 2025 | Neural Information Processing Systems | PR (DOI-verified)| §2.2-2.4, §5 Evaluation |
| `li2025les` | Les Dissonances: Cross-Tool Harvesting and Polluting in Pool-of-Tools Empowered LLM Agents | 2025 | Network and Distributed System Security Symposium | PR (DOI-verified) | §2.2-2.4, §5 Evaluation |
| `song2025beyond` | Beyond the Protocol: Unveiling Attack Vectors in the Model Context Protocol (MCP) Ecosyste | 2025 | IEEE Transactions on Software Engineering | PR (DOI-verified) | §2.2-2.4, §5 Evaluation |
| `anon2025make` | Make Agent Defeat Agent: Automatic Detection of Taint-Style Vulnerabilities in LLM-based A | 2025 | USENIX Security Symposium | PR (proceedings-URL)| §2.2-2.4, §5 Evaluation |
| `xiang2024guardagent` | GuardAgent: Safeguard LLM Agents by a Guard Agent via Knowledge-Enabled Reasoning | 2024 | International Conference on Machine Learning | PR (proceedings-URL)| §2.2-2.4, §5 Evaluation |
| `chen2025shieldagent` | ShieldAgent: Shielding Agents via Verifiable Safety Policy Reasoning | 2025 | International Conference on Machine Learning | PR (proceedings-URL)| §2.2-2.4, §5 Evaluation |
| `yang2023plug` | Plug in the Safety Chip: Enforcing Constraints for LLM-driven Robot Agents | 2023 | IEEE International Conference on Robotics and Automation | PR (DOI-verified) | §2.2-2.4, §5 Evaluation |
| `abdelnabi2025firewalls` | Firewalls to Secure Dynamic LLM Agentic Networks | 2025 | Trans. Mach. Learn. Res. | PR (proceedings-URL)| §2.2-2.4, §5 Evaluation |
| `liu2025processcentric` | Process-Centric Analysis of Agentic Software Systems | 2025 | Proc. ACM Program. Lang. | PR (DOI-verified) | §2.2-2.4, §5 Evaluation |
| `zheng2025agentsight` | AgentSight: System-Level Observability for AI Agents Using eBPF | 2025 | PACMI@SOSP | PR (DOI-verified) | §2.2-2.4, §5 Evaluation |
| `huang2024on` | On the Resilience of LLM-Based Multi-Agent Collaboration with Faulty Agents | 2024 | International Conference on Machine Learning | PR (proceedings-URL)| §2.2-2.4, §5 Evaluation |
| `motwani2024secret` | Secret Collusion among AI Agents: Multi-Agent Deception via Steganography | 2024 | Neural Information Processing Systems | PR (DOI-verified) | §2.2-2.4, §5 Evaluation |
| `peignelefebvre2025multiagent` | Multi-Agent Security Tax: Trading Off Security and Collaboration Capabilities in Multi-Age | 2025 | AAAI Conference on Artificial Intelligence | PR (DOI-verified)| §2.2-2.4, §5 Evaluation |
| `wang2025shadows` | Shadows in the Code: Exploring the Risks and Defenses of LLM-based Multi-Agent Software De | 2025 | AAAI Conference on Artificial Intelligence | PR (DOI-verified)| §2.2-2.4, §5 Evaluation |
| `khan2025agents` | Agents Under Siege: Breaking Pragmatic Multi-Agent LLM Systems with Optimized Prompt Attac | 2025 | Annual Meeting of the Association for Computational Linguist | PR (DOI-verified)| §2.2-2.4, §5 Evaluation |
| `amayuelas2024multiagent` | MultiAgent Collaboration Attack: Investigating Adversarial Attacks in Large Language Model | 2024 | Conference on Empirical Methods in Natural Language Processi | PR (DOI-verified)| §2.2-2.4, §5 Evaluation |
| `zhang2024psysafe` | PsySafe: A Comprehensive Framework for Psychological-based Attack, Defense, and Evaluation | 2024 | Annual Meeting of the Association for Computational Linguist | PR (DOI-verified)| §2.2-2.4, §5 Evaluation |
| `ju2024flooding` | Flooding spread of manipulated knowledge in LLM-based multi-agent communities | 2024 | Science China Information Sciences | PR (DOI-verified) | §2.2-2.4, §5 Evaluation |
| `gomaa2025converse` | ConVerse: Benchmarking Contextual Safety in Agent-to-Agent Conversations | 2025 | Conference of the European Chapter of the Association for Co | PR (DOI-verified)| §2.2-2.4, §5 Evaluation |
| `andriushchenko2024agentharm` | AgentHarm: A Benchmark for Measuring Harmfulness of LLM Agents | 2024 | International Conference on Learning Representations | PR (proceedings-URL)| §2.2-2.4, §5 Evaluation |
| `ruan2023identifying` | Identifying the Risks of LM Agents with an LM-Emulated Sandbox | 2023 | International Conference on Learning Representations | PR (proceedings-URL)| §2.2-2.4, §5 Evaluation |
| `yuan2024rjudge` | R-Judge: Benchmarking Safety Risk Awareness for LLM Agents | 2024 | Conference on Empirical Methods in Natural Language Processi | PR (DOI-verified) | §2.2-2.4, §5 Evaluation |
| `guo2024redcode` | RedCode: Risky Code Execution and Generation Benchmark for Code Agents | 2024 | Neural Information Processing Systems | PR (DOI-verified)| §2.2-2.4, §5 Evaluation |
| `dong2025memory` | Memory Injection Attacks on LLM Agents via Query-Only Interaction | 2025 | Neural Information Processing Systems | PR (DOI-verified) | §2.2-2.4, §5 Evaluation |
| `zou2025security` | Security Challenges in AI Agent Deployment: Insights from a Large Scale Public Competition | 2025 | Neural Information Processing Systems | PR (DOI-verified)| §2.2-2.4, §5 Evaluation |
| `calboreanu2026trace` | TRACE: Runtime Governance, Containment, and Evidence for Autonomous AI Agent Operations | 2026 | IEEE Access | PR (DOI-verified) | §2.2-2.4, §5 Evaluation |
| `gilllakhowal2026deterministic` | Deterministic Runtime Enforcement: The Execution Authority for Autonomous AI Agents | 2026 | IEEE Access | PR (DOI-verified) | §2.2-2.4, §5 Evaluation |
| `le2026crosslayer` | Cross-layer contagion of prompt injections in multi-agent swarms: a multiplex microscopic  | 2026 | Cybersecurity | PR (DOI-verified) | §2.2-2.4, §5 Evaluation |
| `chinaei2026causality` | Causality Laundering: Denial-Feedback Leakage in Tool-Calling LLM Agents | 2026 | arXiv | PP | §2.2 Single-agent tool-call reference monitors (ARM) |
| `chen2026cordon` | Cordon: Semantic Transactions for Tool-Using LLM Agents | 2026 | arXiv | PP | §2.2 Single-agent tool-call reference monitors (Cordon) |
| `narisetty2026adaptive` | Adaptive Evaluation of Out-of-Band Defenses Against Prompt Injection in LLM Agents | 2026 | arXiv | PP | §2.2 Out-of-band adaptive defense evaluation |
| `wang2026killchain` | Kill-Chain Canaries: Stage-Level Tracking of Prompt Injection Across Attack Surfaces and Five Production LLMs | 2026 | arXiv | PP | §2.3 Multi-agent prompt-injection pipeline tracking |
