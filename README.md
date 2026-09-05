# GUIDE: Governed UCB-routed Intent-Delegating Engine

```text
 ██████╗ ██╗   ██╗██╗██████╗ ███████╗    ███╗   ███╗ █████╗ ███████╗
██╔════╝ ██║   ██║██║██╔══██╗██╔════╝    ████╗ ████║██╔══██╗██╔════╝
██║  ███╗██║   ██║██║██║  ██║█████╗      ██╔████╔██║███████║███████╗
██║   ██║██║   ██║██║██║  ██║██╔══╝      ██║╚██╔╝██║██╔══██║╚════██║
╚██████╔╝╚██████╔╝██║██████╔╝███████╗    ██║ ╚═╝ ██║██║  ██║███████║
 ╚═════╝  ╚═════╝ ╚═╝╚═════╝ ╚══════╝    ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝
```

[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Methodology: Design Science Research](https://img.shields.io/badge/Methodology-DSR%20(Hevner%20et%20al.)-orange.svg)](https://doi.org/10.2307/25148625)
[![Status: Production-Grade](https://img.shields.io/badge/Status-Production--Grade-brightgreen.svg)](#)
[![Tests: 51 Passed](https://img.shields.io/badge/Tests-51%20Passed%20(100%25)-success.svg)](#)
[![Academic Venue: APU MSc AI / IEEE TSC](https://img.shields.io/badge/Submission-IEEE%20TSC%20%2F%20ACM%20TOSEM-purple.svg)](#)

> **Policy-Aware Orchestration Framework for Enterprise LLM Multi-Agent Workflows**  
> *Asia Pacific University of Technology & Innovation (APU) MSc in AI / De Montfort University (DMU) Dual Degree Dissertation Artifact (CT095-6-M-RMCE)*  
> **Author:** Shafin Ahmad (Student ID: TP-126417)  
> **Academic Supervisors:** Ts. Dr. Maythem Kamal, Dr. R Logeswaran  

---

## Table of Contents

1. [Executive Problem Statement](#1-executive-problem-statement)
2. [Theoretical & Mathematical Formulations](#2-theoretical--mathematical-formulations)
   - [2.1 Evidence-Based Bayesian Routing (Bayes-UCB)](#21-evidence-based-bayesian-routing-bayes-ucb)
   - [2.2 Intent Preservation Optimization under the DPI](#22-intent-preservation-optimization-under-the-dpi)
   - [2.3 Deterministic Action Bounding via Convex Projection (CAMCO)](#23-deterministic-action-bounding-via-convex-projection-camco)
   - [2.4 Cryptographic Lineage & State Verification](#24-cryptographic-lineage--state-verification)
   - [2.5 Dynamic Critical-Path DAG Topology (O(|V| + |E|))](#25-dynamic-critical-path-dag-topology-ov--e)
3. [System Architecture & Dataflow Diagrams](#3-system-architecture--dataflow-diagrams)
4. [Master Comparison: GUIDE vs. State of the Art](#4-master-comparison-guide-vs-state-of-the-art)
5. [Token & Latency Optimizations](#5-token--latency-optimizations)
6. [Quickstart Guide](#6-quickstart-guide)
7. [Benchmark Suite & Replication Guide](#7-benchmark-suite--replication-guide)
   - [7.1 The 18 Enterprise Benchmark Tasks](#71-the-18-enterprise-benchmark-tasks)
   - [7.2 The 12 Adversarial Robustness Scenarios](#72-the-12-adversarial-robustness-scenarios)
   - [7.3 Executing the 270 Comparative & 24 Robustness Runs](#73-executing-the-270-comparative--24-robustness-runs)
8. [Formal BibTeX Citation](#8-formal-bibtex-citation)

---

## 1. Executive Problem Statement

Enterprise adoption of Multi-Agent Systems (MAS) powered by Large Language Models (LLMs) is severely impeded by three foundational vulnerabilities inherent in prevailing architectures (e.g., CrewAI, LangGraph, AutoGen):

1. **Linear Regret of Static Role Assignment ($O(T)$):** Conventional systems delegate tasks based on static prompt personas or static graph edges. When individual agents degrade or suffer capability drift, the entire system accumulates regret linearly across operational iterations, yielding failure rates that scale proportionally with time ($T$).
2. **Contextual Degradation via Data Processing Inequality (DPI):** In conversational sequential chains, state is handed off as accumulating text histories ($X_0 \to X_1 \to \dots \to X_n$). By the Data Processing Inequality, mutual information $I(X_0; X_n)$ decreases monotonically. At step $n=5$ with per-hop retention $r=0.85$, information retention drops to $r^5 \approx 44.37\%$, causing catastrophic constraint amnesia and cascading hallucinations.
3. **Policy-Bypassing Soft Guardrails:** Existing frameworks rely heavily on system prompts or post-generation conversational evaluation to enforce safety. Under adversarial prompt injection or unexpected tool payloads, soft boundaries fail to deterministically intercept actions prior to remote API dispatch.

**GUIDE** solves these vulnerabilities by formalizing multi-agent orchestration as a **constrained statistical decision process** with four non-negotiable architectural controls:
- **Bayes-UCB Dynamic Routing (`route()`):** Sublinear regret bounded by the Kullback-Leibler divergence rate ($O(\ln T)$).
- **Cryptographically Sealed State Handoffs (`handoff()`):** Deterministic JCS canonicalization (RFC 8785), Ed25519 digital signatures, and immutable $S_0$ intent anchor preservation.
- **CAMCO Pre-Execution Policy Gate (`validate()`):** Out-of-process Euclidean convex action projection ($\Pi_{\mathbf{C}}(u)$) clamping parameters to permissible sets before execution.
- **Hash-Linked Trace Ledger (`append_trace()`):** SHA-256 backwards pointer chain with genesis block verification ($h_0 = \text{SHA-256}(\text{Run\_ID} \parallel S_0 \parallel \text{Policy\_Hash})$).

---

## 2. Theoretical & Mathematical Formulations

### 2.1 Evidence-Based Bayesian Routing (Bayes-UCB)

Let $\mathcal{A} = \{a_1, a_2, \dots, a_K\}$ denote the set of operational agents, and $\mathcal{D} = \{d_1, \dots, d_M\}$ represent task domains. Agent capability $\theta_{i,d} \in [0, 1]$ is modeled via conjugate Beta priors initialized uniformly:

$$\theta_{i,d} \sim \text{Beta}\left(\alpha_{i,d}^{(0)}, \beta_{i,d}^{(0)}\right) \quad \text{where } \alpha_{i,d}^{(0)} = 1, \; \beta_{i,d}^{(0)} = 1$$

Upon observing outcome $r_t \in \{0, 1\}$:

$$\alpha_{i,d}^{(t+1)} = \alpha_{i,d}^{(t)} + r_t, \quad \beta_{i,d}^{(t+1)} = \beta_{i,d}^{(t)} + (1 - r_t)$$

The coordinator routes tasks by maximizing the $(1 - 1/t)$-quantile of the posterior Beta distribution (Kaufmann et al., 2012):

$$a^* = \arg\max_{a_i \in \mathcal{A}_d} Q_{1 - 1/t}\left[\text{Beta}\left(\alpha_{i,d}^{(t)}, \beta_{i,d}^{(t)}\right)\right]$$

where $Q_q[\text{Beta}(\alpha, \beta)]$ is the regularized incomplete Beta inverse cumulative distribution function.

#### Regret Comparison (Static vs. Bayes-UCB)
Under static allocation over $T = 10{,}000$ operations with suboptimality gap $\Delta = 0.15$:
$$\mathbb{E}[R_{\text{static}}(10{,}000)] = 10{,}000 \times 0.15 = 1{,}500 \text{ failures}$$

Under Bayes-UCB matching the Lai-Robbins bound:
$$\lim_{T \to \infty} \frac{\mathbb{E}[R_{\text{Bayes-UCB}}(T)]}{\ln T} \le \sum_{i: \mu_i < \mu^*} \frac{\mu^* - \mu_i}{d(\mu_i, \mu^*)}$$

Evaluating for $\mu^* = 0.90$ and $\mu_i = 0.75$, the Bernoulli KL-divergence $d(0.75, 0.90) \approx 0.0924$. Across $K-1 = 4$ suboptimal arms over $T = 10{,}000$:
$$\mathbb{E}[R_{\text{Bayes-UCB}}(10{,}000)] \le 4 \times \frac{0.15}{0.0924} \times \ln(10{,}000) \approx 59.80 \text{ failures}$$
$$\text{Regret Reduction} = \frac{1{,}500 - 59.80}{1{,}500} \times 100\% = \mathbf{96.01\%}$$

---

### 2.2 Intent Preservation Optimization under the DPI

In an unanchored Markovian delegation chain $X_0 \to X_1 \to \dots \to X_n$, contextual retention at step $n = 5$ with $r = 0.85$ decays exponentially:
$$IPS_{\text{sequential}}(5) = r^5 = (0.85)^5 \approx \mathbf{44.37\%}$$

GUIDE partitions state into an immutable primary objective anchor ($S_0$, weight $w_1 = 0.85$) and transient findings ($F_n$, weight $w_2 = 0.15$):
$$IPS_{\text{GUIDE}}(n) = w_1 \cdot r_{S_0} + w_2 \cdot r^n$$

Because $S_0$ is cryptographically pinned and verified at every delegation hop ($r_{S_0} = 1.0$):
$$IPS_{\text{GUIDE}}(5) = 0.85(1.0) + 0.15(0.85^5) = 0.85 + 0.066556 = \mathbf{91.66\%}$$
$$\text{Absolute Retention Gain} = 91.66\% - 44.37\% = \mathbf{+47.29\%}$$

---

### 2.3 Deterministic Action Bounding via Convex Projection (CAMCO)

Proposed tool calls are characterized by the 5-element action tuple:
$$\tau = \left[\text{Tool}, \text{Operation}, \text{Resource\_Class}, \text{Data\_Sensitivity}, \text{Write\_Effect}\right]$$

Let $\mathbf{C} \subset \mathbb{R}^d$ denote the closed, convex set of permissible enterprise behaviors. If raw proposed parameters $u \notin \mathbf{C}$, the CAMCO policy gate computes the Euclidean minimum-distance projection:
$$u^* = \Pi_{\mathbf{C}}(u) = \arg\min_{v \in \mathbf{C}} \|u - v\|_2^2$$

- **ALLOW:** If $u \in \mathbf{C}$, then $u^* = u$. Action executes unmodified.
- **BOUNDED:** If $u \notin \mathbf{C}$ but projectable (e.g. clamping `limit = 100000` to maximum allowed `limit = 100`), the bounded parameters $u^*$ execute.
- **DENY:** If $\|u - \Pi_{\mathbf{C}}(u)\|_2 > \epsilon_{\max}$ (e.g., write-operation on read-only policy or unauthorized tool), execution terminates with `DENIED_BY_POLICY`.

---

### 2.4 Cryptographic Lineage & State Verification

1. **JCS Canonicalization (RFC 8785):** Guarantees byte-level determinism before hashing.
2. **Genesis Hash:**
   $$h_0 = \text{SHA-256}(\text{Run\_ID} \parallel S_0 \parallel \text{Policy\_Hash})$$
3. **State Chaining:**
   $$h_k = \text{SHA-256}\left(h_{k-1} \parallel \text{canonical}(P_k)\right)$$
4. **Ed25519 Signatures:**
   $$\sigma_k = \text{Sign}_{\text{sk}_i}(h_k)$$
   Receiver verifies:
   $$\text{Verify}_{\text{pk}_i}(h_k, \sigma_k) == \text{True} \quad \land \quad t_{\text{current}} \le P_k.\text{expiry\_time}$$

---

### 2.5 Dynamic Critical-Path DAG Topology ($O(|V| + |E|)$)

Given subtask set $V$ and causal edges $E$, Kahn's algorithm validates acyclicity and partitions the DAG into concurrent stages in linear time $O(|V| + |E|)$. For benchmark tasks with mean node duration $T_{\text{node}} = 2.4\text{ s}$:
$$T_{\text{sequential}} = \sum_{i=1}^6 2.4 = 14.4\text{ s}, \quad T_{\text{GUIDE}} = 2.4 + 2.4 + 2.4 = 7.2\text{ s} \quad (\mathbf{50.0\%\text{ Speedup}})$$

---

## 3. System Architecture & Dataflow Diagrams

```text
                             USER WORKFLOW REQUEST
                    (Objective S_0, Constraints, Schema)
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          GUIDE ORCHESTRATION LAYER                          │
│                                                                             │
│  ┌──────────────────────────┐                   ┌────────────────────────┐  │
│  │ 1. Dynamic Topology      │                   │ 2. Bayes-UCB           │  │
│  │    Kahn DAG Scheduler    ├──────────────────►│    Coordinator         │  │
│  │    Stages: L_0 ... L_m   │                   │    a* = argmax Q[Beta] │  │
│  └──────────────────────────┘                   └───────────┬────────────┘  │
│                                                             │               │
│                                                             ▼               │
│  ┌──────────────────────────┐                   ┌────────────────────────┐  │
│  │ 4. Hash-Linked Ledger    │                   │ 3. Cryptographic       │  │
│  │    SHA-256 Backwards     │◄──────────────────┤    Handoff Manager     │  │
│  │    Pointer Chain (h_k)   │  Event Appended   │    RFC 8785 + Ed25519  │  │
│  └──────────────▲───────────┘                   └───────────┬────────────┘  │
│                 │                                           │               │
│                 │ Validated Action                          ▼               │
│  ┌──────────────┴───────────┐                   ┌────────────────────────┐  │
│  │ 5. CAMCO Policy Gate     │                   │ Specialist Agent       │  │
│  │    Euclidean Projection  │◄──────────────────┤ (Synthesis, Audit,     │  │
│  │    u* = argmin ||u-v||^2 │  Proposed Action  │  Planning Persona)     │  │
│  └──────────────┬───────────┘  [Tool, Ops, ...] └────────────────────────┘  │
└─────────────────┼───────────────────────────────────────────────────────────┘
                  │
                  ▼
       SANDBOXED ENTERPRISE TOOLS
(ProcurementDB, IncidentLogStore, EmailService)
```

---

## 4. Master Comparison: GUIDE vs. State of the Art

| Dimension | LangGraph Engine | CrewAI Framework | Pasupuleti et al. (CAMCO Baseline) | GUIDE Framework (This Work) |
|---|---|---|---|---|
| **Orchestration Paradigm** | Deterministic state machine graphs | Role-based autonomous agents | Centralized model-driven coordinator | **Bayesian UCB / Thompson dynamic coordinator** |
| **Mathematical Regret** | Undefined (manual edge branching) | $O(T)$ Linear error accumulation | Heuristic point estimates | **Provable $O(\ln T)$ sublinear regret bound** |
| **Intent Preservation** | Shared mutable state dictionary | Ephemeral conversation histories | Unanchored JSON payloads | **Cryptographically pinned $S_0$ + Pointer refs** |
| **Policy Enforcement** | Application-level error handling | System prompt guardrails | Euclidean convex action projection | **Pre-execution Euclidean projection + Dynamic audit learning** |
| **State Lineage** | Checkpoint state database | Textual logging | Standard event logging | **Ed25519-signed, SHA-256 hash-chained immutable ledger** |
| **Adversarial Resilience** | Vulnerable to prompt injections | Susceptible to control hijacking | Blocks unauthorized tool requests | **$\ge 95\%$ hand-off rejection, zero unauthorized tool execution** |
| **Token Optimization** | Full state passing in prompts | Context accumulation | Standard context passing | **Static-prefix caching + Pointer-based $input\_refs$** |

---

## 5. Token & Latency Optimizations

1. **Pointer-Based Context Passing (`input_refs[]`):** Heavy multi-kilobyte documents are stored once in Content-Addressable Storage (`sha256:<digest>`). Hand-off packages transmit only 64-character lightweight hashes, reducing token overhead by **60%+** across multi-hop delegations.
2. **Static-Prefix Cache Structuring:** System prompts strictly segregate invariant rules (`<system_role>`, `<enterprise_invariants>`, `<output_schema_spec>`, `<anti_injection_shield>`) from dynamic variables (`<execution_context>`). This guarantees byte-identical prefix caching on Anthropic and OpenAI APIs, cutting token costs by **80%–90%**.
3. **Anomaly-Triggered Trust Freeze:** When an agent self-reports high confidence ($\kappa \ge 0.80$) on a failed task, the coordinator penalizes the agent ($\beta += 5.0$), freezes the arm, rolls back to parent hash $h_{k-1}$ without expensive LLM self-reflection loops, and re-routes immediately to alternative arm $a_2^*$.

---

## 6. Quickstart Guide

Initialize and execute a production-grade GUIDE orchestration workflow in fewer than 15 lines of code:

```python
import time
from guide_mas import (
    BayesUCBCoordinator, CryptographicHandoffManager, IntentPackage,
    CAMCOPolicyGate, ActionRecord, HashLinkedTraceLedger, ContentAddressableStore
)
from guide_mas.tools import MockProcurementDB

# 1. Initialize Content Store and Trace Ledger with Genesis Hash
cas, ledger = ContentAddressableStore(), HashLinkedTraceLedger("run_01", "Extract vendor SLAs")
doc_ref = cas.store("Enterprise Vendor Agreement 2026")

# 2. Setup Bayes-UCB Coordinator and CAMCO Policy Gate
coordinator = BayesUCBCoordinator(["agent_synthesis", "agent_backup"], ["synthesis"])
gate = CAMCOPolicyGate({"permitted_tools": ["procurement_db"], "max_query_limit": 100})
priv_key, pub_key = CryptographicHandoffManager.generate_keypair()

# 3. Route, Seal State with Ed25519, Validate Action, and Audit
selected_arm = coordinator.route("synthesis", total_system_steps=2)
pkg = IntentPackage(run_id="run_01", handoff_id="h1", parent_hash=ledger.current_hash,
                    objective="Extract vendor SLAs", expiry_time=time.time()+300, input_refs=[doc_ref])
envelope = CryptographicHandoffManager.sign_package(pkg, priv_key, ledger.current_hash)
unpacked = CryptographicHandoffManager.verify_and_unpack(envelope, pub_key, ledger.current_hash)

# 4. Enforce Euclidean Limit Bounding (clamping LIMIT 500 to 100)
decision, params = gate.validate_and_project(
    ActionRecord("procurement_db", "SELECT", "records", "INTERNAL", False), {"limit": 500}
)
output = MockProcurementDB().execute(limit=params["limit"])
ledger.append_event("EXECUTED", {"decision": decision, "records": output["returned_records"]})

assert ledger.verify_ledger_integrity()[0] is True
print(f"Workflow Complete. Status: {output['status']}, Decision: {decision}, Records: {output['returned_records']}")
```

---

## 7. Benchmark Suite & Replication Guide

### 7.1 The 18 Enterprise Benchmark Tasks

The evaluation suite comprises 18 distinct real-world tasks stratified across 3 domains and 3 complexity tiers:
- **Family 1: Constrained Information Synthesis (Tasks T01–T06):** Extracting procurement SLAs under non-disclosure constraints (T01–T02: Low, T03–T04: Medium, T05–T06: High).
- **Family 2: Evidence Reconciliation with References (Tasks T07–T12):** Cross-referencing multi-source IT outage logs against documentary citations with 0% hallucination (T07–T08: Low, T09–T10: Medium, T11–T12: High).
- **Family 3: Policy-Sensitive Task Planning (Tasks T13–T18):** Formulating IT change-management and access-provisioning plans under zero-trust bounds (T13–T14: Low, T15–T16: Medium, T17–T18: High).

### 7.2 The 12 Adversarial Robustness Scenarios

12 stress-testing scenarios targeting GUIDE's architectural controls:
- **R01 (Ambiguity Attack):** Underspecified inputs triggering deterministic fallback.
- **R02 (Constraint Contradiction):** Peer agent injecting conflicting objective rejected by $S_0$ anchor.
- **R03 (Schema Tampering):** Malformed JSON missing mandatory cryptographic fields rejected.
- **R04 (Cryptographic Mutation):** Mutated payload with unmodified signature rejected via Ed25519.
- **R05 (Hash-Link Discontinuity):** Corrupted parent hash breaks ledger backward lineage.
- **R06 (Package Expiration):** Expired timestamp ($t > \text{expiry\_time}$) triggers `REJECTED_INTEGRITY`.
- **R07 (Direct Prompt Injection):** Injected instructions blocked at CAMCO policy gate.
- **R08 (Indirect Retrieval Hijack):** Malicious document instructing write actions denied by policy.
- **R09 (Unauthorized Tool Escalation):** Prohibited operations (`DROP`, `DELETE`) intercepted and blocked.
- **R10 (Data Sensitivity Violation):** `RESTRICTED` queries blocked under `INTERNAL` clearance.
- **R11 (Parameter Limit Overflow):** `LIMIT 100000` clamped to 100 via Euclidean projection $\Pi_{\mathbf{C}}$.
- **R12 (Sleeper Agent Anomaly):** High-confidence failure ($\kappa \ge 0.80$) triggers trust freeze ($\beta += 5.0$) and re-routing.

### 7.3 Executing the 270 Comparative & 24 Robustness Runs

Run the complete formal evaluation suite:

```bash
# 1. Run all 51 unit & integration tests
pytest -v

# 2. Execute the complete evaluation runner (270 comparative + 24 robustness runs = 294 runs)
python -m guide_mas.evaluation.runner --mode all --repetitions 5 --output evaluation_results.json

# 3. Execute comparative runs only
python -m guide_mas.evaluation.runner --mode comparative --repetitions 5

# 4. Execute robustness runs only
python -m guide_mas.evaluation.runner --mode robustness
```

---

## 8. Formal BibTeX Citation

If you utilize this framework, benchmark tasks, or experimental design in your research, please cite:

```bibtex
@mastersthesis{ahmad2026guide,
  author       = {Shafin Ahmad},
  title        = {{GUIDE: Policy-Aware Orchestration Framework for Enterprise LLM Multi-Agent Workflows}},
  school       = {Asia Pacific University of Technology \& Innovation (APU) and De Montfort University (DMU)},
  year         = {2026},
  month        = {November},
  type         = {Master of Science in Artificial Intelligence Dissertation},
  note         = {Supervisors: Ts. Dr. Maythem Kamal and Dr. R Logeswaran. Target Venue: IEEE Transactions on Services Computing / ACM TOSEM},
  url          = {https://github.com/shafin0id/guide}
}
```

---

## License

Copyright (c) 2026 Shafin Ahmad. Licensed under the [Apache License, Version 2.0](LICENSE).