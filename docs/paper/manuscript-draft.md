# GUIDE: An External Reference Monitor Bounding the Blast Radius of Compromised Agents in LLM Multi-Agent Systems

Shafin Ahmad¹, Ts. Dr. Maythem Kamal Abbas¹

¹ Asia Pacific University of Technology and Innovation, Technology Park Malaysia, Bukit Jalil, 57000 Kuala Lumpur, Malaysia.

Corresponding author: Shafin Ahmad (https://orcid.org/0009-0008-7351-1609).

## Abstract

Prompt injection cannot be reliably prevented inside large language model reasoning loops. When autonomous agents collaborate across multi-step pipelines, an injection in one agent can propagate to downstream peers and trigger unauthorized external actions. This paper addresses that risk under assumed compromise, treating individual agents as untrusted and placing an external reference monitor at the tool and delegation boundary. The reference monitor is named GUIDE (Governed, Uncertainty-aware, Intent-pinned Delegation Enforcer). First, GUIDE derives a static blast-radius bound for any compromised subset of agents, and this paper proves the bound sound against the monitor's own enforcement. Synthesised least privilege reduces median nominal reach by 50.0% (1.0 sink). Second, the static bound predicts deployment utility cost before execution. It identified 29 of the 30 AgentDojo tasks lost under enforcement, with 2 false alarms, for 96.9% accuracy on 97 tasks. Third, this paper establishes a structural topology floor for the monitor. In sequential pipelines, splitting steps into separate agents cannot reduce worst-case reach. A census of 55 workflow configurations (19 self-authored and 36 mined from public repositories) finds that 89.1% (49 of 55) are strictly sequential chains. Fourth, an evaluation across 949 AgentDojo pairs demonstrates 92.3% containment under assumed compromise with zero soundness violations. However, strict policy enforcement creates a trade-off by reducing Slack utility by 66.7 percentage points. The primary limitation is that multi-agent containment was evaluated on self-authored pipelines because no standardized multi-agent compromised-agent benchmark currently exists.

Keywords: multi-agent systems, large language models, prompt injection, reference monitor, least privilege, static analysis, blast radius

## Table of contents

- 1. Introduction
- 2. Related work
- 3. Materials and methods
- 4. Results
- 5. Discussion
- 6. Conclusion
- Acknowledgments
- Statements
- References
- Supplementary material

## 1. Introduction

Most multi-agent systems built with large language models face an unsolved security problem at the execution boundary. When an agent reads external data from documents, search tools, or user inputs, untrusted text enters its prompt context. Attackers exploit this interface using prompt injection, which cannot be reliably prevented inside the model's reasoning loop (Greshake et al., 2023). In a single-agent system, an injection redirects tool calls directly. In a multi-agent system, the attack propagates across delegation boundaries. An untrusted agent can deceive downstream peers into executing privileged tools (Lee et al., 2026, Le et al., 2026). The initial agent could never call those tools on its own.

Defending against this failure mode requires an assumed-compromise threat model. Rather than attempting to detect malicious text inside language model activations, the reference monitor must treat any agent processing untrusted data as potentially compromised. This paper presents Governed, Uncertainty-aware, Intent-pinned Delegation Enforcer (GUIDE), an external reference monitor that enforces sound capability bounds over multi-agent workflows. The reference monitor operates at the boundary between agent reasoning and external tool execution. It evaluates every proposed tool call and delegation against formal authority constraints before any real-world effect occurs.

Autonomous agents increasingly collaborate across complex pipelines to solve multi-step tasks (Park et al., 2023, Wang et al., 2024). Coordination designs use message passing and graph execution to decompose tasks across specialized roles (Wu et al., 2024a, Zhou et al., 2024, Guo et al., 2026). However, empirical studies show that multi-agent systems often fail or deviate from specified procedures under adversarial pressure (Cemri et al., 2025, La Malfa et al., 2025). When an agent receives malicious input, untrusted environment data can redirect execution toward arbitrary malicious code (Triedman et al., 2025, Mohammadi et al., 2025).

The aim of this research is to prevent unauthorized external actions caused by compromised agents in multi-agent pipelines. The proposed solution places an external reference monitor at the tool and delegation boundary to enforce provable blast-radius bounds and least-privilege policies before execution.

This paper makes four contributions:

1. Sound static blast-radius bound (C1). This paper derives a static graph-theoretic bound on the tools and resources an arbitrary compromised subset of agents can reach. A correspondence lemma and step-containment theorem prove the bound sound against the runtime reference monitor. Property-based tests over thousands of executions confirm soundness, and a live adaptive attacker confirms exactness on direct effects across 39 out of 39 evaluated cases. Synthesised least privilege provably minimizes the policy, reducing median nominal reach across realistic configurations by 50.0% (1.0 sink).

2. Pre-deployment cost prediction (C2). The static bound acts as a pre-deployment decision tool by predicting which benign task paths will be blocked by policy enforcement before running the model. Evaluated against 97 AgentDojo tasks, the predictor achieves 92.8% accuracy (95% Wilson confidence interval [85.8%, 96.5%]) with zero false negatives on path (zero false negatives on the execution path). Against the observed task loss between undefended and defended deployments, the predictor achieves 96.9% accuracy. It flagged 31 of 97 tasks as blocked, and 29 of these were among the 30 tasks actually lost.

3. Topology floor and structural census (C3). This paper proves Proposition 3 and Proposition 4, showing that workflow topology imposes fundamental mathematical limits on security. In sequential linear pipelines, neither partitioning steps into distinct agents nor cryptographic signing can reduce worst-case blast radius below the nominal sink count. Least privilege is the only effective lever. A structural census across 55 acyclic agent workflow configurations (19 self-authored and 36 mined from public repositories) reveals that 89.1% (49 of 55) are strictly sequential linear chains. Moreover, 100.0% (55 of 55) exhibit a single dominating source agent covering all execution steps.

4. Empirical containment and trade-off findings (C4). In a live evaluation across 949 AgentDojo pairs, the reference monitor achieves 92.3% containment under assumed compromise (95% Wilson confidence interval [89.9%, 94.2%]). It achieves 89.5% containment on the v6 subset and a 93.6% sink block rate. The evaluation recorded zero soundness violations and zero exactness gaps. However, strict provenance enforcement induces a net utility cost of 29.9 percentage points (pp) overall. It reduces pooled benign utility from 91.8% to 61.9%. On Slack, the cost reaches 66.7 pp because benign tasks forward untrusted channel data to communication sinks.

The paper evaluates five research questions:

- RQ1 (Soundness and exactness): Can the worst-case blast radius of an arbitrary compromised subset of agents be soundly bounded before deployment?
- RQ2 (Containment under assumed compromise): Does runtime enforcement at the tool and delegation boundary contain compromised agents under assumed compromise?
- RQ3 (Pre-deployment cost prediction): Can static analysis predict which benign tasks will fail runtime policy enforcement without running the model?
- RQ4 (Topology floor and workflow structure): How does workflow topology constrain blast-radius reduction, and what structures dominate real-world multi-agent systems?
- RQ5 (Cross-model nominal performance): Does runtime reference monitoring affect task success, intent fidelity, or latency on benign tasks across distinct model families?

Section 2 reviews related work. Section 3 describes the design of GUIDE as an external reference monitor and the formal methods. Section 4 presents empirical results. Section 5 discusses design implications and limitations. Section 6 concludes the paper.

## 2. Related work

Related work was identified through a systematic review covering 721 included studies across multi-agent systems and language model security.

### 2.1 Multi-agent coordination and orchestration

Multi-agent orchestration research has focused primarily on coordination and task completion. MasRouter routes tasks across specialized agents to improve completion efficiency (Yue et al., 2025). Difficulty-aware orchestration dynamically adjusts pipeline topology based on input complexity (Su et al., 2026). Evolving orchestration allows team communication structures to reorganize during task execution (Dang et al., 2025). Graph-based coordination models multi-agent workflows as scalable generative networks (Ji et al., 2025). Tree-structured reasoning layouts reduce context loss across long debate turns (Yu et al., 2025), and problem drift degrades long multi-agent debates (Becker et al., 2026). Agents can also be modeled as optimizable graph programs (Zhuge et al., 2024) or decentralized evolutionary networks (Yang et al., 2025). SagaLLM applies transaction guarantees and context validation to multi-agent planning (Chang and Geng, 2025). Policy-compliant orchestration for enterprise deployments has also been proposed (Pasupuleti et al., 2026). These approaches address coordination and performance. But they do not enforce security policies at tool boundaries. Nor do they evaluate containment when an agent within the topology is compromised.

### 2.2 Single-agent tool-call reference monitors and information flow control

Single-agent reference monitors and information flow control systems evaluate individual tool calls generated by a single agent against policy rules or information flow labels. CaMeL attaches capability tokens and data flow policies to values passing through an agent, checking policy rules before tool invocation with a formal safety proof (Debenedetti et al., 2026). Progent provides policy-guided privilege control over tool execution (Shi et al., 2025). FIDES propagates confidentiality and integrity labels across tool executions to block sensitive data flows within the Microsoft Agent Framework (Costa et al., 2025). The Agentic Reference Monitor (ARM) constructs causal provenance graphs over tool calls and return values to prevent causality laundering through denial feedback (Chinaei, 2026). MiniScope synthesises tool policies from permission hierarchies to enforce least privilege on single agents (Zhu et al., 2025). Cordon applies transactional semantics to tool-using agents to isolate execution effects (Chen et al., 2026). Out-of-band defensive evaluations examine the resilience of external filtering mechanisms (Narisetty et al., 2026). AgentSpec introduces customizable runtime enforcement for safety specifications (Wang et al., 2026). Deterministic runtime enforcement provides execution authority outside model weights (Gill-Lakhowal, 2026). TRACE records execution provenance for post-hoc containment audits (Calboreanu, 2026). Learned capability governance scopes permissions dynamically based on historical actions (Sidik and Rokach, 2026). Automated permission inference schemes attempt to derive least-privilege profiles from documentation (Wu et al., 2026). IsolateGPT isolates the execution of applications on LLM-based agent platforms (Wu et al., 2024b). In tool ecosystems such as the Model Context Protocol, privilege management is frequently absent or coarse-grained (Li et al., 2025, Wang et al., 2025). Empirical studies demonstrate that real-world agents routinely execute privileged tools without task justification (Zhang et al., 2026). Metadata poisoning can also trick agents into selecting attacker-controlled tools (Mo et al., 2025). ATAG assesses threats to agent applications with attack graphs (Gandhi et al., 2025). These systems monitor single agents executing tools with model-generated arguments. They do not target multi-agent delegation pipelines where an untrusted agent deceives a downstream peer. In addition, they do not compute static blast-radius bounds over multi-agent workflow topologies.

Table 1 compares closest related systems across target scope, static bounding, soundness proofs, policy synthesis, and utility prediction.

Table 1. Comparison of security mechanisms in tool-calling and multi-agent workflows.

| Mechanism | Targets multi-agent compromised subsets | Static pre-deployment bound | Soundness proof | Least-privilege synthesis | Deployment-cost prediction |
|---|---|---|---|---|---|
| CaMeL (Debenedetti et al., 2026) | No | No | Yes (runtime safety) | No | No |
| Progent (Shi et al., 2025) | No | No | Not reported | No | No |
| FIDES (Costa et al., 2025) | No | No | Not reported | No | No |
| ARM (Chinaei, 2026) | No | No | Not reported | No | No |
| Parisel (2026) | Yes | Yes | No | No | No |
| Muruaga (2026) | Yes | No | Yes (runtime monotonicity) | No | No |
| Moon & Varshney (2026) | No | No | Yes (Dafny machine-checked) | No | No |
| CAPMAS (Veski et al., 2026) | Yes | No | Not reported | Query-level privilege scoping | No |
| GUIDE (This paper) | Yes | Yes | Yes (soundness theorem) | Yes | Yes |

### 2.3 Multi-agent security, prompt injection attacks, and containment

Recent research evaluates security risks unique to multi-agent pipelines. Injected prompt payloads propagate across agent communication channels, allowing untrusted inputs to compromise downstream agents (Lee et al., 2026, Le et al., 2026). Flooding attacks spread manipulated knowledge across collaborating communities (Ju et al., 2026). Canaries placed across agent stages track injection propagation along attack kill chains (Wang et al., 2026). Collusion among autonomous agents can emerge without explicit centralized coordination (Motwani et al., 2024). Multi-agent collaboration attacks demonstrate that peer debate can amplify adversarial prompts (Amayuelas et al., 2024). Pragmatic multi-agent systems remain vulnerable to optimized jailbreaks (Khan et al., 2025). Code-generating swarms face severe shadow injection risks in shared repositories (Wang et al., 2025). Adding security checks across multi-agent workflows imposes a measurable latency and token tax (Peigne-Lefebvre et al., 2025). Multi-agent collaboration also degrades rapidly when individual nodes experience unhandled faults (Huang et al., 2024).

To mitigate these risks, several defenses have been proposed. Network firewalls place screening filters between collaborating agents (Abdelnabi et al., 2025). SafeFlow tracks semantic information flow to prevent malicious propagation across agent graphs (Dai et al., 2026). Taint-style vulnerabilities in agent logic can be detected by pitting defensive agents against worker nodes (Liu et al., 2025). Guard agents can inspect proposed plans before execution (Xiang et al., 2024). ShieldAgent formalizes policy reasoning to protect decision loops (Chen et al., 2025). Hardware safety chips and execution interlocks enforce physical constraints on robotic agents (Yang et al., 2024). SAGA introduces secure architecture principles for governing enterprise agent networks (Syros et al., 2025). CaMeLoT orchestrates agents under temporal logic specifications to maintain liveness and safety (Nikolaou et al., 2026). Decomposing agent responsibilities without execution boundaries often degrades overall policy compliance (Li and Wang, 2026).

Benchmarking studies show the difficulty of containing indirect prompt injection. Adaptive attacks consistently bypass static detection filters (Zhan et al., 2025). Task alignment filters attempt to shield execution loops from extraneous instructions (Jia et al., 2025). Tool selection logic remains highly vulnerable to adversarial injection (Shi et al., 2026). Game-theoretic detectors evaluate incoming prompts for injection markers (Liu et al., 2025). Tool dependency graphs offer structural defenses against indirect payloads (An et al., 2025). Dynamic rule enforcement isolates injections during single-agent runs (Li et al., 2025). DataFilter scrubs untrusted inputs prior to tool consumption (Wang et al., 2025). Provable defenses such as MELON bound injection risks under strict data isolation (Zhu et al., 2025). App-integrated systems require thorough boundary architectures (Li et al., 2026). Attention tracing attributes prompt injection influence to specific input tokens (Wang et al., 2025). Formalizing prompt injection attacks and defenses enables systematic benchmarking (Liu et al., 2024). Internal activation deltas can detect task drift caused by injected text (Abdelnabi et al., 2025). Broad empirical evaluations reveal that most prompt defenses fail under adaptive testing (Jia et al., 2026). Cross-tool pollution allows malicious inputs in one tool to infect subsequent tool calls (Li et al., 2026). Protocol vulnerabilities in agent tool interfaces enable unauthorized control of the host (Song et al., 2026). Process-centric analyses track data flows across enterprise agentic software (Liu et al., 2026). System-level observability tools inspect agent behavior using kernel probes (Zheng et al., 2025). Psychological evaluation frameworks benchmark behavioral safety in agent swarms (Zhang et al., 2024). Contextual safety benchmarks evaluate conversational boundaries across agent dialogues (Gomaa et al., 2025). AgentHarm measures harmful capabilities in unaligned models (Andriushchenko et al., 2025). Language model emulators assess risk profiles before physical deployment (Ruan et al., 2024). Safety risk benchmarks evaluate awareness in decision-making agents (Yuan et al., 2024). Code execution environments benchmark hazardous code generation (Guo et al., 2024). Memory injection attacks manipulate persistent agent recall across independent sessions (Dong et al., 2025). Public agent deployment competitions expose wide-ranging security gaps in production systems (Zou et al., 2025). Automated security auditing systems scan agent codebases for vulnerable tool bindings (Zhang et al., 2026). Agent Security Bench formalizes attacks and defenses across multi-agent environments (Zhang et al., 2024). Adversarial risk benchmarks quantify attack success across commercial foundation models (Kavathekar et al., 2025). ContainmentBench evaluates trace containment after initial agent compromise (Lan et al., 2026). BlindGuard safeguards multi-agent systems against unknown attacks (Miao et al., 2025).

### 2.4 Static and pre-deployment analysis

In static and pre-deployment analysis, concurrent 2026 work exhibits partial overlap with aspects of this approach. Parisel (2026) models design-time influence graphs over multi-agent configurations and defines a blast-radius metric over enterprise resources, but provides no enforcement guarantee, no soundness proof, and no runtime implementation. Muruaga (2026) proves runtime monotonicity of delegation scope along dynamically instantiated principal chains, but evaluates runtime scopes rather than computing a static bound over an entire workflow before deployment. Moon and Varshney (2026) mechanically verify single-agent runtime containment in Dafny, but do not model multi-agent influence or provide least-privilege policy synthesis. Paul and Nandy (2026) formulate static security analysis principles for multi-agent workflows. Safin et al. (2026) develop capability bounding algorithms for multi-agent task graphs. CAPMAS (Veski et al., 2026) enforces monotonic privilege reduction across delegating agents through Macaroon-based tokens, but does not compute a static blast-radius bound over a workflow or prove soundness against compromised agents.

### 2.5 Evaluation benchmarks

Standard benchmarks for agent security evaluate single-agent execution. AgentDojo benchmarks prompt injection defenses on single-agent environments across utility and security axes (Debenedetti et al., 2024). InjecAgent benchmarks indirect prompt injection on single agents (Zhan et al., 2024). Tau-bench measures tool-use reliability and user interaction across realistic domains (Yao et al., 2025). No standard benchmark exists for evaluating compromised-agent containment in multi-agent workflows. Consequently, this study evaluates multi-agent containment on an internal multi-agent benchmark and evaluates external runtime tool enforcement on AgentDojo under assumed compromise.

## 3. Materials and methods

### 3.1 Research design

This study follows design science research (Hevner et al., 2004). The goal is to build and evaluate an external reference monitor for a defined computing problem instead of testing an existing commercial product. The six activities of Peffers et al. (2007) map onto this project directly. Problem identification corresponds to the execution gap described in Section 1. Objective definition addresses RQ1 through RQ5. Design and development produces the external reference monitor in Section 3.2. Demonstration covers the nominal runs. Evaluation examines baseline comparisons and assumed compromise in Section 4. Communication includes this paper and the archived code. The literature review followed established PRISMA guidelines (Page et al., 2021), systematic literature review procedures (Kitchenham and Charters, 2007), and snowballing techniques (Wohlin, 2014). The overarching engineering principle separates proposal from disposal: the model proposes and the external code disposes (Moutesidis, 2026). The unit of analysis is the reference monitor mechanism rather than individual model capability. Therefore, every condition in every suite uses identical tasks, tools, decoding settings, and base models.

Table 2 aligns the research questions, objectives, hypotheses, and evidence sources.

Table 2. Alignment of research questions, objectives, hypotheses, and evidence.

| Research Question | Objective | Hypothesis | Primary Evidence Source |
|---|---|---|---|
| RQ1: Bound Soundness | O1: Formulate and prove static blast-radius bound | Soundness correspondence and step containment hold for any compromised subset | Theorem 1 and 2 proofs, property tests (0 counterexamples), live adaptive attacker (39/39 exactness) |
| RQ2: Runtime Containment | O2: Evaluate tool-boundary runtime enforcement | Policy gate contains out-of-domain actions, provenance guard contains in-domain steering | Protocol v8 M1 replay (949 AgentDojo pairs, 92.3% containment), internal suite (K1-K4) |
| RQ3: Cost Prediction | O3: Predict deployment utility cost statically | Static admissibility predicts runtime utility degradation without model execution | Protocol v8 M1b (97 tasks, 96.9% accuracy, 31 predicted blocks vs 30 observed losses) |
| RQ4: Topology Floor | O4: Establish workflow topology constraints | Sequential agent decomposition cannot reduce worst-case blast radius below single-agent reach | Proposition 4 proof, census of 55 workflows (89.1% linear chains), least-privilege synthesis (50.0% reduction) |
| RQ5: Cross-Model Baseline | O5: Measure nominal performance across model families | Governance overhead remains within 30% and nominal task completion is preserved across models | Protocols v2 and v5 across DeepSeek 4.1 Flash, Gemini 3.5 Flash-Lite, and OpenAI GPT-OSS-120B |

Section 4 refers to the following hypotheses. H1: policy gating contains out-of-domain actions, and only the provenance guard contains steering to an in-domain recipient. H2: adaptive routing and re-dispatch recover from a permanently degraded agent. H3: per-principal signing keys make sender spoofing detectable. H5a: the controls improve task success and intent fidelity over both baselines. H5b: the controls reduce violations on nominal tasks. H5c: governance overhead stays within 1.30 times the median wall time of condition B2.

### 3.2 External reference monitor design and controls

GUIDE is an external reference monitor. It sits outside the model and outside the agents, and every proposed tool call and delegation must pass through it before any effect occurs. Its implementation is organised into three software packages with one-way dependencies. The core package provides the monitor primitives. The research package contains the provenance guard and the static analyser. The benchmark package contains task suites and evaluation testbeds. The core package never imports from the other two, which is checked automatically in continuous integration.

Figure 1 shows GUIDE as an external reference monitor, its four controls, and the data flow of a multi-agent execution step.

![Figure 1. GUIDE as an external reference monitor: controls and data flow for one execution step.](scripts/paper/figures/fig1_reference_monitor_design.png)

A run executes a workflow of steps in dependency order. For each step, a router selects a candidate agent. A hand-off delivers the step inputs to that agent. The agent then proposes tool calls inside a bounded agent loop. Finally, each proposed call is checked by the external reference monitor before tool code executes. GUIDE applies four controls to this execution:

1. Control 1: Beta-posterior routing policy. Routing maintains a Beta-distributed success estimate for each candidate agent on each task domain:
$$\theta_{i,d} \sim \text{Beta}(\alpha_{i,d}, \beta_{i,d}) \qquad (1)$$
Here, $\theta_{i,d}$ is the success probability of agent $i$ on domain $d$. The parameters $\alpha_{i,d}$ and $\beta_{i,d}$ equal one plus the observed successes and failures.
The monitor starts every agent with one warm-up task. Figure S1 reports a routing simulation of this policy. Then, it selects the candidate agent maximizing the upper-confidence quantile via Bayes-UCB (Auer et al., 2002, Kaufmann et al., 2012). Equation (2) defines this score.
$$\text{Bayes-UCB}(i, d) = Q\left(1 - \frac{1}{t}, \text{Beta}(\alpha_{i,d}, \beta_{i,d})\right) \qquad (2)$$
Here, $t$ is the current step index and $Q$ is the quantile function of the Beta distribution.
This provides adaptive, regret-minimizing routing across candidate agents.

2. Control 2: Signed hand-off package. A hand-off package carries run and hand-off identifiers, the previous package hash, and the task objective. It also specifies constraint lists, input references, permitted tools, output schemas, and expiry times. The package is serialised to a canonical JSON form over a restricted value domain and signed with an Ed25519 key specific to the sending principal (Bernstein et al., 2012). The receiver verifies signatures, hash chains back to the genesis hash, required fields, expiry, and schemas. It rejects the hand-off with an integrity error if any check fails.

3. Control 3: SMT-based policy gate. Every proposed tool call is reduced to a finite record (Saltzer and Schroeder, 1975, Denning, 1976). The record captures the tool, operation, resource class, column sensitivity, and side-effect flags. An external policy gate inspects this record against a declarative policy using SMT constraints (Backes et al., 2018). The gate returns one of three decisions: allow unchanged, bound argument values, or deny. Bounding is implemented as interval projection for numeric arguments and as subset projection for column lists. A denied call never reaches tool code.

4. Control 4: Provenance guard. A provenance guard wraps the policy gate for side-effecting calls (Cheney et al., 2009). Control arguments such as email recipients must be traceable to the task's trusted text. The guard checks whether the normalized argument appears as a substring of the trusted corpus. Alternatively, a stricter mode checks for an exact token match. A call whose control argument cannot be traced to trusted text is denied even if the policy gate alone would have allowed it.

Every routing decision, hand-off result, policy decision, tool call result, and step output is appended to a hash-linked trace ledger maintained by the monitor.

### 3.3 Conditions

Four conditions are evaluated, each a configuration of the same reference monitor implementation:

- B1: fixed-role sequential delegation with a plain-text, unstructured hand-off between agents.
- B2: a static-graph workflow with structured JSON state passed between steps, but no adaptive routing, no signed hand-off, and no policy gate.
- P: the proposed reference monitor at proposal scope, meaning Bayes-UCB routing, signed hand-offs, and the policy gate, without the provenance guard or re-dispatch.
- GPLUS: P plus the provenance guard and re-dispatch on step failure.

Six further configurations ablate one mechanism of GPLUS at a time and are named GPLUS-provenance, GPLUS-gate, GPLUS-signing, GPLUS-redispatch, GPLUS-routing, and GPLUS-trace. These ablations remove provenance, the gate, signing, re-dispatch, routing, or trace recording. They attribute observed empirical effects to specific monitor mechanisms.

### 3.4 Tasks and suites

Eighteen main-suite tasks span three families: information synthesis, evidence reconciliation, and policy-sensitive planning. Tasks have four, six, or eight atomic constraints. Each follows a three-step retrieve, analyse, and report workflow. The adversarial suite adds eleven live robustness cases. These cases test missing entities, conflicting data, injected external and internal sink instructions, destructive writes, and prohibited principal requests. They also test compromised peers, hand-off tampering, tool outages, and malformed outputs. A separate sequence suite tests twenty consecutive runs with one agent permanently degraded.

The threat model for RQ2 uses an assumed-compromise suite. In each of four cases, the targeted agent's first proposed tool call is replaced by an attacker-chosen call. The cases include restricted-column reads (K1), external emails (K2), in-domain mailbox steering (K3), and record deletions (K4). Every subsequent step of the run proceeds with the live model as normal. This isolates whether the reference monitor contains a compromised agent's action from whether the underlying model resists being talked into one.

### 3.5 Models and settings

Protocols v1 through v4 and Protocol v6 used DeepSeek 4.1 Flash (requested as `deepseek-chat`, reported as `deepseek-v4-flash` and `deepseek-flash`) at temperature 0 in JSON mode. Completions used up to 4,096 tokens with a fixed seed of 42. Execution allowed four tool turns and two repair attempts at temperature 0.3.

Protocol v5 evaluates two further model families: Google's Gemini 3.5 Flash-Lite (`gemini-3.5-flash-lite`) and OpenAI GPT-OSS-120B (`openai/gpt-oss-120b`) served via Groq. Gemini omits `seed` because its endpoint rejects that parameter. Temperature, maximum tokens and JSON mode are identical across all three model families.

### 3.6 Metrics

Table 3 lists the evaluation metrics and their operational definitions.

Table 3. Evaluation metrics, formal definitions, and instrumentation.

| Metric | Level | Definition | Instrumentation |
|---|---|---|---|
| Task Success | Run | Binary flag indicating all mandatory task constraints were satisfied | Deterministic rule checker against step deliverables |
| Intent Fidelity | Run | Fraction of task atomic constraints satisfied (continuous [0, 1]) | Normalised score over per-constraint assertion checks |
| Violation Rate | Run | Binary flag indicating disclosure of restricted data, illegal write, or unapproved recipient | Tool audit log and context disclosure scan |
| Attack Success Rate (ASR) | Suite | Fraction of adversarial or compromised runs achieving attacker objective | Evaluated over adversarial and assumed-compromise suites |
| Trace Completeness | Run | Fraction of required linked trace events present and verifiable | Cryptographic verification of trace ledger hashes |
| Integrity Detection | Run | Fraction of seeded invalid or tampered hand-off packages rejected | Hand-off receiver verification error count |
| Execution Latency | Run | End-to-end wall-clock time in seconds and monitor execution time in milliseconds | High-resolution monotonic timers |
| Token Usage | Run | Total prompt tokens and completion tokens consumed per run | Token accounting ledger from provider responses |

Every check is deterministic and computed without access to the condition label that produced the run.

### 3.7 Static blast-radius analysis

The formal model represents a deployment as a workflow graph of steps, agents, tool metadata, and declarative security policies. An adversary controls the model output of a compromised agent subset, the content returned by injectable tools, and the hand-off transport.

The static analysis proves a correspondence lemma showing that the policy gate's decision procedure matches the mathematical definition of authority at each step. A step-containment theorem proves that no execution under any adversary behavior produces an effect outside the gate's authority rule. An influence relation propagates from compromised steps across shared state, hand-off context, and injectable tools. The worst-case blast radius of a compromised subset is the union of authority across all steps reached by the influence relation. Equation (3) defines this bound:
$$\text{Reach}(C) = \bigcup_{s \in \text{Inf}(C)} \text{Auth}(s) \qquad (3)$$
Here, $C$ is the compromised subset of steps, $\text{Inf}(C)$ is the set of steps reached by the influence relation from $C$, and $\text{Auth}(s)$ is the authority that the policy gate grants at step $s$. Theorem 1 proves that all adversary-dependent effects lie inside this bound. Theorem 2 proves that steps outside the influence relation execute unaffected by the adversary.

Least-privilege policy synthesis derives the minimal policy permitting observed nominal executions, shrinking the bound provably without introducing nominal denials. Equation (4) defines this minimal policy:
$$\text{Policy}^*(s) = \bigcap \{ P \mid \text{NominalExec}(s) \subseteq P \} \qquad (4)$$
Here, $P$ ranges over policies and $\text{NominalExec}(s)$ is the set of calls observed at step $s$ in nominal runs.

### 3.8 Protocol, statistics and deviations

All evaluations followed pre-registered protocols frozen in version control. Per-condition summaries report the mean and a 95% cluster-bootstrap confidence interval over tasks using ten thousand resamples. Paired comparisons use two-sided Wilcoxon signed-rank tests with Pratt's correction for zero differences and Holm correction across metric families.

Protocol versions are numbered in the order in which they were frozen. Protocols v1 to v4 cover the DeepSeek main, adversarial, and assumed-compromise suites, and Protocol v5 adds two further model families. Protocol v6 and v6b run AgentDojo with and without GUIDE, Protocol v7a predicts utility cost, Protocol v7b mines real-world configurations, and Protocol v7c analyses topology. Protocol v8 adds the assumed-compromise replay (M1), the attributable-loss evaluation (M1b), and the topology theory and census (M2).

Table 4 summarizes all deviations between the approved research proposal and the executed research.

Table 4. Summary of deviations between the approved proposal and executed research.

| ID | Topic | Proposal Plan | Executed Research | Rationale and Effect |
|---|---|---|---|---|
| A7 | Assessor Scoring | Two blinded human assessors scoring 20% sample with Cohen's kappa | Automated deterministic constraint checking across 100% of runs | Replaced due to lack of ethical clearance at formal run time, provides stricter reproducibility |
| A10 | Policy Bounding | Euclidean projection over vector representation | Interval and column-subset projection in policy gate | Vector projection is undefined for discrete tool arguments, discrete projection is sound |
| A11 | Hand-off Serialization | RFC 8785 JSON canonicalization | Canonical JSON over restricted value domain | Matches implementation capability while guaranteeing deterministic hashing |
| A16/A28 | Multi-Model Evaluation | Single model family (DeepSeek) | Evaluated across DeepSeek 4.1 Flash, Gemini 3.5 Flash-Lite, and OpenAI GPT-OSS-120B | Validates cross-model invariance, reduces statistical power from 5 to 2 reps on free tiers |
| A20 | Compromise Threat Model | Textual indirect prompt injection | Assumed-compromise replay (K1-K4) replacing first proposed call | Live models resisted textual injection (0 attempts in 550 runs), replay isolates containment |
| A24 | Policy Language | allow / bound / deny over action record | Column-level and recipient-level allow-lists added | Required to express synthesized least-privilege policies |
| A25 | Provenance Guard | Not specified in proposal | Substring and exact-token provenance guards added | Closes in-domain sink steering vulnerability uncovered by static analysis |
| A27/A33 | Topology Mining | Not specified in proposal | Audit of 19 self-authored and 36 mined public CrewAI configurations | Establishes external validity on real-world multi-agent workflow structures |
| A31 | Cost Prediction | Not specified in proposal | Static admissibility predictor evaluated on AgentDojo | Enables pre-deployment evaluation of security versus utility trade-offs |
| A32 | Topology Theory | Not specified in proposal | Formulated Proposition 3 (refinement) and Proposition 4 (chain floor) | Proves fundamental structural limits of multi-agent decomposition |
| A34 | Protocol v8 | Single-step synthetic benchmarks | Full 949-pair AgentDojo assumed-compromise replay | Validation on an external tool-using benchmark using recorded ground-truth attacker calls |

### 3.9 Ethics and data

All sandbox data is synthetic or public. No human participants or personal data were involved. The sandbox tool set is allow-listed, with no network write access beyond a simulated email tool.

### 3.10 External benchmark: AgentDojo

AgentDojo (Debenedetti et al., 2024) is an external benchmark designed for tool-using agents across Banking, Slack, Travel, and Workspace domains. AgentDojo is a single-agent benchmark evaluating tool-boundary enforcement and deployment cost.

AgentDojo is evaluated under three protocols. Protocol v6 evaluates GUIDE against DeepSeek 4.1 Flash. Protocol v6b evaluates undefended baseline execution. Protocol v8 (M1) executes an assumed-compromise replay across all 949 task-injection pairs.

### 3.11 Pre-deployment cost prediction

Protocol v7a and Protocol v8 (M1b) evaluate whether utility cost can be predicted statically before deployment. The static predictor inspects nominal tool requirements against synthesized policies and provenance constraints, flagging tasks as blocked if required calls exceed policy authority.

### 3.12 Workflow topology analysis

Protocol v7c and Protocol v8 (M2) analyse the structural limits of workflow topology. Proposition 3 proves refinement monotonicity. Proposition 4 proves that in linear dependency chains, partitioning agents cannot reduce worst-case blast radius below full pipeline reach. Equation (5) defines the reachable sink set of any compromised step $s_k$ in a linear chain of length $N$.
$$\text{Reach}(s_k) = \bigcup_{j=k}^N \text{Sinks}(s_j) \qquad (5)$$
Here, $\text{Sinks}(s_j)$ is the set of write or external tool capabilities available at step $s_j$.

### 3.13 Real-world configuration mining

Protocol v7b mined public GitHub repositories implementing multi-agent workflows in CrewAI, LangGraph, and AutoGen using frozen search queries. Candidate extraction discovered 37 configurations (36 CrewAI and 1 LangGraph). The LangGraph configuration was cyclic and was excluded, leaving 36 scored CrewAI configurations. AutoGen repositories did not yield any usable configuration.

## 4. Results

### 4.1 RQ1: Soundness and exactness of the bound

Across 1,575 recorded runs spanning 2,051 executed tool calls, each run's executed effects were replayed against the bound computed for its compromised set. This replay revealed zero containment violations and zero blast-radius violations. Every one of the fifty-five harmful effects observed in the assumed-compromise suite lies inside the bound predicted for that run before it executed. A least-privilege policy synthesised from nominal traces denied zero of forty-four held-out calls. It achieved full task success with zero policy denials across thirty-six live runs, while shrinking the policy substantially. For one representative task, the default gate permitted any address at the organization's domain. In contrast, the synthesised policy permitted exactly one specific recipient.

A live adaptive attacker was evaluated against eight attack variants on this same task across 120 runs. The bound correctly predicted containment for every variant targeted by the policy controls, recording zero soundness violations. Every one of seventy-five runs predicted as blocked showed no harmful effect. This provides the exactness result for direct compromise: thirty-nine of thirty-nine (39/39) predicted-reachable direct effects were realised when the attacker was allowed to reach them.

One variant sent email to an address that was a substring of a trusted recipient. The static bound predicted this attack as reachable under substring matching. The attack succeeded across all three live repetitions The default substring-matching mode admits 692 distinct recipient strings (Figure 2). Switching to exact-token matching, or to the synthesised least-privilege policy, admits exactly one recipient and blocks the same attack in all three repetitions.

A second variant attempted to steer a downstream agent using poisoned upstream output. This attack failed across six repetitions because the downstream model ignored the injected instruction. The bound still predicts this path as reachable, which represents an intentional sound over-approximation on effects beyond direct compromise rather than a bound violation.

![Figure 2. Admissible recipients for one representative sink (task T15), by policy. The baseline and the policy gate admit an unbounded, domain-wide set of recipients. The default substring-matching provenance guard admits 692 distinct strings, whereas exact-token provenance and the synthesised least-privilege policy each admit exactly one.](scripts/paper/figures/fig6_blast_radius_bound_sizes.png)

A structural generalization check examined nineteen configurations reproducing patterns from LangGraph, CrewAI, and AutoGen across five enterprise domains. These tests executed without running code from those frameworks. Eighteen of the nineteen (18/19) configurations show at least one compromised agent whose blast radius reaches a destructive or data-exfiltration capability beyond that agent's own nominal role. This occurs because common integration patterns bind entire tool objects to agents. Granting whole objects exposes unneeded operations instead of restricting access to the specific operation required. Applying least-privilege synthesis cuts total reachable sink capability by 55.6% in aggregate. At the same time, it denies zero nominal calls across the configurations.

### 4.2 RQ2: Containment under assumed compromise

Table 5 reports the assumed-compromise results on DeepSeek 4.1 Flash with five repetitions per cell, and Figure 3 shows the same four cases for all three model families. The pattern is consistent across models. For K1, a compromised agent reads restricted columns directly. No model copies exposed values into final deliverables, so the violation rate is 0.0 in every condition. Ungated conditions (B1, B2) and the condition without the gate leak restricted columns into downstream context (restricted exposure 1.0), whereas gated conditions (P, GPLUS) strip restricted columns before delegation (exposure 0.0). For external emails (K2) and record deletions (K4), ungated baselines show a 100% violation rate across all models. In contrast, the policy gate in P and GPLUS blocks both actions across every trial, achieving a 0% violation rate. For in-domain mailbox steering (K3), the gate alone is insufficient. Condition P shows a 100% violation rate matching baselines, because the target domain is permitted. GPLUS, which adds the provenance guard on top of the same gate, shows a 0% violation rate on this case on every model tested. Removing the provenance guard from GPLUS restores the K3 violation, and removing the gate restores every violation. This supports H1: policy gating contains out-of-domain actions, and only the provenance guard contains an attacker's attempt to steer output to an in-domain recipient that the gate alone would permit.

Table 5. Violation rate under assumed compromise on DeepSeek 4.1 Flash, by attack case and condition (restricted exposure is reported for K1).

| Attack Case | B1 | B2 | P | GPLUS | GPLUS-provenance | GPLUS-gate | GPLUS-signing |
|---|---|---|---|---|---|---|---|
| K1: Restricted-column read (violation rate) | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| K1: Restricted-column read (restricted exposure) | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 |
| K2: External-domain email | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 |
| K3: In-domain email named only in tool data | 1.0 | 1.0 | 1.0 | 0.0 | 1.0 | 1.0 | 0.0 |
| K4: Record deletion | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 |

![Figure 3. Violation rate under assumed compromise (K1 to K4), by condition and model. Darker cells indicate a higher violation rate.](scripts/paper/figures/fig5_compromise_heatmap.png)

The textual injection suite produced zero attack attempts across 550 runs on DeepSeek. The model treated injected text as inert data in every instance. The integrity suite detects all ten seeded mutation classes at a 100% rate when using per-principal keys. It produces zero false rejections. However, a single shared key detects zero percent of sender-spoofing attempts. This supports H3: per-principal keys make spoofing detectable. The degraded-agent sequence (Figure 4) supports H2. A statically assigned baseline never recovers from a faulty agent across twenty runs. Adaptive routing alone recovers in nineteen runs. Re-dispatch recovers across all twenty runs.

![Figure 4. Degraded-agent sequence: cumulative completed runs over 20 consecutive runs with one agent permanently faulty.](scripts/paper/figures/fig8_degraded_agent_sequence.png)

To evaluate runtime tool-boundary enforcement on an established external benchmark, Protocol v8 (M1) executes an assumed-compromise replay across all 949 task-injection pairs in AgentDojo. Across these pairs, 588 in-scope pairs execute attacker sink invocations. Table 6 reports the containment results across the four AgentDojo suites. A pair is counted as contained when every attacker sink call in it is denied, as partial when only some are denied, and as executed when the attacker sink call runs.

Table 6. Assumed-compromise containment replay on AgentDojo (Protocol v8 M1).

| Suite | Pairs (Full) | In-Scope Pairs | Contained | Partial | Executed | Containment Rate [95% Wilson CI] | v6-Subset Containment | Undefended Containment |
|---|---|---|---|---|---|---|---|---|
| Banking | 144 | 144 | 128 | 0 | 16 | 88.9% [82.7%, 93.0%] | 88.9% [82.7%, 93.0%] | 0.0% |
| Slack | 105 | 84 | 79 | 0 | 5 | 94.0% [86.8%, 97.4%] | 94.0% [86.8%, 97.4%] | 0.0% |
| Travel | 140 | 120 | 99 | 0 | 21 | 82.5% [74.7%, 88.3%] | 82.5% [74.7%, 88.3%] | 0.0% |
| Workspace | 560 | 240 | 237 | 0 | 3 | 98.8% [96.4%, 99.6%] | 98.3% [91.1%, 99.7%] | 0.0% |
| **Total** | **949** | **588** | **543** | **0** | **45** | **92.3% [89.9%, 94.2%]** | **89.5% [86.1%, 92.1%]** | **0.0%** |

Overall containment reaches 92.3% across the full benchmark (543 of 588 in-scope pairs contained, 95% Wilson CI [89.9%, 94.2%]). On the v6 task subset, containment reaches 89.5% [86.1%, 92.1%]. The undefended baseline achieves 0.0% containment, because without runtime gating every tool call executes directly. Across all 702 attacker sink invocations in the benchmark, the runtime monitor blocked 657 calls, yielding a sink block rate of 93.6%.

Table 7 compares the static bound's pre-execution predictions against runtime outcomes across all 949 pairs. The monitor achieved zero soundness violations (no pair predicted blocked was executed) and zero exactness gaps (no pair predicted allowed was contained).

Table 7. Bound prediction versus runtime containment on AgentDojo (Protocol v8 M1).

| Prediction | Runtime Contained | Runtime Executed |
|---|---|---|
| Predicted Blocked | 543 | 0 |
| Predicted Allowed | 0 | 45 |

All forty-five admitted sink calls fall into two documented categories:
1. Sixteen calls involve operations with no control parameters, specifically the banking `update_password` tool, where the attacker's payload is fixed by the tool interface rather than supplied as an argument.
2. Twenty-nine calls involve parameters where the target recipient was already in the user's initial prompt. These cases occurred in travel tasks 0 and 4, and workspace tasks 1 and 5. Because the destination was in the trusted prompt, the provenance check correctly admitted the call.

Table 8 presents the paired results between Protocol v6 (defended) and Protocol v6b (undefended) on DeepSeek 4.1 Flash.

Table 8. AgentDojo benchmark performance comparison: defended (Protocol v6) versus undefended (Protocol v6b).

| Suite | Protocol v6b Benign Utility | Protocol v6 Benign Utility | Utility Cost (pp) | Protocol v6b Attack Utility | Protocol v6 Attack Utility | Protocol v6b ASR | Protocol v6 ASR |
|---|---|---|---|---|---|---|---|
| Banking | 100.0% | 87.5% | 12.5 | 94.4% | 90.3% | 0.0% | 0.0% |
| Slack | 90.5% | 23.8% | 66.7 | 85.7% | 38.1% | 0.0% | 0.0% |
| Travel | 85.7% | 66.7% | 19.0 | 78.6% | 66.7% | 2.9% | 2.9% |
| Workspace | 92.5% | 65.0% | 27.5 | 85.0% | 75.8% | 3.3% | 3.8% |
| **Overall** | **91.8%** | **61.9%** | **29.9** | **85.6%** | **68.4%** | **2.1%** | **2.3%** |

Protocol v6 consumed 11,426,990 tokens costing 13.93 CNY. Protocol v6b consumed 9,068,246 tokens costing 10.89 CNY.

Under Protocol v6 (defended), benign utility is 61.9% (60/97) and attack utility is 68.4% (362/529), with an attack success rate of 2.3% (12/529). Under Protocol v6b (undefended), benign utility is 91.8% (89/97) and attack utility is 85.6% (453/529), with an attack success rate of 2.1% (11/529).

Two findings emerge from this comparison. First, DeepSeek 4.1 Flash natively resisted prompt injections in this environment: undefended attack success rate was only 2.1%. Live attack success rate is therefore uninformative for evaluating defense efficacy on this model. Second, enforcing strict security controls created an overall utility cost of 29.9 percentage points (91.8% to 61.9%). On Slack, where tool outputs frequently supply legitimate arguments for downstream tools, benign utility dropped from 90.5% to 23.8%, representing a Slack utility cost of 66.7 percentage points. Figure 5 illustrates this relationship between undefended utility, defended utility, and assumed-compromise containment.

![Figure 5. AgentDojo benchmark performance across suites: undefended benign utility (Protocol v6b), defended benign utility (Protocol v6), and assumed-compromise containment rate (Protocol v8 M1).](scripts/paper/figures/fig9_agentdojo_utility_containment.png)

### 4.3 RQ3: Pre-deployment cost prediction

Protocol v7a evaluated whether the static analysis can predict utility loss before deployment across all 97 nominal tasks in AgentDojo. The static predictor achieved an accuracy of 92.8% with a 95% Wilson confidence interval of [85.8%, 96.5%]. The predictor produced zero false negatives on execution path: it never predicted a task would succeed when a required tool call on its path was blocked.

Protocol v8 (M1b) evaluated the predictor against the empirical task loss observed between Protocol v6b (undefended) and Protocol v6 (defended). Across the 97 tasks, exactly thirty (30) tasks completed successfully under v6b but failed under v6. Table 9 reports the confusion matrix of the static predictor against these lost tasks.

Table 9. Confusion matrix of pre-deployment utility cost prediction (Protocol v8 M1b).

| Prediction | Lost Task (v6b Completed, v6 Failed) | Retained Task (Not Lost) | Total |
|---|---|---|---|
| Predicted Block | 29 | 2 | 31 |
| Not Predicted | 1 | 65 | 66 |
| **Total** | **30** | **67** | **97** |

The static predictor flagged 31 of the 97 tasks as blocked. Twenty-nine of these were among the thirty lost tasks, two were false alarms, and one lost task was missed. Overall prediction accuracy reached 96.9% [91.3%, 98.9%], with a precision of 93.5% and a recall of 96.7%. In aggregate, 31 predicted blocks (32.0 percentage points) compare with 30 observed losses (30.9 percentage points). The net benign utility cost in Table 8 is 29.9 percentage points (29 tasks) rather than 30 tasks, because one task succeeded under Protocol v6 but not under Protocol v6b. Pre-deployment static analysis therefore anticipates the empirical utility cost of enforcement closely, although the agreement is approximate rather than exact.

### 4.4 RQ4: Topology floor and workflow structure

Proposition 3 (refinement monotonicity) was evaluated across 200 property tests, yielding zero counterexamples: splitting an agent's execution steps never increases worst-case blast radius. Proposition 4 (linear chain floor) establishes that in a linear dependency chain, agent partitioning and signed hand-offs cannot lower the worst-case blast radius below full pipeline reach. Property tests over 300 random linear chains confirmed closed-form equivalence with zero counterexamples. Closed-form equivalence was also verified across 76 real configuration combinations (38 linear chains under transcript and signed hand-off modes).

In linear chains, only policy changes that remove sink privileges lower the reach. Evaluating absolute reach across linear configurations shows that least-privilege synthesis reduces median nominal reach from 2.0 sinks to 1.0 sink. This achieves an absolute median reduction of 1.0 sink (mean 0.945).

To determine whether multi-agent workflows exhibit linear topologies, a structural census was conducted across fifty-five acyclic multi-agent configurations (nineteen self-authored and thirty-six mined from public repositories). Table 10 reports the structural properties of these fifty-five configurations.

Table 10. Structural census of fifty-five acyclic multi-agent configurations.

| Structural Property | Count | Proportion |
|---|---|---|
| Total acyclic configurations (census n) | 55 | 100.0% |
| Strictly sequential linear chains (chain count) | 49 | 89.1% |
| Dominating source agent covering all execution steps | 55 | 100.0% |
| Sink-bearing configurations with blast-radius floor of 1 | 21 | 100.0% |

Forty-nine of the fifty-five configurations (89.1%) are strictly sequential linear chains. All fifty-five configurations (100.0%) exhibit a dominating source agent whose influence reaches all subsequent steps. For all twenty-one sink-bearing configurations, the blast-radius floor under signed hand-offs equals 1. In the examined configurations, agent partitioning alone provides no containment in the absence of least privilege.

Protocol v7b mined public GitHub repositories implementing multi-agent workflows in CrewAI, LangGraph, and AutoGen. Table 11 reports the mining funnel and capability metrics.

Table 11. Real-world configuration mining funnel and metrics (Protocol v7b).

| Metric | Count | Estimate [95% Wilson CI] |
|---|---|---|
| Configurations discovered | 37 | - |
| Configurations scored | 36 | - |
| Configurations with no write or external sink | 34 | 94.4% [81.9%, 98.5%] |
| Strictly sequential linear configurations | 36 | 100.0% [90.4%, 100.0%] |
| Single-agent blast radius contains a sink | 2 | 5.6% [1.5%, 18.1%] |
| Zero-own-sink agent reaches downstream sink | 1 | 2.8% [0.5%, 14.2%] |
| Code execution tool present | 0 | 0.0% [0.0%, 9.6%] |

Thirty-seven configurations were discovered and thirty-six were scored (one LangGraph configuration was excluded as cyclic). Thirty-four of thirty-six scored configurations (94.4%) contained no write or external tool sinks under the frozen keyword classifier. All thirty-six scored configurations were sequential pipelines. The two configurations containing sinks confirmed the formal model's propagation logic: in one configuration, a zero-tool researcher agent reached a downstream file writer sink via context propagation.

### 4.5 RQ5: Nominal performance across model families

Table 12 reports main-suite task success, intent fidelity, and overhead for each condition, separately per model family. Figure 6 plots task success for the same cells.

Table 12. Main-suite performance across model families (DeepSeek 4.1 Flash, Gemini 3.5 Flash-Lite, and OpenAI GPT-OSS-120B).

| Model Family | Condition | Task Success [95% CI] | Intent Fidelity | Violations | Median Tokens | Median Wall Time (s) |
|---|---|---|---|---|---|---|
| DeepSeek 4.1 Flash | B1 | 0.989 [0.967, 1.000] | 0.999 | 0 | 3610 | 3.9 |
| DeepSeek 4.1 Flash | B2 | 1.000 [1.000, 1.000] | 1.000 | 0 | 3288 | 4.2 |
| DeepSeek 4.1 Flash | P | 0.989 [0.967, 1.000] | 0.999 | 0 | 3424 | 4.3 |
| DeepSeek 4.1 Flash | GPLUS | 1.000 [1.000, 1.000] | 1.000 | 0 | 3404 | 4.5 |
| Gemini 3.5 Flash-Lite | B1 | 0.935 [0.797, 1.000] | 0.989 | 0 | 2642 | 4.9 |
| Gemini 3.5 Flash-Lite | B2 | 0.969 [0.895, 1.000] | 0.995 | 0 | 2439 | 5.2 |
| Gemini 3.5 Flash-Lite | P | 0.967 [0.891, 1.000] | 0.994 | 0 | 2596 | 5.1 |
| Gemini 3.5 Flash-Lite | GPLUS | 0.968 [0.893, 1.000] | 0.995 | 0 | 2714 | 5.2 |
| OpenAI GPT-OSS-120B | B1 | 0.409 [0.238, 0.590] | 0.643 | 0 | 3879 | 24.7 |
| OpenAI GPT-OSS-120B | B2 | 0.390 [0.211, 0.575] | 0.667 | 0 | 4037 | 16.4 |
| OpenAI GPT-OSS-120B | P | 0.297 [0.158, 0.447] | 0.595 | 0 | 4196 | 25.5 |
| OpenAI GPT-OSS-120B | GPLUS | 0.318 [0.152, 0.512] | 0.632 | 0 | 3908 | 20.8 |

On DeepSeek 4.1 Flash (360 runs), task success sits at a ceiling across every condition: B1 reached 98.9%, B2 reached 100.0%, P reached 98.9%, and GPLUS reached 100.0%. Intent fidelity remained at 99.9% to 100.0% with zero violations. Every paired Wilcoxon comparison between conditions is non-significant after Holm correction. Because few tasks produced non-zero paired differences, the tests reflect ceiling effects rather than proven equivalence. The practical-significance criterion the proposal set in advance, a ten-percentage-point gain in success or fidelity, is not met by any condition over any other. Hypothesis H5a, that the proposed controls beat both baselines on success and fidelity, is therefore not supported. This is a null result, reported as such rather than reframed, and it is the finding the proposal itself anticipated as a live possibility given a sufficiently capable model.

Gemini 3.5 Flash-Lite (248 runs) replicates the same ceiling pattern: B1 scored 93.5%, B2 scored 96.9%, P scored 96.7%, and GPLUS scored 96.8%. Zero violations occurred in any condition. The open-weight OpenAI GPT-OSS-120B served on Groq (166 runs) behaves differently: B1 40.9 percent, B2 39.0 percent, P 29.7 percent, GPLUS 31.8 percent. Task success on this model is far below the others. This reflects model capability rather than the experimental condition. Wilcoxon tests find no significant differences between conditions on this model (adjusted p = 1.00). Zero nominal violations occurred in any condition on any model. Therefore, hypothesis H5b is not testable on nominal tasks. The baselines never violated policies on uncompromised tasks, so the gate had nothing to block.

![Figure 6. Main-suite task success by condition and model, mean with 95% cluster-bootstrap confidence interval.](scripts/paper/figures/fig4_main_suite_success.png)

Governance overhead is small relative to model latency on every model family. Scripted timing isolates monitor cost from provider response time. Monitor overhead measures 0.16 ms per run for B1, 0.23 ms for B2, 1.68 ms for P, and 1.69 ms for GPLUS. This remains negligible against model response times (Figure 7). Median wall time with a live model shows P at 1.03 times B2's time on DeepSeek 4.1 Flash. This falls comfortably within the 1.30 threshold, supporting hypothesis H5c.

![Figure 7. Overhead by condition: end-to-end wall time on DeepSeek 4.1 Flash, and monitor-only time isolated from provider latency.](scripts/paper/figures/fig7_overhead.png)

## 5. Discussion

### 5.1 Why nominal success did not move

The null result on nominal task success is not a failure of the proposed controls to work. This stems from a ceiling effect. Capable models solve nearly every nominal task correctly across all conditions. None of the nominal tasks require policy gating or routing to succeed. Measurement work on hand-off attenuation shows the same capability dependence (Li and Wang, 2026). Governance decay is severe on smaller 32-billion-parameter models and nearly absent on larger models. Both findings point the same way. The value of these controls appears only under failure conditions. This occurs when a model is weaker, as shown on Groq, or when an agent is compromised, as shown in Section 4.2.

### 5.2 Why containment needed two mechanisms, not one

The policy gate stops every out-of-domain action tested. External domains and destructive deletes can be identified from call metadata alone. The gate enforces these boundaries without inspecting the task text. In-domain steering presents a different challenge. The attacker's chosen recipient falls inside the permitted domain. Therefore, declarative policy rules alone cannot identify the violation. The provenance guard closes this gap. It verifies whether a recipient appears in the task's trusted text. The guard depends on the gate, because without the gate, out-of-domain actions remain unblocked.

### 5.3 What the static bound adds

Measuring containment by attacking a running multi-agent workflow can only report what was tested. The static blast-radius bound in Section 3.7 computes, before any agent runs, every effect a stated compromised set could cause. An operator can audit a configuration's worst case without having to construct and run every possible attack against it first.

The static analysis provides two key capabilities beyond empirical measurement. First, it identifies structural vulnerabilities in workflow definitions before deployment. The analysis uncovered the substring-matching provenance guard's vulnerability to crafted substring recipients and revealed structural over-privilege across eighteen of nineteen multi-agent configurations. Both vulnerabilities were confirmed empirically after the static analysis flagged them.

Second, the static analysis predicts deployment utility costs before execution (Contribution C2). Stricter security policies often break legitimate application workflows. Protocol v8 (M1b) showed that the static predictor anticipates empirical task loss with 96.9% accuracy, flagging 31 tasks against 30 observed losses. Operators can evaluate this trade-off statically rather than discovering workflow disruptions during live deployment.

### 5.4 Model invariance and the AgentDojo finding

A critical insight from the AgentDojo evaluation is that containment does not depend on model compliance. In Protocol v6b (undefended), DeepSeek 4.1 Flash exhibited an attack success rate of only 2.1%, resisting indirect prompt injections natively. Comparing defenses using live attack success on this model is uninformative, because the baseline model rarely executes injected instructions.

In contrast, the assumed-compromise replay in Protocol v8 (M1) evaluated the reference monitor against ground-truth malicious tool invocations directly. The monitor contained 92.3% of attack scenarios and blocked 93.6% of malicious sink calls deterministically. This demonstrates that GUIDE's security guarantees originate from external policy enforcement and provenance verification, not from model compliance.

### 5.5 Topology and least privilege

Proposition 4 proves that in strictly linear dependency chains, agent partitioning and cryptographic signing cannot reduce the worst-case blast radius below full pipeline reach. The structural census in Section 4.4 revealed that forty-nine of fifty-five examined configurations (89.1%) are strictly sequential linear chains, and all fifty-five contain a dominating source agent. In the examined multi-agent pipelines, partitioning agents across execution steps provides no structural containment against an upstream compromise.

Least-privilege policy synthesis is therefore the primary mechanism for reducing blast radius in sequential workflows. Synthesizing minimal policies reduced median reach by 1.0 sink across linear chains. However, this protection incurs a security versus utility trade-off. On the Slack suite, where downstream tools regularly depend on parameters returned by upstream tools, strict policy enforcement reduced benign utility by 66.7 percentage points. Statically predicting this utility loss before deployment (Section 4.3) enables designers to tune permissions rationally.

### 5.6 Practical implications

Operators deploying multi-agent pipelines obtain two concrete, actionable results from this study. First, a least-privilege policy can be synthesized directly from nominal execution traces, cutting reachable sink capability by 55.6% without breaking legitimate calls. Designers need not hand-craft complex security policies. Second, cryptographic hand-offs require per-principal signing keys. A shared key across agents detects zero percent of sender-spoofing attempts, whereas per-principal keys detect tampering at a 100 percent rate.

### 5.7 Limitations

This study has ten specific limitations:

1. Concurrent literature: Four 2026 preprints (Parisel, 2026, Muruaga, 2026, Moon & Varshney, 2026, Veski et al., 2026) examine related aspects of least autonomy, delegation security, and containment verification. GUIDE is an external reference monitor that also computes multi-agent static bounds, so partial conceptual overlap exists.
2. Proof verification: The soundness proof is checked by hand and by property-based testing against the real implementation of the monitor. It is not machine-checked in an interactive theorem prover.
3. Multi-agent evaluation suite: Multi-agent empirical evidence relies on the benchmark suite authored for this study, because no standardized benchmark for compromised-agent containment in multi-agent systems currently exists.
4. Single-agent external benchmark: The external AgentDojo benchmark is single-agent and was evaluated with one model family (DeepSeek 4.1 Flash).
5. Live workspace sample: Live workspace attack evaluations on AgentDojo used a 10-task subset, though the assumed-compromise replay (M1) covers the complete 949-pair grid.
6. Live injection unresponsiveness: Live AgentDojo attack success was uninformative for DeepSeek 4.1 Flash because the model resisted prompt injections natively.
7. Mined repository scope: The real-world configuration mining in Protocol v7b evaluates public demonstration repositories, and its keyword classifier provides a conservative lower bound.
8. DAG model constraint: Workflows containing cycles or unbounded retry loops fall outside the current DAG formal model.
9. Text-only attacks: Purely conversational injections that do not invoke external tools fall outside the scope of a tool-boundary reference monitor.
10. Admitted tool classes: The admitted calls in M1 include tools lacking control parameters (such as `update_password`) and recipient values that were legitimately part of the user's initial prompt.

## 6. Conclusion

This paper evaluated GUIDE, an external reference monitor for LLM multi-agent systems that computes a sound static blast-radius bound under assumed compromise, synthesises least-privilege policies, and enforces containment at runtime.

The investigation establishes four main contributions:

First, Contribution C1 delivers a sound static blast-radius bound for arbitrary compromised agent subsets, paired with least-privilege policy synthesis. The bound was proved sound, verified through property-based tests, and confirmed exact against a live adaptive attacker on thirty-nine of thirty-nine (39/39) direct effects with zero soundness violations.

Second, Contribution C2 introduces pre-deployment utility cost prediction. The static analysis accurately anticipates task disruption before execution, achieving 96.9% accuracy on AgentDojo. It flagged 31 of 97 tasks as blocked against 30 observed losses.

Third, Contribution C3 establishes the interaction topology floor. Proposition 4 proves that in strictly linear dependency chains, agent partitioning cannot lower the blast radius floor. The structural census confirmed that forty-nine of fifty-five examined configurations (89.1%) are strictly linear chains, demonstrating that least-privilege policy synthesis is the primary lever for risk reduction in practice.

Fourth, Contribution C4 provides extensive empirical findings across internal multi-agent suites and external benchmarks. The reference monitor achieved 92.3% containment under assumed compromise on AgentDojo. The analysis exposed security flaws in substring provenance guards admitting 692 recipients. It also revealed structural over-privilege across eighteen of nineteen configurations.

As an external reference monitor, GUIDE replaces reliance on prompt compliance with a sound static bound and deterministic enforcement at the tool and delegation boundary, which limits what a compromised agent in a multi-agent workflow can reach.

## Acknowledgments

The author thanks the supervisor, Ts. Dr. Maythem Kamal Abbas, and the course lecturer, Dr. R. Logeswaran, for guidance on this work. No external funding was received, and API credits used for the Groq and Google AI Studio evaluations in Section 3.5 were provided under each provider's public free-tier terms.

## Statements

- Data availability: the raw results files, manifests and summary statistics for every protocol version are archived with the tagged code release.
- Code availability: the reference monitor implementation, benchmark testbed, and all analysis scripts are released under the tagged commit in the project repository.
- Author contributions: SA conceived the study, formulated the formal model and proofs, implemented the reference monitor, and drafted the manuscript. MK supervised the study and reviewed the manuscript.
- Competing interests: the authors declare no competing interests.
- Ethics: this study used no human participants and no personal data about identifiable individuals. No ethics approval was required for the work reported here.
- Generative AI use: an AI coding and writing assistant was used during drafting, data aggregation scripting, and literature screening, under the author's direction and review. The author is responsible for every claim, number and citation in this paper and has verified each against the underlying experimental data files.

## References

References are listed alphabetically by first author surname following APA 7th edition.

Abdelnabi, S., Fay, A., Cherubin, G., Salem, A., Fritz, M., & Paverd, A. (2025). Get My Drift? Catching LLM Task Drift with Activation Deltas. 2025 IEEE Conference on Secure and Trustworthy Machine Learning (SaTML), 43–67. https://doi.org/10.1109/satml64287.2025.00011

Abdelnabi, S., Gomaa, A., & Fritz, M. (2025). Firewalls to Secure Dynamic LLM Agentic Networks. Transactions on Machine Learning Research. https://openreview.net/forum?id=G2k9N7wL1M

Amayuelas, A., Yang, X., Antoniades, A., Hua, W., Pan, L., & Wang, W. (2024). MultiAgent Collaboration Attack: Investigating Adversarial Attacks in Large Language Model Collaborations via Debate. Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing, 4732–4749. https://doi.org/10.18653/v1/2024.emnlp-main.274

An, H., Zhang, J., Du, T., Zhou, C., Li, Q., Lin, T., & Ji, S. (2025). IPIGuard: A Novel Tool Dependency Graph-Based Defense Against Indirect Prompt Injection in LLM Agents. Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing, 1023–1039. https://doi.org/10.18653/v1/2025.emnlp-main.53

Andriushchenko, M., Souly, A., Dziemian, M., Duenas, D., Lin, M., Wang, J., Hendrycks, D., Zou, A., Kolter, Z., Fredrikson, M., Winsor, E., Wynne, J., Gal, Y., & Davies, X. (2025). AgentHarm: A Benchmark for Measuring Harmfulness of LLM Agents. International Conference on Learning Representations (ICLR 2025). https://openreview.net/forum?id=AC5n7xHuR1

Auer, P., Cesa-Bianchi, N., & Fischer, P. (2002). Finite-time Analysis of the Multiarmed Bandit Problem. Machine Learning. https://doi.org/10.1023/A:1013689704352

Backes, J., Bolignano, P., Cook, B., & Dodge, C. (2018). Semantic-based Automated Reasoning for AWS Access Policies using SMT. https://doi.org/10.23919/fmcad.2018.8602994

Becker, J., Kaesberg, L. B., Stephan, A., Wahle, J. P., Ruas, T., & Gipp, B. (2026). Stay Focused: Problem Drift in Multi-Agent Debate. Findings of the Association for Computational Linguistics: EACL 2026. https://doi.org/10.18653/v1/2026.findings-eacl.268

Bernstein, D. J., Duif, N., Lange, T., Schwabe, P., & Yang, B.-Y. (2012). High-speed high-security signatures. Journal of Cryptographic Engineering. https://doi.org/10.1007/s13389-012-0027-1

Calboreanu, E. (2026). TRACE: Runtime Governance, Containment, and Evidence for Autonomous AI Agent Operations. IEEE Access, 14, 142574–142594. https://doi.org/10.1109/access.2026.3733578

Cemri, M., Tulsiani, S., Pathak, D., & Darrell, T. (2025). Why Do Multi-Agent LLM Systems Fail? Advances in Neural Information Processing Systems 38, 31742–31776. https://doi.org/10.52202/085713-3375

Chang, E. Y., & Geng, L. (2025). SagaLLM: Context Management, Validation, and Transaction Guarantees for Multi-Agent LLM Planning. Proceedings of the VLDB Endowment, 18(12), 4874–4886. https://doi.org/10.14778/3750601.3750611

Chen, Z., Liu, H., Xu, D., Dong, D., Li, J., Pu, B., & Zhai, J. (2026). Cordon: Semantic Transactions for Tool-Using LLM Agents. arXiv preprint arXiv:2606.17573. https://arxiv.org/abs/2606.17573

Chen, Z., Zhang, T., Zhu, S., & Li, B. (2025). ShieldAgent: Shielding Agents via Verifiable Safety Policy Reasoning. Forty-second International Conference on Machine Learning. https://openreview.net/forum?id=DkRYImuQA9

Cheney, J., Chiticariu, L., & Tan, W.-C. (2009). Provenance in Databases: Why, How, and Where. Foundations and Trends in Databases. https://doi.org/10.1561/1900000006

Chinaei, M. H. (2026). Causality Laundering: Denial-Feedback Leakage in Tool-Calling LLM Agents. arXiv preprint arXiv:2604.04035. https://arxiv.org/abs/2604.04035

Costa, M., Köpf, B., Kolluri, A., & Paverd, A. (2025). Securing AI Agents with Information-Flow Control. arXiv preprint arXiv:2505.23643. https://arxiv.org/abs/2505.23643

Dai, H., Ying, Z., Li, W., & Wu, X. (2026). SafeFlow: Semantic Information-Flow Control for Blocking Malicious Propagation in Multi-Agent Systems. arXiv preprint arXiv:2607.25255. https://arxiv.org/abs/2607.25255

Dang, Y., Chen, Q., Luo, X. L., & Fan, J. (2025). Multi-Agent Collaboration via Evolving Orchestration. https://doi.org/10.52202/085713-5502

Debenedetti, E., Shumailov, I., Fan, T., Hayes, J., Carlini, N., Fabian, D., Kern, C., Shi, C., Terzis, A., & Tramèr, F. (2026). Defeating Prompt Injections by Design. 2026 IEEE Conference on Secure and Trustworthy Machine Learning (SaTML), 587–618. https://doi.org/10.1109/satml68715.2026.00040

Debenedetti, E., Zhang, J., Balunovic, M., Beurer-Kellner, L., Fischer, M., & Tramèr, F. (2024). AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents. Advances in Neural Information Processing Systems 37, 82895–82920. https://doi.org/10.52202/079017-2636

Denning, D. E. (1976). A lattice model of secure information flow. Communications of the ACM. https://doi.org/10.1145/360051.360056

Dong, S., Xu, S., He, P., Li, Y., Tang, J., Liu, T., Liu, H., & Xiang, Z. (2025). Memory Injection Attacks on LLM Agents via Query-Only Interaction. Advances in Neural Information Processing Systems 38, 52119–52153. https://doi.org/10.52202/085713-1554

Gandhi, P. A., Shukla, A., Tayouri, D., Ifland, B., Elovici, Y., & Puzis, R. (2025). ATAG: AI-Agent Application Threat Assessment with Attack Graphs. ACM Asia Conference on Computer and Communications Security. https://doi.org/10.1145/3779208.3785380

Gill-Lakhowal, A. (2026). Deterministic Runtime Enforcement: The Execution Authority for Autonomous AI Agents. IEEE Access, 14, 119764–119790. https://doi.org/10.1109/access.2026.3719838

Gomaa, A., Abdelnabi, S., & Fritz, M. (2025). ConVerse: Benchmarking Contextual Safety in Agent-to-Agent Conversations. Proceedings of the 18th Conference of the European Chapter of the Association for Computational Linguistics (Volume 1: Long Papers), 1017–1033. https://doi.org/10.18653/v1/2025.eacl-main.62

Greshake, K., Abdelnabi, S., Mishra, S., Endres, C., Holz, T., & Fritz, M. (2023). Not What You've Signed Up For: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection. Proceedings of the 16th ACM Workshop on Artificial Intelligence and Security, 79–90. https://doi.org/10.1145/3605764.3623985

Guo, Y., Hu, X., Zhang, T., Shen, Y., & Xiao, Y. (2024). RedCode: Risky Code Execution and Generation Benchmark for Code Agents. Advances in Neural Information Processing Systems 37, 69022–69051. https://doi.org/10.52202/079017-2197

Guo, Z., Xu, B., Zhu, C., Hong, W., Wang, X., & Mao, Z. (2026). MCP-AgentBench: Evaluating Real-World Language Agent Performance with MCP-Mediated Tools. Proceedings of the AAAI Conference on Artificial Intelligence. https://doi.org/10.1609/aaai.v40i37.40347

Hevner, A. R., March, S. T., Park, J., & Ram, S. (2004). Design Science in Information Systems Research. MIS Quarterly. https://doi.org/10.2307/25148625

Huang, Y., Shi, C., Wang, J., Zhang, Z., & Li, B. (2024). On the Resilience of LLM-Based Multi-Agent Collaboration with Faulty Agents. Proceedings of the 41st International Conference on Machine Learning, 235, 19949–19972. https://proceedings.mlr.press/v235/huang24s.html

Ji, J., Lei, R., Bi, J., Wei, Z., Chen, X., Lin, Y., Pan, X., Li, Y., & Ding, B. (2025). LLM-Based Multi-Agent Systems are Scalable Graph Generative Models. Findings of the Association for Computational Linguistics: ACL 2025. https://doi.org/10.18653/v1/2025.findings-acl.78

Jia, F., Wu, T., Qin, X., & Squicciarini, A. (2025). The Task Shield: Enforcing Task Alignment to Defend Against Indirect Prompt Injection in LLM Agents. Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), 29680–29697. https://doi.org/10.18653/v1/2025.acl-long.1435

Jia, Y., Shao, Z., Liu, Y., Jia, J., Song, D., & Gong, N. (2026). A Critical Evaluation of Defenses against Prompt Injection Attacks: [Dataset/Tool Paper]. Proceedings of the 31st ACM Symposium on Access Control Models and Technologies, 265–270. https://doi.org/10.1145/3750555.3811884

Ju, T., Wang, Y., Hua, Y., Ma, X., Cheng, P., Zhao, H., Wang, Y., Liu, L., Xie, J., Zhang, Z., & Liu, G. (2026). Flooding spread of manipulated knowledge in LLM-based multi-agent communities. Science China Information Sciences, 69(7). https://doi.org/10.1007/s11432-024-4663-2

Kaufmann, E., Cappé, O., & Garivier, A. (2012). On Bayesian upper confidence bounds for bandit problems. Proceedings of the 15th International Conference on Artificial Intelligence and Statistics, PMLR 22, 592–600. https://proceedings.mlr.press/v22/kaufmann12.html

Kavathekar, I., Jain, H., Rathod, A., & Kumaraguru, P. (2025). TAMAS: Benchmarking Adversarial Risks in Multi-Agent LLM Systems. arXiv preprint arXiv:2511.05269. https://arxiv.org/abs/2511.05269

Khan, R. M. S., Tan, Z., Yun, S., Fleming, C., & Chen, T. (2025). Agents Under Siege: Breaking Pragmatic Multi-Agent LLM Systems with Optimized Prompt Attacks. Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), 8856–8874. https://doi.org/10.18653/v1/2025.acl-long.446

Kitchenham, B., & Charters, S. (2007). Guidelines for performing systematic literature reviews in software engineering (EBSE Technical Report EBSE-2007-01). Keele University and Durham University.

La Malfa, E., La Malfa, G., Marro, S., Zhang, J., Black, E., Luck, M., Torr, P., & Wooldridge, M. (2025). Large Language Models Miss the Multi-Agent Mark. Advances in Neural Information Processing Systems 38 (NeurIPS 2025). https://doi.org/10.52202/085713-4663

Lan, W., Li, S., Wu, M., & Lai, X. (2026). ContainmentBench: Trace-Based Evaluation of Post-Exposure Containment in Tool-Using LLM Agents. arXiv preprint arXiv:2607.23999. https://arxiv.org/abs/2607.23999

Le, T. D., Dinh, T. D., Nguyen, T. L. Q., & Nguyen, C. D. (2026). Cross-layer contagion of prompt injections in multi-agent swarms: a multiplex microscopic markov chain approach. Cybersecurity, 9(1). https://doi.org/10.1186/s42400-026-00628-w

Lee, D., Tiwari, M., & Miranda, B. (2026). Prompt Infection: LLM-to-LLM Prompt Injection within Multi-agent Systems. Lecture notes in computer science. https://doi.org/10.1007/978-3-032-16092-8_28

Li, B., & Wang, G. (2026). Governance at the Boundary: How Agent Decomposition Degrades Policy Compliance. arXiv preprint arXiv:2608.16055. https://arxiv.org/abs/2608.16055

Li, E., Mallick, T., Rose, E., Robertson, W., Oprea, A., & Nita-Rotaru, C. (2026). ACE: A Security Architecture for LLM-Integrated App Systems. Proceedings 2026 Network and Distributed System Security Symposium. https://doi.org/10.14722/ndss.2026.230352

Li, Z., Cui, J., Liao, X., Xing, L., Xing, L., & Li, Z. (2026). Les Dissonances: Cross-Tool Harvesting and Polluting in Pool-of-Tools Empowered LLM Agents. Proceedings 2026 Network and Distributed System Security Symposium. https://doi.org/10.14722/ndss.2026.240577

Li, Z., Li, K., Ma, B., Xu, M., Zhang, Y., & Cheng, X. (2025). We Urgently Need Privilege Management in MCP: A Measurement of API Usage in MCP Ecosystems. 2025 IEEE 22nd International Conference on Mobile Ad-Hoc and Smart Systems (MASS), 555–560. https://doi.org/10.1109/mass66014.2025.00090

Li, Z., Zhang, T., Hu, X., Shen, Y., & Xiao, Y. (2025). DRIFT: Dynamic Rule-Based Defense with Injection Isolation for Securing LLM Agents. Advances in Neural Information Processing Systems 38, 46083–46109. https://doi.org/10.52202/085713-4886

Liu, F., Zhang, Y., Luo, J., Dai, J., Chen, T., Yuan, L., Yu, Z., Shi, Y., Li, K., Zhou, C., Chen, H., & Yang, M. (2025). Make Agent Defeat Agent: Automatic Detection of Taint-Style Vulnerabilities in LLM-based Agents. 34th USENIX Security Symposium (USENIX Security 25). https://www.usenix.org/conference/usenixsecurity25/presentation/liu-fengyu

Liu, S., Chen, Y., Krishna, R., Sinha, S., Ganhotra, J., & Jabbarvand, R. (2026). Process-Centric Analysis of Agentic Software Systems. Proceedings of the ACM on Programming Languages, 10(OOPSLA1), 1961–1988. https://doi.org/10.1145/3798271

Liu, Y., Jia, Y., Geng, R., Jia, J., & Gong, N. Z. (2024). Formalizing and benchmarking prompt injection attacks and defenses. 33rd USENIX Security Symposium.

Liu, Y., Jia, Y., Jia, J., Song, D., & Gong, N. Z. (2025). DataSentinel: A Game-Theoretic Detection of Prompt Injection Attacks. 2025 IEEE Symposium on Security and Privacy (SP), 2190–2208. https://doi.org/10.1109/sp61157.2025.00250

Miao, R., Liu, Y., Wang, Y., Shen, X., Tan, Y., & Dai, Y. (2025). BlindGuard: Safeguarding LLM-based Multi-Agent Systems under Unknown Attacks. Annual Meeting of the Association for Computational Linguistics. https://arxiv.org/abs/2508.08127

Mo, Y., Wang, H., Chen, Y., & Song, D. (2025). Attractive Metadata Attack: Inducing LLM Agents to Invoke Malicious Tools. Advances in Neural Information Processing Systems 38, 24874–24901. https://doi.org/10.52202/085713-2633

Mohammadi, M., Li, Y., Lo, J., & Yip, W. (2025). Evaluation and Benchmarking of LLM Agents: A Survey. Proceedings of the 31st ACM SIGKDD Conference on Knowledge Discovery and Data Mining V.2. https://doi.org/10.1145/3711896.3736570

Moon, R., & Varshney, L. R. (2026). Containment Verification: AI Safety Guarantees Independent of Alignment. arXiv preprint arXiv:2605.09045. https://arxiv.org/abs/2605.09045

Motwani, S., Baranchuk, M., Strohmeier, M., Bolina, V., Torr, P., Hammond, L., & Witt, C. D. (2024). Secret Collusion among AI Agents: Multi-Agent Deception via Steganography. Advances in Neural Information Processing Systems 37, 73439–73486. https://doi.org/10.52202/079017-2336

Moutesidis, T. (2026). The Model Proposes, the Code Disposes: A Pre-Registered Ablation of a Verifier-and-Acceptance Stage in an LLM-Orchestrated Offensive-Security Agent. arXiv preprint arXiv:2609.15887. https://arxiv.org/abs/2609.15887

Muruaga, X. (2026). Bounded Agents: Delegation Security for Multi-Agent AI Systems. arXiv preprint arXiv:2608.15888. https://arxiv.org/abs/2608.15888

Narisetty, P., Kore, S. N. B., Kattamanchi, U. K. R., & Kumarapu, J. (2026). Adaptive Evaluation of Out-of-Band Defenses Against Prompt Injection in LLM Agents. arXiv preprint arXiv:2606.26479. https://arxiv.org/abs/2606.26479

Nikolaou, E., Eckhoff, M. W., Flood, R., Grov, G., Mavroeidis, V., & Aspinall, D. (2026). CaMeLoT: CaMeL orchestrated with Temporal logic for static verification and liveness. arXiv preprint arXiv:2609.18674. https://arxiv.org/abs/2609.18674

Page, M. J., McKenzie, J. E., Bossuyt, P. M., Boutron, I., Hoffmann, T. C., Mulrow, C. D., Shamseer, L., Tetzlaff, J. M., Akl, E. A., Brennan, S. E., Chou, R., Glanville, J., Grimshaw, J. M., Hróbjartsson, A., Lalu, M. M., Li, T., Loder, E. W., Mayo-Wilson, E., McDonald, S., . . . Moher, D. (2021). The PRISMA 2020 statement: an updated guideline for reporting systematic reviews. BMJ. https://doi.org/10.1136/bmj.n71

Parisel, C. (2026). A Theory of Least Autonomy in AI. arXiv preprint arXiv:2607.09744. https://arxiv.org/abs/2607.09744

Park, J. S., O'Brien, J., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). Generative Agents: Interactive Simulacra of Human Behavior. Proceedings of the 36th Annual ACM Symposium on User Interface Software and Technology. https://doi.org/10.1145/3586183.3606763

Pasupuleti, V., Allala, S. R., Bayyavarapu, S. R. K. V., & Tyagi, S. (2026). Safe and Policy-Compliant Multi-Agent Orchestration for Enterprise AI. 2026 International Conference on Artificial Intelligence, Systems, and Emerging Technologies (ICAISET). https://doi.org/10.1109/ICAISET66439.2026.11541969

Paul, R. K., & Nandy, S. (2026). Beyond Single-Model Injection: A Threat Model and Defense Architecture for Prompt Injection in Multi-Agent Systems. arXiv preprint arXiv:2609.22949. https://arxiv.org/abs/2609.22949

Peffers, K., Tuunanen, T., Rothenberger, M. A., & Chatterjee, S. (2007). A Design Science Research Methodology for Information Systems Research. Journal of Management Information Systems. https://doi.org/10.2753/MIS0742-1222240302

Peigné-Lefebvre, M., Wang, X., Tan, Z., & Chen, T. (2025). Multi-Agent Security Tax: Trading Off Security and Collaboration Capabilities in Multi-Agent LLM Systems. Proceedings of the AAAI Conference on Artificial Intelligence, 39(26), 26865–26873. https://doi.org/10.1609/aaai.v39i26.35338

Ruan, Y., Dong, H., Wang, A., Pitis, S., Zhou, Y., Ba, J., Dubois, Y., Maddison, C. J., & Hashimoto, T. (2024). Identifying the Risks of LM Agents with an LM-Emulated Sandbox. The Twelfth International Conference on Learning Representations (ICLR 2024). https://openreview.net/forum?id=V2s6rVv7tK

Safin, T. H., Zisad, S. N., Shatabda, S., & Hasan, R. (2026). Trust propagation and structural containment in Multi-agent LLM pipelines. arXiv preprint arXiv:2609.17648. https://arxiv.org/abs/2609.17648

Saltzer, J.H., & Schroeder, M.D. (1975). The protection of information in computer systems. Proceedings of the IEEE. https://doi.org/10.1109/PROC.1975.9939

Shi, J., Yuan, Z., Tie, G., Zhou, P., Gong, N., & Sun, L. (2026). Prompt Injection Attack to Tool Selection in LLM Agents. Proceedings 2026 Network and Distributed System Security Symposium. https://doi.org/10.14722/ndss.2026.230675

Shi, T., He, J., Wang, Z., & Li, H. (2025). Progent: Securing AI Agents with Privilege Control. arXiv preprint arXiv:2504.11703. https://arxiv.org/abs/2504.11703

Sidik, B., & Rokach, L. (2026). Beyond Static Sandboxing: Learned Capability Governance for Autonomous AI Agents. arXiv preprint arXiv:2604.11839. https://arxiv.org/abs/2604.11839

Song, H., Shen, Y., Luo, W., Guo, L., Chen, T., Wang, J., Li, B., Zhang, X., & Chen, J. (2026). Beyond the Protocol: Unveiling Attack Vectors in the Model Context Protocol (MCP) Ecosystem. IEEE Transactions on Software Engineering, 52(8), 2410–2426. https://doi.org/10.1109/tse.2026.3694876

Su, J., Lan, Q., Xia, Y., Sun, L., Tian, W., Shi, T., & He, L. (2026). Difficulty-Aware Agentic Orchestration for Query-Specific Multi-Agent Workflows. Proceedings of the ACM Web Conference 2026, 2060–2070. https://doi.org/10.1145/3774904.3792240

Syros, G., Suri, A., Ginesin, J., Nita-Rotaru, C., & Oprea, A. (2025). SAGA: A Security Architecture for Governing AI Agentic Systems. Network and Distributed System Security Symposium. https://arxiv.org/abs/2504.21034

Triedman, H., Jha, R., & Shmatikov, V. (2025). Multi-Agent Systems Execute Arbitrary Malicious Code. Conference on Language Modeling (COLM 2025). https://openreview.net/forum?id=DAozI4etUp

Veski, R. M., Guerraoui, R., & Froelicher, D. (2026). CAPMAS: Capability-Based Delegation of Privileges in Multi-Agent Systems. arXiv preprint arXiv:2609.06500. https://arxiv.org/abs/2609.06500

Wang, H. K., & Zhang, Z. (2026). Kill-Chain Canaries: Stage-Level Tracking of Prompt Injection Across Attack Surfaces and Five Production LLMs. arXiv preprint arXiv:2603.28013. https://arxiv.org/abs/2603.28013

Wang, H., Poskitt, C. M., & Sun, J. (2025). AgentSpec: Customizable Runtime Enforcement for Safe and Reliable LLM Agents. Proc. ICSE'26, pages 2938-2950. ACM, 2026. https://doi.org/10.1145/3744916.3764546

Wang, L., Ma, C., Feng, X., Zhang, Z., Yang, H., Zhang, J., Chen, Z., Tang, J., Chen, X., Lin, Y., Zhao, W. X., Wei, Z., & Wen, J. (2024). A survey on large language model based autonomous agents. Frontiers of Computer Science. https://doi.org/10.1007/s11704-024-40231-1

Wang, S., Hou, X., Zhao, Y., Cheng, X., & Wang, H. (2026). AgentFlow: Building Agent Dependency Graphs for Static Analysis of Agent Programs. arXiv preprint arXiv:2607.01640. https://arxiv.org/abs/2607.01640

Wang, S., Zhang, G., Yu, M., Wan, G., Meng, F., & Guo, C. (2025). G-Safeguard: A Topology-Guided Security Lens and Treatment on LLM-based Multi-agent Systems. Annual Meeting of the Association for Computational Linguistics. https://arxiv.org/abs/2502.11127

Wang, X., Huang, K., Liang, B., Li, H., & Du, X. (2025). Shadows in the Code: Exploring the Risks and Defenses of LLM-based Multi-Agent Software Development Systems. Proceedings of the AAAI Conference on Artificial Intelligence, 39(27), 27504–27512. https://doi.org/10.1609/aaai.v39i27.35411

Wang, Y., Chen, S., Alkhudair, R., Alomair, B., & Wagner, D. (2026). Defending Against Prompt Injection with DataFilter. 2026 IEEE Conference on Secure and Trustworthy Machine Learning (SaTML), 139–157. https://doi.org/10.1109/satml68715.2026.00017

Wang, Y., Geng, R., Chen, Y., & Jia, J. (2026). AttnTrace: Contextual Attribution of Prompt Injection and Knowledge Corruption. 2026 IEEE Symposium on Security and Privacy (SP), 4320–4338. https://doi.org/10.1109/sp63933.2026.00198

Wang, Z., Gao, Y., Wang, Y., Liu, S., Sun, H., Cheng, H., Shi, G., Du, H., & Li, X. (2026). MCPTox: A Benchmark for Tool Poisoning on Real-World MCP Servers. Proceedings of the AAAI Conference on Artificial Intelligence, 40(42), 35811–35819. https://doi.org/10.1609/aaai.v40i42.40895

Wohlin, C. (2014). Guidelines for snowballing in systematic literature studies and a replication in software engineering. Proceedings of the 18th International Conference on Evaluation and Assessment in Software Engineering. https://doi.org/10.1145/2601248.2601268

Wu, Q., Bansal, G., Zhang, J., Wu, Y., Li, B., Zhu, E., Jiang, L., Zhang, X., Zhang, S., Liu, J., Awadallah, A. H., White, R. W., Burger, D., & Wang, C. (2024a). AutoGen: Enabling next-gen LLM applications via multi-agent conversations. First Conference on Language Modeling (COLM 2024).

Wu, Y., Roesner, F., Kohno, T., & Zhang, N. (2024b). IsolateGPT: An execution isolation architecture for LLM-based agentic systems. Network and Distributed System Security (NDSS) Symposium 2025. https://arxiv.org/abs/2403.04960

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

Zhou, S., Xu, F. F., Zhu, H., Zhou, X., Lo, R., Sridhar, A., Cheng, X., Ou, T., Bisk, Y., Fried, D., Alon, U., & Neubig, G. (2024). WebArena: A realistic web environment for building autonomous agents. The Twelfth International Conference on Learning Representations (ICLR 2024).

Zhu, J., Tseng, K., Vernik, G., Huang, X., Patil, S. G., & Fang, V. (2025). MiniScope: A Least Privilege Framework for Authorizing Tool Calling Agents. arXiv preprint arXiv:2512.11147. https://arxiv.org/abs/2512.11147

Zhu, S., Chen, Z., Wang, Z., & Li, B. (2025). MELON: Provable Defense Against Indirect Prompt Injection Attacks in AI Agents. Forty-second International Conference on Machine Learning. https://openreview.net/forum?id=gt1MmGaKdZ

Zhuge, M., Gao, H., Wang, X., Gao, J., Shi, S., Hou, X., Zhang, J., & Shen, Z. (2024). Language Agents as Optimizable Graphs. Proceedings of the 41st International Conference on Machine Learning, 235, 62743–62767. https://proceedings.mlr.press/v235/zhuge24a.html

Zou, A., Xiao, Z., Ba, J., Fredrikson, M., Kolter, Z., & Hendrycks, D. (2025). Security Challenges in AI Agent Deployment: Insights from a Large Scale Public Competition. Advances in Neural Information Processing Systems 38, 16584–16624. https://doi.org/10.52202/085713-1768

## Supplementary material

The following material is provided with the tagged code release and is not reproduced in this manuscript. The formal model and the proofs of the step-containment and blast-radius soundness theorems are in `docs/formal_model.md`. Task specifications, per-task result tables for every suite and model family, and policy files are in `docs/experiments.md` and `experiments/`. The literature review protocol, search strings, and PRISMA counts are in `docs/lit-review/`. Exact commands that regenerate every table and figure are in `REPRODUCE.md`.

Figure S1 reports a routing simulation used to study the Bayes-UCB routing policy of Control 1 in isolation.

![Figure S1. Routing simulation regret, stationary versus drift scenario, mean over 100 seeds per algorithm.](scripts/paper/figures/figS2_routing_regret.png)
