# Final Competitor Check (Novelty Guard)

Generated: 2026-10-02 18:36:45 UTC
Queries: 6 arXiv queries (submitted >= 2026-07-01).
Total unique papers retrieved: 55.
- NOVELTY-CRITICAL: 1
- RELATED: 20
- UNRELATED: 34

---

## Novelty-Critical Hits

### [2608.15888v1] Bounded Agents: Delegation Security for Multi-Agent AI Systems
- **Date**: 2026-08-16
- **Verdict**: `NOVELTY-CRITICAL`
- **First Sentence**: LLM-based agents can act on behalf of a user to access cloud services, call tools, or invoke agents.
- **Analysis & Contrast**: Claims Blast Radius Monotonicity proof along dynamically instantiated principal chains and evaluates runtime containment on AgentDojo and InjecAgent. Honest contrast: APC is a runtime delegation authorization mechanism tracking dynamic chains, whereas GUIDE computes a sound static graph-theoretic bound over MAS workflow DAGs before execution and predicts deployment utility cost.

---

## Related Work (Potential Context / Citations)

- **[2609.38248v1]** (2026-09-29) *ContractWarden: Kernel-Enforced Damage Boundaries for AI Agents via Human-Authorized Contracts*
  - Verdict: `RELATED`
  - First Sentence: Large language model agents can execute commands, create subprocesses, and directly access files and networks, allowing prompt injection or planning errors to become operating-system side effects.

- **[2609.33102v1]** (2026-09-27) *ORBIT: A Framework for Multi-Agent Safety and Security Evaluations*
  - Verdict: `RELATED`
  - First Sentence: Multi-agent LLM systems are increasingly deployed for complex, long-horizon tasks or emerge as a natural consequence of agents interacting in the wild.

- **[2609.33371v1]** (2026-09-27) *API Secrets Should Never Become Tokens in the LLM's Vocabulary: A Threat Analysis of API Credential Handling in LLM Agent Systems and an Empirical Evaluation of a Vault-Mediated Execution Boundary*
  - Verdict: `RELATED`
  - First Sentence: Tool-using large language model (LLM) agents turn credential hygiene from a storage problem into an execution-security problem.

- **[2609.22949v1]** (2026-09-19) *Beyond Single-Model Injection: A Threat Model and Defense Architecture for Prompt Injection in Multi-Agent Systems*
  - Verdict: `RELATED`
  - First Sentence: Existing prompt injection research focuses on single-model chatbot scenarios, where an attacker manipulates one LLM through crafted input.

- **[2609.19391v1]** (2026-09-16) *MAGS: Multi-agent Auto-formalization Guarantees Safety for Agentic Outputs*
  - Verdict: `RELATED`
  - First Sentence: LLM coding agents now generate complex programs at a scale that makes thorough human review increasingly difficult, raising the risk of safety and security failures.

- **[2609.17648v1]** (2026-09-15) *Trust propagation and structural containment in Multi-agent LLM pipelines*
  - Verdict: `RELATED`
  - First Sentence: Multi-agent LLM systems increasingly automate tasks involving agents with different levels of privilege, creating a security risk in which a compromised low-privilege agent can influence a higher-privilege agent and trigger an unauthorized action.

- **[2609.13731v1]** (2026-09-12) *Trustworthy Agentic AI: A Comprehensive Cybersecurity and Systems Survey on Threat Landscapes, Defense Architectures, and Open Challenges*
  - Verdict: `RELATED`
  - First Sentence: The transition from passive foundation models to autonomous, goal-directed agentic AI systems has introduced unprecedented capabilities by coupling recursive cognitive reasoning loops, persistent memory architectures, live tool execution planes, and multi-agent collaboration topologies.

- **[2609.12582v1]** (2026-09-11) *NovaFabric: Tamper-Evident, Replayable Evidence for Autonomous AI Agent Runs*
  - Verdict: `RELATED`
  - First Sentence: When an autonomous AI agent does something consequential, what can be proven about what it did?

- **[2609.05920v1]** (2026-09-05) *Versioned Transitive Dependency-Closure Binding and Operation-Time Effect Governance for Agent Skills: ClosureBound*
  - Verdict: `RELATED`
  - First Sentence: Agent Skills combine instructions with files, packages, tools, models, and services, so operational identity can exceed a signed directory.

- **[2609.00267v1]** (2026-08-31) *Delegation Without Trust: An Empirical Gap Analysis of Identity, Authorization, and Runtime Governance in Multi-Agent LLM Systems*
  - Verdict: `RELATED`
  - First Sentence: Autonomous LLM agents increasingly act on a user's behalf: they hold credentials, call tools and services, and spawn sub-agents that act further on their behalf.

- **[2608.30387v1]** (2026-08-31) *Attesting Outputs and Delegation Ancestry in Multi-Agent AI Systems*
  - Verdict: `RELATED`
  - First Sentence: Multi-agent applications delegate work across independently operated deployers.

- **[2608.30041v1]** (2026-08-30) *Reachability-Based Capability Confinement for LLM Agents under Indirect Prompt Injection*
  - Verdict: `RELATED`
  - First Sentence: Large language model agents place outputs from external skills into their execution context, allowing attacker-controlled data to influence later privileged actions.

- **[2608.22868v1]** (2026-08-24) *AgentFlow: A Flow-Centric Policy Language and Framework for Securing LLM Agent Systems*
  - Verdict: `RELATED`
  - First Sentence: LLM agents increasingly read untrusted content, invoke external tools, access private data, and delegate work to other agents.

- **[2608.01719v1]** (2026-08-03) *MNC: Scope-Bound Semantic Declassification for Private LLM-Agent Communication*
  - Verdict: `RELATED`
  - First Sentence: Multi-agent large language model (LLM) systems can expose protected state through internal messages, tool arguments, logs, and persistent memory even when their public outputs appear innocuous.

- **[2608.00202v1]** (2026-07-31) *From Monoliths to Swarms: A Study of Attack Surface Evolution in the Transition to Multi-Agent Web Systems*
  - Verdict: `RELATED`
  - First Sentence: Large Language Model (LLM)-based web agents are increasingly evolving from single-agent systems (SAS) to multi-agent systems (MAS).

- **[2607.24625v2]** (2026-07-27) *APPA: Recoverable Information-Flow Control for Real-World LLM Agents*
  - Verdict: `RELATED`
  - First Sentence: LLM agents deployed in practical workflows routinely mix private context, untrusted tool and web outputs, and external side effects.

- **[2607.22445v1]** (2026-07-24) *Dynamic Capability Scoping for Enterprise AI Agents: A Synthetic Dataset and Three-Source Permission Architecture*
  - Verdict: `RELATED`
  - First Sentence: Enterprise AI agents are typically granted static credential sets at configuration time, holding every tool the role might need for every task they perform.

- **[2607.06807v1]** (2026-07-07) *When Agents Go Rogue: Activation-Based Detection of Malicious Behaviors in Multi-Agent Systems*
  - Verdict: `RELATED`
  - First Sentence: While enabling effective collaboration on complex tasks, LLM-based Multi-Agent Systems (MAS) face critical security challenges due to vulnerabilities at the agent and interaction levels.

- **[2607.02294v1]** (2026-07-02) *Coding Agents Are Guessing: Measuring Action-Boundary Violations in Underspecified DevOps Instructions*
  - Verdict: `RELATED`
  - First Sentence: LLM coding agents are increasingly deployed to act autonomously on real production infrastructure.

- **[2607.01640v1]** (2026-07-02) *AgentFlow: Building Agent Dependency Graphs for Static Analysis of Agent Programs*
  - Verdict: `RELATED`
  - First Sentence: LLM agents are increasingly developed as source-code applications built on agent frameworks.

---

## Unrelated Hits

- **[2610.00430v1]** (2026-09-30) *Memetic Trojans: Social Contagions as Carriers of Adversarial Payloads in Agent Networks*
  - First Sentence: Autonomous large language model (LLM) agents increasingly interact in network environments where adversarial content can propagate between agents.
- **[2609.37567v1]** (2026-09-29) *Concealing LLM-Based Multi-Agent Topology via Phantom Structure Injection*
  - First Sentence: Driven by the rapid advancement of large language models (LLMs), LLM-based multi-agent systems (MAS) have emerged as a powerful paradigm for collaborative reasoning over complex tasks.
- **[2609.37094v1]** (2026-09-29) *LLM-Based Multi-Agent Systems over Wireless Networks: A Joint Agent--Network Design Perspective*
  - First Sentence: As large language models (LLMs) evolve from standalone models into collaborative agents embedded in physical systems, their reasoning and execution are increasingly distributed across wireless edge nodes.
- **[2609.36170v1]** (2026-09-28) *Assay: Claims That Decay With the Code. Content-Addressed Evidence Graphs for Accountable AI-Assisted Software Delivery*
  - First Sentence: AI coding agents fail in two coupled ways.
- **[2609.34619v1]** (2026-09-28) *LLMs for Executable Multi-Agent System Specification Generation*
  - First Sentence: MAS specifications express the effects of the actions of the agents and their environment, as well as other temporal phenomena, such as the intervals during which an agent may perform an action.
- **[2609.26667v1]** (2026-09-22) *MAGIC: Mixed-Granularity Agent Graphs via Incremental Construction with Dense-Reward Reinforcement Learning*
  - First Sentence: Collaboration topology shapes both the performance and execution cost of LLM-based multi-agent systems.
- **[2609.22723v1]** (2026-09-19) *ANI-Gamut: Benchmarking Agent Reliability across the Gamut of Agent-Network Interface Abstractions*
  - First Sentence: Large Language Model (LLM) agents are increasingly trusted to operate live networks: they read state, change configuration, and verify the result.
- **[2609.16599v1]** (2026-09-15) *Large Language Models in the Loop: A Stability- and Network-Aware Survey in Networked Control, Cyber-Physical, and Multi-Agent Systems*
  - First Sentence: Modern networked control systems (NCSs), cyber-physical systems (CPSs), and complex multi-agent network systems (CNSs) increasingly rely on large language models (LLMs) for high-level decision-making.
- **[2609.14896v1]** (2026-09-14) *Forty Shades of Blue: Quality-Diversity Alignment via Mode-Conditioned Reinforcement Learning*
  - First Sentence: A notable byproduct of LLM alignment training is mode collapse: the progressive loss of output diversity that narrows a model's expressivity at inference time.
- **[2609.14631v1]** (2026-09-13) *LLM Agent Capabilities Should Follow Task Intent and Context Source*
  - First Sentence: LLM agents take real actions, including executing code, modifying files, calling services, and delegating tasks, driven by context sources: user requests, tool results, documents, shell outputs, Skill and MCP instructions, memory.
- **[2609.10181v2]** (2026-09-09) *Can AI Agents Deliver Verifiable Network-Wide Outcomes Across Authority Boundaries?*
  - First Sentence: AI agents are increasingly involved in network automation, where they can initiate configuration changes through mediated operational interfaces and assess the resulting state.
- **[2609.04820v1]** (2026-09-04) *Cost-Aware Hierarchical Multi-Agent Ransomware Detection and Family Attribution*
  - First Sentence: Ransomware detection and family attribution require analysis of different modalities because it can use packing, obfuscation, process manipulation and runtime evasion techniques.
- **[2608.28502v1]** (2026-08-28) *Recognition Without Enforcement: Configuration-Dependent Failures in LLM Agent Instruction Arbitration and External Control*
  - First Sentence: LLM agents arbitrate among instructions from system prompts, users, memory, and tools, but this arbitration cannot be assumed to enforce trust boundaries.
- **[2608.25817v1]** (2026-08-26) *SkillShield: Prompt-Space Security Skills for LLM Coding Agents*
  - First Sentence: A coding agent edits files and executes shell commands with its developer's privileges, allowing malicious requests to translate directly into harmful actions or functional malware.
- **[2608.25152v1]** (2026-08-25) *Belief Cascades Drive Persuasion in LLM Agent Networks*
  - First Sentence: Multi-agent LLM systems increasingly debate answers, coordinate research, simulate users, and mediate information flows, making agent-to-agent persuasion a basic but undermeasured capability.
- **[2608.23611v1]** (2026-08-21) *REFINE: A Multi-Agent LLM Approach for Evidence-Guided Code Refactoring*
  - First Sentence: Large Language Models (LLMs) offer new opportunities for automated code refactoring.
- **[2608.13791v2]** (2026-08-13) *VLM- and LLM-Driven Multi-Agent System for PET Image Denoising*
  - First Sentence: Positron emission tomography (PET) imaging suffers from limited spatial resolution and low signal-to-noise ratio, which can compromise quantitative accuracy and lesion detectability.
- **[2608.12172v1]** (2026-08-12) *Rethinking Agent Security as a Networking Problem*
  - First Sentence: AI agents are rapidly becoming more capable and widely deployed, promising substantial gains in productivity and enabling new classes of applications.
- **[2608.11436v1]** (2026-08-11) *When Agents Talk: Honeytokens under Shared Memory*
  - First Sentence: During a 2026 cyber-capability evaluation, short-lived AI agents turned a shared package repository into persistent memory, passing exploit findings to later agents and rebuilding the channel after it was removed.
- **[2608.07440v3]** (2026-08-07) *Blast Radius*
  - First Sentence: Agentic coding faces growing problems of affordability and wasted tokens.
- **[2608.06830v1]** (2026-08-07) *When Coordination Becomes a Threat: Communication Attacks in LLM-Controlled Multi-Robot Systems*
  - First Sentence: Large Language Models (LLMs) are increasingly used as high-level planners in embodied multi-robot systems, enabling robots to interpret natural language instructions and coordinate executable actions.
- **[2608.01311v1]** (2026-08-02) *RH-RAG: Trustworthy Long-Form Generation for Privacy-Constrained Settings*
  - First Sentence: Generating long-form content from extensive internal reports remains challenging for organizations operating under strict privacy and security constraints, where proprietary cloud-based LLM APIs are often not viable.
- **[2607.25914v1]** (2026-07-28) *Toward Standardized Cross-Vendor Agent Tool Trust Management in Autonomous Networks*
  - First Sentence: Autonomous Network Levels 4-5 require AI agents to invoke tools across vendor boundaries without human oversight, yet existing management standards lack a standardized mechanism for cross-vendor trust visibility.
- **[2607.26120v1]** (2026-07-28) *Even More Deception: Objective Misalignment in Mixed-Motive LLM Multi-Agent Systems*
  - First Sentence: Large Language Models (LLMs)-powered multi-agent systems are increasingly deployed in mixed-motive environments, where agents operate under asymmetric information and strategic deception due to conflicting or hidden objectives.
- **[2607.22947v1]** (2026-07-24) *Let AI Agents Translate Networks, Not Reason About Them*
  - First Sentence: A formal model enables verifying reachability, localizing an outage, or anticipating the blast radius of a change.
- **[2607.22758v1]** (2026-07-23) *Spectral Dynamics of Semantic Drift in Clinical Multi-Agent Language Model Networks*
  - First Sentence: The integration of iterative LLMs within multi-agent diagnostic frameworks requires a rigorous quantitative reevaluation of underlying communication topologies.
- **[2607.20005v1]** (2026-07-22) *Safe Remediation as Risk-Constrained Intervention Decision in Microservice Systems*
  - First Sentence: In modern IT operations (IT-Ops), the cost of an incorrect repair often exceeds the cost of no action at all.
- **[2607.18847v1]** (2026-07-21) *Data Leakage Prevention in Agentic Applications via Preemptive Hardening*
  - First Sentence: Agentic systems integrate LLM driven planning with interfaces to external tools, making data leakage and tool misuse feasible via instruction/data boundary failures and prompt injection attacks.
- **[2607.16175v1]** (2026-07-17) *Evaluating Open-Weight LLMs for Generating Structured Threat Information for Autonomous Vehicle Vulnerabilities*
  - First Sentence: Connected and Autonomous Vehicles (CAVs) rely on interconnected software and hardware components, including sensors, Electronic Control Units, in-vehicle infotainment systems, and telematics units, where vulnerabilities can compromise assets, users, and vehicle operations.
- **[2607.15095v2]** (2026-07-16) *Digital Pantheon: Simulating and Auditing Coalition Formation with LLM Agents*
  - First Sentence: The formation of political coalitions is a complex negotiation driven by both concrete policy objectives and deep-seated ideological convictions.
- **[2607.09179v1]** (2026-07-10) *Malaika: Understanding Malware through Tri-Grounded Agentic Reasoning*
  - First Sentence: Recent LLM-based systems have shown promising capabilities for security-focused code analysis.
- **[2607.09101v1]** (2026-07-10) *Multi-Agent LLM Collaboration for Unit Test Generation via Human-Testing-Inspired Workflows*
  - First Sentence: Recently, the emergence of Large Language Models (LLMs) has spurred a surge of research into automated unit test generation, yielding impressive performance and reducing manual effort.
- **[2607.09744v1]** (2026-07-03) *A Theory of Least Autonomy in AI*
  - First Sentence: Least privilege, the principle that an identity should hold only the permissions strictly required for its task, has been a foundational primitive of access control for decades.
- **[2607.00555v1]** (2026-07-01) *Rise From The Ashes: LLM-based Static Analysis for Deep Learning Framework Bugs*
  - First Sentence: Deep learning (DL) frameworks are critical AI infrastructures that often hide bugs with serious security implications.
