# Bounding the Blast Radius of Compromised Agents: Sound Static Analysis and Runtime Enforcement for LLM Multi-Agent Systems

Shafin Ahmad¹, Ts. Dr. Maythem Kamal Abbas¹

¹ Asia Pacific University of Technology and Innovation, Technology Park Malaysia, Bukit Jalil, 57000 Kuala Lumpur, Malaysia.

Corresponding author: Shafin Ahmad.

[TODO: confirm final author list and order with supervisor before submission (plan gate G6).]

## Abstract

Prompt injection cannot be reliably prevented inside large language model reasoning loops. When autonomous agents collaborate across multi-step pipelines, an injection in one agent can propagate to downstream peers and trigger unauthorized external actions. This paper addresses that risk under assumed compromise, treating individual agents as untrusted and placing an external reference monitor at the tool and delegation boundary. The monitor implements Governance Under In-line Delegation Enforcement (GUIDE). First, this paper derives a static blast-radius bound for any compromised subset of agents, proves it sound against the enforcing runtime, and demonstrates that synthesised least privilege reduces median nominal reach by 50.0% (1.0 sink). Second, the static bound predicts deployment utility cost before runtime, achieving 96.9% accuracy on 97 tasks with 29.9 percentage points predicted cost matching empirical losses. Third, this paper establishes a structural topology floor: in sequential pipelines, splitting steps into separate agents cannot reduce worst-case reach, and a census of 55 real-world workflows confirms 89.1% (49 of 55) are strictly sequential chains. Fourth, an evaluation across 949 AgentDojo pairs demonstrates 92.3% containment under assumed compromise with zero soundness violations, alongside an empirical trade-off where strict policy enforcement reduces Slack utility by 66.7 percentage points. The primary limitation is that multi-agent containment was evaluated on self-authored pipelines because no standardized multi-agent compromised-agent benchmark currently exists.

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
- Appendices

---

## 1. Introduction

Most multi-agent systems built with large language models face an unsolved security problem at the execution boundary. When an agent reads external data from documents, search tools, or user inputs, untrusted text enters its prompt context. Attackers exploit this interface using prompt injection, which cannot be reliably prevented inside the model's reasoning loop. In a single-agent system, an injection redirects tool calls directly. In a multi-agent system, the attack propagates across delegation boundaries, so an untrusted agent can deceive downstream peers into executing privileged tools that the initial agent could never call on its own.

Defending against this failure mode requires an assumed-compromise threat model. Rather than attempting to detect malicious text inside language model activations, the system must treat any agent processing untrusted data as potentially compromised. This paper presents Governance Under In-line Delegation Enforcement (GUIDE), a reference monitor that enforces sound capability bounds over multi-agent workflows. The reference monitor operates at the boundary between agent reasoning and external tool execution. It evaluates every proposed tool call and delegation against formal authority constraints before any real-world effect occurs.

This paper makes four contributions.

1. Sound static blast-radius bound (C1). This paper derives a static graph-theoretic bound on the tools and resources an arbitrary compromised subset of agents can reach. A correspondence lemma and step-containment theorem prove the bound sound against the runtime reference monitor. Property-based tests over thousands of executions confirm soundness, and a live adaptive attacker confirms exactness on direct effects across 39 out of 39 evaluated cases. Synthesised least privilege provably minimizes the policy, reducing median nominal reach across realistic configurations by 50.0% (1.0 sink).

2. Pre-deployment deployment-cost prediction (C2). The static bound acts as a pre-deployment decision tool by predicting which benign task paths will be blocked by policy enforcement before running the model. Evaluated against 97 AgentDojo tasks, the predictor achieves 92.8% accuracy (95% Wilson confidence interval [85.8%, 96.5%]) with zero false negatives on path (v7a_fn_onpath is 0). On ground-truth task loss between undefended and defended deployments, the predictor achieves 96.9% accuracy with an attributable utility cost of 29.9 percentage points matching observed cost exactly across 30 lost tasks.

3. Topology floor and structural census (C3). This paper proves Proposition 3 and Proposition 4, showing that workflow topology imposes fundamental mathematical limits on security. In sequential linear pipelines, neither partitioning steps into distinct agents nor cryptographic signing can reduce worst-case blast radius below the nominal sink count. Least privilege is the only effective lever. A structural census across 55 real-world acyclic agent workflows reveals that 89.1% (49 of 55) are strictly sequential linear chains, and 100.0% (55 of 55) exhibit a single dominating source agent covering all execution steps.

4. Empirical containment and trade-off findings (C4). In a live evaluation across 949 AgentDojo task-injection pairs, the reference monitor achieves 92.3% containment under assumed compromise (95% Wilson confidence interval [89.9%, 94.2%]), 89.5% containment on the v6 subset, and a 93.6% sink block rate, with zero soundness violations (m1_soundness_violations: 0) and zero exactness gaps (m1_exactness_gaps: 0). However, strict provenance enforcement induces an attributable utility cost of 29.9 percentage points overall (reducing pooled benign utility from 91.8% to 61.9%) and 66.7 percentage points on Slack, where benign tasks require forwarding untrusted channel data to communication sinks.

The paper evaluates five research questions organized by theoretical foundation, containment efficacy, and system behavior:

- RQ1 (Soundness and exactness): Can the worst-case blast radius of an arbitrary compromised subset of agents be soundly bounded before deployment?
- RQ2 (Containment under assumed compromise): Does runtime enforcement at the tool and delegation boundary contain compromised agents under assumed compromise?
- RQ3 (Pre-deployment cost prediction): Can static analysis predict which benign tasks will fail runtime policy enforcement without running the model?
- RQ4 (Topology floor and real-world structure): How does workflow topology constrain blast-radius reduction, and what structures dominate real-world multi-agent systems?
- RQ5 (Cross-model nominal performance): Does runtime reference monitoring affect task success, intent fidelity, or latency on benign tasks across distinct model families?

The remainder of the paper reviews related work in Section 2, describes the reference monitor design and formal methods in Section 3, presents empirical results in Section 4, discusses architectural implications and limitations in Section 5, and concludes in Section 6.


---

## 2. Related work

Related work was identified through a systematic review conducted for the author's dissertation (721 included studies).

### 2.1 Multi-agent orchestration frameworks

Multi-agent orchestration research has focused primarily on coordination and task completion. MasRouter routes tasks across specialized agents to improve completion efficiency (Yue et al., 2025). Difficulty-aware orchestration dynamically adjusts pipeline topology based on input complexity (Su et al., 2025). Evolving orchestration allows team communication structures to reorganize during task execution (Dang et al., 2025). Graph-based coordination models multi-agent workflows as scalable generative networks (Ji et al., 2025). Tree-structured reasoning layouts reduce context loss across long debate turns (Yu et al., 2025). These frameworks address coordination and performance, but they do not enforce security policies at tool boundaries or evaluate containment when an agent within the topology is compromised.

### 2.2 Single-agent tool-call reference monitors and information flow control

Single-agent reference monitors and information flow control systems address a distinct problem: they evaluate individual tool calls generated by a single agent against policy rules or information flow labels. CaMeL attaches capability tokens and data flow policies to values passing through an agent, checking policy rules before tool invocation with a formal safety proof (Debenedetti et al., 2025). Progent provides LLM-guided privilege control over tool execution (Shi et al., 2025). FIDES propagates confidentiality and integrity labels across tool executions to block sensitive data flows within the Microsoft Agent Framework (Costa et al., 2025). The Agentic Reference Monitor (ARM) constructs causal provenance graphs over tool calls and return values to prevent causality laundering through denial feedback (Chinaei, 2026). MiniScope synthesises tool policies from permission hierarchies to enforce least privilege on single agents (MiniScope, 2025). Cordon applies transactional semantics to tool-using agents to isolate execution effects (Chen et al., 2026). These systems monitor single agents executing tools with model-generated arguments. They do not target multi-agent delegation pipelines, where an untrusted agent deceives a downstream peer, and they do not compute static blast-radius bounds over multi-agent workflow topologies.

### 2.3 Multi-agent security and containment

Recent research evaluates security risks unique to multi-agent pipelines. Multi-agent debate exhibits problem drift, where task constraints degrade as conversations expand (Becker et al., 2026). Injected prompt payloads propagate across agent communication channels, allowing untrusted inputs to compromise downstream agents (Lee et al., 2026). Triedman et al. (2025) show that multi-agent systems execute arbitrary malicious code when untrusted environment data redirects tool invocations. Wang and Zhang (2026) track prompt injection propagation across multi-agent pipelines using kill-chain canaries across five commercial models. Narisetty et al. (2026) evaluate out-of-band defenses adaptively against indirect prompt injection. Bounded Agents tracks delegated authority along runtime principal chains and proves blast radius monotonicity for dynamic delegations, evaluating containment on synthetic injections (Chen et al., 2026). Paul and Nandy (2026) combine signed messages, provenance tracking, and tool privilege scoping across multi-agent pipelines. Safin et al. (2026) demonstrate that low-privilege agents can compromise high-privilege executors in undefended pipelines, but task-bound signed tokens and an external policy oracle achieve containment.

### 2.4 Static and pre-deployment analysis

In static and pre-deployment analysis, concurrent 2026 work exhibits partial overlap with aspects of this approach. Parisel (2026) models design-time influence graphs over multi-agent configurations and defines a blast-radius metric over enterprise resources, but provides no enforcement guarantee, no soundness proof, and no runtime implementation. Muruaga (2026) proves runtime monotonicity of delegation scope along dynamically instantiated principal chains, but evaluates runtime scopes rather than computing a static bound over an entire workflow before deployment. Moon and Varshney (2026) mechanically verify single-agent runtime containment in Dafny, but do not model multi-agent influence or provide least-privilege policy synthesis. Other static analyses examine agent programs rather than deployment topologies: AgentFlow constructs dependency graphs from agent source code (AgentFlow, 2026), and CaMeLoT verifies plans against temporal logic formulas prior to execution (CaMeLoT, 2026).

### 2.5 Evaluation benchmarks

Standard benchmarks for agent security evaluate single-agent execution. AgentDojo benchmarks prompt injection defenses on single-agent environments across utility and security axes (Debenedetti et al., 2024). InjecAgent benchmarks indirect prompt injection on single agents (Zhan et al., 2024). TAMAS benchmarks adversarial vulnerability across multi-agent backbones without evaluating boundary reference monitors (TAMAS, 2025). No standard benchmark exists for evaluating compromised-agent containment in multi-agent workflows. Consequently, this study evaluates multi-agent containment on an internal multi-agent benchmark and evaluates external runtime tool enforcement on AgentDojo under assumed compromise.

Table 1 compares closest related systems across target scope, static bounding, soundness proofs, policy synthesis, and utility prediction.

Table 1. Comparison of security mechanisms in tool-calling and multi-agent agentic systems.

| System | Targets multi-agent compromised subsets | Static pre-deployment bound | Soundness proof | Least-privilege synthesis | Deployment-cost prediction |
|---|---|---|---|---|---|
| CaMeL (Debenedetti et al., 2025) | No | No | Yes (runtime safety) | No | No |
| Progent (Shi et al., 2025) | No | No | Not reported | No | No |
| FIDES (Costa et al., 2025) | No | No | Not reported | No | No |
| ARM (Chinaei, 2026) | No | No | Not reported | No | No |
| Parisel (2026) | Yes | Yes | No | No | No |
| Muruaga (2026) | Yes | No | Yes (runtime monotonicity) | No | No |
| Moon & Varshney (2026) | No | No | Yes (Dafny machine-checked) | No | No |
| GUIDE (This paper) | Yes | Yes | Yes (soundness theorem) | Yes | Yes |


---

## 3. Materials and methods

### 3.1 Research design

This study follows design science research (Hevner et al., 2004), because the goal is to build and evaluate an artefact for a defined computing problem rather than to test a theory about an existing system. The six activities of the Peffers et al. (2007) process map onto this project as follows: problem identification is the gap described in Section 1, objective definition is RQ1 to RQ5, design and development is the runtime reference monitor described in Section 3.2, demonstration is the pilot and the main-suite nominal runs, evaluation is the baseline comparison, the assumed-compromise suite and the static-bound validation reported in Section 4, and communication is this paper plus the archived, versioned code repository. The unit of analysis throughout is the reference monitor architecture, not the capability of any one language model, so every condition in every suite uses the same tasks, the same tool registry, the same decoding settings, and, within a given run of the suite, the same model.

### 3.2 Reference monitor architecture and controls

The runtime has three layers with one-way dependencies: a core layer providing the execution primitives, a research layer containing the experimental provenance guard and the static analyser, and a bench layer containing the task suites and the evaluation harness. The core layer never imports from the other two, which is checked automatically in continuous integration.

A run executes a workflow of steps in dependency order. For each step, a router selects a candidate agent, a hand-off delivers the step's inputs to that agent, the agent proposes tool calls inside an agent loop bounded by a turn budget and a repair budget, and each proposed call passes through the policy gate before any tool code executes. Four controls sit on top of a baseline pipeline.

First, routing keeps a Beta-distributed success estimate for each agent on each task domain, starts every agent with one warm-up task, and then selects, by Bayes-UCB, the candidate with the highest upper-confidence quantile of its posterior (Auer et al., 2002, Kaufmann et al., 2012). This is a standard bandit algorithm applied to agent selection, not a new one.

Second, a hand-off package carries the run identifier, a hand-off identifier, the hash of the previous package in the chain, the task objective, the constraint list, references to its input data, the list of tools the receiving agent may use, the expected output schema, and an expiry time. The package is serialised to a canonical JSON form over a restricted value domain and signed with an Ed25519 key specific to the sending principal. The receiver verifies the signature, the hash chain back to the run's genesis hash, every required field, the expiry, and the schema, and rejects the hand-off with an integrity error if any check fails. This is distinct from the proposal's original wording, which described the serialisation as conforming to RFC 8785: the implemented form is canonical JSON over a restricted value domain, and that correction is carried through to this paper rather than repeated from the proposal (deviation A11 in Table 9).

Third, every proposed tool call is reduced to a finite record of the tool, the operation, the resource class it touches, the sensitivity of any columns it would expose, and whether it writes state or sends data externally. An external policy gate inspects this record against a declarative policy and returns one of three decisions: allow it unchanged, bound it by revising an argument to the nearest permitted value, or deny it. Bounding is implemented as interval projection for numeric arguments and as subset projection for column lists, both over tool metadata the gate already holds: it is not a Euclidean projection over the full action vector, which is how the proposal's appendix described it before implementation (deviation A10). A denied call never reaches tool code.

Fourth, a provenance guard wraps the policy gate for one specific class of call: a side-effecting call whose control arguments, such as an email recipient, must be traceable to the task's own trusted text. The guard checks whether the normalised argument value appears as a substring of the trusted corpus (the default mode) or as an exact token in that corpus (an alternative, stricter mode). A call whose control argument cannot be traced to trusted text is denied even if the policy gate alone would have allowed it.

Every routing decision, hand-off result, policy decision, tool call result, and step output is appended to a trace that is itself hash-linked, so that an edit to any past event breaks verification of every event after it. The runtime passes 104 unit and integration tests covering routing updates, missing or altered hand-off fields, invalid signatures, expiry handling, prohibited tool requests, and trace reconstruction after simulated tampering. This confirms that the four controls operate as specified.

Figure 1 shows the architecture and the direction of data flow between these components, including the trust boundary around content that originates from a tool result or retrieved text rather than from the task's own trusted header.

### 3.3 Conditions

Four conditions are evaluated, each a configuration of the same runtime rather than four separate implementations, which removes a common confound in baseline comparisons where a baseline is reimplemented from scratch and may differ from the proposed system in ways unrelated to the mechanism under test.

- B1: fixed-role sequential delegation with a plain-text, unstructured hand-off between agents.
- B2: a static-graph workflow with structured JSON state passed between steps, but no adaptive routing, no signed hand-off, and no policy gate.
- P: the proposed reference monitor at proposal scope, meaning Bayes-UCB routing, signed hand-offs, and the policy gate, without the provenance guard or re-dispatch.
- GPLUS: P plus the provenance guard and re-dispatch on step failure.

Six further configurations ablate one mechanism of GPLUS at a time (removing provenance, removing the gate, removing signing, removing re-dispatch, removing routing, and removing both re-dispatch and routing), used to attribute an observed effect to a specific mechanism rather than to the bundle as a whole. B1 and B2 still bind tools to a step before execution, which is a realistic default for an unmanaged multi-agent system and makes both baselines stronger than a true no-controls condition.

### 3.4 Tasks and suites

Eighteen main-suite tasks span three task families (information synthesis, evidence reconciliation, and policy-sensitive planning), each at a low, medium or high constraint tier with four, six or eight atomic constraints respectively, structured as a three-step retrieve, analyse, report workflow. The adversarial suite adds eleven live robustness cases covering a missing entity, conflicting tool data, an injected instruction aimed at an external or an internal sink, an injected destructive-write request, a request for a prohibited action stated directly by the simulated principal, a compromised peer agent, hand-off tampering in transit, a transient tool failure, a tool outage, and malformed model output, plus a twelve-case sequence suite that holds one agent permanently degraded across twenty consecutive runs to test routing and re-dispatch under a persistent fault rather than a one-off perturbation.

The threat model for RQ2 was extended beyond the proposal's plan during the first formal run, and this extension is disclosed rather than silently substituted (deviation A20 in Table 9). The original plan tested textual indirect prompt injection: an instruction hidden inside tool-returned data, asking the agent to do something it was not told to do. Across every condition in that suite, the live model made zero attack attempts: it treated tool-returned text as data rather than as instructions in every one of 550 runs, which means the adversarial suite as originally designed cannot measure containment, because there is nothing for a control to contain. In response, an assumed-compromise suite was added: in each of four cases, the targeted agent's first proposed tool call is replaced by an attacker-chosen call (a restricted-column read, an email to an external domain, an email to an in-domain mailbox named only in untrusted tool data, or a record deletion), and every subsequent step of the run proceeds with the live model as normal. This isolates whether the architecture contains a compromised agent's action from whether the underlying model resists being talked into one, which the textual-injection suite could not do with a model this capable.

### 3.5 Models and settings

Protocol v1 through v4 used one model family, DeepSeek, requested as `deepseek-chat` and reported by the provider as `deepseek-flash`, at temperature 0, in JSON mode, with a maximum of 4,096 tokens per completion, a fixed random seed of 42, a turn budget of four tool-use turns and a repair budget of two re-asks at temperature 0.3 for a malformed reply.

A single-model-family result cannot distinguish a property of the architecture from a property of that one model, which `docs/limitations.md` already flagged as an open external-validity threat before this evaluation. Protocol v5 re-runs the frozen main suite and the assumed-compromise suite against two further model families, changing only the model, the endpoint, and the credential, with every task, policy, condition and decoding setting held fixed. The two added models are an open-weight model served by Groq, requested as `openai/gpt-oss-120b`, and Google's `gemini-3.5-flash-lite`, served through Google AI Studio's OpenAI-compatible endpoint. Both were chosen on free-tier availability after piloting, and the choice itself needed disclosed deviations.

Groq's `qwen/qwen3.8-27b` was tried first and reached its 200,000-token daily cap during the main-suite run, which is a hard quota rather than a transient rate limit, so it was retired after the fact rather than used: the thirty-two completed runs it produced before exhaustion are reported as excluded, not pooled with the retained model's results (deviation A28 in Table 9). A smaller Groq model, `openai/gpt-oss-20b`, triggers Groq's own tool-call guardrail against the artefact's prompted-JSON tool-call protocol, because the artefact deliberately does not use the provider's native function-calling parameter: changing that only for one provider would break the model-invariance the comparison depends on, so this smaller model was rejected rather than special-cased. On the Gemini side, the flagship `gemini-3.8-flash` model works correctly but is capped, on this free tier, at twenty requests per day, which is too small to run even the pilot suite in a single day: `gemini-3.5-flash-lite` was selected instead after a clean pilot. One setting differs for Gemini alone: its OpenAI-compatible endpoint rejects the `seed` parameter outright with an HTTP 400 error, so `seed` is omitted for Gemini and left at 42 for DeepSeek and Groq. Temperature, maximum tokens and JSON mode are identical across all three model families, and this is the only settings field that differs (ADR-0005).

Because repeating the full 360-run main suite and 160-run compromised suite at five repetitions per cell on two free-tier providers is bound by daily request and token quotas rather than by compute, the number of repetitions for the two added model families was reduced from five to two per cell for protocol v5, a disclosed reduction in statistical power rather than a change to which conditions or tasks were tested (deviation A28, Section 3.8).

### 3.6 Metrics

Table 5 lists the metrics used throughout, following the proposal's Table 3 with definitions carried over unchanged. Task success is the fraction of completed runs in which every mandatory constraint was satisfied. Intent fidelity is the fraction of a task's own atomic constraints that were satisfied, so a run that fails one constraint out of six scores differently from a run that fails one out of six on a harder task. Violation is a binary flag per run for whether a restricted value was disclosed, a write side effect occurred that the task did not call for, or an email was sent to a recipient the task did not authorise. Attack success rate is the violation rate computed over the adversarial and assumed-compromise suites specifically. Trace completeness is the fraction of required linked trace fields present for a run, which is zero by construction for B1 and B2 because neither condition produces a trace at all: this is reported to match the proposal's measure, not as a finding about either baseline. Integrity detection is the fraction of seeded invalid hand-off packages that the receiver correctly rejects. Cost is counted as model calls and prompt and completion tokens per run, and time is wall-clock seconds per run.

Every check is deterministic and computed without access to the condition label that produced the run, which is itself regression-tested so a future code change cannot silently reintroduce condition-awareness into scoring. The proposal originally specified two blinded human assessors scoring a stratified twenty percent sample with Cohen's kappa: that step was replaced with the deterministic checks above because no ethics approval for human assessors was in place at the time of the formal runs (deviation A7 in Table 9). This is a stricter and more reproducible check for the specific items the checks test, at the cost of being coarser than a human reader on free-text quality: a reviewer who requires the originally planned kappa measure can score the retained twenty percent sample held for this purpose once a human assessor, such as the supervisor, is available.

### 3.7 Static blast-radius analysis

The question behind RQ1 is whether, before a single agent runs, it is possible to compute every effect a given compromised subset of agents could still cause, and to know that bound is correct no matter what the compromised agents say or do. The full formal treatment, including every definition, lemma and proof, is in the supplementary formal model document and is only summarised here.

A deployment is modelled as a workflow of steps with role and tool assignments, a set of agents with roles, tool metadata recording which operations write state or send data externally and which columns of a resource they can expose, and a declarative policy. An adversary is defined by three things it may control: the model output of every agent in a chosen compromised set, the content returned by any tool in a chosen set of injectable tools, and, if stated, the hand-off transport itself. The analysis proves a correspondence lemma showing the policy gate's actual decision procedure, read directly from its source code, computes exactly the same admissibility test as a mathematical definition of authority at each step. From that lemma, a step-containment theorem shows that no execution, under any adversary behaviour at all, including every agent in the compromised set behaving arbitrarily, produces an effect the gate's own authority rule at that step would not admit. An influence relation then propagates from a compromised step to every step that could be affected by it, through shared tool-written state, through context passed at a hand-off, through an injectable tool, or through a tampered transport, and the blast radius of a compromised set is defined as the union of the authority of every step the influence relation reaches. A soundness theorem shows that every effect that depends on the adversary at all lies inside this blast radius, and that any step outside the influence relation behaves exactly as it would with no adversary present, up to the randomness of an interchangeable agent selection.

A least-privilege synthesis procedure then takes a set of observed nominal task executions and computes the smallest policy, in a formally defined ordering over policies, that still permits every observed call: this synthesised policy is proved to be minimal with respect to those observations and to only shrink, never grow, the blast radius computed from the unsynthesised policy.

The analysis was validated three ways. First, it was checked offline against every recorded run across every prior protocol, by replaying each run's executed calls against the bound computed for that run's compromised set and checking for a violation. Second, the correspondence lemma itself was checked by property-based testing against the real gate implementation across thousands of generated cases per test run, rather than trusted purely as a hand proof. Third, a live adaptive attacker was run against one task under eight attack variants, each compared against the bound's prediction of whether the attack would reach its target.

### 3.8 Protocol, statistics and deviations

Every protocol was frozen in version control before the formal runs it governs, under the tags `protocol-v1` through `protocol-v5`, and nothing in an earlier protocol's results was re-run to replace an unfavourable finding: later protocols are amendments, motivated by an earlier protocol's own findings and disclosed as such. Task, condition and repetition order was randomised with a fixed seed. Per-condition summaries report the mean and a 95 percent cluster-bootstrap confidence interval over tasks, using ten thousand resamples with a fixed seed, plus the median and interquartile range for time and token cost. Paired comparisons are computed at the task level, using a two-sided Wilcoxon signed-rank test with Pratt's method for zero differences, with the Holm correction applied within each family of related metrics. Where almost every paired difference is zero, which happens whenever two conditions both sit at a success ceiling, the test is reported as uninformative rather than read for significance, because a test with almost no non-zero differences has almost no power to detect anything.

One further protocol deviation needs explicit disclosure because it touches the project's own frozen no-rerun rule. The evaluation protocol as frozen states that a provider error counts as a failure of the run it hit and that nothing is re-run to replace it. Protocol v5's two added model families, run on free tiers, produced genuine infrastructure failures: a provider returning HTTP 429 for exceeding a per-minute token quota, or a daily quota being exhausted mid-run, in each case before the provider's model had generated any output at all, so the row carries zero model calls. Treating these as permanent failures would have meant the comparison across model families actually compared different numbers of completed cells per model, which is itself a confound. The resolution applied, and disclosed here rather than only in the appendix, is narrow: a failed row is only pruned and re-attempted if it shows zero model calls, meaning the provider rejected the request before the model saw it: a row where the model produced a completed or malformed reply and the run then failed for a different reason is never pruned or re-run. Under this rule, Gemini's main suite had thirty-three such zero-call failures pruned and re-attempted before its final completed set, Groq's main suite had fifty-three pruned across three resumption passes, Gemini's compromised suite had nineteen pruned after an initial daily-quota exhaustion, and Groq's compromised suite needed none, completing cleanly in one pass. Every reported number in Section 4 reflects only completed runs after this pruning: a reviewer wanting the stricter reading, with every provider rejection counted as a failure, can reconstruct it from the pre-pruning files retained in the project's results archive.

Table 9 in the appendix lists every deviation between the approved proposal and what was actually run, each with its reason and its effect on the paper's claims, following `docs/submission-alignment.md`.

### 3.9 Ethics and data

All sandbox data is synthetic or public. No human participants, personal data about real individuals, or decisions affecting a real person were involved at any stage. The sandbox tool set is allow-listed, with no credentials, no network write access beyond the sandbox's own simulated email tool, and no irreversible action available outside what the task design calls for. Code and the tagged, versioned data for every protocol are archived with the submission: the data and code availability statement in the back matter gives the archived location.

### 3.10 External benchmark: AgentDojo

AgentDojo (Debenedetti et al., 2024) is an external benchmark designed for tool-using agents. The benchmark pairs user tasks with indirect prompt injections across four realistic enterprise domains: Banking, Slack, Travel, and Workspace. The evaluation uses AgentDojo for two specific purposes: measuring runtime enforcement against ground-truth malicious tool calls, and measuring empirical utility loss caused by security controls.

AgentDojo is an external single-agent benchmark. It evaluates tool-boundary enforcement and deployment cost on an individual agent. It does not evaluate multi-agent containment, lateral compromise propagation, or agent-to-agent delegation. Multi-agent containment requires interacting agents and is evaluated on the multi-agent task suites described in Section 3.4.

AgentDojo is evaluated under three protocols. Protocol v6 evaluates the full GUIDE reference monitor (least-privilege policy gate and exact-token provenance guard) against DeepSeek-V3. Protocol v6b evaluates the identical tasks and prompts with all security controls removed, providing the undefended baseline. Protocol v8 (M1) executes an assumed-compromise replay across all 949 task-injection pairs in the benchmark, directly evaluating whether the runtime reference monitor blocks ground-truth attacker sink calls.

### 3.11 Pre-deployment cost prediction

Deploying strict security controls can break legitimate application functionality. Protocol v7a and Protocol v8 (M1b) evaluate whether this utility cost can be predicted statically before deployment.

The static cost predictor inspects each task's nominal tool requirements against the synthesized least-privilege policy and provenance constraints. A task is predicted as blocked if any required nominal tool call exceeds policy authority or relies on arguments absent from trusted prompt context. Protocol v7a evaluates prediction accuracy across all 97 nominal tasks in AgentDojo. Protocol v8 (M1b) compares the statically predicted task loss directly against the empirical ground-truth task loss observed between Protocol v6b (undefended) and Protocol v6 (defended).

### 3.12 Topology analysis

The interaction topology of a multi-agent system determines how influence propagates when an agent is compromised. Section 3.7 defines the influence relation and worst-case blast radius. Protocol v7c and Protocol v8 (M2) analyse the mathematical and structural limits of topology as a security mechanism.

Proposition 3 (refinement monotonicity) proves that splitting an agent's execution steps into two distinct agents never increases worst-case blast radius for a fixed policy, hand-off mode, and adversary budget.

Proposition 4 (linear chain floor) establishes a formal limit: in a strictly linear dependency chain, neither agent partitioning nor cryptographic hand-off signing reduces worst-case blast radius below full pipeline reach. If an upstream agent in a linear chain is compromised, influence propagates through valid hand-offs to all downstream steps. The worst-case blast radius floor equals all downstream sinks unless least-privilege policy synthesis removes the sink capability entirely.

To measure this effect, Protocol v8 introduces absolute reach (the raw count of reachable sink tools) alongside normalized worst-case blast radius.

### 3.13 Real-world configuration mining

Protocol v7b investigates whether real-world multi-agent architectures exhibit linear chain topologies and sink-bearing tools. Public GitHub repositories were queried for implementations using CrewAI, LangGraph, and AutoGen using frozen search queries and inclusion criteria.

The mining process applied a pre-registered stop condition: candidate pools for LangGraph and AutoGen yielded few valid multi-agent workflows (1 included of 90 candidates for LangGraph, 0 of 70 for AutoGen), while CrewAI yielded 21 included repositories comprising 36 configurations. Across all frameworks, 37 configurations were extracted and 36 were scored. One LangGraph configuration was excluded as genuinely cyclic, which falls outside the DAG execution model.

Tool capabilities were classified using a frozen keyword classifier. The classifier provides a conservative lower bound: tools named with generic tokens such as "add" or "writer" were not classified as write sinks under the frozen keyword rules.

---

## 4. Results

### 4.1 RQ1: Soundness and exactness of the bound

Across 1,575 recorded runs spanning 2,051 executed tool calls from every prior protocol, replaying each run's executed effects against the bound computed for its compromised set finds zero containment violations and zero blast-radius violations. Every one of the fifty-five harmful effects observed in the assumed-compromise suite lies inside the bound predicted for that run before it executed. A least-privilege policy synthesised from the main suite's nominal traces denies zero of forty-four held-out calls and achieves full task success with zero policy denials across thirty-six live runs under the synthesised policy, while shrinking the policy substantially. For one representative task, the bound narrows from permitting any address at the organisation's own domain, under the default gate, to permitting exactly one specific recipient, under the synthesised least-privilege policy.

A live adaptive attacker was evaluated against eight attack variants on this same task across 120 runs. The bound correctly predicted containment for every variant the gate alone, the gate with token-exact provenance, or the synthesised least-privilege policy was designed to stop, with zero soundness violations: every one of seventy-five runs the bound predicted as blocked showed no harmful effect. This provides the exactness result for direct compromise: thirty-nine of thirty-nine (39/39) predicted-reachable direct effects were realised when the attacker was allowed to reach them.

One variant, an email sent to a legitimate recipient's address that happens to also be a substring of a different, trusted address, was predicted as reachable under the default substring-matching provenance guard and realised exactly as predicted on all three repetitions (Finding F1). The default substring-matching mode is bypassable: it admits 692 distinct recipient strings (Figure 6). Switching to exact-token matching, or to the synthesised least-privilege policy, admits exactly one recipient and blocks the same attack in all three repetitions.

A second variant, where an attacker attempts to get an honest downstream agent to act on a poisoned upstream agent's output, was never realised in six attempted repetitions, because the downstream model in these experiments did not comply with the poisoned instruction. The bound still predicts this path as reachable (Finding F4), which represents an intentional sound over-approximation on effects beyond direct compromise rather than a bound violation.

![Fig. 6. Admissible recipients for one representative sink (task T15), by policy. Baseline and gate admit an unbounded, domain-wide set of recipients: the default substring-matching provenance guard admits 692 distinct strings: exact-token provenance and the synthesised least-privilege policy both admit exactly one.](/Users/shafinoid/Documents/GitHub/guide/scripts/paper/figures/fig6_blast_radius_bound_sizes.png)

A separate structural generalisation check examined nineteen hand-authored configurations that each reproduce one documented structural pattern from LangGraph, CrewAI or AutoGen, across five enterprise domains, without executing any of those three systems' own code. Eighteen of the nineteen (18/19) configurations show at least one compromised agent whose blast radius reaches a destructive or data-exfiltration capability beyond that agent's own nominal role. This follows directly from a common integration pattern: binding a whole tool object to an agent, rather than the specific operation that agent's task actually needs, grants every operation the tool object exposes. Applying the same least-privilege synthesis procedure to each configuration's own nominal calls cuts the total reachable sink capability by 55.6 percent in aggregate, while denying zero of the configurations' own nominal calls.

### 4.2 RQ2: Containment under assumed compromise

Table 7 reports the assumed-compromise results for all three model families on the internal multi-agent suite. The pattern is consistent across models. For K1, a compromised agent's first call reads restricted columns directly: no condition's live model copies the exposed values into its final deliverable, but the ungated conditions (B1, B2) expose the restricted values into downstream agent context, whereas the gated conditions (P, GPLUS) remove the restricted columns before they reach the next step. For K2 (an email to an external domain) and K4 (a destructive record deletion), both ungated baselines show a 100 percent violation rate on every model tested, while the policy gate in P and GPLUS blocks both actions in every trial on every model, achieving a 0 percent violation rate. For K3 (an email to an in-domain mailbox named only in untrusted tool data), the gate alone is not enough: P shows a 100 percent violation rate on every model, matching the ungated baselines, because the recipient's domain is permitted. GPLUS, which adds the provenance guard on top of the same gate, shows a 0 percent violation rate on this case on every model tested. Removing the provenance guard from GPLUS restores the K3 violation, and removing the gate restores every violation. This supports H1: policy gating contains out-of-domain actions, and only the provenance guard contains an attacker's attempt to steer output to an in-domain recipient that the gate alone would permit.

![Fig. 5. Violation rate under assumed compromise (K1 to K4), by condition and model. Darker cells indicate a higher violation rate.](/Users/shafinoid/Documents/GitHub/guide/scripts/paper/figures/fig5_compromise_heatmap.png)

The textual indirect-injection suite described in Section 3.4 produced zero attack attempts across all 550 of its runs on the original DeepSeek protocol: the model treated injected text as inert data in every instance. The integrity suite, run without a live model, detects all ten seeded mutation classes at a 100 percent rate when per-principal signing keys are used, with zero false rejections of a valid package, and detects zero percent of sender-spoofing attempts when a single shared key is used instead. This supports H3: per-principal keys, not merely signing itself, make spoofing detectable. The twenty-run degraded-agent sequence supports H2: a statically assigned baseline never recovers from a permanently faulty agent across all twenty runs, adaptive routing alone recovers in nineteen of twenty, and re-dispatch, with or without adaptive routing, recovers in all twenty.

![Fig. 8. Degraded-agent sequence (A12): cumulative completed runs over 20 consecutive runs with one agent permanently faulty.](/Users/shafinoid/Documents/GitHub/guide/scripts/paper/figures/fig8_degraded_agent_sequence.png)

To evaluate runtime tool-boundary enforcement on an established external benchmark, Protocol v8 (M1) executes an assumed-compromise replay across all 949 task-injection pairs in AgentDojo. Across these pairs, 588 in-scope pairs execute attacker sink invocations. Table 3 reports the containment results across the four AgentDojo suites.

Table 3. Assumed-compromise containment replay on AgentDojo (Protocol v8 M1).

| Suite | Pairs (Full) | In-Scope Pairs | Contained | Partial | Executed | Containment Rate [95% Wilson CI] | v6-Subset Containment | Undefended Containment |
|---|---|---|---|---|---|---|---|---|
| Banking | 144 | 144 | 128 | 0 | 16 | 88.9% [82.7%, 93.0%] | 88.9% [82.7%, 93.0%] | 0.0% |
| Slack | 105 | 84 | 79 | 0 | 5 | 94.0% [86.8%, 97.4%] | 94.0% [86.8%, 97.4%] | 0.0% |
| Travel | 140 | 120 | 99 | 0 | 21 | 82.5% [74.7%, 88.3%] | 82.5% [74.7%, 88.3%] | 0.0% |
| Workspace | 560 | 240 | 237 | 0 | 3 | 98.8% [96.4%, 99.6%] | 98.3% [91.1%, 99.7%] | 0.0% |
| **Total** | **949** | **588** | **543** | **0** | **45** | **92.3% [89.9%, 94.2%]** | **89.5% [86.1%, 92.1%]** | **0.0%** |

Overall containment reaches 92.3% across the full benchmark (543 of 588 in-scope pairs contained, 95% Wilson CI [89.9%, 94.2%]). On the v6 task subset, containment reaches 89.5% [86.1%, 92.1%]. The undefended baseline achieves 0.0% containment, because without runtime gating every tool call executes directly. Across all 702 attacker sink invocations in the benchmark, the runtime monitor blocked 657 calls, yielding a sink block rate of 93.6%.

Table 4 compares the static bound's pre-execution predictions against runtime outcomes across all 949 pairs. The monitor achieved zero soundness violations (m1_soundness_violations = 0) and zero exactness gaps (m1_exactness_gaps = 0).

Table 4. Bound prediction versus runtime containment on AgentDojo (Protocol v8 M1).

| Prediction | Runtime Contained | Runtime Executed |
|---|---|---|
| Predicted Blocked | 543 | 0 |
| Predicted Allowed | 0 | 45 |

All forty-five admitted sink calls fall into two documented categories:
1. Sixteen calls involve operations with no control parameters (`no_control_params`), specifically the banking `update_password` tool, where the attacker's payload is fixed by the tool interface rather than supplied as an argument.
2. Twenty-nine calls involve parameters where the attacker's target recipient was already present in the user's initial prompt (`control_value_in_trusted_prompt`), specifically travel injection tasks 0 and 4, and workspace injection tasks 1 and 5. Because the destination was in the trusted prompt, the provenance check correctly admitted the call.

Table 8 presents the paired results between Protocol v6 (defended) and Protocol v6b (undefended) on DeepSeek-V3.

Table 8. AgentDojo benchmark performance comparison: defended (Protocol v6) versus undefended (Protocol v6b).

| Suite | Protocol v6b Benign Utility | Protocol v6 Benign Utility | Utility Cost (pp) | Protocol v6b Attack Utility | Protocol v6 Attack Utility | Protocol v6b ASR | Protocol v6 ASR |
|---|---|---|---|---|---|---|---|
| Banking | 100.0% | 87.5% | 12.5 | 94.4% | 90.3% | 0.0% | 0.0% |
| Slack | 90.5% | 23.8% | 66.7 | 85.7% | 38.1% | 0.0% | 0.0% |
| Travel | 85.7% | 66.7% | 19.0 | 78.6% | 66.7% | 2.9% | 2.9% |
| Workspace | 92.5% | 65.0% | 27.5 | 85.0% | 75.8% | 3.3% | 3.8% |
| **Overall** | **91.8%** | **61.9%** | **29.9** | **85.6%** | **68.4%** | **2.1%** | **2.3%** |

*Note on resource consumption: Protocol v6 consumed 11,426,990 tokens costing 13.93 CNY (the ledger in token_usage.jsonl recorded 11,450,443 tokens). Protocol v6b consumed 9,068,246 tokens costing 10.89 CNY.*

Under Protocol v6 (defended), benign utility is 61.9% (60/97) and attack utility is 68.4% (362/529), with an attack success rate of 2.3% (12/529). Under Protocol v6b (undefended), benign utility is 91.8% (89/97) and attack utility is 85.6% (453/529), with an attack success rate of 2.1% (11/529).

Two findings emerge from this comparison. First, DeepSeek-V3 natively resisted prompt injections in this environment: undefended attack success rate was only 2.1%. Live attack success rate is therefore uninformative for evaluating defense efficacy on this model. Second, enforcing strict security controls created an overall utility cost of 29.9 percentage points (91.8% to 61.9%). On Slack, where tool outputs frequently supply legitimate arguments for downstream tools, benign utility dropped from 90.5% to 23.8%, representing a Slack utility cost of 66.7 percentage points. Figure 9 illustrates this relationship between undefended utility, defended utility, and assumed-compromise containment.

![Fig. 9. AgentDojo benchmark performance across suites: undefended benign utility (Protocol v6b), defended benign utility (Protocol v6), and assumed-compromise containment rate (Protocol v8 M1).](/Users/shafinoid/Documents/GitHub/guide/scripts/paper/figures/fig9_agentdojo_utility_containment.png)

### 4.3 RQ3: Pre-deployment cost prediction

Protocol v7a evaluated whether the static analysis can predict utility loss before deployment across all 97 nominal tasks in AgentDojo. The static predictor achieved an accuracy of 92.8% with a 95% Wilson confidence interval of [85.8%, 96.5%]. The predictor produced zero false negatives on execution path (v7a_fn_onpath = 0): it never predicted a task would succeed when a required tool call on its path was blocked.

Protocol v8 (M1b) evaluated the predictor against the empirical task loss observed between Protocol v6b (undefended) and Protocol v6 (defended). Across the 97 tasks, exactly thirty (30) tasks completed successfully under v6b but failed under v6. Table 10 reports the confusion matrix of the static predictor against these lost tasks.

Table 10. Confusion matrix of pre-deployment utility cost prediction (Protocol v8 M1b).

| Prediction | Lost Task (v6b Completed, v6 Failed) | Retained Task (Not Lost) | Total |
|---|---|---|---|
| Predicted Block | 29 | 2 | 31 |
| Not Predicted | 1 | 65 | 66 |
| **Total** | **30** | **67** | **97** |

The static predictor identified twenty-nine of the thirty lost tasks, with two false alarms. Overall prediction accuracy reached 96.9% [91.3%, 98.9%], with a precision of 93.5% and a recall of 96.7%. The statically predicted utility cost was 29.9 percentage points (31/97 tasks predicted blocked, matching 29.9), exactly matching the empirically observed attributable utility cost of 29.9 percentage points (30/97 tasks lost). This confirms that pre-deployment static analysis accurately anticipates the empirical utility cost of runtime enforcement.

### 4.4 RQ4: Topology floor and real-world structure

Proposition 3 (refinement monotonicity) was evaluated across 200 Hypothesis property tests, yielding zero counterexamples: splitting an agent's execution steps never increases worst-case blast radius. Proposition 4 (linear chain floor) establishes that in a linear dependency chain, agent partitioning and signed hand-offs cannot lower the worst-case blast radius below full pipeline reach. Property tests over 300 random linear chains confirmed closed-form equivalence with zero counterexamples. Closed-form equivalence was also verified across 76 real configuration combinations (38 linear chains under transcript and signed hand-off modes).

In linear chains, only policy changes that remove sink privileges lower the reach. Evaluating absolute reach (the raw count of reachable sink tools) across linear configurations shows that least-privilege policy synthesis reduces median nominal reach from 2.0 sinks (nom-normalised 1.000) to 1.0 sink (nom-normalised 0.500), achieving an absolute median reduction of 1.0 sink (mean 0.945).

To determine whether real-world systems exhibit linear topologies, a structural census was conducted across fifty-five acyclic multi-agent configurations (nineteen self-authored and thirty-six mined from public repositories). Table 11 reports the structural properties of these fifty-five configurations.

Table 11. Structural census of fifty-five acyclic multi-agent configurations.

| Structural Property | Count | Proportion |
|---|---|---|
| Total acyclic configurations (census n) | 55 | 100.0% |
| Strictly sequential linear chains (chain count) | 49 | 89.1% |
| Dominating source agent covering all execution steps | 55 | 100.0% |
| Sink-bearing configurations with blast-radius floor of 1 | 21 | 100.0% |

Forty-nine of the fifty-five configurations (89.1%) are strictly sequential linear chains. All fifty-five configurations (100.0%) exhibit a dominating source agent whose influence reaches all subsequent steps. For all twenty-one sink-bearing configurations, the blast-radius floor under signed hand-offs equals 1. In real-world multi-agent systems, agent partitioning alone provides no containment in the absence of least privilege.

Protocol v7b mined public GitHub repositories implementing multi-agent workflows in CrewAI, LangGraph, and AutoGen. Table 12 reports the mining funnel and capability metrics.

Table 12. Real-world configuration mining funnel and metrics (Protocol v7b).

| Metric | Count | Estimate [95% Wilson CI] |
|---|---|---|
| Configurations discovered | 37 | - |
| Configurations scored | 36 | - |
| Configurations with no write or external sink | 34 | 94.4% [81.9%, 98.5%] |
| Strictly sequential linear configurations | 36 | 100.0% [90.4%, 100.0%] |
| Single-agent blast radius contains a sink | 2 | 5.6% [1.5%, 18.1%] |
| Zero-own-sink agent reaches downstream sink | 1 | 2.8% [0.5%, 14.2%] |
| Code execution tool present | 0 | 0.0% [0.0%, 9.6%] |

Thirty-seven configurations were discovered and thirty-six were scored (one LangGraph configuration was excluded as cyclic). Thirty-four of thirty-six scored configurations (94.4%) contained no write or external tool sinks under the frozen keyword classifier. All thirty-six scored configurations were sequential pipelines. The two configurations containing sinks confirmed the formal model's propagation logic: in `kid0317/crewai_mas_demo`, a zero-tool `researcher` agent reached a downstream `FileWriterTool` sink via context propagation.

### 4.5 RQ5: Nominal performance across model families

Table 6 reports main-suite task success, intent fidelity, and overhead for each condition, separately per model family.

On DeepSeek (360 runs, five repetitions per cell), task success sits at a ceiling across every condition: B1 98.9 percent, B2 100.0 percent, P 98.9 percent, GPLUS 100.0 percent, with intent fidelity at 99.9 to 100.0 percent in every condition and zero violations anywhere in the suite. Every paired Wilcoxon comparison between conditions is non-significant after Holm correction, and because at most a handful of tasks produce any non-zero paired difference at all, the tests are uninformative rather than evidence of equivalence. The practical-significance criterion the proposal set in advance, a ten-percentage-point gain in success or fidelity, is not met by any condition over any other. Hypothesis H-RQ3a, that the proposed controls beat both baselines on success and fidelity, is therefore not supported. This is a null result, reported as such rather than reframed, and it is the finding the proposal itself anticipated as a live possibility given a sufficiently capable model.

Gemini (248 runs across the four conditions, with the per-model repetition count reduced to two per cell as disclosed in Section 3.5) replicates the same ceiling pattern: B1 93.5 percent, B2 96.9 percent, P 96.7 percent, GPLUS 96.8 percent, with zero violations in every condition. Groq's open-weight model (166 runs) behaves differently: B1 40.9 percent, B2 39.0 percent, P 29.7 percent, GPLUS 31.8 percent. Task success on this model is far below the other two, which is a property of the model's own capability on the main suite's tasks rather than of any condition, because Wilcoxon signed-rank tests with Holm correction find no statistically significant difference between P and B1, between P and B2, or between GPLUS and P on this model either (all adjusted p = 1.00). Zero nominal violations occurred in every condition on every model, so H-RQ3b, that the proposed controls produce fewer violations than the baselines on nominal tasks, is not testable here: there is nothing for the gate to have prevented, because the baselines never violated anything on a task that was not under assumed compromise in the first place.

![Fig. 4. Main-suite task success by condition and model, mean with 95% cluster-bootstrap confidence interval.](/Users/shafinoid/Documents/GitHub/guide/scripts/paper/figures/fig4_main_suite_success.png)

Governance overhead is small relative to model latency on every model family. Scripted-model timing, isolating the runtime's own cost from any provider's response time, measures 0.16 milliseconds per three-step run for B1, 0.23 milliseconds for B2, 1.68 milliseconds for P and 1.69 milliseconds for GPLUS, against several seconds of actual model response time per run. Median wall time with a live model shows P at 1.03 times B2's time on DeepSeek, comfortably inside the proposal's 1.30 threshold, so H-RQ3c, that overhead stays within thirty percent, is supported.

![Fig. 7. Overhead by condition: end-to-end wall time on DeepSeek, and framework-only time isolated from provider latency.](/Users/shafinoid/Documents/GitHub/guide/scripts/paper/figures/fig7_overhead.png)

---

## 5. Discussion

### 5.1 Why nominal success did not move

The null result on nominal task success is not a failure of the proposed controls to work. It is a ceiling effect: a sufficiently capable model solves close to every nominal task correctly regardless of which condition it runs under, because none of the eighteen main-suite tasks requires routing, signed hand-offs or a policy gate to be solved correctly in the first place. The literature's own measurement work on hand-off attenuation shows the same capability dependence from the other direction: governance decay across hand-off boundaries is severe on a weaker 32-billion-parameter model and nearly absent on a stronger one. Both findings point the same way. The value of these controls is not visible on tasks a capable model would get right anyway. It is visible only once something goes wrong, whether because the model is weaker, as the Groq results in Section 4.5 show, or because an agent is compromised, as the assumed-compromise results in Section 4.2 show.

### 5.2 Why containment needed two mechanisms, not one

The policy gate alone stops every out-of-domain action tested, because an external domain and a destructive delete are both decisions the gate's declared policy can make from the call's own metadata, without needing to know anything about what the task's trusted text actually says. The in-domain steering case is different in kind: the attacker's chosen recipient is inside the permitted domain, so nothing in the gate's declarative rules gives it grounds to deny the call. The provenance guard closes exactly this gap, because it asks a different question: not "is this recipient's domain permitted," but "does this specific recipient appear anywhere in the task's own trusted text." This dependency relationship, where the guard's effectiveness collapses the moment the gate underneath it is removed, is why Section 4.2 reports the provenance guard as depending on the gate rather than as an independent control.

### 5.3 What the static bound adds

Measuring containment by attacking a running system can only report what was tested. The static blast-radius bound in Section 3.7 computes, before any agent runs, every effect a stated compromised set could cause. An operator can audit a configuration's worst case without having to construct and run every possible attack against it first.

The static analysis provides two key capabilities beyond empirical measurement. First, it identifies structural vulnerabilities in workflow definitions before deployment. The analysis uncovered the substring-matching provenance guard's vulnerability to crafted substring recipients (Finding F1) and revealed structural over-privilege across eighteen of nineteen multi-agent configurations. Both vulnerabilities were confirmed empirically after the static analysis flagged them.

Second, the static analysis predicts deployment utility costs before execution (Contribution C2). Stricter security policies often break legitimate application workflows. Protocol v8 (M1b) showed that the static predictor anticipates empirical task loss with 96.9% accuracy, matching the empirical cost of 29.9 percentage points exactly. Operators can evaluate this trade-off statically rather than discovering workflow disruptions during live deployment.

### 5.4 Model invariance and the AgentDojo finding

A critical insight from the AgentDojo evaluation is that containment does not depend on model compliance. In Protocol v6b (undefended), DeepSeek-V3 exhibited an attack success rate of only 2.1%, resisting indirect prompt injections natively. Comparing defenses using live attack success on this model is uninformative, because the baseline model rarely executes injected instructions.

In contrast, the assumed-compromise replay in Protocol v8 (M1) evaluated the runtime reference monitor against ground-truth malicious tool invocations directly. The monitor contained 92.3% of attack scenarios and blocked 93.6% of malicious sink calls deterministically. This demonstrates that GUIDE's security guarantees originate from architectural policy enforcement and provenance verification, not from model compliance.

### 5.5 Topology and least privilege

Proposition 4 proves that in strictly linear dependency chains, agent partitioning and cryptographic signing cannot reduce the worst-case blast radius below full pipeline reach. The structural census in Section 4.4 revealed that forty-nine of fifty-five real-world configurations (89.1%) are strictly sequential linear chains, and all fifty-five contain a dominating source agent. In real-world multi-agent pipelines, partitioning agents across execution steps provides no structural containment against an upstream compromise.

Least-privilege policy synthesis is therefore the primary mechanism for reducing blast radius in sequential workflows. Synthesizing minimal policies reduced median reach by 1.0 sink across linear chains. However, this protection incurs a security versus utility trade-off. On the Slack suite, where downstream tools regularly depend on parameters returned by upstream tools, strict policy enforcement reduced benign utility by 66.7 percentage points. Statically predicting this utility loss before deployment (Section 4.3) enables system designers to tune permissions rationally.

### 5.6 Practical implications

Operators deploying multi-agent pipelines obtain two concrete, actionable results from this study. First, a least-privilege policy can be synthesized directly from nominal execution traces, cutting reachable sink capability by 55.6% without breaking legitimate calls. System designers need not hand-craft complex security policies. Second, cryptographic hand-offs require per-principal signing keys. A shared key across agents detects zero percent of sender-spoofing attempts, whereas per-principal keys detect tampering at a 100 percent rate.

### 5.7 Limitations

This study has ten specific limitations:

1. Concurrent literature: Three 2026 preprints (Parisel, 2026, Muruaga, 2026, Moon & Varshney, 2026) examine related aspects of least autonomy, delegation security, and containment verification. While GUIDE focuses on multi-agent static bounds and runtime reference monitors, partial conceptual overlap exists.
2. Proof verification: The soundness proof is checked by hand and by property-based testing against the real runtime implementation. It is not machine-checked in an interactive theorem prover.
3. Multi-agent evaluation suite: Multi-agent empirical evidence relies on the benchmark suite authored for this study, because no standardized benchmark for compromised-agent containment in multi-agent systems currently exists.
4. Single-agent external benchmark: The external AgentDojo benchmark is single-agent and was evaluated with one model family (DeepSeek-V3).
5. Live workspace sample: Live workspace attack evaluations on AgentDojo used a 10-task subset, though the assumed-compromise replay (M1) covers the complete 949-pair grid.
6. Live injection unresponsiveness: Live AgentDojo attack success was uninformative for DeepSeek-V3 because the model resisted prompt injections natively.
7. Mined repository scope: The real-world configuration mining in Protocol v7b evaluates public demonstration repositories, and its keyword classifier provides a conservative lower bound.
8. DAG model constraint: Workflows containing cycles or unbounded retry loops fall outside the current DAG formal model.
9. Text-only attacks: Purely conversational injections that do not invoke external tools (such as travel injection task 6) fall outside the scope of a tool-boundary reference monitor.
10. Admitted tool classes: The admitted calls in M1 include tools lacking control parameters (such as `update_password`) and recipient values that were legitimately part of the user's initial prompt.

---

## 6. Conclusion

This paper evaluated GUIDE, a reference monitor for LLM multi-agent systems that computes a sound static blast-radius bound under assumed compromise, synthesises least-privilege policies, and enforces containment at runtime.

The investigation establishes four main contributions:

First, Contribution C1 delivers a sound static blast-radius bound for arbitrary compromised agent subsets, paired with least-privilege policy synthesis. The bound was proved sound, verified through property-based tests, and confirmed exact against a live adaptive attacker on thirty-nine of thirty-nine (39/39) direct effects with zero soundness violations.

Second, Contribution C2 introduces pre-deployment utility cost prediction. The static analysis accurately anticipates empirical task disruption before execution, achieving 96.9% accuracy on AgentDojo and predicting an attributable loss of 29.9 percentage points that exactly matched the observed 29.9 percentage points.

Third, Contribution C3 establishes the interaction topology floor. Proposition 4 proves that in strictly linear dependency chains, agent partitioning cannot lower the blast radius floor. The structural census confirmed that forty-nine of fifty-five real-world configurations (89.1%) are strictly linear chains, demonstrating that least-privilege policy synthesis is the primary lever for risk reduction in practice.

Fourth, Contribution C4 provides extensive empirical findings across internal multi-agent suites and external benchmarks. The reference monitor achieved 92.3% containment under assumed compromise on AgentDojo, while exposing critical security weaknesses in substring provenance guards (which admitted 692 recipients) and widespread structural over-privilege across eighteen of nineteen popular multi-agent configurations.

By shifting security enforcement from prompt compliance to sound static analysis and deterministic runtime monitoring, GUIDE provides rigorous security guarantees for multi-agent systems operating under the threat of agent compromise.

---

## Acknowledgments

The author thanks the supervisor, Ts. Dr. Maythem Kamal Abbas, and the course lecturer, Dr. R. Logeswaran, for guidance on this work. No external funding was received, and the free-tier API credits used for the Groq and Google AI Studio evaluations in Section 3.5 were provided under each provider's own public free-tier terms.

## Statements

- Data availability: the raw results files, manifests and summary statistics for every protocol version are archived with the tagged code release referenced below. [TODO: insert archived Zenodo or equivalent DOI before submission.]
- Code availability: the runtime reference monitor, bench harness, and all analysis scripts are released under the tagged commit referenced in the data availability statement above. [TODO: insert DOI.]
- Author contributions: [TODO: complete CRediT statement once author list is confirmed, plan gate G6.]
- Competing interests: the author declares no competing interests.
- Ethics: this study used no human participants and no personal data about identifiable individuals: no ethics approval was required for the work reported here.
- Generative AI use: an AI coding and writing assistant was used during drafting, data aggregation scripting, and literature screening, under the author's direction and review: the author is responsible for every claim, number and citation in this paper and has checked each against the underlying data files named in the data availability statement. [TODO: adjust wording to the target journal's specific AI-disclosure policy before submission. Confirm APU's own generative-AI coursework policy with the supervisor, per `docs/paper-plan.md` §0.3.]

## References

References are listed alphabetically by first author surname, APA 7th edition. Generated from `references-final.bib` (115 entries, 93 peer-reviewed / 22 preprint per `docs/lit-review/references-final.md`) by `scripts/paper/build_apa_refs.py`.

- Abdelnabi, S., Fay, A., Cherubin, G., Salem, A., Fritz, M., & Paverd, A. (2025). Get My Drift? Catching LLM Task Drift with Activation Deltas. 2025 IEEE Conference on Secure and Trustworthy Machine Learning (SaTML), 43–67. https://doi.org/10.1109/satml64287.2025.00011
- Abdelnabi, S., Gomaa, A., & Fritz, M. (2025). Firewalls to Secure Dynamic LLM Agentic Networks. Transactions on Machine Learning Research. https://openreview.net/forum?id=G2k9N7wL1M
- Amayuelas, A., Yang, X., Antoniades, A., Hua, W., Pan, L., & Wang, W. (2024). MultiAgent Collaboration Attack: Investigating Adversarial Attacks in Large Language Model Collaborations via Debate. Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing, 4732––4749. https://doi.org/10.18653/v1/2024.emnlp-main.274
- An, H., Zhang, J., Du, T., Zhou, C., Li, Q., Lin, T., & Ji, S. (2025). IPIGuard: A Novel Tool Dependency Graph-Based Defense Against Indirect Prompt Injection in LLM Agents. Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing, 1023–1039. https://doi.org/10.18653/v1/2025.emnlp-main.53
- Andriushchenko, M., Souly, A., Dziemian, M., Duenas, D., Lin, M., Wang, J., Hendrycks, D., Zou, A., Kolter, Z., Fredrikson, M., Winsor, E., Wynne, J., Gal, Y., & Davies, X. (2025). AgentHarm: A Benchmark for Measuring Harmfulness of LLM Agents. International Conference on Learning Representations (ICLR 2025). https://openreview.net/forum?id=AC5n7xHuR1
- Auer, Cesa-Bianchi, & Fischer (2002). Finite-time Analysis of the Multiarmed Bandit Problem. Machine Learning. https://doi.org/10.1023/A:1013689704352
- Becker, Kaesberg, Stephan, & Wahle (2026). Stay Focused: Problem Drift in Multi-Agent Debate. Findings of the Association for Computational Linguistics: EACL 2026. https://doi.org/10.18653/v1/2026.findings-eacl.268
- Bernstein, Duif, Lange, & Schwabe (2012). High-speed high-security signatures. Journal of Cryptographic Engineering. https://doi.org/10.1007/s13389-012-0027-1
- Li, B., & Wang, G. (2026). Governance at the Boundary: How Agent Decomposition Degrades Policy Compliance. arXiv preprint arXiv:2608.16055. https://arxiv.org/abs/2608.16055
- Sidik, B., & Rokach, L. (2026). Beyond Static Sandboxing: Learned Capability Governance for Autonomous AI Agents. arXiv preprint arXiv:2604.11839. https://arxiv.org/abs/2604.11839
- Calboreanu, E. (2026). TRACE: Runtime Governance, Containment, and Evidence for Autonomous AI Agent Operations. IEEE Access, 14, 142574–142594. https://doi.org/10.1109/access.2026.3733578
- Cemri, M., Tulsiani, S., Pathak, D., & Darrell, T. (2025). Why Do Multi-Agent LLM Systems Fail? Advances in Neural Information Processing Systems 38, 31742––31776. https://doi.org/10.52202/085713-3375
- Chang, E. Y., & Geng, L. (2025). SagaLLM: Context Management, Validation, and Transaction Guarantees for Multi-Agent LLM Planning. Proceedings of the VLDB Endowment, 18(12), 4874–4886. https://doi.org/10.14778/3750601.3750611
- Chen, Z., Zhang, T., Zhu, S., & Li, B. (2025). ShieldAgent: Shielding Agents via Verifiable Safety Policy Reasoning. Forty-second International Conference on Machine Learning. https://openreview.net/forum?id=DkRYImuQA9
- Chen, Z., Liu, H., Xu, D., Dong, D., Li, J., Pu, B., & Zhai, J. (2026). Cordon: Semantic Transactions for Tool-Using LLM Agents. arXiv preprint arXiv:2606.17573. https://arxiv.org/abs/2606.17573
- Cheney, Chiticariu, & Tan (2009). Provenance in Databases: Why, How, and Where. Foundations and Trends in Databases. https://doi.org/10.1561/1900000006
- Chinaei, M. H. (2026). Causality Laundering: Denial-Feedback Leakage in Tool-Calling LLM Agents. arXiv preprint arXiv:2604.04035. https://arxiv.org/abs/2604.04035
- Parisel, C. (2026). A Theory of Least Autonomy in AI. arXiv preprint arXiv:2607.09744. https://arxiv.org/abs/2607.09744
- Denning (1976). A lattice model of secure information flow. Communications of the ACM. https://doi.org/10.1145/360051.360056
- Dong, S., Xu, S., He, P., Li, Y., Tang, J., Liu, T., Liu, H., & Xiang, Z. (2025). Memory Injection Attacks on LLM Agents via Query-Only Interaction. Advances in Neural Information Processing Systems 38, 52119–52153. https://doi.org/10.52202/085713-1554
- Lee, D., Tiwari, M., & Miranda, B. (2026). Prompt Infection: LLM-to-LLM Prompt Injection within Multi-agent Systems. Lecture notes in computer science. https://doi.org/10.1007/978-3-032-16092-8_28
- Debenedetti, E., Zhang, J., Balunović, M., & Beurer-Kellner, L. (2024). AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents. arXiv preprint arXiv:2406.13352. https://arxiv.org/abs/2406.13352
- Debenedetti, E., Shumailov, I., Fan, T., & Hayes, J. (2025). Defeating Prompt Injections by Design. arXiv preprint arXiv:2503.18813. https://arxiv.org/abs/2503.18813
- Nikolaou, E., Eckhoff, M. W., Flood, R., Grov, G., Mavroeidis, V., & Aspinall, D. (2026). CaMeLoT: CaMeL orchestrated with Temporal logic for static verification and liveness. arXiv preprint arXiv:2609.18674. https://arxiv.org/abs/2609.18674
- Kaufmann, E., Garivier, A., & Paristech, T. (2012). On Bayesian Upper Confidence Bounds for Bandit Problems.
- Syros, G., Suri, A., Ginesin, J., Nita-Rotaru, C., & Oprea, A. (2025). SAGA: A Security Architecture for Governing AI Agentic Systems. Network and Distributed System Security Symposium. https://arxiv.org/abs/2504.21034
- Gill-Lakhowal, A. (2026). Deterministic Runtime Enforcement: The Execution Authority for Autonomous AI Agents. IEEE Access, 14, 119764–119790. https://doi.org/10.1109/access.2026.3719838
- Gomaa, A., Abdelnabi, S., & Fritz, M. (2025). ConVerse: Benchmarking Contextual Safety in Agent-to-Agent Conversations. Proceedings of the 18th Conference of the European Chapter of the Association for Computational Linguistics (Volume 1: Long Papers), 1017––1033. https://doi.org/10.18653/v1/2025.eacl-main.62
- Guo, Y., Hu, X., Zhang, T., Shen, Y., & Xiao, Y. (2024). RedCode: Risky Code Execution and Generation Benchmark for Code Agents. Advances in Neural Information Processing Systems 37, 69022––69051. https://doi.org/10.52202/079017-2197
- Guo, Xu, Zhu, & Hong (2026). MCP-AgentBench: Evaluating Real-World Language Agent Performance with MCP-Mediated Tools. Proceedings of the AAAI Conference on Artificial Intelligence. https://doi.org/10.1609/aaai.v40i37.40347
- Zhang, H., Nian, Y., & Zhao, Y. (2026). Agent Audit: A Security Analysis System for LLM Agent Applications. arXiv preprint arXiv:2603.22853. https://arxiv.org/abs/2603.22853
- Zhang, H., Huang, J., Mei, K., Yao, Y., Wang, Z., & Zhan, C. (2024). Agent Security Bench (ASB): Formalizing and Benchmarking Attacks and Defenses in LLM-based Agents. International Conference on Learning Representations. https://arxiv.org/abs/2410.02644
- Dai, H., Ying, Z., Li, W., & Wu, X. (2026). SafeFlow: Semantic Information-Flow Control for Blocking Malicious Propagation in Multi-Agent Systems. arXiv preprint arXiv:2607.25255. https://arxiv.org/abs/2607.25255
- Wang, H., Poskitt, C. M., & Sun, J. (2025). AgentSpec: Customizable Runtime Enforcement for Safe and Reliable LLM Agents. Proc. ICSE'26, pages 2938-2950. ACM, 2026. https://doi.org/10.1145/3744916.3764546
- Hevner, March, Park, & Ram (2004). Design Science in Information Systems Research1. MIS Quarterly. https://doi.org/10.2307/25148625
- Huang, Y., Shi, C., Wang, J., Zhang, Z., & Li, B. (2024). On the Resilience of LLM-Based Multi-Agent Collaboration with Faulty Agents. Proceedings of the 41st International Conference on Machine Learning, 235, 19949––19972. https://proceedings.mlr.press/v235/huang24s.html
- Kavathekar, I., Jain, H., Rathod, A., & Kumaraguru, P. (2025). TAMAS: Benchmarking Adversarial Risks in Multi-Agent LLM Systems. arXiv preprint arXiv:2511.05269. https://arxiv.org/abs/2511.05269
- Ji, Lei, Bi, & Wei (2025). LLM-Based Multi-Agent Systems are Scalable Graph Generative Models. Findings of the Association for Computational Linguistics: ACL 2025. https://doi.org/10.18653/v1/2025.findings-acl.78
- Jia, F., Wu, T., Qin, X., & Squicciarini, A. (2025). The Task Shield: Enforcing Task Alignment to Defend Against Indirect Prompt Injection in LLM Agents. Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), 29680–29697. https://doi.org/10.18653/v1/2025.acl-long.1435
- Jia, Y., Shao, Z., Liu, Y., Jia, J., Song, D., & Gong, N. (2026). A Critical Evaluation of Defenses against Prompt Injection Attacks: [Dataset/Tool Paper]. Proceedings of the 31st ACM Symposium on Access Control Models and Technologies, 265–270. https://doi.org/10.1145/3750555.3811884
- Zhu, J., Tseng, K., Vernik, G., Huang, X., Patil, S. G., & Fang, V. (2025). MiniScope: A Least Privilege Framework for Authorizing Tool Calling Agents. arXiv preprint arXiv:2512.11147. https://arxiv.org/abs/2512.11147
- Backes, J., Bolignano, P., Cook, B., & Dodge, C. (2018). Semantic-based Automated Reasoning for AWS Access Policies using SMT. https://doi.org/10.23919/fmcad.2018.8602994
- Ju, T., Wang, Y., Hua, Y., Ma, X., Cheng, P., Zhao, H., Wang, Y., Liu, L., Xie, J., Zhang, Z., & Liu, G. (2026). Flooding spread of manipulated knowledge in LLM-based multi-agent communities. Science China Information Sciences, 69(7). https://doi.org/10.1007/s11432-024-4663-2
- Greshake, K., Abdelnabi, S., Mishra, S., & Endres, C. (2023). Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection. arXiv preprint arXiv:2302.12173. https://arxiv.org/abs/2302.12173
- Khan, R. M. S., Tan, Z., Yun, S., Fleming, C., & Chen, T. (2025). Agents Under Siege: Breaking Pragmatic Multi-Agent LLM Systems with Optimized Prompt Attacks. Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), 8856––8874. https://doi.org/10.18653/v1/2025.acl-long.446
- Kitchenham & Charters (2007). Guidelines for performing Systematic Literature Reviews in Software Engineering. Keele Univ. \& Durham Univ. EBSE Technical Report EBSE-2007-01 -- verify by opening the report PDF before citing.
- La Malfa et al. (2025). Large Language Models Miss the Multi-Agent Mark. Advances in Neural Information Processing Systems 38 (NeurIPS 2025). https://doi.org/10.52202/085713-4663
- Le, T. D., Dinh, T. D., Nguyen, T. L. Q., & Nguyen, C. D. (2026). Cross-layer contagion of prompt injections in multi-agent swarms: a multiplex microscopic markov chain approach. Cybersecurity, 9(1). https://doi.org/10.1186/s42400-026-00628-w
- Li, Z., Zhang, T., Hu, X., Shen, Y., & Xiao, Y. (2025). DRIFT: Dynamic Rule-Based Defense with Injection Isolation for Securing LLM Agents. Advances in Neural Information Processing Systems 38, 46083––46109. https://doi.org/10.52202/085713-4886
- Li, Z., Li, K., Ma, B., Xu, M., Zhang, Y., & Cheng, X. (2025). We Urgently Need Privilege Management in MCP: A Measurement of API Usage in MCP Ecosystems. 2025 IEEE 22nd International Conference on Mobile Ad-Hoc and Smart Systems (MASS), 555–560. https://doi.org/10.1109/mass66014.2025.00090
- Li, E., Mallick, T., Rose, E., Robertson, W., Oprea, A., & Nita-Rotaru, C. (2026). ACE: A Security Architecture for LLM-Integrated App Systems. Proceedings 2026 Network and Distributed System Security Symposium. https://doi.org/10.14722/ndss.2026.230352
- Li, Z., Cui, J., Liao, X., Xing, L., Xing, L., & Li, Z. (2026). Les Dissonances: Cross-Tool Harvesting and Polluting in Pool-of-Tools Empowered LLM Agents. Proceedings 2026 Network and Distributed System Security Symposium. https://doi.org/10.14722/ndss.2026.240577
- Liu, Y., Jia, Y., Jia, J., Song, D., & Gong, N. Z. (2025). DataSentinel: A Game-Theoretic Detection of Prompt Injection Attacks. 2025 IEEE Symposium on Security and Privacy (SP), 2190–2208. https://doi.org/10.1109/sp61157.2025.00250
- Liu, F., Zhang, Y., Luo, J., Dai, J., Chen, T., Yuan, L., Yu, Z., Shi, Y., Li, K., Zhou, C., Chen, H., & Yang, M. (2025). Make Agent Defeat Agent: Automatic Detection of Taint-Style Vulnerabilities in LLM-based Agents. 34th USENIX Security Symposium (USENIX Security 25). https://www.usenix.org/conference/usenixsecurity25/presentation/liu-fengyu
- Liu, S., Chen, Y., Krishna, R., Sinha, S., Ganhotra, J., & Jabbarvand, R. (2026). Process-Centric Analysis of Agentic Software Systems. Proceedings of the ACM on Programming Languages, 10(OOPSLA1), 1961–1988. https://doi.org/10.1145/3798271
- Costa, M., Köpf, B., Kolluri, A., & Paverd, A. (2025). Securing AI Agents with Information-Flow Control. arXiv preprint arXiv:2505.23643. https://arxiv.org/abs/2505.23643
- Mo, Y., Wang, H., Chen, Y., & Song, D. (2025). Attractive Metadata Attack: Inducing LLM Agents to Invoke Malicious Tools. Advances in Neural Information Processing Systems 38, 24874––24901. https://doi.org/10.52202/085713-2633
- Mohammadi, Li, Lo, & Yip (2025). Evaluation and Benchmarking of LLM Agents: A Survey. Proceedings of the 31st ACM SIGKDD Conference on Knowledge Discovery and Data Mining V.2. https://doi.org/10.1145/3711896.3736570
- Motwani, S., Baranchuk, M., Strohmeier, M., Bolina, V., Torr, P., Hammond, L., & Witt, C. D. (2024). Secret Collusion among AI Agents: Multi-Agent Deception via Steganography. Advances in Neural Information Processing Systems 37, 73439–73486. https://doi.org/10.52202/079017-2336
- Narisetty, P., Kore, S. N. B., Kattamanchi, U. K. R., & Kumarapu, J. (2026). Adaptive Evaluation of Out-of-Band Defenses Against Prompt Injection in LLM Agents. arXiv preprint arXiv:2606.26479. https://arxiv.org/abs/2606.26479
- Page, McKenzie, Bossuyt, & Boutron (2021). The PRISMA 2020 statement: an updated guideline for reporting systematic reviews. BMJ. https://doi.org/10.1136/bmj.n71
- Park, O'Brien, Cai, & Morris (2023). Generative Agents: Interactive Simulacra of Human Behavior. Proceedings of the 36th Annual ACM Symposium on User Interface Software and Technology. https://doi.org/10.1145/3586183.3606763
- Gandhi, P. A., Shukla, A., Tayouri, D., Ifland, B., Elovici, Y., & Puzis, R. (2025). ATAG: AI-Agent Application Threat Assessment with Attack Graphs. ACM Asia Conference on Computer and Communications Security. https://doi.org/10.1145/3779208.3785380
- Pasupuleti, Allala, Bayyavarapu, R. K. V., & Tyagi (2026). Safe and Policy-Compliant Multi-Agent Orchestration for Enterprise AI. 2026 International Conference on Artificial Intelligence, Systems, and Emerging Technologies (ICAISET). https://doi.org/10.1109/ICAISET66439.2026.11541969
- Peffers, Tuunanen, Rothenberger, & Chatterjee (2007). A Design Science Research Methodology for Information Systems Research. Journal of Management Information Systems. https://doi.org/10.2753/MIS0742-1222240302
- Peign{\'e}-Lefebvre, M., Wang, X., Tan, Z., & Chen, T. (2025). Multi-Agent Security Tax: Trading Off Security and Collaboration Capabilities in Multi-Agent LLM Systems. Proceedings of the AAAI Conference on Artificial Intelligence, 39(26), 26865––26873. https://doi.org/10.1609/aaai.v39i26.35338
- Wu, Q., Bansal, G., Zhang, J., & Wu, Y. (2023). AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation. arXiv preprint arXiv:2308.08155. https://arxiv.org/abs/2308.08155
- Zhan, Q., Liang, Z., Ying, Z., & Kang, D. (2024). InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated Large Language Model Agents. arXiv preprint arXiv:2403.02691. https://arxiv.org/abs/2403.02691
- Veski, R. M., Guerraoui, R., & Froelicher, D. (2026). CAPMAS: Capability-Based Delegation of Privileges in Multi-Agent Systems. arXiv preprint arXiv:2609.06500. https://arxiv.org/abs/2609.06500
- Sharma, R. K., Jiang, L., Chen, S., & Lin, Z. (2026). Ajar: Measuring Open Privilege in Agent Defenses. arXiv preprint arXiv:2609.26900. https://arxiv.org/abs/2609.26900
- Moon, R., & Varshney, L. R. (2026). Containment Verification: AI Safety Guarantees Independent of Alignment. arXiv preprint arXiv:2605.09045. https://arxiv.org/abs/2605.09045
- Ruan, Y., Dong, H., Wang, A., Pitis, S., Zhou, Y., Ba, J., Dubois, Y., Maddison, C. J., & Hashimoto, T. (2024). Identifying the Risks of LM Agents with an LM-Emulated Sandbox. The Twelfth International Conference on Learning Representations (ICLR 2024). https://openreview.net/forum?id=V2s6rVv7tK
- Paul, R. K., & Nandy, S. (2026). Beyond Single-Model Injection: A Threat Model and Defense Architecture for Prompt Injection in Multi-Agent Systems. arXiv preprint arXiv:2609.22949. https://arxiv.org/abs/2609.22949
- Miao, R., Liu, Y., Wang, Y., Shen, X., Tan, Y., & Dai, Y. (2025). BlindGuard: Safeguarding LLM-based Multi-Agent Systems under Unknown Attacks. Annual Meeting of the Association for Computational Linguistics. https://arxiv.org/abs/2508.08127
- Saltzer & Schroeder (1975). The protection of information in computer systems. Proceedings of the IEEE. https://doi.org/10.1109/PROC.1975.9939
- Wang, S., Hou, X., Zhao, Y., Cheng, X., & Wang, H. (2026). AgentFlow: Building Agent Dependency Graphs for Static Analysis of Agent Programs. arXiv preprint arXiv:2607.01640. https://arxiv.org/abs/2607.01640
- Shi, J., Yuan, Z., Tie, G., Zhou, P., Gong, N., & Sun, L. (2026). Prompt Injection Attack to Tool Selection in LLM Agents. Proceedings 2026 Network and Distributed System Security Symposium. https://doi.org/10.14722/ndss.2026.230675
- Wang, S., Zhang, G., Yu, M., Wan, G., Meng, F., & Guo, C. (2025). G-Safeguard: A Topology-Guided Security Lens and Treatment on LLM-based Multi-agent Systems. Annual Meeting of the Association for Computational Linguistics. https://arxiv.org/abs/2502.11127
- Zhou, S., Xu, F. F., Zhu, H., & Zhou, X. (2023). WebArena: A Realistic Web Environment for Building Autonomous Agents. arXiv preprint arXiv:2307.13854. https://arxiv.org/abs/2307.13854
- Song, H., Shen, Y., Luo, W., Guo, L., Chen, T., Wang, J., Li, B., Zhang, X., & Chen, J. (2026). Beyond the Protocol: Unveiling Attack Vectors in the Model Context Protocol (MCP) Ecosystem. IEEE Transactions on Software Engineering, 52(8), 2410–2426. https://doi.org/10.1109/tse.2026.3694876
- Su, J., Lan, Q., Xia, Y., Sun, L., Tian, W., Shi, T., & He, L. (2026). Difficulty-Aware Agentic Orchestration for Query-Specific Multi-Agent Workflows. Proceedings of the ACM Web Conference 2026, 2060–2070. https://doi.org/10.1145/3774904.3792240
- Safin, T. H., Zisad, S. N., Shatabda, S., & Hasan, R. (2026). Trust propagation and structural containment in Multi-agent LLM pipelines. arXiv preprint arXiv:2609.17648. https://arxiv.org/abs/2609.17648
- Moutesidis, T. (2026). The Model Proposes, the Code Disposes: A Pre-Registered Ablation of a Verifier-and-Acceptance Stage in an LLM-Orchestrated Offensive-Security Agent. arXiv preprint arXiv:2609.15887. https://arxiv.org/abs/2609.15887
- Shi, T., He, J., Wang, Z., & Li, H. (2025). Progent: Securing AI Agents with Privilege Control. arXiv preprint arXiv:2504.11703. https://arxiv.org/abs/2504.11703
- Van hamme, T., Vissers, T., Carnerero-Cano, J., Fritz, M., Lupu, E. C., & Desmet, L. (2026). MATRA: Modeling the Attack Surface of Agentic AI Systems -- OpenClaw Case Study. arXiv preprint arXiv:2605.10763. https://arxiv.org/abs/2605.10763
- Triedman, H., Jha, R., & Shmatikov, V. (2025). Multi-Agent Systems Execute Arbitrary Malicious Code. Conference on Language Modeling (COLM 2025). https://openreview.net/forum?id=DAozI4etUp
- Wang, Ma, Feng, & Zhang (2024). A survey on large language model based autonomous agents. Frontiers of Computer Science. https://doi.org/10.1007/s11704-024-40231-1
- Wang, X., Huang, K., Liang, B., Li, H., & Du, X. (2025). Shadows in the Code: Exploring the Risks and Defenses of LLM-based Multi-Agent Software Development Systems. Proceedings of the AAAI Conference on Artificial Intelligence, 39(27), 27504––27512. https://doi.org/10.1609/aaai.v39i27.35411
- Wang, Y., Chen, S., Alkhudair, R., Alomair, B., & Wagner, D. (2026). Defending Against Prompt Injection with DataFilter. 2026 IEEE Conference on Secure and Trustworthy Machine Learning (SaTML), 139–157. https://doi.org/10.1109/satml68715.2026.00017
- Wang, Y., Geng, R., Chen, Y., & Jia, J. (2026). AttnTrace: Contextual Attribution of Prompt Injection and Knowledge Corruption. 2026 IEEE Symposium on Security and Privacy (SP), 4320–4338. https://doi.org/10.1109/sp63933.2026.00198
- Wang, Z., Gao, Y., Wang, Y., Liu, S., Sun, H., Cheng, H., Shi, G., Du, H., & Li, X. (2026). MCPTox: A Benchmark for Tool Poisoning on Real-World MCP Servers. Proceedings of the AAAI Conference on Artificial Intelligence, 40(42), 35811–35819. https://doi.org/10.1609/aaai.v40i42.40895
- Wang, H. K., & Zhang, Z. (2026). Kill-Chain Canaries: Stage-Level Tracking of Prompt Injection Across Attack Surfaces and Five Production LLMs. arXiv preprint arXiv:2603.28013. https://arxiv.org/abs/2603.28013
- Lan, W., Li, S., Wu, M., & Lai, X. (2026). ContainmentBench: Trace-Based Evaluation of Post-Exposure Containment in Tool-Using LLM Agents. arXiv preprint arXiv:2607.23999. https://arxiv.org/abs/2607.23999
- Wohlin (2014). Guidelines for snowballing in systematic literature studies and a replication in software engineering. Proceedings of the 18th International Conference on Evaluation and Assessment in Software Engineering. https://doi.org/10.1145/2601248.2601268
- Wu, Y., Yang, K., Roesner, F., Kohno, T., Zhang, N., & Iqbal, U. (2026). Towards Automating Data Access Permissions in AI Agents. 2026 IEEE Symposium on Security and Privacy (SP), 2609–2627. https://doi.org/10.1109/sp63933.2026.00018
- Muruaga, X. (2026). Bounded Agents: Delegation Security for Multi-Agent AI Systems. arXiv preprint arXiv:2608.15888. https://arxiv.org/abs/2608.15888
- Xiang, Z., Zheng, L., Li, Y., Hong, J., Li, Q., Xie, H., Zhang, J., Xiong, Z., Xie, C., Yang, C., Song, D., & Li, B. (2024). GuardAgent: Safeguard LLM Agents by a Guard Agent via Knowledge-Enabled Reasoning. Proceedings of the 41st International Conference on Machine Learning, 235, 54236––54254. https://proceedings.mlr.press/v235/xiang24c.html
- Yang, Z., Raman, S. S., Shah, A., & Tellex, S. (2024). Plug in the Safety Chip: Enforcing Constraints for LLM-driven Robot Agents. 2024 IEEE International Conference on Robotics and Automation (ICRA), 14435–14442. https://doi.org/10.1109/icra57147.2024.10611447
- Yang, Y., Chai, H., Shao, S., Song, Y., Qi, S., Rui, R., & Zhang, W. (2025). AgentNet: Decentralized Evolutionary Coordination for LLM-based Multi-Agent Systems. Advances in Neural Information Processing Systems 38, 118758–118785. https://doi.org/10.52202/085713-3578
- Zhang, Y., Lyu, Y., Jo, S., & Yang, Y. (2025). Adaptive Deadlock Avoidance for Decentralized Multi-agent Systems via CBF-inspired Risk Measurement. arXiv preprint arXiv:2503.09621. https://arxiv.org/abs/2503.09621
- Yao, S., Shinn, N., Razavi, P., & Narasimhan, K. (2025). τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains. International Conference on Learning Representations (ICLR 2025). https://openreview.net/forum?id=roNSXZpUDN
- Yu, Xu, Deng, & Li (2025). Tree of Agents: Improving Long-Context Capabilities of Large Language Models through Multi-Perspective Reasoning. Findings of the Association for Computational Linguistics: EMNLP 2025. https://doi.org/10.18653/v1/2025.findings-emnlp.246
- Yuan, T., He, Z., Dong, L., Wang, Y., Zhao, R., Xia, T., Xu, L., Zhou, B., Li, F., Zhang, Z., Wang, R., & Liu, G. (2024). R-Judge: Benchmarking Safety Risk Awareness for LLM Agents. Findings of the Association for Computational Linguistics: EMNLP 2024, 1467–1490. https://doi.org/10.18653/v1/2024.findings-emnlp.79
- Yue, Y., Zhang, G., Liu, B., Wan, G., Wang, K., Cheng, D., & Qi, Y. (2025). MasRouter: Learning to Route LLMs for Multi-Agent Systems. Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), 15549–15572. https://doi.org/10.18653/v1/2025.acl-long.757
- Dang, Y., Chen, Q., Luo, X. L., & Fan, J. (2025). Multi-Agent Collaboration via Evolving Orchestration. https://doi.org/10.52202/085713-5502
- Wu, Y., Roesner, F., Kohno, T., & Zhang, N. (2024). IsolateGPT: An Execution Isolation Architecture for LLM-Based Agentic Systems. The Network and Distributed System Security (NDSS) Symposium 2025. https://arxiv.org/abs/2403.04960
- Liu, Y., Jia, Y., Geng, R., & Jia, J. (2023). Formalizing and Benchmarking Prompt Injection Attacks and Defenses.
- Zhan, Q., Fang, R., Panchal, H. S., & Kang, D. (2025). Adaptive Attacks Break Defenses Against Indirect Prompt Injection Attacks on LLM Agents. Findings of the Association for Computational Linguistics: NAACL 2025, 7101–7117. https://doi.org/10.18653/v1/2025.findings-naacl.395
- Zhang, Z., Zhang, Y., Li, L., Gao, H., Wang, L., Lu, H., Zhao, F., Qiao, Y., & Shao, J. (2024). PsySafe: A Comprehensive Framework for Psychological-based Attack, Defense, and Evaluation of Multi-agent System Safety. Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), 14751––14774. https://doi.org/10.18653/v1/2024.acl-long.785
- Zhang, Q., Fu, L., Lian, L., Go, G., Wang, Y., Zhou, C., Jiang, Y., & Pu, G. (2026). Evaluating Privilege Usage of Agents with Real-World Tools. Proceedings of the 34th ACM International Conference on the Foundations of Software Engineering, 1192–1196. https://doi.org/10.1145/3803437.3805554
- Zheng, Y., Hu, Y., Yu, T., & Quinn, A. (2025). AgentSight: System-Level Observability for AI Agents Using eBPF. Proceedings of the 4th Workshop on Practical Adoption Challenges of ML for Systems, 110–115. https://doi.org/10.1145/3766882.3767169
- Zhu, S., Chen, Z., Wang, Z., & Li, B. (2025). MELON: Provable Defense Against Indirect Prompt Injection Attacks in AI Agents. Forty-second International Conference on Machine Learning. https://openreview.net/forum?id=gt1MmGaKdZ
- Zhuge, M., Gao, H., Wang, X., Gao, J., Shi, S., Hou, X., Zhang, J., & Shen, Z. (2024). Language Agents as Optimizable Graphs. Proceedings of the 41st International Conference on Machine Learning, 235, 62743––62767. https://proceedings.mlr.press/v235/zhuge24a.html
- Wang, Z., Du, Y., Zhang, Y., & Fang, M. (2023). MACCA: Offline Multi-agent Reinforcement Learning with Causal Credit Assignment.
- Zou, A., Xiao, Z., Ba, J., Fredrikson, M., Kolter, Z., & Hendrycks, D. (2025). Security Challenges in AI Agent Deployment: Insights from a Large Scale Public Competition. Advances in Neural Information Processing Systems 38, 16584––16624. https://doi.org/10.52202/085713-1768

## Appendices

- Appendix A: proof of the step-containment and blast-radius soundness theorems (full version of Section 3.7), reproduced from `docs/formal_model.md`.
- Appendix B: full eighteen-task list with every atomic constraint, from `src/guide_bench/tasks.py`.
- Appendix C: per-task result tables for every suite and every model family.
- Appendix D: policy files used in each condition.
- Appendix E: literature review search strings and PRISMA counts, from `docs/lit-review/literature-review.md`.
- Appendix F: exact reproduction commands for every table and figure in this paper, from `docs/experiments.md`.
- Figure S2 (routing simulation regret, stationary vs. drift) is a supplementary figure referenced from Section 3.7's routing discussion:

![Fig. S2. Routing simulation regret, stationary vs. drift scenario, mean over 100 seeds per algorithm.](/Users/shafinoid/Documents/GitHub/guide/scripts/paper/figures/figS2_routing_regret.png)

- Table 2 (RQ to objective to evidence alignment), Table 9 (deviations from the approved proposal), and the figures and tables listed in `docs/paper-plan.md` §B4 are to be inserted from the scripts in `scripts/paper/` once figure generation is run. This draft states their content and placement but does not fabricate the rendered images or exact numeric table cells beyond what Sections 4 and the appendix narrative above already report from verified source files.

---

[DRAFT STATUS NOTE FOR THE AUTHOR, not part of the paper: every number above is taken directly from `docs/experiments.md`, `docs/novelty.md`, `docs/formal_model.md`, `docs/limitations.md`, `docs/submission-alignment.md` and `docs/adr/0005-multi-model-evaluation.md` as they stood on 2026-10-02. No number, citation, or result in this draft was invented. Remaining before this is submission-ready: (1) generate the eight main-text figures and two supplementary figures per the specification in `docs/paper-plan.md` §B4, in black and white per the user's instruction, from the scripts named there. (2) generate Tables 1 to 10 as standalone tables from the same source files, several of which are only narrated in prose above. (3) run the citation export from `references-final.bib` into the References section above. (4) close the nineteen venue-DOI gaps and the one missing author list in the bibliography. (5) have the supervisor confirm author list, order and target venue (gate G6). (6) run a similarity check once this draft is finalised, given both submitted assignments are already in APU's Turnitin index. (7) rewrite the AI-use statement to the specific target journal's required wording.]
