## GUIDE: An External Reference Monitor That Bounds the Blast Radius of Compromised Agents in LLM Multi-Agent Systems

Author: Shafin Ahmad (https://orcid.org/0009-0008-7351-1609).

Supervisor: Ts. Dr. Maythem Kamal Abbas

Asia Pacific University of Technology and Innovation, Technology Park Malaysia, Bukit Jalil, 57000 Kuala Lumpur, Malaysia.

### Abstract

Prompt injection is hard to prevent inside an LLM reasoning loop. In a multi-step pipeline, an injection in one agent can spread to downstream agents and cause unauthorized actions. This paper assumes that any agent can be compromised and places an external reference monitor at the boundary between agents and tools. The monitor, GUIDE (Governed, Uncertainty-aware, Intent-pinned Delegation Enforcer), computes a static blast-radius bound for any subset of compromised agents. The bound is sound with respect to the monitor's own enforcement, and a bounded exhaustive check of 594,516 influence cases found no violation. On AgentDojo, the static analysis flagged 29 of the 30 benign tasks that enforcement later lost (96.9% accuracy). An assumed-compromise replay contained 92.3% of the 588 in-scope task-injection pairs. Strict enforcement cut benign utility from 95.9% to 62.9%. A directory-aware variant recovered utility to 78.4%, and live attack success under it stayed at 0.5%. On 15 applications built with LangGraph, CrewAI and AutoGen, a compromised reader agent reached its goal in 23 of 90 undefended runs and in none under strict enforcement. A census of 55 workflow configurations found 49 linear chains, where splitting work across agents cannot reduce worst-case reach and least privilege can. Live attacks rarely succeeded on DeepSeek 4.1 Flash even without a defense, so the live security gain rests mainly on a weakened agent, the framework applications and a 20-pair Gemini replication.

Keywords: multi-agent systems, large language models, prompt injection, reference monitor, least privilege, static analysis, blast radius

### 1. Introduction

Most multi-agent systems built on large language models have an unsolved security problem at the execution boundary. When an agent reads an external source, such as a document, a search result, or user input, that untrusted text enters its prompt context. Attacks of this kind are called prompt injection (Greshake et al., 2023), and they are very hard to prevent inside the model's reasoning loop. In a single-agent system, an injection can redirect a tool call directly. In a multi-agent system, the attack can also cross delegation boundaries. A compromised agent can trick downstream agents into running privileged tools (Lee et al., 2026; Le et al., 2026), which the first agent could not call itself.

A defense against this failure mode must assume that compromise can happen. Instead of trying to inspect the model's internal activations, the monitor treats any agent that handles untrusted data as potentially compromised. This paper proposes an external reference monitor, the Governed, Uncertainty-aware, Intent-pinned Delegation Enforcer (GUIDE), which enforces sound capability bounds over multi-agent workflows. GUIDE sits between agent reasoning and the execution of external tools. It checks every proposed tool call and delegation against formal authority limits before any real-world action takes place.

Autonomous agents increasingly cooperate along complex pipelines to complete multi-step tasks (Park et al., 2023; Wang et al., 2024). These systems split a task into specialized roles and coordinate them through message passing or graph execution (Wu et al., 2024; Zhuge et al., 2024). However, empirical studies show that multi-agent systems can fail or drift off course under adversarial pressure (Huang et al., 2024; Khan et al., 2025). Untrusted data in the environment can redirect execution to malicious code (Triedman et al., 2025).

This paper studies how to limit what a compromised agent can do in a multi-agent workflow. GUIDE places an external monitor between agent decisions and tool execution. Before a proposed call or delegation runs, the monitor checks it against the authority that the workflow policy grants and records the result. The design does not assume that agents resist malicious instructions. It limits the damage a compromised agent can cause.

This paper makes four contributions:

- Sound static blast-radius bound (C1). The first contribution is a graph-based upper bound on the tools and resources that any set of compromised agents can reach. Replay testing over 1,575 runs and 2,051 tool calls found no soundness violation, and a bounded exhaustive check of workflow graphs of up to five steps found none either. All 39 direct effects that the bound predicted were also observed in a separate live adaptive-attacker test. Policies synthesized from nominal traces kept every observed valid call and cut the median nominal reach by 50%, or one sink.

- Pre-deployment cost prediction (C2). The static bound also predicts, before any model runs, which benign tasks policy enforcement will block. Two checks were run on all 97 AgentDojo tasks. Against whether the defended run met a policy denial on the task path, the predictor reached 92.8% accuracy (95% Wilson CI [85.8%, 96.5%]). Against the tasks actually lost between the undefended and defended runs, it reached 96.9% accuracy and caught 29 of the 30 lost tasks.

- Topology floor and structural census (C3). For the influence model of Section 3.7, splitting a workflow across more agents never increases the blast radius (Proposition 3). In a linear dependency chain it also cannot lower the worst case below the reach of the whole pipeline, with or without cryptographic signing (Proposition 4). A census of 55 acyclic workflows, 19 self-authored and 36 mined from public repositories, found that 49 (89.1%) are linear chains. All 55 have a single source agent whose influence reaches every later step, so least privilege is the lever that works.

- Empirical containment, trade-off and comparison findings (C4). Under assumed compromise, the reference monitor contained 92.3% of the 588 in-scope AgentDojo pairs (95% Wilson CI [89.9%, 94.2%]) with no soundness violation. Strict provenance enforcement costs benign utility, from 95.9% to 62.9% overall and from 100% to 28.6% on Slack. A directory-aware variant recovers utility to 78.4% overall. Against four AgentDojo baseline defenses under the same model and loop, GUIDE gave the lowest or tied-lowest live attack success. On 15 LangGraph, CrewAI and AutoGen applications it stopped every compromised-reader attack under strict enforcement.

The paper evaluates six research questions:

- RQ1 (Soundness and exactness): Can the worst-case blast radius of an arbitrary compromised subset of agents be soundly bounded before deployment?

- RQ2 (Containment under assumed compromise): Does runtime enforcement at the tool and delegation boundary contain compromised agents under assumed compromise?

- RQ3 (Pre-deployment cost prediction): Can static analysis predict which benign tasks will fail runtime policy enforcement without running the model?

- RQ4 (Topology floor and workflow structure): How does workflow topology constrain blast-radius reduction, and what structures dominate real-world multi-agent systems?

- RQ5 (Cross-model nominal performance): Does runtime reference monitoring affect task success, intent fidelity, or latency on benign tasks across distinct model families?

- RQ6 (Comparison and real-world validity): How does GUIDE compare with existing defenses under identical conditions, and does containment hold in applications built with LangGraph, CrewAI and AutoGen and on a more vulnerable model?

Section 2 reviews related work. Section 3 describes the design of GUIDE and the formal methods. Section 4 reports the results. Section 5 discusses design implications and limitations. Section 6 concludes.

### 2. Related work

Related work was identified through a systematic review that followed PRISMA 2020 (Page et al., 2021) and the guidelines of Kitchenham and Charters (2007). Six search strings combined agent terms such as multi-agent, agentic, LLM agent and tool use with security or orchestration terms such as prompt injection, least privilege, information flow, blast radius and provenance. Each string was run on OpenAlex, arXiv and Semantic Scholar (which replaced DBLP after a bot-challenge failure) for work from January 2022 to the search date. The first 200 records per string and source were kept, so the 18 queries returned 3,600 records.

A record was included if it was in English, concerned LLM-based agents that call tools or exchange messages, and proposed or evaluated a control, an attack analysis or a benchmark. Records were excluded for chatbot safety without tools, multi-agent systems without LLMs, or positions and surveys with no mechanism. Duplicates, inaccessible texts and off-topic term collisions were also excluded. After de-duplication 2,766 records remained. A deterministic keyword pre-filter kept 1,712, title screening kept 631 and abstract screening included 607. Snowballing (Wohlin, 2014) on 43 core works added 114, for 721 included studies. One author screened all records, so no inter-rater agreement is reported. The PRISMA flow diagram (Figure S1) is in the supplementary material.

2.1 Multi-agent coordination and orchestration

Most work on multi-agent orchestration aims at coordination and task completion. MasRouter routes each task to a specialized agent to improve completion efficiency (Yue et al., 2025). Difficulty-aware orchestration adjusts the pipeline topology to the complexity of the input (Su et al., 2026). Evolving orchestration changes the team communication structure during a task (Dang et al., 2025). Ji et al. (2025) model multi-agent workflows as scalable graph generative models. Tree-structured reasoning layouts reduce context loss in long inputs (Yu et al., 2025), and problem drift degrades long multi-agent debates (Becker et al., 2026). Other work models agents as optimizable graphs (Zhuge et al., 2024) or as decentralized evolutionary networks (Yang et al., 2025). SagaLLM adds transaction guarantees and context validation to multi-agent planning (Chang & Geng, 2025), and Pasupuleti et al. (2026) propose policy-compliant orchestration for enterprise deployments. These approaches improve coordination and performance. They do not enforce security policy at the tool boundary, and they do not measure containment when an agent in the topology is compromised.

2.2 Single-agent tool-call reference monitors and information flow control

Single-agent reference monitors and information-flow-control systems check each tool call from one agent against policy rules or information-flow labels. CaMeL attaches capability tokens and data-flow policies to values passing through an agent and checks the policy before each tool call, with a formal safety proof (Debenedetti et al., 2026). Progent controls tool privileges through policy (Shi et al., 2025). FIDES propagates confidentiality and integrity labels through tool executions so that sensitive data cannot flow where it should not (Costa et al., 2025). The Agentic Reference Monitor (ARM) of Chinaei (2026) builds causal provenance graphs of tool calls and return values to stop causality laundering, where information leaks through denial feedback. MiniScope generates tool policies from a permission set to give individual agents least privilege (Zhu et al., 2025). Cordon gives tool-using agents transactional semantics so that tool effects can be separated from execution (Chen et al., 2026).

Narisetty et al. (2026) evaluate how well out-of-band defenses hold against adaptive prompt injection. AgentSpec enforces customizable safety specifications at runtime (H. Wang, Poskitt & Sun, 2025). Gill-Lakhowal (2026) places deterministic execution authority outside the model weights. TRACE records execution provenance for later containment audits (Calboreanu, 2026). Sidik and Rokach (2026) adjust permission scope from past actions, and Y. Wu et al. (2026) infer least-privilege permission profiles from documentation. Permission management is often missing, too broad or too static, as in the Model Context Protocol (Z. Li, K. Li, et al., 2025; Z. Wang et al., 2026). Real-world agents often call privileged tools that the task does not need (Q. Zhang et al., 2026), and they can be misled into choosing an attacker's tool (Mo et al., 2025). ATAG uses attack graphs to assess threats to agent applications (Gandhi et al., 2025). These systems govern the tool calls of one agent. They are not designed for pipelines in which a compromised agent misleads a downstream agent, and they do not compute static blast-radius bounds over multi-agent workflows.

Table 1 compares the closest related systems on target scope, static bound, soundness proof, policy synthesis, and utility prediction.

Table 1. Comparison of security mechanisms in tool-calling and multi-agent workflows.

| Mechanism | Targets multi-agent compromised subsets | Static pre-deployment bound | Soundness proof | Least-privilege synthesis | Deployment-cost prediction |
|---|---|---|---|---|---|
| CaMeL (Debenedetti et al., 2026) | No | No | Yes (runtime safety) | No | No |
| Progent (Shi et al., 2025) | No | No | Not reported | No | No |
| FIDES (Costa et al., 2025) | No | No | Not reported | No | No |
| ARM (Chinaei, 2026) | No | No | Not reported | No | No |
| Parisel (2026) | Yes | Partial (pairwise organizational) | No | No | No |
| Muruaga (2026) | Yes | No | Yes (runtime monotonicity) | No | No |
| Moon & Varshney (2026) | No | No | Yes (Dafny machine-checked) | No | No |
| CAPMAS (Veski et al., 2026) | Yes | No | Not reported | Query-level privilege scoping | No |
| Paul & Nandy (2026) | Yes | No | No | No | No |
| Safin et al. (2026) | Yes | No | No | No | No |
| GUIDE (This paper) | Yes | Yes | Yes (soundness theorem) | Yes | Yes |

2.3 Multi-agent security, prompt injection attacks, and containment

Security risks specific to multi-agent pipelines are a recent research area. Injected prompts can travel through agent messages and infect downstream agents (Lee et al., 2026; Le et al., 2026). Flooding attacks can spread misinformation across communities of agents (Ju et al., 2026). Canary tokens placed at each agent stage can track how injections move along an attack kill chain (Wang & Zhang, 2026). Autonomous agents can collude without central coordination (Motwani et al., 2024), and peer debate can amplify adversarial prompts (Amayuelas et al., 2024). Optimized prompt attacks still break multi-agent systems when bandwidth and topology limit how an attack travels (Khan et al., 2025). Multi-agent code generation systems are open to shadow injection, especially through shared repositories (X. Wang et al., 2025). Security checks also add latency and token cost, which Peigné-Lefebvre et al. (2025) describe as a security tax. Collaboration degrades quickly when a failing agent goes unhandled (Huang et al., 2024).

Several defenses target these risks. Abdelnabi, Gomaa and Fritz (2025) place firewall-style filters between collaborating agents to screen their messages. SafeFlow traces semantic data flow so that malicious content cannot spread through the agent graph (Dai et al., 2026). G-Safeguard uses a topology-guided graph model to detect and treat attacks in multi-agent systems (S. Wang et al., 2025). F. Liu et al. (2025) detect taint-style vulnerabilities in agent logic automatically. GuardAgent checks proposed plans before they run (Xiang et al., 2024), and ShieldAgent uses formal policy reasoning to guard agent decisions (Chen et al., 2025). For robot agents, a safety chip module enforces constraints on planned actions (Z. Yang et al., 2024). SAGA is a security architecture for governing agentic systems (Syros et al., 2025). CaMeLoT monitors agents at runtime and enforces safety and liveness properties written in temporal logic (Nikolaou et al., 2026). Splitting an agent's responsibilities across several agents can also reduce compliance with the overall policy (Li & Wang, 2026).

Benchmark studies show how hard indirect prompt injection is to contain. Adaptive attacks get past static detection filters (Zhan et al., 2025). Task alignment filters try to stop irrelevant instructions from entering the execution loop (F. Jia et al., 2025). Injection into tool selection remains a serious problem (J. Shi et al., 2026). DataSentinel uses a game-theoretic detector to flag injected prompts (Y. Liu et al., 2025). IPIGuard uses tool dependency graphs as a structural defense against indirect payloads (An et al., 2025). DRIFT isolates injections in single-agent runs through dynamic rules (Z. Li, Zhang, et al., 2025). DataFilter cleans untrusted input before the agent uses it (Y. Wang, Chen, et al., 2026). MELON detects injections by re-running the agent with the user task masked and comparing the tool calls (S. Zhu et al., 2025). ACE proposes a security architecture for LLM-integrated app systems (E. Li et al., 2026).

AttnTrace uses attention weights to trace which input tokens caused an injected output (Y. Wang, Geng, et al., 2026). Formal definitions of prompt-injection attacks and defenses make systematic benchmarking possible (Y. Liu et al., 2024). Activation deltas inside the model can detect task drift caused by injected text (Abdelnabi, Fay, et al., 2025). Large-scale evaluations show that most prompt-injection defenses fail under adaptive attacks (Y. Jia et al., 2026). With many tools, cross-tool pollution lets input from one tool affect later calls (Z. Li et al., 2026). Protocol flaws in agent tool interfaces can give an attacker control of the host (Song et al., 2026). Process-centric analysis traces data flows through enterprise agentic software (S. Liu et al., 2026). AgentSight observes agent activity with eBPF kernel probes (Zheng et al., 2025). PsySafe uses psychological tests to measure the behavioral safety of multi-agent systems (Z. Zhang et al., 2024). ConVerse benchmarks contextual safety in agent-to-agent dialogue (Gomaa et al., 2025).

AgentHarm measures the harmfulness of LLM agents on malicious multi-step tasks (Andriushchenko et al., 2025). Language-model emulators help to identify the risks of agents before deployment (Ruan et al., 2024). Safety-risk benchmarks evaluate how well agents recognize risk (Yuan et al., 2024). Code-execution environments measure how much risky code agents generate or run (Y. Guo et al., 2024). Memory injection attacks alter an agent’s persistent recall across separate sessions (Dong et al., 2025). Public agent-deployment competitions have exposed a broad range of security vulnerabilities in production systems (Zou et al., 2025). Security auditing tools such as Agent Audit automatically check agent codebases for risky tool bindings (H. Zhang et al., 2026).

Agent Security Bench combines attacks and defenses for LLM-based agents (H. Zhang et al., 2024). TAMAS benchmarks adversarial risks in multi-agent LLM systems (Kavathekar et al., 2025). ContainmentBench is a benchmark that assesses containment after the initial compromise of an agent (Lan et al., 2026). BlindGuard protects multi-agent systems against unknown attacks (Miao et al., 2025).

2.4 Static and pre-deployment analysis

Several 2026 preprints partly address pre-deployment and static analysis. Parisel (2026) models an influence graph and a pairwise compositional blast radius over an organizational hierarchy. It gives no static bound, no soundness proof and no running implementation. Muruaga (2026) shows that the delegation scope of a chain of principals shrinks monotonically at runtime. It checks scopes during execution and does not compute a scope for a whole workflow before deployment. Moon and Varshney (2026) verify single-agent runtime containment mechanically but do not model multi-agent influence. Paul and Nandy (2026) list 14 attack vectors and propose a defense architecture with signed messages, provenance tracking, boundary sanitization, role-scoped tool privileges and anomaly detection.

Safin et al. (2026) propose an architectural pattern with per-task signed tokens and a policy oracle against a malicious validator in a four-agent LangGraph pipeline. CAPMAS (Veski et al., 2026) passes monotonic Macaroon tokens for delegation. Neither computes an a priori blast-radius bound for a workflow, and CAPMAS does not prove soundness against a compromised delegating agent. AgentFlow builds agent dependency graphs for static analysis of agent programs (S. Wang et al., 2026). Its focus is finding bugs in agent code, not limiting what a compromised agent can reach.

2.5 Evaluation benchmarks

Standard security benchmarks focus on single-agent execution. AgentDojo evaluates prompt-injection defenses for single agents on both utility and security (Debenedetti et al., 2024). InjecAgent evaluates indirect prompt injection for single agents (Zhan et al., 2024), and τ-bench measures reliability in realistic tasks that involve agents and users (Yao et al., 2025). There is no standard benchmark for compromised agents in multi-agent workflows. This paper therefore builds a multi-agent containment suite with internal attack scenarios, evaluates runtime tool enforcement on AgentDojo under assumed compromise, and tests 15 applications built with LangGraph, CrewAI and AutoGen.

### 3. Materials and methods

3.1 Research design

This study follows design science research (Hevner et al., 2004). It builds and tests an external reference monitor for a defined computing problem, not a commercial product. The study maps onto the six activities of Peffers et al. (2007). Section 1 identifies the problem, the objectives answer RQ1 to RQ6 and the reference monitor is the design artifact. Nominal runs give the demonstration, Section 4 gives the evaluation, and this paper with the archived code is the communication. The engineering principle is that the model proposes and external code disposes (Moutesidis, 2026). The unit of analysis is the monitor, not the model, so every condition uses the same tasks, tools, decoding settings and base models. Table 2 maps research questions to objectives, hypotheses and evidence.

Table 2. Correspondence between research questions, research objectives, research hypotheses and evidence.

| Research Question | Objective | Hypothesis | Primary Evidence Source |
|---|---|---|---|
| RQ1: Bound Soundness | O1: Formulate and prove static blast-radius bound | H1: Soundness correspondence and step containment hold for any compromised subset | Theorem 1 and 2 proofs, property tests (0 counterexamples), live adaptive attacker (39/39 exactness) |
| RQ2: Runtime Containment | O2: Evaluate tool-boundary runtime enforcement | H2a to H2c: Policy gate and provenance guard contain out-of-domain and in-domain steering (H2a), adaptive routing and re-dispatch recover from degraded agents (H2b), and per-principal keys detect spoofing (H2c) | Protocol v8 M1 replay (588 in-scope of 949 AgentDojo pairs, 92.3% containment), internal suite (K1 to K4) |
| RQ3: Cost Prediction | O3: Predict deployment utility cost statically | H3: Static admissibility predicts runtime utility degradation without model execution | Protocol v8 M1b (97 tasks, 96.9% accuracy, 31 predicted blocks vs 30 observed losses) |
| RQ4: Topology Floor | O4: Establish workflow topology constraints | H4: Sequential agent decomposition cannot reduce worst-case blast radius below the full pipeline reach | Proposition 4 proof, census of 55 workflows (89.1% linear chains), least-privilege synthesis (50.0% reduction) |
| RQ5: Cross-Model Baseline | O5: Measure nominal performance across model families | H5 (H5a to H5c): Governance overhead stays within 1.30 times the B2 median wall time, and nominal task completion is preserved across models | Protocols v1 to v5 across DeepSeek 4.1 Flash, Gemini 3.5 Flash-Lite, and OpenAI GPT-OSS-120B |
| RQ6: Comparison and Real-World Validity | O6: Compare with existing defenses and validate on framework-built applications | H6: GUIDE lowers attack success compared with no defense, at a utility cost the variants can trade off | Protocol v9 (AgentDojo, 97 tasks and 200 attack pairs, 8 defenses; 15 LangGraph, CrewAI and AutoGen applications, 720 runs; Gemini replication, 20 pairs) |

The hypotheses follow the numbering of the research questions. H1 states that the bound holds for any compromised subset, so no execution produces an effect outside it. H2a states that the policy gate blocks out-of-domain actions and that only the provenance guard stops steering to an in-domain recipient. H2b states that adaptive routing and re-dispatch recover from a permanently degraded agent. H2c states that per-principal signing keys detect sender spoofing. H3 states that static admissibility predicts which benign tasks enforcement will lose.

H4 states that splitting a linear chain across agents cannot lower its worst-case blast radius. H5a states that the controls raise task success and intent fidelity over both baselines, and H5b that they reduce violations on nominal tasks. H5c states that the median wall time stays within 1.30 times that of B2. H6 states that GUIDE lowers attack success compared with no defense, at a utility cost that the enforcement variants can trade off.

3.2 External reference monitor design and controls

GUIDE is an external reference monitor. It sits outside the model and outside the agents, and every proposed tool call and delegation passes through it before any action is taken. The code is split into three packages with a one-way dependency order. The core package holds the monitor primitives. The research package holds the provenance guard and the static analyzer, and the benchmark package holds the task suites and test beds. Continuous integration tests check that the core package imports nothing from the other two. Figure 1 shows GUIDE with its four controls and the data flow of one execution step.

Figure 1. GUIDE as an external reference monitor: controls and data flow for one execution step.

The steps in a run are executed sequentially. A router chooses a candidate agent for each step, and the step inputs reach that agent through a hand-off. The agent then proposes tool calls inside a closed agent loop. Finally, the external reference monitor verifies each proposed call before any tool code runs. GUIDE applies four controls during this execution:

Control 1: Beta posterior routing policy. Routing keeps a success estimate for each candidate agent in each task domain, modeled as a beta distribution (equation (1)):

θi,d∼Beta(αi,d,βi,d)  (1)

Here, θi,d is the success probability of agent i on domain d. The parameters αi,d and βi,d equal one plus the observed successes and failures. The monitor first gives each agent one warm-up task. It then chooses the candidate agent with the largest upper-confidence quantile, following the Bayes-UCB method (Auer et al., 2002; Kaufmann et al., 2012). The score is computed with equation (2). Figure S2 shows a prior simulation of this policy.

Bayes-UCB(i, d) = Q(1 - 1/t, Beta(α_{i,d}, β_{i,d}))  (2)

Here, t is the current step index and Q is the quantile function of the Beta distribution. This gives adaptive routing across candidate agents that aims to minimize regret.

Control 2: Signed hand-off package. A hand-off package holds the run and hand-off identifiers, the hash of the previous package and the task objective. It also lists the constraints, input references, allowed tools, output schemas and expiry time. The package is serialized to canonical JSON over a restricted set of values and signed with the sender's Ed25519 private key (Bernstein et al., 2012). The receiver checks the signature, the hash chain back to the genesis hash, the mandatory fields, the expiry time and the schemas. If any check fails, the hand-off is rejected with an integrity error.

Control 3: Policy gate with SMT. Each proposed tool call is represented as a finite record (Saltzer & Schroeder, 1975; Denning, 1976). The record holds the tool, the operation, the resource class, the column sensitivity and the side-effect flags. The gate checks this record against an external declarative policy written as SMT constraints (Backes et al., 2018). It returns one of three results. It allows the call unchanged, bounds its arguments or denies it. Bounding clamps numeric arguments and restricts column lists to allowed subsets. Denied calls never reach the tool code.

Control 4: Provenance guard. The provenance guard adds a check to the policy gate for calls with side effects (Cheney et al., 2009). Control arguments such as email recipients must be traceable to the trusted task text. In the default mode, the guard accepts a normalized argument if it is a substring of the trusted text. The strict mode requires an exact token match instead. A control argument that cannot be traced to trusted text is refused even when the policy gate allows the call.

The monitor also keeps a hash-linked trace ledger that records each routing decision, hand-off result, policy decision, tool result and step output as it happens.

3.3 Conditions

The four conditions use the same tasks, tools and base model and run in the same evaluation harness.

B1: sequential delegation with fixed agent roles and unstructured plain-text hand-offs.

B2: a workflow graph of steps that passes structured JSON state between steps, with no adaptive routing, no signed hand-off and no policy gate.

P: the reference monitor with Bayes-UCB routing, signed hand-offs and the policy gate, without the provenance guard and without re-dispatch.

GPLUS: P plus the provenance guard, re-dispatch and fail-closed rejection of failed steps.

Six ablations each remove one part of GPLUS. GPLUS-provenance removes the provenance guard, GPLUS-gate the policy gate and GPLUS-signing the signed hand-off. GPLUS-redispatch, GPLUS-routing and GPLUS-trace remove re-dispatch, adaptive routing and the trace ledger. The ablations show which part causes each observed effect.

3.4 Tasks and suites

The main suite has 18 tasks in three families, which are information synthesis, evidence reconciliation and policy-sensitive planning. Each task has 4, 6 or 8 atomic constraints and runs as a three-stage sequence of retrieve, analyze and report. The adversarial suite adds 11 cases. They test missing entities, conflicting data, injected instructions aimed at external and internal sinks, destructive writes and privilege escalation. They also test compromised peers, hand-off tampering, tool outages and malformed outputs. A separate sequence of 20 runs keeps one agent permanently degraded.

The assumed-compromise suite implements the threat model of RQ2. In four scenarios, an attacker call replaces the compromised agent's first tool call. The scenarios are a restricted column read (K1), an external email (K2), in-domain mailbox steering (K3) and a record deletion (K4). The live model runs every later step of the run. This separates what the monitor contains, the action of the compromised agent, from any change in the behavior of the model.

3.5 Models and settings

Protocols v1 to v4 and v6 used DeepSeek 4.1 Flash through the DeepSeek API (requested as deepseek-chat, reported as deepseek-v4-flash or deepseek-flash), with temperature 0, JSON mode and seed 42. Each run allowed 4 tool turns and 2 repairs, and repairs used temperature 0.3. Protocol v9 requested deepseek-flash, which the provider served as the DeepSeek-V4.1-Flash-1017 snapshot, because the earlier name had been dropped. Thinking mode was disabled and temperature was 0. Each call allowed up to 1,024 output tokens, and each AgentDojo task allowed up to 12 agent turns.

Protocol v5 adds OpenAI GPT-OSS-120B (openai/gpt-oss-120b) served through Groq and Google Gemini 3.5 Flash-Lite (gemini-3.5-flash-lite) served through the Gemini API. Temperature, token limit and JSON mode match the DeepSeek runs. No seed was set, because the Gemini endpoint does not accept one. The Protocol v9 replication used Gemini 3.1 Flash-Lite (gemini-3.1-flash-lite) with minimal reasoning effort, because Gemini 2.5 Flash-Lite was closed to new accounts. AgentDojo runs used package version 0.1.35 and benchmark version v1.2.2. The framework applications used LangGraph 1.2.21 (LangChain Inc., 2026), CrewAI 1.15.41 (CrewAI Inc., 2026) and AutoGen AgentChat 0.7.5 (Wu et al., 2024).

3.6 Metrics

Table 3 lists the evaluation metrics and their operational definitions.

Table 3. Evaluation metrics, formal definitions, and instrumentation.

| Metric | Level | Definition | Instrumentation |
|---|---|---|---|
| Task Success | Run | Binary flag indicating all mandatory task constraints were satisfied | Deterministic rule checker against step deliverables |
| Intent Fidelity | Run | Fraction of task atomic constraints satisfied (continuous [0, 1]) | Normalized score over per-constraint assertion checks |
| Violation Rate | Run | Binary flag indicating disclosure of restricted data, illegal write, or unapproved recipient | Tool audit log and context disclosure scan |
| Attack Success Rate (ASR) | Suite | Fraction of adversarial or compromised runs achieving attacker objective | Evaluated over adversarial and assumed-compromise suites |
| Trace Completeness | Run | Fraction of required linked trace events present and verifiable | Cryptographic verification of trace ledger hashes |
| Integrity Detection | Run | Fraction of seeded invalid or tampered hand-off packages rejected | Hand-off receiver verification error count |
| Execution Latency | Run | End-to-end wall-clock time in seconds and monitor execution time in milliseconds | High-resolution monotonic timers |
| Token Usage | Run | Total prompt tokens and completion tokens consumed per run | Token accounting ledger from provider responses |

Every check is deterministic and computed without access to the condition label that produced the run.

3.7 Static blast-radius analysis

The formal model treats a deployment as a workflow graph of steps and agents, with metadata for tools and declarative security policies. An adversary controls the output of a compromised subset of agents, the content returned by injectable tools and the hand-off transport. The correspondence lemma shows that the policy gate’s decision procedure at every step corresponds to the mathematical definition of authority. The step-containment theorem then shows that, whatever the adversary does, no execution produces an effect outside the gate’s authority rule. An influence relation propagates from compromised steps through shared state, hand-off context and injectable tools. The blast radius of a compromised subset is bounded by the union of the authority of every step that the influence relation can reach. Equation (3) defines this bound:

Reach(C)=⋃s∈Inf(C)Auth(s)  (3)

Here, C is the set of compromised steps, Inf(C) is the set of steps influenced by C and Auth(s) is the authority that the policy gate awards at step s. This is an upper bound on all adversary-dependent effects (Theorem 1). Theorem 2 shows that actions outside the influence relation are unaffected by the adversary. Least-privilege policy synthesis produces a minimal policy that admits the observed nominal executions, keeps the bound and adds no nominal denials. Equation (4) defines this policy:

Policy*(s)=⋂{P∣NominalExec(s)⊆P}  (4)

Here P denotes a policy, and NominalExec(s) is the set of calls observed at step s in nominal runs.

The bound rests on four assumptions. The monitor, the policy and the tool metadata are trusted, and no agent can change them. Each tool is classified correctly, meaning which operations write or reach outside the system and which arguments are control parameters. Every effect passes through a tool call that the monitor checks, so text-only harm is out of scope. The workflow graph is acyclic and fixed before the run.

Under these assumptions the bound limits which effects can happen, not whether their content is harmful. A call that the policy allows with a trusted recipient can still carry attacker-written content, such as a calendar event body. Signing also does not help when a compromised upstream agent writes a malicious package and signs it legitimately, because the signature only proves who sent it. Soundness is therefore stated with respect to the monitor's own enforcement.

A bounded exhaustive check tested the formal model without any API calls. It compared the influence analysis with an independent graph-reachability oracle on every acyclic workflow of up to five steps. The enumeration covered hand-off modes, tool assignments, write policies and compromised subsets. It also compared the authority rule with the real gate over a full grid of policies, delegations, gate settings and calls.

3.8 Protocol, statistics and deviations

All evaluation protocols were frozen in version control before the corresponding runs. Deviations from the proposal are listed in Table 4. Per-condition summaries are based on the mean and a 95% cluster-bootstrap confidence interval over tasks (with 10,000 resamples). Paired comparisons involve two-sided Wilcoxon signed-rank tests (with Pratt's correction for zero difference) and Holm correction within metric families.

Protocol v9 reports rates with 95% Wilson intervals (Wilson, 1927). Paired comparisons on the same tasks use the exact McNemar test (McNemar, 1947), and effect sizes use Cohen's h (Cohen, 1988). The 200 attack pairs give a Wilson half-width of at most 6.9 percentage points, and the 97 benign tasks give at most 9.8 points. These sizes were fixed before the runs to fit the API budget. Benign runs for the four GUIDE conditions were repeated three times, and attack runs were run once at temperature 0.

Protocols are numbered in the order in which they were frozen. Protocols v1 to v4 cover the DeepSeek main suite and the adversarial and assumed-compromise suites. Protocol v5 covers the two additional model families. AgentDojo runs under protocols v6 and v6b (with and without GUIDE), v7a (predicting utility cost), v7b (mining real-world configurations) and v7c (analyzing topology). Protocol v8 adds the assumed-compromise replay (M1), the cost-prediction check (M1b) and the topology theory and census (M2). Protocol v9 adds the live AgentDojo comparison with baseline defenses and enforcement variants (v9a), the framework-built applications (v9b), the adaptive attacker (v9c) and the Gemini replication (v9g).

A summary of all the deviations between the approved research proposal and carried out research is presented in Table 4.

Table 4. Summary of deviations between the approved proposal and executed research. Only deviations that changed the evaluation are listed (12 of 35 IDs).

| ID | Topic | Proposal Plan | Executed Research | Rationale and Effect |
|---|---|---|---|---|
| A7 | Assessor Scoring | Two blinded human assessors scoring 20% sample with Cohen’s kappa | Automated deterministic constraint checking across 100% of runs | Replaced because the study involves no human participants, and automated deterministic checking is more reproducible |
| A10 | Policy Bounding | Euclidean projection over vector representation | Interval and column-subset projection in policy gate | Vector projection is undefined for discrete tool arguments, and discrete projection is sound |
| A11 | Hand-off Serialization | RFC 8785 JSON canonicalization | Canonical JSON over restricted value domain | Matches implementation capability while guaranteeing deterministic hashing |
| A16/A28 | Multi-Model Evaluation | Single model family (DeepSeek) | Evaluated across DeepSeek 4.1 Flash, Gemini 3.5 Flash-Lite, and OpenAI GPT-OSS-120B | Tests whether results hold across model families, but free tiers allowed only 2 repetitions instead of 5, which lowers statistical power |
| A20 | Compromise Threat Model | Textual indirect prompt injection | Assumed-compromise replay (K1 to K4) replacing the first proposed call | Live models resisted textual injection (0 attempts in 550 runs), replay isolates containment |
| A24 | Policy Language | allow / bound / deny over action record | Column-level and recipient-level allow-lists added | Required to express synthesized least-privilege policies |
| A25 | Provenance Guard | Not specified in proposal | Substring and exact-token provenance guards added | Closes the substring-matching steering vulnerability uncovered by static analysis |
| A27/A33 | Topology Mining | Not specified in proposal | Audit of 19 self-authored and 36 mined public CrewAI configurations | Tests whether the structure generalizes to public multi-agent workflows (CrewAI demonstration repositories only) |
| A31 | Cost Prediction | Not specified in proposal | Static admissibility predictor evaluated on AgentDojo | Enables pre-deployment evaluation of security versus utility trade-offs |
| A32 | Topology Theory | Not specified in proposal | Formulated Proposition 3 (refinement) and Proposition 4 (chain floor) | Shows a structural floor on worst-case blast radius under agent decomposition |
| A34 | Protocol v8 | Single-step synthetic benchmarks | Full 949-pair AgentDojo assumed-compromise replay | Validation on an external tool-using benchmark using recorded ground-truth attacker calls |
| A35 | Protocol v9 | Not specified in proposal | Live AgentDojo comparison with four baseline defenses and two enforcement variants, 15 framework-built applications, an adaptive attacker and a Gemini replication | Adds quantitative comparison and real-world validation. The model snapshot changed, so every live condition was rerun |

3.9 Ethics and data

All data in the sandbox are synthetic or public. No human subjects or human data were used. The sandbox tool set is allow-listed, and nothing can write to the network beyond the simulated email tool.

3.10 External benchmark: AgentDojo

AgentDojo (Debenedetti et al., 2024) is an external benchmark for tool-using agents in the Banking, Slack, Travel and Workspace domains. This paper uses it to evaluate the deployment cost of agent defenses and tool-boundary enforcement.

AgentDojo is evaluated under three protocols. Protocol v6 runs GUIDE on DeepSeek 4.1 Flash. Protocol v6b is the baseline run with no defense. Protocol v8 (M1) replays all 949 task-injection pairs under assumed compromise. Protocol v9a reruns AgentDojo on the current model snapshot and adds the baselines and enforcement variants of Section 3.14.

3.11 Pre-deployment cost prediction

Protocols v7a and v8 (M1b) test whether the utility cost can be determined in advance, without deployment. The static predictor flags a task as blocked when its required calls conflict with the synthesized policies or the provenance constraints.

3.12 Workflow topology analysis

Protocols v7c and v8 (M2) investigate the limits that workflow topology places on blast radius. Proposition 3 states that refinement is monotonic. In linear dependency chains, Proposition 4 shows that the worst-case blast radius equals that of the unpartitioned pipeline, however the steps are split across agents. The reachable sink set of any compromised step sk in a linear chain of length N is given by equation (5).

Reach(s_k) = ⋃_{j=k..N} Sinks(s_j)  (5)

Here, Sinks(sj) is the set of write or external tool capabilities available at step sj.

3.13 Real-world configuration mining

Protocol v7b mines public repositories (CrewAI, LangGraph and AutoGen) through search queries. Extraction found 37 configurations (36 CrewAI and 1 LangGraph). The LangGraph configuration was cyclic, so it was not scored, which leaves 36 scored CrewAI configurations. No usable AutoGen configuration was available.

3.14 Protocol v9: variants, baselines and framework applications

Protocol v9 adds two enforcement variants that were designed from the Slack failures of Protocol v6. In 13 of the 15 Slack tasks that failed under GUIDE, a provenance denial blocked a value that the agent had read from a tool, most often a channel or user name from a listing tool. The cred variant also treats credential and profile fields as control parameters. The flexI_cred variant adds this and admits an identifier returned by a directory tool, but only for internal sinks. Both were chosen on a seeded 30% development split of AgentDojo tasks before the held-out tasks were scored.

The comparison uses four AgentDojo baseline defenses inside the same agent loop, model and settings. They are tool filtering, spotlighting with delimiters (Hines et al., 2024), repeating the user prompt and a DeBERTa prompt-injection detector (Protect AI, 2024). Benign utility was measured on all 97 tasks. Attacks used a seeded sample of 200 in-scope pairs, stratified so that every injection task appears. The attacked agent was told to follow instructions found in tool outputs, because the default agent resisted the standard attacks.

Three attack templates were used. Two are the AgentDojo direct and important_instructions attacks, and the third is a GUIDE-aware text that claims prior authorization and asks the agent to retry or switch tools after a denial. An adaptive attacker was also run on 30 pairs. A second LLM wrote the injection, read the monitor's denial or the agent's reply and rewrote the text for up to five rounds. The tool filter lists the tools in its prompt, because the provider ignored tool schemas when tool calling was disabled. Detector inputs were truncated to its 512-token window partway through the run.

Fifteen applications were built with the real frameworks, five per framework, so the framework runs the orchestration and only the tool boundary is instrumented. The LangGraph applications cover sequential, supervisor, parallel fan-out, conditional router and cyclic review topologies. The CrewAI applications cover sequential, hierarchical, parallel, conditional and guardrail-retry topologies. The AutoGen applications cover round-robin, selector, swarm and two graph-flow topologies. Each application uses one of five sandboxed domains with stateful tool backends, from customer support to recruiting.

Each application ran 2 benign tasks and 10 injected tasks under four conditions, for 720 runs. In 6 of the injected tasks the reader agent was assumed compromised and relayed an attacker's request to the acting agent, which matches the threat model of Section 3.7. The other 4 placed the injection in a tool output. Success was read from the sandbox state, not from model text. Before the runs, the guard rule predicted whether each attacker sink call would be admitted, which tests the predictor on applications it had not seen.

A replication on Gemini 3.1 Flash-Lite used the default agent prompt, the important_instructions attack and the first 20 pairs of the frozen sample under the four GUIDE conditions. Its size was set by the free-tier request quota.

### 4. Results

4.1 RQ1: Soundness and exactness of the bound

For 1,575 runs that generated 2,051 tool calls, the effects of each run were replayed against the bound computed for the compromised set of tools. The replay found no containment violations and no blast-radius violations. All 55 harmful effects seen in the assumed-compromise suite fell within the bound predicted for that run before it was executed. A least-privilege policy built from nominal traces rejected none of 44 held-out calls. It completed its tasks in 36 runs with no policy denials and made the policy much smaller. For one representative task, the default gate admitted any recipient in the organization’s domain, whereas the synthesized policy admitted exactly one recipient.

The same task was then attacked with eight variants by a live adaptive attacker in 120 runs. There was no soundness violation, and all 75 runs that the bound predicted blocked showed no harmful effect. For direct compromise the bound was tight. All 39 predicted-reachable direct effects happened when the attacker was free to cause them.

One variant sent an email to an address that contained a trusted recipient as a substring. The static bound predicts that this attack is reachable under substring matching. In the default substring matching mode, the guard admits 692 distinct recipient strings (Figure 2). With exact-token matching or the synthesized least-privilege policy, only one recipient is accepted, and the same attack was refused in each of three rounds.

A second variant tried to control a downstream agent with tainted upstream output. The downstream model ignored the injected instruction, so the attack failed in all six repetitions. This does not violate the predicted bound. The bound over-approximates what this attack could do, as intended.

The bounded exhaustive check found no disagreement. The influence analysis matched the oracle in all 594,516 cases and was monotone in the compromised set. The authority rule matched the real gate in all 1,966,080 evaluations, with no soundness and no exactness violation. The gate executed 250,880 of these calls and denied 1,715,200, so both outcomes were well covered. The check covers only the enumerated space, so it adds to the proofs but does not replace a machine-checked proof.

Figure 2. Admissible recipients for one representative sink (task T15), by policy. The baseline and the policy gate admit an unbounded, domain-wide set of recipients. The default substring-matching provenance guard admits 692 distinct strings, whereas exact-token provenance and the synthesized least-privilege policy each admit exactly one.

To test whether the analysis generalizes to new enterprise domains, 19 self-authored configurations that reproduce LangGraph, CrewAI and AutoGen patterns were analyzed. The framework code was not executed for this analysis. In 18 of the 19 configurations, at least one agent can reach more effects than its role needs, because common integration methods hand whole tool objects to agents. Giving agents single operations instead removes this excess. Least-privilege synthesis cut reachable sink capability by 55.6% overall and rejected no nominal call in any configuration.

4.2 RQ2: Containment under assumed compromise

Table 5 reports the assumed-compromise results on DeepSeek 4.1 Flash with five repetitions per cell, and Figure 3 shows the four cases for all three model families. The pattern is the same in every model. In K1 the compromised agent reads restricted columns. The violation rate is 0.0 in all conditions because no model copied a restricted value into the final output. But the ungated conditions B1 and B2 expose restricted columns, while P and GPLUS do not.

The ungated baselines violated policy in every trial of external email (K2) and record deletion (K4), and the gated conditions in none. The gate cannot stop in-domain mailbox steering (K3), so P shows 100% violations like the baselines, because the target domain is allowed. GPLUS adds the provenance guard to the same gate and shows 0% on K3 for all models. Removing either the guard or the gate from GPLUS brings the K3 violations back. This supports H2a.

Table 5. Violation rate under assumed compromise on all attack cases and conditions for DeepSeek 4.1 Flash (restricted exposure is reported for K1).

| Attack Case | B1 | B2 | P | GPLUS | GPLUS-provenance | GPLUS-gate | GPLUS-signing |
|---|---|---|---|---|---|---|---|
| K1: Restricted-column read (violation rate) | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| K1: Restricted-column read (restricted exposure) | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 |
| K2: External-domain email | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 |
| K3: In-domain email named only in tool data | 1.0 | 1.0 | 1.0 | 0.0 | 1.0 | 1.0 | 0.0 |
| K4: Record deletion | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 |

Figure 3. Violation rate when assuming compromise (K1 to K4) per condition and model. The darker the cell, the higher the rate of violations.

The textual injection suite produced no successful attack in 550 runs on DeepSeek, because the model treated the injected text as data. With per-principal keys, the integrity suite flagged all 10 seeded tampering classes with no false rejections. With a shared key, no sender-spoofing attempt was detected, which supports H2c. In the degraded-agent sequence (Figure 4), the statically assigned baseline did not recover within 20 runs. Adaptive routing failed once in warm-up and then completed 19 of 20 runs, and every re-dispatch succeeded, which supports H2b.

Figure 4. Degraded-agent sequence: cumulative completed runs over 20 consecutive runs with one agent permanently faulty.

To measure tool-boundary enforcement on a standard external benchmark, Protocol v8 (M1) replays an assumed-compromise scenario over all 949 task-injection pairs in AgentDojo. Of these, 588 pairs are in scope because the attacker's goal needs at least one write or external call. The other 361 pairs have read-only goals, so there is no action to contain. A pair counts as contained if all attacker sink calls in it are denied, as partial if some are denied, and as executed if they run. Table 6 shows the results for the four suites.

Table 6. Assumed-compromise containment replay on AgentDojo (Protocol v8 M1).

| Suite | Pairs (Full) | In-Scope Pairs | Contained | Partial | Executed | Containment Rate [95% Wilson CI] | v6-Subset Containment | Undefended Containment |
|---|---|---|---|---|---|---|---|---|
| Banking | 144 | 144 | 128 | 0 | 16 | 88.9% [82.7%, 93.0%] | 88.9% [82.7%, 93.0%] | 0.0% |
| Slack | 105 | 84 | 79 | 0 | 5 | 94.0% [86.8%, 97.4%] | 94.0% [86.8%, 97.4%] | 0.0% |
| Travel | 140 | 120 | 99 | 0 | 21 | 82.5% [74.7%, 88.3%] | 82.5% [74.7%, 88.3%] | 0.0% |
| Workspace | 560 | 240 | 237 | 0 | 3 | 98.8% [96.4%, 99.6%] | 98.3% [91.1%, 99.7%] | 0.0% |
| Total | 949 | 588 | 543 | 0 | 45 | 92.3% [89.9%, 94.2%] | 89.5% [86.1%, 92.1%] | 0.0% |

The overall containment score is 92.3% (543 of 588 in-scope pairs contained, 95% Wilson CI [89.9%, 94.2%]). On the v6 task subset, containment reaches 89.5% [86.1%, 92.1%]. Without runtime gating, containment is 0.0%, because every tool call runs. The runtime monitor blocked 657 of the 702 attacker sink invocations (93.6%).

Table 7 shows that the static bound correctly predicts the runtime outcome for all 588 in-scope pairs. There were no soundness violations (no pair predicted blocked was executed) and no exactness gaps (no pair predicted allowed was contained).

Table 7. Bound prediction versus runtime containment on AgentDojo (Protocol v8 M1).

| Prediction | Runtime Contained | Runtime Executed |
|---|---|---|
| Predicted Blocked | 543 | 0 |
| Predicted Allowed | 0 | 45 |

The 45 uncontained pairs fall into two classes. In 16 banking pairs the attacker changes the password through update_password, an operation with no argument that the v8 policy treats as a control parameter. In the other 29 pairs the control value also appears in the user's request, so the provenance check accepts it. These are 20 travel pairs that create a calendar event, 1 travel email, 5 Slack direct messages and 3 workspace file deletions. The cred variant of Section 3.14 closes the first class and raises full-grid containment to 559 of 588 pairs (95.1%). The second class remains, because the call itself is allowed and only its content is harmful.

Table 8 gives the paired results of Protocol v6 (defended) and Protocol v6b (undefended) on DeepSeek 4.1 Flash.

Table 8. AgentDojo benchmark performance comparison: defended (Protocol v6) versus undefended (Protocol v6b).

| Suite | Protocol v6b Benign Utility | Protocol v6 Benign Utility | Utility Cost (pp) | Protocol v6b Attack Utility | Protocol v6 Attack Utility | Protocol v6b ASR | Protocol v6 ASR |
|---|---|---|---|---|---|---|---|
| Banking | 93.8% | 75.0% | 18.8 | 86.8% | 79.2% | 0.0% | 0.0% |
| Slack | 95.2% | 28.6% | 66.7 | 75.2% | 28.6% | 0.0% | 0.0% |
| Travel | 80.0% | 80.0% | 0.0 | 77.9% | 75.7% | 7.9% | 8.6% |
| Workspace | 95.0% | 65.0% | 30.0 | 100.0% | 80.0% | 0.0% | 0.0% |
| Overall | 91.8% | 61.9% | 29.9 | 85.6% | 68.4% | 2.1% | 2.3% |

Note. Benign utility is evaluated over 97 benign tasks (Banking: 16, Slack: 21, Travel: 20, Workspace: 40). Attack utility and attack success rate (ASR) are evaluated over 529 attacked task–injection pairs (Banking: 144, Slack: 105, Travel: 140, Workspace: 140).

Protocol v6 consumed 11,426,990 tokens costing 13.93 CNY. Protocol v6b consumed 9,068,246 tokens costing 10.89 CNY.

Under Protocol v6 (defended), benign utility is 61.9% (60/97) and attack utility is 68.4% (362/529), with an attack success rate of 2.3% (12/529). Under Protocol v6b (undefended), benign utility is 91.8% (89/97) and attack utility is 85.6% (453/529), with an attack success rate of 2.1% (11/529).

Two findings stand out. First, DeepSeek 4.1 Flash resists prompt injection on its own, with an undefended attack success rate of only 2.1%. Live attack success therefore says little about how well a defense works on this model. Section 4.6 tests this with a more susceptible agent configuration and a second model. Second, strict enforcement has a large utility cost. Benign utility fell by 29.9 percentage points overall, from 91.8% to 61.9%. On Slack it fell from 95.2% to 28.6%, a cost of 66.7 points. Figure 5 shows undefended utility, defended utility and assumed-compromise containment.

Figure 5. AgentDojo benchmark performance across suites: undefended benign utility (Protocol v6b), defended benign utility (Protocol v6), and assumed-compromise containment rate (Protocol v8 M1).

4.3 RQ3: Pre-deployment cost prediction

Protocol v7a tested whether static analysis predicts, before deployment, which of AgentDojo's 97 nominal tasks enforcement will block. Its reference is whether the defended run met a policy denial on the task path. Against this reference the predictor reached 92.8% accuracy (95% Wilson CI [85.8%, 96.5%]), with 28 correct blocks and 3 false blocks. It never predicted success for a task whose required path contained a blocked call. All 4 misses were denials on calls off the required path.

Protocol v8 (M1b) uses a stricter reference, the tasks actually lost, meaning those that succeeded under v6b and failed under v6. Of the 97 tasks, 30 were lost. Table 9 shows the confusion matrix against this reference.

Table 9. Confusion matrix of pre-deployment utility cost prediction (Protocol v8 M1b).

| Prediction | Lost Task (v6b Completed, v6 Failed) | Retained Task (Not Lost) | Total |
|---|---|---|---|
| Predicted Block | 29 | 2 | 31 |
| Not Predicted | 1 | 65 | 66 |
| Total | 30 | 67 | 97 |

The static predictor flagged 31 of the 97 tasks as blocked. It caught 29 of the 30 lost tasks, raised 2 false alarms and missed 1 lost task. Overall accuracy was 96.9% [91.3%, 98.9%], with a precision of 93.5% and a recall of 96.7%. The 31 predicted blocks (32.0 percentage points) compare with 30 observed losses (30.9 percentage points). The net benign utility cost in Table 8 is 29.9 percentage points (29 tasks) rather than 30, because one task succeeded under Protocol v6 but not under Protocol v6b. Static analysis therefore predicts the practical cost of enforcement reasonably well, though not exactly. The two figures answer different questions. The 92.8% measures whether a denial occurs on the task path, and the 96.9% measures whether the task is lost. This supports H3.

4.4 RQ4: Topology floor and workflow structure

Proposition 3 (refinement monotonicity) passed 200 property tests with no counterexample, so splitting an agent's steps never increased the blast radius. Proposition 4 states that, in a linear dependency chain, partitioning cannot lower the worst-case blast radius below that of the whole pipeline. It passed property tests on more than 300 random linear chains and matched the closed form. It also held on 76 real configuration combinations, which are the 19 linear configurations in transcript and signed hand-off modes under nominal and synthesized policies.

In linear chains, only policy changes that remove sink privileges reduce the reach. The median reach is 1.0 sink under the synthesized least-privilege policy and 2.0 sinks under the nominal policy. The median reduction is 1.0 sink and the mean reduction is 0.945 sink.

A structural census covered 55 acyclic multi-agent configurations, 19 self-authored and 36 mined from public repositories, to measure how many are linear chains. Table 10 reports their structural properties.

Table 10. Structural census of 55 acyclic multi-agent configurations.

| Structural Property | Count | Proportion |
|---|---|---|
| Total acyclic configurations (census n) | 55 | 100.0% |
| Strictly sequential linear chains (chain count) | 49 | 89.1% |
| Dominating source agent covering all execution steps | 55 | 100.0% |
| Sink-bearing configurations with blast-radius floor of 1 | 21 | 100.0% |

Of the 55 configurations, 49 (89.1%) are strictly sequential linear chains. All 55 have a single dominating source agent whose influence reaches every later step. All 21 configurations with a sink have a blast-radius floor of one under signed hand-off. In the configurations studied, partitioning agents does not reduce the blast radius without least privilege.

Protocol v7b mined multi-agent workflow configurations from public GitHub repositories for CrewAI, LangGraph and AutoGen. Table 11 reports the mining funnel and the capability metrics.

Table 11. Real-world configuration mining funnel and metrics (Protocol v7b).

| Metric | Count | Estimate [95% Wilson CI] |
|---|---|---|
| Configurations discovered | 37 | - |
| Configurations scored | 36 | - |
| Configurations with no write or external sink | 34 | 94.4% [81.9%, 98.5%] |
| Sequential process type (CrewAI) | 36 | 100.0% [90.4%, 100.0%] |
| Single-agent blast radius contains a sink | 2 | 5.6% [1.5%, 18.1%] |
| Zero-own-sink agent reaches downstream sink | 1 | 2.8% [0.5%, 14.2%] |
| Code execution tool present | 0 | 0.0% [0.0%, 9.6%] |

In total, 37 configurations were found and 36 were scored, because one cyclic LangGraph configuration was excluded. The frozen keyword classifier found no write or external sink in 34 of the 36 (94.4%). All 36 use the CrewAI sequential process type, and 30 of them are linear dependency chains. The two configurations with sinks confirmed the propagation rule of the formal model. In one, a researcher agent with no tools reached a downstream file-writer sink through its context. This supports H4.

4.5 RQ5: Nominal performance across model families

For each condition, separately per model family, main-suite task success, intent fidelity and overhead are reported in Table 12. Task success for the same cells is plotted in Figure 6.

Table 12. Performance across model families (DeepSeek 4.1 Flash, Gemini 3.5 Flash-Lite and OpenAI GPT-OSS-120B) on main-suite tasks.

| Model Family | Condition | Task Success [95% CI] | Intent Fidelity | Violations | Median Tokens | Median Wall Time (s) |
|---|---|---|---|---|---|---|
| DeepSeek 4.1 Flash | B1 | 98.9% [96.7%, 100.0%] | 99.9% | 0 | 3610 | 3.9 |
| DeepSeek 4.1 Flash | B2 | 100.0% [100.0%, 100.0%] | 100.0% | 0 | 3288 | 4.2 |
| DeepSeek 4.1 Flash | P | 98.9% [96.7%, 100.0%] | 99.9% | 0 | 3424 | 4.3 |
| DeepSeek 4.1 Flash | GPLUS | 100.0% [100.0%, 100.0%] | 100.0% | 0 | 3404 | 4.5 |
| Gemini 3.5 Flash-Lite | B1 | 93.5% [79.7%, 100.0%] | 98.9% | 0 | 2642 | 4.9 |
| Gemini 3.5 Flash-Lite | B2 | 96.9% [89.5%, 100.0%] | 99.5% | 0 | 2439 | 5.2 |
| Gemini 3.5 Flash-Lite | P | 96.7% [89.1%, 100.0%] | 99.4% | 0 | 2596 | 5.1 |
| Gemini 3.5 Flash-Lite | GPLUS | 96.8% [89.3%, 100.0%] | 99.5% | 0 | 2714 | 5.2 |
| OpenAI GPT-OSS-120B | B1 | 40.9% [23.8%, 59.0%] | 64.3% | 0 | 3879 | 24.7 |
| OpenAI GPT-OSS-120B | B2 | 39.0% [21.1%, 57.5%] | 66.7% | 0 | 4037 | 16.4 |
| OpenAI GPT-OSS-120B | P | 29.7% [15.8%, 44.7%] | 59.5% | 0 | 4196 | 25.5 |
| OpenAI GPT-OSS-120B | GPLUS | 31.8% [15.2%, 51.2%] | 63.2% | 0 | 3908 | 20.8 |

Task success is at ceiling on DeepSeek 4.1 Flash, with 100.0% for B2 and GPLUS and 98.9% for B1 and P over 360 runs. No run had a violation, and intent fidelity was between 99.9% and 100.0%. After Holm correction, no paired Wilcoxon comparison between conditions is significant. Many tasks had a paired difference of zero, so this is a ceiling effect and not a test of equivalence. No condition met the proposal's bar of a 10-point gain in both success and fidelity, so H5a is not supported. The research plan anticipated this outcome for a capable model.

Gemini 3.5 Flash-Lite shows the same ceiling pattern over 248 completed runs, which include repetitions beyond the two-repetition target. Task success was 93.5% for B1, 96.9% for B2, 96.7% for P and 96.8% for GPLUS, with no violations. OpenAI GPT-OSS-120B on Groq, over 166 completed runs, reached only 40.9% for B1, 39.0% for B2, 29.7% for P and 31.8% for GPLUS. Its low success appears in every condition, so it reflects the model and not the controls. No difference between conditions on this model is significant (Wilcoxon, adjusted p = 1.00). No model had a nominal violation in any condition, so H5b could not be tested because there was nothing for the gate to block.

Figure 6. Main-suite task success by condition and model, mean with 95% cluster-bootstrap confidence interval.

The monitor adds little time compared with model latency. A scripted timing run separates provider latency from monitor cost. The monitor needs 0.16 ms per run for B1, 0.23 ms for B2, 1.68 ms for P and 1.69 ms for GPLUS (Figure 7). With the live DeepSeek model, the median wall time of GPLUS was 1.07 times that of B2, within the 1.30 limit of H5c.

Figure 7. Overhead by condition: Multi-model wall time on DeepSeek 4.1 Flash and monitor-only time (after subtracting out provider latency).

4.6 RQ6: Comparison with existing defenses and framework-built applications

Table 13 compares GUIDE with the AgentDojo baseline defenses on DeepSeek 4.1 Flash under Protocol v9a. Without a defense, benign utility was 95.9%. Strict GUIDE kept 62.9%, close to the 61.9% of Protocol v6, and Slack fell from 100% to 28.6%. The flexI_cred variant raised utility to 78.4% and Slack to 66.7% (exact McNemar p = 0.0007 against strict). The cred variant matched strict on utility. Spotlighting and prompt repetition kept utility near the undefended level, while tool filtering kept 86.6% and the detector 57.7%.

Table 13. Assumed-compromise containment, benign utility and live attack success by defense on AgentDojo (Protocol v9a, DeepSeek 4.1 Flash).

| Defense | Benign utility (97 tasks) | Slack benign utility | Direct attack success | Important-instructions attack success | Utility under direct attack | Full-grid containment (588 pairs) |
|---|---|---|---|---|---|---|
| None | 95.9% | 100.0% | 9.0% | 2.5% | 88.5% | 0.0% |
| GUIDE strict | 62.9% | 28.6% | 0.5% | 0.5% | 58.5% | 92.3% |
| GUIDE cred | 62.9% | 28.6% | 1.0% | 0.5% | 58.5% | 95.1% |
| GUIDE flexI_cred | 78.4% | 66.7% | 0.5% | 0.5% | 73.5% | 88.8% |
| Tool filter | 86.6% | 71.4% | 1.0% | 0.5% | 87.5% | n/a |
| Spotlighting | 95.9% | 100.0% | 4.5% | 0.5% | 85.0% | n/a |
| Repeat user prompt | 94.8% | 100.0% | 4.0% | 0.5% | 90.0% | n/a |
| PI detector | 57.7% | 33.3% | 1.5% | 0.5% | 48.5% | n/a |

Note. Attack success is over a stratified sample of 200 in-scope pairs with an agent told to follow tool outputs. Containment is the assumed-compromise replay and applies only to policy-based defenses.

The direct attack succeeded in 9.0% of the 200 pairs without a defense. Strict GUIDE and flexI_cred cut this to 0.5% (exact McNemar p < 0.001, Cohen's h = 0.47). Tool filtering reached 1.0% and the detector 1.5%, but spotlighting and prompt repetition still allowed 4.5% and 4.0%. The important_instructions and GUIDE-aware attacks rarely succeeded even without a defense (2.5% and 1.0%), so no defense differed significantly on them. The adaptive attacker reached its goal in none of the 30 pairs under any condition, including no defense.

Repeated benign runs changed the outcome of at most 2 of the 97 tasks per condition. Utility for flexI_cred varied between 76.3% and 78.4% across the three runs, so the variant effects are much larger than run-to-run noise.

Table 14 reports the 15 framework applications. The compromised reader reached the attacker's goal in 23 of 90 undefended relay runs (25.6%), and strict and cred enforcement stopped all of them. The flexI_cred variant allowed 6, all in one CrewAI application whose attacker target was a service name returned by a listing tool. Undefended success depended on the application, from 6 of 6 relay runs in the AutoGen selector and CrewAI parallel applications to none in eight others. Insertion attacks in tool output succeeded in only 2 of 60 undefended runs.

Table 14. Benign success and attack success on 15 LangGraph, CrewAI and AutoGen applications by condition (Protocol v9b, DeepSeek 4.1 Flash).

| Condition | Benign success (30 runs) | Compromised-reader attack success (90 runs) | Insertion attack success (60 runs) | Runs with an attacker sink attempt (relay) |
|---|---|---|---|---|
| None | 73.3% | 25.6% | 3.3% | 25 of 90 |
| GUIDE strict | 26.7% | 0.0% | 0.0% | 19 of 90 |
| GUIDE cred | 30.0% | 0.0% | 0.0% | 21 of 90 |
| GUIDE flexI_cred | 43.3% | 6.7% | 3.3% | 27 of 90 |

Enforcement also cost utility in these applications. Benign success fell from 73.3% undefended to 26.7% under strict and 43.3% under flexI_cred. In 52 of the 60 failed benign runs under the three GUIDE conditions, the monitor had denied a value on provenance grounds, the same cause as in AgentDojo.

The guard rule, applied before the runs, predicted the monitor's decision on 84.1% of the 69 attacker sink calls in these unseen applications. No call that it predicted blocked was executed. The 11 disagreements were calls that the monitor denied although the rule predicted them admissible, because the agent had not yet run the lookup that the rule assumed.

On Gemini 3.1 Flash-Lite, the important_instructions attack succeeded in 15 of 20 undefended pairs. All three GUIDE conditions allowed 1 of 20, and utility under attack fell from 12 of 20 to 10 or 11 of 20. The sample is small, so it shows the direction of the effect on a more susceptible model but not its size. This supports H6.

### 5. Discussion

5.1 Why nominal success did not move

The nominal task success result does not show that the controls failed. It is a ceiling effect, because capable models complete most nominal tasks correctly with or without gating and routing. Li and Wang (2026) report the same pattern for hand-off attenuation, which is near zero for large models but grows quickly for smaller models of about 32 billion parameters. The controls can only show a difference when something fails, when the model is weaker, as with GPT-OSS-120B in Section 4.5, or when an agent is compromised, as in Section 4.2.

5.2 Why containment needed two mechanisms, not one

The policy gate blocked every out-of-domain action tested. It does this without reading the task text, because call metadata is enough to identify external domains and destructive deletes. In-domain steering is different. The attacker's target sits inside the allowed domain, so no declarative policy rule can tell it apart. The provenance guard covers this case by checking whether the recipient appears in the trusted task text. The guard still needs the gate, because without it out-of-domain actions would not be blocked.

5.3 What the static bound adds

Measured containment needs a live attacked workflow. The static blast-radius bound of Section 3.7 instead computes, before any code runs, everything that a tainted set of steps can cause. An auditor can then judge the worst case of a configuration without building and running every possible attack.

Static analysis has two further uses. First, it finds structural problems in workflows before deployment. The analysis found over-privilege in 18 of 19 multi-agent configurations. It also found a weakness in the substring-matching provenance guard, which accepts crafted recipients that contain a trusted recipient as a substring. Each finding was then confirmed empirically.

Second, static analysis predicts the utility cost of deployment before execution (C2). Stricter enforcement is more likely to block normal business flows. The predictor caught 29 of the 30 lost AgentDojo tasks (96.9% accuracy), so the trade-off can be judged before deployment.

5.4 Model dependence and the AgentDojo finding

Model compliance is not a reliable form of containment, and AgentDojo shows that it is also a poor way to measure a defense. DeepSeek 4.1 Flash resisted indirect injection on its own, with 2.1% attack success undefended in Protocol v6b. Even an agent told to obey tool outputs was hit by only 9.0% of direct attacks in Protocol v9a. Gemini 3.1 Flash-Lite was hit by 15 of 20, and GUIDE reduced this to 1 of 20. So the size of the live benefit depends on the model, but the assumed-compromise results do not depend on whether the model resists.

The assumed-compromise replay (Protocol v8 M1) tested the monitor directly against the ground-truth malicious tool calls. The monitor blocked 657 of 702 malicious sink calls (93.6%) deterministically. This assurance comes from checking provenance outside the model, not from the model's compliance.

5.5 Topology and least privilege

In strictly linear dependency chains, agent partitioning and cryptographic signing cannot lower the worst-case blast radius below the full pipeline reach (Proposition 4). The structural census found that 49 of the 55 configurations (89.1%) are linear chains and that all 55 have a dominating source agent. So, on the pipelines studied, nothing in the structure stops an upstream compromise from reaching downstream steps. The framework applications show the same, because in all 15 the reader agent can structurally reach an agent that holds a sink.

For sequential workflows, least-privilege policy synthesis is therefore the main way to reduce the blast radius. In linear chains, synthesized policies cut the median reach by 1.0 sink. This protection has a cost. Strict provenance cut Slack benign utility by 71.4 percentage points in Protocol v9a, because downstream calls use values read by earlier calls. The flexI_cred variant recovered 15.5 points of overall utility for a 3.6-point drop in full-grid containment (from 543 to 522 of 588 pairs). Because the cost can be predicted in advance (Section 4.3), a designer can choose the setting on purpose.

5.6 Practical implications

This study gives operators who deploy multi-agent pipelines two concrete outcomes. First, a least-privilege policy can be synthesized directly from recorded traces. It reduces the total reachable sink capability by 55.6% (and the median per-chain reach by 50.0%) while letting valid calls run, so designers do not have to write full security policies by hand. Second, cryptographic hand-offs should use per-principal signing keys. With a shared key, no sender spoofing attempt is detected, although tampering is still detected 100% of the time. With per-principal keys, spoofing is detected as well.

The baseline comparison shows where GUIDE fits. Tool filtering also blocked most direct attacks and kept more utility, because it removes tools that the task does not need. But it depends on the model choosing the right tools, and it gives no bound and no prediction. Spotlighting and prompt repetition kept full or near-full utility but stopped only about half of the direct attacks. GUIDE costs more utility, and in return its containment does not depend on the model.

5.7 Limitations

This study has the following limitations:

Concurrent literature: Six 2026 preprints (Moon & Varshney, 2026; Muruaga, 2026; Parisel, 2026; Paul & Nandy, 2026; Safin et al., 2026; Veski et al., 2026) examine related aspects of least autonomy, delegation security, containment verification and multi-agent authorization. GUIDE is an external reference monitor that also computes multi-agent static bounds, so partial conceptual overlap exists.

Proof verification: The soundness proofs were checked by hand, by property-based testing of the real monitor and by a bounded exhaustive check of workflows of up to five steps. They were not verified with an interactive theorem prover.

Multi-agent evaluation suite: The internal suites and the 15 framework applications were written by the author, with sandboxed tools and author-written tasks. They use the real frameworks but are not third-party production systems, so they may favor the design of the monitor.

External benchmark and models: AgentDojo is a single-agent benchmark. The main runs used DeepSeek 4.1 Flash, and the Gemini replication covered only 20 pairs because of a free-tier quota.

Live sample sizes: The Protocol v6 live attack runs used 10 workspace user tasks, and the Protocol v9 attack runs used a stratified sample of 200 pairs. The assumed-compromise replay covers the full 949-pair grid.

Live injection resistance: DeepSeek 4.1 Flash resisted most live injections even when told to obey tool outputs, so most live attack comparisons have low power. The adaptive attacker was limited to five rounds.

Mined repository scope: Protocol v7b mined public demonstration repositories, and the keyword classifier gives only a lower bound on the number of sinks found.

DAG model constraint: The bound covers directed acyclic graphs only. Cyclic applications were tested live, but the bound was not computed for them.

Text-only attacks: Purely conversational attacks do not call external tools, so a tool-boundary reference monitor cannot address them.

Admitted call classes: Calls whose control value appears in the user's request are admitted, so harmful content in an allowed call is not stopped. This class accounts for 29 of the uncontained AgentDojo pairs.

Comparison scope: CaMeL and Progent were not run under the same conditions, so the quantitative comparison covers the four AgentDojo baseline defenses only.

Baseline implementation: The tool filter lists the tools in its prompt, and detector inputs were truncated to 512 tokens partway through the run.

### 6. Conclusion

This paper evaluated GUIDE, an external reference monitor for LLM multi-agent systems. It computes a static blast-radius bound, synthesizes least-privilege policies and enforces them at runtime.

This paper makes four contributions:

- C1 is a static blast-radius bound for any subset of compromised agents, with least-privilege policy synthesis. Property tests, a bounded exhaustive check and a live adaptive attacker found no soundness violation, and all 39 predicted direct effects were observed.

- C2 is pre-deployment prediction of utility cost. On AgentDojo the static predictor identified, before any run, 29 of the 30 tasks that enforcement lost (96.9% accuracy).

- C3 is the topology floor. Proposition 4 shows that partitioning cannot lower the worst-case reach of a linear chain. Of 55 surveyed configurations, 49 (89.1%) are linear chains, so least privilege is the main way to reduce risk.

- C4 covers the empirical results. Under assumed compromise the monitor contained 543 of 588 in-scope AgentDojo pairs (92.3%). On 15 LangGraph, CrewAI and AutoGen applications, strict enforcement stopped all 90 compromised-reader attack runs (0 of 90 vs. 23 of 90 undefended successes). This protection cost benign utility, which a directory-aware variant partly recovers.

GUIDE is an external reference monitor. It does not depend on agents following their prompts. It enforces bounds at the tool and delegation boundary, which limits what a compromised agent in a multi-agent workflow can reach. It remains open how to constrain the content of allowed calls and how to extend the bound to cyclic workflows.

### Acknowledgments

The author thanks the supervisor, Ts. Dr. Maythem Kamal Abbas, for his guidance. This work received no external funding. API usage for the evaluations in Sections 3.5 and 3.14 on Groq and Google AI Studio fell under each provider’s public free tier. API credits for DeepSeek 4.1 Flash were self-financed.

### Statements

Data availability: All raw results files, code summaries and code manifests of all the protocol versions are archived with the tagged code release at https://github.com/shafin0id/guide.

Code availability: All reference monitor implementation, benchmark tasks and analysis scripts are available at https://github.com/shafin0id/guide.

Author contributions: The author conceived the study, formal model and formal proof, implementation of the reference monitor, and the manuscript. The study was supervised and the manuscript reviewed by the supervisor.

Competing interests: The author declares no competing interests.

Ethics: No human participants or information that could personally identify human participants was used. This study did not need ethics approval.

Generative AI use: Author coding and data aggregation, literature screening, and language editing were done with generative AI tools with the author's guidance and supervision. The author has verified all claims, all numbers and all citations with the data files used in the experiments in this paper.

### References

References are listed alphabetically by first author surname following APA 7th edition.

Abdelnabi, S., Fay, A., Cherubin, G., Salem, A., Fritz, M., & Paverd, A. (2025). Get My Drift? Catching LLM Task Drift with Activation Deltas. 2025 IEEE Conference on Secure and Trustworthy Machine Learning (SaTML), 43–67. https://doi.org/10.1109/satml64287.2025.00011

Abdelnabi, S., Gomaa, A., & Fritz, M. (2025). Firewalls to Secure Dynamic LLM Agentic Networks. Transactions on Machine Learning Research. https://openreview.net/forum?id=G2k9N7wL1M

Amayuelas, A., Yang, X., Antoniades, A., Hua, W., Pan, L., & Wang, W. (2024). MultiAgent Collaboration Attack: Investigating Adversarial Attacks in Large Language Model Collaborations via Debate. Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing, 4732–4749. https://doi.org/10.18653/v1/2024.emnlp-main.274

An, H., Zhang, J., Du, T., Zhou, C., Li, Q., Lin, T., & Ji, S. (2025). IPIGuard: A Novel Tool Dependency Graph-Based Defense Against Indirect Prompt Injection in LLM Agents. Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing, 1023–1039. https://doi.org/10.18653/v1/2025.emnlp-main.53

Andriushchenko, M., Souly, A., Dziemian, M., Duenas, D., Lin, M., Wang, J., Hendrycks, D., Zou, A., Kolter, Z., Fredrikson, M., Winsor, E., Wynne, J., Gal, Y., & Davies, X. (2025). AgentHarm: A Benchmark for Measuring Harmfulness of LLM Agents. International Conference on Learning Representations (ICLR 2025). https://openreview.net/forum?id=AC5n7xHuR1

Auer, P., Cesa-Bianchi, N., & Fischer, P. (2002). Finite-time Analysis of the Multiarmed Bandit Problem. Machine Learning, 47(2–3), 235–256. https://doi.org/10.1023/A:1013689704352

Backes, J., Bolignano, P., Cook, B., & Dodge, C. (2018). Semantic-based Automated Reasoning for AWS Access Policies using SMT. Formal Methods in Computer-Aided Design (FMCAD 2018), 1–9. https://doi.org/10.23919/fmcad.2018.8602994

Becker, J., Kaesberg, L. B., Stephan, A., Wahle, J. P., Ruas, T., & Gipp, B. (2026). Stay Focused: Problem Drift in Multi-Agent Debate. Findings of the Association for Computational Linguistics: EACL 2026. https://doi.org/10.18653/v1/2026.findings-eacl.268

Bernstein, D. J., Duif, N., Lange, T., Schwabe, P., & Yang, B.-Y. (2012). High-speed high-security signatures. Journal of Cryptographic Engineering, 2(2), 77–89. https://doi.org/10.1007/s13389-012-0027-1

Calboreanu, E. (2026). TRACE: Runtime Governance, Containment, and Evidence for Autonomous AI Agent Operations. IEEE Access, 14, 142574–142594. https://doi.org/10.1109/access.2026.3733578

Chang, E. Y., & Geng, L. (2025). SagaLLM: Context Management, Validation, and Transaction Guarantees for Multi-Agent LLM Planning. Proceedings of the VLDB Endowment, 18(12), 4874–4886. https://doi.org/10.14778/3750601.3750611

Chen, Z., Liu, H., Xu, D., Dong, D., Li, J., Pu, B., & Zhai, J. (2026). Cordon: Semantic Transactions for Tool-Using LLM Agents. arXiv preprint arXiv:2606.17573. https://arxiv.org/abs/2606.17573

Chen, Z., Zhang, T., Zhu, S., & Li, B. (2025). ShieldAgent: Shielding Agents via Verifiable Safety Policy Reasoning. Forty-second International Conference on Machine Learning. https://openreview.net/forum?id=DkRYImuQA9

Cheney, J., Chiticariu, L., & Tan, W.-C. (2009). Provenance in Databases: Why, How, and Where. Foundations and Trends in Databases, 1(4), 379–474. https://doi.org/10.1561/1900000006

Chinaei, M. H. (2026). Causality Laundering: Denial-Feedback Leakage in Tool-Calling LLM Agents. arXiv preprint arXiv:2604.04035. https://arxiv.org/abs/2604.04035

Cohen, J. (1988). Statistical power analysis for the behavioral sciences (2nd ed.). Lawrence Erlbaum Associates.

Costa, M., Köpf, B., Kolluri, A., Paverd, A., Russinovich, M., Salem, A., Tople, S., Wutschitz, L., & Zanella-Béguelin, S. (2025). Securing AI Agents with Information-Flow Control. arXiv preprint arXiv:2505.23643. https://arxiv.org/abs/2505.23643

CrewAI Inc. (2026). CrewAI (Version 1.15.41) [Computer software]. https://github.com/crewAIInc/crewAI

Dai, H., Ying, Z., Li, W., Wu, X., Xiao, Y., Zhang, T., Lin, J., Wei, L., Dong, G., Ling, X., Lin, X., Zou, Q., & Zhang, X. (2026). SafeFlow: Semantic Information-Flow Control for Blocking Malicious Propagation in Multi-Agent Systems. arXiv preprint arXiv:2607.25255. https://arxiv.org/abs/2607.25255

Dang, Y., Chen, Q., Luo, X. L., & Fan, J. (2025). Multi-Agent Collaboration via Evolving Orchestration. Proceedings of the 2025 International Conference on Autonomous Agents and Multiagent Systems (AAMAS 2025), 5502–5510. https://doi.org/10.52202/085713-5502

Debenedetti, E., Shumailov, I., Fan, T., Hayes, J., Carlini, N., Fabian, D., Kern, C., Shi, C., Terzis, A., & Tramèr, F. (2026). Defeating Prompt Injections by Design. 2026 IEEE Conference on Secure and Trustworthy Machine Learning (SaTML), 587–618. https://doi.org/10.1109/satml68715.2026.00040

Debenedetti, E., Zhang, J., Balunovic, M., Beurer-Kellner, L., Fischer, M., & Tramèr, F. (2024). AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents. Advances in Neural Information Processing Systems 37, 82895–82920. https://doi.org/10.52202/079017-2636

Denning, D. E. (1976). A lattice model of secure information flow. Communications of the ACM, 19(5), 236–243. https://doi.org/10.1145/360051.360056

Dong, S., Xu, S., He, P., Li, Y., Tang, J., Liu, T., Liu, H., & Xiang, Z. (2025). Memory Injection Attacks on LLM Agents via Query-Only Interaction. Advances in Neural Information Processing Systems 38, 52119–52153. https://doi.org/10.52202/085713-1554

Gandhi, P. A., Shukla, A., Tayouri, D., Ifland, B., Elovici, Y., & Puzis, R. (2025). ATAG: AI-Agent Application Threat Assessment with Attack Graphs. ACM Asia Conference on Computer and Communications Security. https://doi.org/10.1145/3779208.3785380

Gill-Lakhowal, A. (2026). Deterministic Runtime Enforcement: The Execution Authority for Autonomous AI Agents. IEEE Access, 14, 119764–119790. https://doi.org/10.1109/access.2026.3719838

Gomaa, A., Abdelnabi, S., & Fritz, M. (2025). ConVerse: Benchmarking Contextual Safety in Agent-to-Agent Conversations. Proceedings of the 18th Conference of the European Chapter of the Association for Computational Linguistics (Volume 1: Long Papers), 1017–1033. https://doi.org/10.18653/v1/2025.eacl-main.62

Greshake, K., Abdelnabi, S., Mishra, S., Endres, C., Holz, T., & Fritz, M. (2023). Not What You’ve Signed Up For: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection. Proceedings of the 16th ACM Workshop on Artificial Intelligence and Security, 79–90. https://doi.org/10.1145/3605764.3623985

Guo, Y., Hu, X., Zhang, T., Shen, Y., & Xiao, Y. (2024). RedCode: Risky Code Execution and Generation Benchmark for Code Agents. Advances in Neural Information Processing Systems 37, 69022–69051. https://doi.org/10.52202/079017-2197

Hevner, A. R., March, S. T., Park, J., & Ram, S. (2004). Design Science in Information Systems Research. MIS Quarterly, 28(1), 75–105. https://doi.org/10.2307/25148625

Hines, K., Lopez, G., Hall, M., Zarfati, F., Zunger, Y., & Kiciman, E. (2024). Defending Against Indirect Prompt Injection Attacks With Spotlighting. arXiv preprint arXiv:2403.14720. https://arxiv.org/abs/2403.14720

Huang, Y., Shi, C., Wang, J., Zhang, Z., & Li, B. (2024). On the Resilience of LLM-Based Multi-Agent Collaboration with Faulty Agents. Proceedings of the 41st International Conference on Machine Learning, 235, 19949–19972. https://proceedings.mlr.press/v235/huang24s.html

Ji, J., Lei, R., Bi, J., Wei, Z., Chen, X., Lin, Y., Pan, X., Li, Y., & Ding, B. (2025). LLM-Based Multi-Agent Systems are Scalable Graph Generative Models. Findings of the Association for Computational Linguistics: ACL 2025. https://doi.org/10.18653/v1/2025.findings-acl.78

Jia, F., Wu, T., Qin, X., & Squicciarini, A. (2025). The Task Shield: Enforcing Task Alignment to Defend Against Indirect Prompt Injection in LLM Agents. Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), 29680–29697. https://doi.org/10.18653/v1/2025.acl-long.1435

Jia, Y., Shao, Z., Liu, Y., Jia, J., Song, D., & Gong, N. (2026). A Critical Evaluation of Defenses against Prompt Injection Attacks: [Dataset/Tool Paper]. Proceedings of the 31st ACM Symposium on Access Control Models and Technologies, 265–270. https://doi.org/10.1145/3750555.3811884

Ju, T., Wang, Y., Hua, Y., Ma, X., Cheng, P., Zhao, H., Wang, Y., Liu, L., Xie, J., Zhang, Z., & Liu, G. (2026). Flooding spread of manipulated knowledge in LLM-based multi-agent communities. Science China Information Sciences, 69(7). https://doi.org/10.1007/s11432-024-4663-2

Kaufmann, E., Cappé, O., & Garivier, A. (2012). On Bayesian upper confidence bounds for bandit problems. Proceedings of the 15th International Conference on Artificial Intelligence and Statistics, PMLR 22, 592–600. https://proceedings.mlr.press/v22/kaufmann12.html

Kavathekar, I., Jain, H., Rathod, A., & Kumaraguru, P. (2025). TAMAS: Benchmarking Adversarial Risks in Multi-Agent LLM Systems. arXiv preprint arXiv:2511.05269. https://arxiv.org/abs/2511.05269

Khan, R. M. S., Tan, Z., Yun, S., Fleming, C., & Chen, T. (2025). Agents Under Siege: Breaking Pragmatic Multi-Agent LLM Systems with Optimized Prompt Attacks. Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), 8856–8874. https://doi.org/10.18653/v1/2025.acl-long.446

Kitchenham, B., & Charters, S. (2007). Guidelines for performing systematic literature reviews in software engineering (EBSE Technical Report EBSE-2007-01). Keele University and Durham University. https://www.elsevier.com/__data/promis_misc/525444systematicreviewsguide.pdf

Lan, W., Li, S., Wu, M., Lai, X., Yang, J., & Shen, H. (2026). ContainmentBench: Trace-Based Evaluation of Post-Exposure Containment in Tool-Using LLM Agents. arXiv preprint arXiv:2607.23999. https://arxiv.org/abs/2607.23999

LangChain Inc. (2026). LangGraph (Version 1.2.21) [Computer software]. https://github.com/langchain-ai/langgraph

Le, T. D., Dinh, T. D., Nguyen, T. L. Q., & Nguyen, C. D. (2026). Cross-layer contagion of prompt injections in multi-agent swarms: a multiplex microscopic markov chain approach. Cybersecurity, 9(1). https://doi.org/10.1186/s42400-026-00628-w

Lee, D., Tiwari, M., & Miranda, B. (2026). Prompt Infection: LLM-to-LLM Prompt Injection within Multi-agent Systems. Lecture Notes in Computer Science. https://doi.org/10.1007/978-3-032-16092-8_28

Li, B., & Wang, G. (2026). Governance at the Boundary: How Agent Decomposition Degrades Policy Compliance. arXiv preprint arXiv:2608.16055. https://arxiv.org/abs/2608.16055

Li, E., Mallick, T., Rose, E., Robertson, W., Oprea, A., & Nita-Rotaru, C. (2026). ACE: A Security Architecture for LLM-Integrated App Systems. Proceedings 2026 Network and Distributed System Security Symposium. https://doi.org/10.14722/ndss.2026.230352

Li, Z., Cui, J., Liao, X., Xing, L., Xing, L., & Li, Z. (2026). Les Dissonances: Cross-Tool Harvesting and Polluting in Pool-of-Tools Empowered LLM Agents. Proceedings 2026 Network and Distributed System Security Symposium. https://doi.org/10.14722/ndss.2026.240577

Li, Z., Li, K., Ma, B., Xu, M., Zhang, Y., & Cheng, X. (2025). We Urgently Need Privilege Management in MCP: A Measurement of API Usage in MCP Ecosystems. 2025 IEEE 22nd International Conference on Mobile Ad-Hoc and Smart Systems (MASS), 555–560. https://doi.org/10.1109/mass66014.2025.00090

Li, Z., Zhang, T., Hu, X., Shen, Y., & Xiao, Y. (2025). DRIFT: Dynamic Rule-Based Defense with Injection Isolation for Securing LLM Agents. Advances in Neural Information Processing Systems 38, 46083–46109. https://doi.org/10.52202/085713-4886

Liu, F., Zhang, Y., Luo, J., Dai, J., Chen, T., Yuan, L., Yu, Z., Shi, Y., Li, K., Zhou, C., Chen, H., & Yang, M. (2025). Make Agent Defeat Agent: Automatic Detection of Taint-Style Vulnerabilities in LLM-based Agents. 34th USENIX Security Symposium (USENIX Security 25). https://www.usenix.org/conference/usenixsecurity25/presentation/liu-fengyu

Liu, S., Chen, Y., Krishna, R., Sinha, S., Ganhotra, J., & Jabbarvand, R. (2026). Process-Centric Analysis of Agentic Software Systems. Proceedings of the ACM on Programming Languages, 10(OOPSLA1), 1961–1988. https://doi.org/10.1145/3798271

Liu, Y., Jia, Y., Geng, R., Jia, J., & Gong, N. Z. (2024). Formalizing and benchmarking prompt injection attacks and defenses. Proceedings of the 33rd USENIX Security Symposium (USENIX Security 24), 2131–2148. https://www.usenix.org/conference/usenixsecurity24/presentation/liu-yuping

Liu, Y., Jia, Y., Jia, J., Song, D., & Gong, N. Z. (2025). DataSentinel: A Game-Theoretic Detection of Prompt Injection Attacks. 2025 IEEE Symposium on Security and Privacy (SP), 2190–2208. https://doi.org/10.1109/sp61157.2025.00250

McNemar, Q. (1947). Note on the sampling error of the difference between correlated proportions or percentages. Psychometrika, 12(2), 153–157. https://doi.org/10.1007/BF02295996

Miao, R., Liu, Y., Wang, Y., Shen, X., Tan, Y., & Dai, Y. (2025). BlindGuard: Safeguarding LLM-based Multi-Agent Systems under Unknown Attacks. Annual Meeting of the Association for Computational Linguistics. https://arxiv.org/abs/2508.08127

Mo, Y., Wang, H., Chen, Y., & Song, D. (2025). Attractive Metadata Attack: Inducing LLM Agents to Invoke Malicious Tools. Advances in Neural Information Processing Systems 38, 24874–24901. https://doi.org/10.52202/085713-2633

Moon, R., & Varshney, L. R. (2026). Containment Verification: AI Safety Guarantees Independent of Alignment. arXiv preprint arXiv:2605.09045. https://arxiv.org/abs/2605.09045

Motwani, S., Baranchuk, M., Strohmeier, M., Bolina, V., Torr, P., Hammond, L., & Witt, C. D. (2024). Secret Collusion among AI Agents: Multi-Agent Deception via Steganography. Advances in Neural Information Processing Systems 37, 73439–73486. https://doi.org/10.52202/079017-2336

Moutesidis, T. (2026). The Model Proposes, the Code Disposes: A Pre-Registered Ablation of a Verifier-and-Acceptance Stage in an LLM-Orchestrated Offensive-Security Agent. arXiv preprint arXiv:2609.15887. https://arxiv.org/abs/2609.15887

Muruaga, X. (2026). Bounded Agents: Delegation Security for Multi-Agent AI Systems. arXiv preprint arXiv:2608.15888. https://arxiv.org/abs/2608.15888

Narisetty, P., Kore, S. N. B., Kattamanchi, U. K. R., & Kumarapu, J. (2026). Adaptive Evaluation of Out-of-Band Defenses Against Prompt Injection in LLM Agents. arXiv preprint arXiv:2606.26479. https://arxiv.org/abs/2606.26479

Nikolaou, E., Eckhoff, M. W., Flood, R., Grov, G., Mavroeidis, V., & Aspinall, D. (2026). CaMeLoT: CaMeL orchestrated with Temporal logic for static verification and liveness. arXiv preprint arXiv:2609.18674. https://arxiv.org/abs/2609.18674

Page, M. J., McKenzie, J. E., Bossuyt, P. M., Boutron, I., Hoffmann, T. C., Mulrow, C. D., Shamseer, L., Tetzlaff, J. M., Akl, E. A., Brennan, S. E., Chou, R., Glanville, J., Grimshaw, J. M., Hróbjartsson, A., Lalu, M. M., Li, T., Loder, E. W., Mayo-Wilson, E., McDonald, S., . . . Moher, D. (2021). The PRISMA 2020 statement: an updated guideline for reporting systematic reviews. BMJ, 372, n71. https://doi.org/10.1136/bmj.n71

Parisel, C. (2026). A Theory of Least Autonomy in AI. arXiv preprint arXiv:2607.09744. https://arxiv.org/abs/2607.09744

Park, J. S., O’Brien, J., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). Generative Agents: Interactive Simulacra of Human Behavior. Proceedings of the 36th Annual ACM Symposium on User Interface Software and Technology. https://doi.org/10.1145/3586183.3606763

Pasupuleti, V., Allala, S. R., Bayyavarapu, S. R. K. V., & Tyagi, S. (2026). Safe and Policy-Compliant Multi-Agent Orchestration for Enterprise AI. 2026 International Conference on Artificial Intelligence, Systems, and Emerging Technologies (ICAISET). https://doi.org/10.1109/ICAISET66439.2026.11541969

Paul, R. K., & Nandy, S. (2026). Beyond Single-Model Injection: A Threat Model and Defense Architecture for Prompt Injection in Multi-Agent Systems. arXiv preprint arXiv:2609.22949. https://arxiv.org/abs/2609.22949

Peffers, K., Tuunanen, T., Rothenberger, M. A., & Chatterjee, S. (2007). A Design Science Research Methodology for Information Systems Research. Journal of Management Information Systems, 24(3), 45–77. https://doi.org/10.2753/MIS0742-1222240302

Peigné-Lefebvre, M., Wang, X., Tan, Z., & Chen, T. (2025). Multi-Agent Security Tax: Trading Off Security and Collaboration Capabilities in Multi-Agent LLM Systems. Proceedings of the AAAI Conference on Artificial Intelligence, 39(26), 26865–26873. https://doi.org/10.1609/aaai.v39i26.35338

Protect AI. (2024). deberta-v3-base-prompt-injection-v2 [Model]. Hugging Face. https://huggingface.co/protectai/deberta-v3-base-prompt-injection-v2

Ruan, Y., Dong, H., Wang, A., Pitis, S., Zhou, Y., Ba, J., Dubois, Y., Maddison, C. J., & Hashimoto, T. (2024). Identifying the Risks of LM Agents with an LM-Emulated Sandbox. The Twelfth International Conference on Learning Representations (ICLR 2024). https://openreview.net/forum?id=V2s6rVv7tK

Safin, T. H., Zisad, S. N., Shatabda, S., & Hasan, R. (2026). Trust propagation and structural containment in Multi-agent LLM pipelines. arXiv preprint arXiv:2609.17648. https://arxiv.org/abs/2609.17648

Saltzer, J. H., & Schroeder, M. D. (1975). The protection of information in computer systems. Proceedings of the IEEE, 63(9), 1278–1308. https://doi.org/10.1109/PROC.1975.9939

Shi, J., Yuan, Z., Tie, G., Zhou, P., Gong, N., & Sun, L. (2026). Prompt Injection Attack to Tool Selection in LLM Agents. Proceedings 2026 Network and Distributed System Security Symposium. https://doi.org/10.14722/ndss.2026.230675

Shi, T., He, J., Wang, Z., & Li, H. (2025). Progent: Securing AI Agents with Privilege Control. arXiv preprint arXiv:2504.11703. https://arxiv.org/abs/2504.11703

Sidik, B., & Rokach, L. (2026). Beyond Static Sandboxing: Learned Capability Governance for Autonomous AI Agents. arXiv preprint arXiv:2604.11839. https://arxiv.org/abs/2604.11839

Song, H., Shen, Y., Luo, W., Guo, L., Chen, T., Wang, J., Li, B., Zhang, X., & Chen, J. (2026). Beyond the Protocol: Unveiling Attack Vectors in the Model Context Protocol (MCP) Ecosystem. IEEE Transactions on Software Engineering, 52(8), 2410–2426. https://doi.org/10.1109/tse.2026.3694876

Su, J., Lan, Q., Xia, Y., Sun, L., Tian, W., Shi, T., & He, L. (2026). Difficulty-Aware Agentic Orchestration for Query-Specific Multi-Agent Workflows. Proceedings of the ACM Web Conference 2026, 2060–2070. https://doi.org/10.1145/3774904.3792240

Syros, G., Suri, A., Ginesin, J., Nita-Rotaru, C., & Oprea, A. (2025). SAGA: A Security Architecture for Governing AI Agentic Systems. Network and Distributed System Security Symposium. https://arxiv.org/abs/2504.21034

Triedman, H., Jha, R., & Shmatikov, V. (2025). Multi-Agent Systems Execute Arbitrary Malicious Code. Conference on Language Modeling (COLM 2025). https://openreview.net/forum?id=DAozI4etUp

Veski, R. M., Guerraoui, R., & Froelicher, D. (2026). CAPMAS: Capability-Based Delegation of Privileges in Multi-Agent Systems. arXiv preprint arXiv:2609.06500. https://arxiv.org/abs/2609.06500

Wang, H. K., & Zhang, Z. (2026). Kill-Chain Canaries: Stage-Level Tracking of Prompt Injection Across Attack Surfaces and Five Production LLMs. arXiv preprint arXiv:2603.28013. https://arxiv.org/abs/2603.28013

Wang, H., Poskitt, C. M., & Sun, J. (2025). AgentSpec: Customizable Runtime Enforcement for Safe and Reliable LLM Agents. Proceedings of the 48th International Conference on Software Engineering (ICSE 2026), 2938–2950. https://doi.org/10.1145/3744916.3764546

Wang, L., Ma, C., Feng, X., Zhang, Z., Yang, H., Zhang, J., Chen, Z., Tang, J., Chen, X., Lin, Y., Zhao, W. X., Wei, Z., & Wen, J. (2024). A survey on large language model based autonomous agents. Frontiers of Computer Science. https://doi.org/10.1007/s11704-024-40231-1

Wang, S., Hou, X., Zhao, Y., Cheng, X., & Wang, H. (2026). AgentFlow: Building Agent Dependency Graphs for Static Analysis of Agent Programs. arXiv preprint arXiv:2607.01640. https://arxiv.org/abs/2607.01640

Wang, S., Zhang, G., Yu, M., Wan, G., Meng, F., & Guo, C. (2025). G-Safeguard: A Topology-Guided Security Lens and Treatment on LLM-based Multi-agent Systems. Annual Meeting of the Association for Computational Linguistics. https://arxiv.org/abs/2502.11127

Wang, X., Huang, K., Liang, B., Li, H., & Du, X. (2025). Shadows in the Code: Exploring the Risks and Defenses of LLM-based Multi-Agent Software Development Systems. Proceedings of the AAAI Conference on Artificial Intelligence, 39(27), 27504–27512. https://doi.org/10.1609/aaai.v39i27.35411

Wang, Y., Chen, S., Alkhudair, R., Alomair, B., & Wagner, D. (2026). Defending Against Prompt Injection with DataFilter. 2026 IEEE Conference on Secure and Trustworthy Machine Learning (SaTML), 139–157. https://doi.org/10.1109/satml68715.2026.00017

Wang, Y., Geng, R., Chen, Y., & Jia, J. (2026). AttnTrace: Contextual Attribution of Prompt Injection and Knowledge Corruption. 2026 IEEE Symposium on Security and Privacy (SP), 4320–4338. https://doi.org/10.1109/sp63933.2026.00198

Wang, Z., Gao, Y., Wang, Y., Liu, S., Sun, H., Cheng, H., Shi, G., Du, H., & Li, X. (2026). MCPTox: A Benchmark for Tool Poisoning on Real-World MCP Servers. Proceedings of the AAAI Conference on Artificial Intelligence, 40(42), 35811–35819. https://doi.org/10.1609/aaai.v40i42.40895

Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference. Journal of the American Statistical Association, 22(158), 209–212. https://doi.org/10.1080/01621459.1927.10502953

Wohlin, C. (2014). Guidelines for snowballing in systematic literature studies and a replication in software engineering. Proceedings of the 18th International Conference on Evaluation and Assessment in Software Engineering. https://doi.org/10.1145/2601248.2601268

Wu, Q., Bansal, G., Zhang, J., Wu, Y., Li, B., Zhu, E., Jiang, L., Zhang, X., Zhang, S., Liu, J., Awadallah, A. H., White, R. W., Burger, D., & Wang, C. (2024). AutoGen: Enabling next-gen LLM applications via multi-agent conversations. First Conference on Language Modeling (COLM 2024). https://arxiv.org/abs/2308.08155

Wu, Y., Yang, K., Roesner, F., Kohno, T., Zhang, N., & Iqbal, U. (2026). Towards Automating Data Access Permissions in AI Agents. 2026 IEEE Symposium on Security and Privacy (SP), 2609–2627. https://doi.org/10.1109/sp63933.2026.00018

Xiang, Z., Zheng, L., Li, Y., Hong, J., Li, Q., Xie, H., Zhang, J., Xiong, Z., Xie, C., Yang, C., Song, D., & Li, B. (2024). GuardAgent: Safeguard LLM Agents by a Guard Agent via Knowledge-Enabled Reasoning. Proceedings of the 41st International Conference on Machine Learning, 235, 54236–54254. https://proceedings.mlr.press/v235/xiang24c.html

Yang, Y., Chai, H., Shao, S., Song, Y., Qi, S., Rui, R., & Zhang, W. (2025). AgentNet: Decentralized Evolutionary Coordination for LLM-based Multi-Agent Systems. Advances in Neural Information Processing Systems 38, 118758–118785. https://doi.org/10.52202/085713-3578

Yang, Z., Raman, S. S., Shah, A., & Tellex, S. (2024). Plug in the Safety Chip: Enforcing Constraints for LLM-driven Robot Agents. 2024 IEEE International Conference on Robotics and Automation (ICRA), 14435–14442. https://doi.org/10.1109/icra57147.2024.10611447

Yao, S., Shinn, N., Razavi, P., & Narasimhan, K. (2025). τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains. International Conference on Learning Representations (ICLR 2025). https://openreview.net/forum?id=roNSXZpUDN

Yu, S., Xu, X., Deng, K., Li, L., & Tian, L. (2025). Tree of Agents: Improving Long-Context Capabilities of Large Language Models through Multi-Perspective Reasoning. Findings of the Association for Computational Linguistics: EMNLP 2025. https://doi.org/10.18653/v1/2025.findings-emnlp.246

Yuan, T., He, Z., Dong, L., Wang, Y., Zhao, R., Xia, T., Xu, L., Zhou, B., Li, F., Zhang, Z., Wang, R., & Liu, G. (2024). R-Judge: Benchmarking Safety Risk Awareness for LLM Agents. Findings of the Association for Computational Linguistics: EMNLP 2024, 1467–1490. https://doi.org/10.18653/v1/2024.findings-emnlp.79

Yue, Y., Zhang, G., Liu, B., Wan, G., Wang, K., Cheng, D., & Qi, Y. (2025). MasRouter: Learning to Route LLMs for Multi-Agent Systems. Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), 15549–15572. https://doi.org/10.18653/v1/2025.acl-long.757

Zhan, Q., Fang, R., Panchal, H. S., & Kang, D. (2025). Adaptive Attacks Break Defenses Against Indirect Prompt Injection Attacks on LLM Agents. Findings of the Association for Computational Linguistics: NAACL 2025, 7101–7117. https://doi.org/10.18653/v1/2025.findings-naacl.395

Zhan, Q., Liang, Z., Ying, Z., & Kang, D. (2024). InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated Large Language Model Agents. Findings of the Association for Computational Linguistics ACL 2024, 10471–10506. https://doi.org/10.18653/v1/2024.findings-acl.624

Zhang, H., Huang, J., Mei, K., Yao, Y., Wang, Z., & Zhan, C. (2024). Agent Security Bench (ASB): Formalizing and Benchmarking Attacks and Defenses in LLM-based Agents. International Conference on Learning Representations. https://arxiv.org/abs/2410.02644

Zhang, H., Nian, Y., & Zhao, Y. (2026). Agent Audit: A Security Analysis System for LLM Agent Applications. arXiv preprint arXiv:2603.22853. https://arxiv.org/abs/2603.22853

Zhang, Q., Fu, L., Lian, L., Go, G., Wang, Y., Zhou, C., Jiang, Y., & Pu, G. (2026). Evaluating Privilege Usage of Agents with Real-World Tools. Proceedings of the 34th ACM International Conference on the Foundations of Software Engineering, 1192–1196. https://doi.org/10.1145/3803437.3805554

Zhang, Z., Zhang, Y., Li, L., Gao, H., Wang, L., Lu, H., Zhao, F., Qiao, Y., & Shao, J. (2024). PsySafe: A Comprehensive Framework for Psychological-based Attack, Defense, and Evaluation of Multi-agent System Safety. Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), 14751–14774. https://doi.org/10.18653/v1/2024.acl-long.785

Zheng, Y., Hu, Y., Yu, T., & Quinn, A. (2025). AgentSight: System-Level Observability for AI Agents Using eBPF. Proceedings of the 4th Workshop on Practical Adoption Challenges of ML for Systems, 110–115. https://doi.org/10.1145/3766882.3767169

Zhu, J., Tseng, K., Vernik, G., Huang, X., Patil, S. G., & Fang, V. (2025). MiniScope: A Least Privilege Framework for Authorizing Tool Calling Agents. arXiv preprint arXiv:2512.11147. https://arxiv.org/abs/2512.11147

Zhu, S., Chen, Z., Wang, Z., & Li, B. (2025). MELON: Provable Defense Against Indirect Prompt Injection Attacks in AI Agents. Forty-second International Conference on Machine Learning. https://openreview.net/forum?id=gt1MmGaKdZ

Zhuge, M., Gao, H., Wang, X., Gao, J., Shi, S., Hou, X., Zhang, J., & Shen, Z. (2024). Language Agents as Optimizable Graphs. Proceedings of the 41st International Conference on Machine Learning, 235, 62743–62767. https://proceedings.mlr.press/v235/zhuge24a.html

Zou, A., Xiao, Z., Ba, J., Fredrikson, M., Kolter, Z., & Hendrycks, D. (2025). Security Challenges in AI Agent Deployment: Insights from a Large Scale Public Competition. Advances in Neural Information Processing Systems 38, 16584–16624. https://doi.org/10.52202/085713-1768

