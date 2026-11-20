# Stage 6 — Primary-Source Evidence Matrix for Table 1 (Related-Work Comparison)

Generated: 2026-11-20 UTC  
Verification data: [`version-2/results/offline/reference_verification.json`](../results/offline/reference_verification.json) and primary-source checks (Crossref, arXiv Atom API, SaTML/ICSE proceedings).

---

## 1. Corrections to V1 Manuscript Table 1 (`ISS-034`)

Primary-source inspection revealed **three substantive inaccuracies** in V1 Table 1 plus **three closely related systems** already cited in the manuscript prose that belong in Table 1:

1. **FIDES (`[17]`, `arXiv:2505.23643v2`):** V1 Table 1 wrote `Soundness proof = "Not reported"`. Primary source proves **integrity noninterference** and **explicit secrecy** over its lattice-labeled planner model with selective variable hiding (`HIDE`). Corrected to **`Yes (integrity noninterference & explicit secrecy)`**.
2. **Progent (`[76]`, `arXiv:2504.11703v3`):** V1 Table 1 wrote `Soundness proof = "Not reported"` and `Least-privilege synthesis = "No"`. Primary source uses an LLM to automatically generate task-scoped symbolic policies and an **SMT solver** to verify **monotonic confinement** (blocking non-narrowing updates without approval). Corrected to **`Yes (SMT monotonic confinement)`** and **`Yes (LLM task-policy generation)`** — distinct from GUIDE's deterministic trace-based lattice intersection.
3. **Parisel (`[62]`, `arXiv:2607.09744v1`):** V1 Table 1 wrote `Soundness proof = "No"`. Primary source proves **Proposition A.1 (ultrametric property)** and **Proposition 5.7 (collusion monotonicity)** on its conceptual influence graph $G(\theta)$, while explicitly omitting an executable runtime enforcement proof. Corrected to **`Partial (structural propositions; no runtime enforcement proof)`**.
4. **Omitted Close Comparators Added for V2 Table 1:**
   - **CaMeLoT (`[61]`, `arXiv:2609.18674v1`):** Extends CaMeL with **static pre-execution plan verification** via `nuXmv` against CTL temporal-logic policies (single-agent plan scope, not multi-agent compromised subsets).
   - **SafeFlow (`[19]`, `arXiv:2607.25255`):** Multi-agent semantic information-flow control with taint propagation across dynamic collaboration graphs.
   - **MiniScope (`[113]`, `arXiv:2512.11147v2`):** Automated hierarchical permission discovery and contextual least-privilege authorization (single-agent scope).

---

## 2. Verified Cell-by-Cell Evidence Matrix (V2 Table 1)

| System & Primary Source | Targets Multi-Agent Compromised Subsets | Static Pre-Deployment Bound | Formal Proof / Soundness Scope | Least-Privilege Policy Synthesis | Pre-Deployment Utility/Cost Prediction | Primary-Source Evidence Summary |
|---|---|---|---|---|---|---|
| **CaMeL** `[21]` (Debenedetti et al., IEEE SaTML 2026, DOI `10.1109/satml68715.2026.00040`, `arXiv:2503.18813`) | No (single-agent P-LLM/Q-LLM split) | No (runtime capability enforcement) | Yes (control/data-flow safety proof) | No (manual capability policies) | Not reported | Control/data-flow separation with capability tokens & runtime policy enforcement; evaluated on AgentDojo; no multi-agent workflow graph bound. |
| **CaMeLoT** `[61]` (Nikolaou et al., `arXiv:2609.18674v1`, Sep 2026) | No (single-agent generated plan) | **Yes** (CTL static plan verification via `nuXmv`) | Yes (model-checked temporal safety/liveness) | No (policies supplied in CTL) | Not reported | Translates CaMeL-generated plan into finite-state transition system and model-checks before tool execution; rejects unsafe plans pre-execution. |
| **Progent** `[76]` (Shi et al., `arXiv:2504.11703v3`, Apr 2025) | No (single-agent tool calls) | No (runtime symbolic rule engine) | **Yes** (SMT monotonic confinement of updates) | **Yes** (LLM-generated task policy + SMT update check) | Not reported | Symbolic DSL over tool names/args; LLM generates initial task policy & updates; SMT verifies narrowing; deterministic runtime check. |
| **FIDES** `[17]` (Costa et al., `arXiv:2505.23643v2`, May 2025) | No (single-agent planner) | No (dynamic taint-tracking) | **Yes** (integrity noninterference & explicit secrecy) | No (policy/labels provided) | Not reported | Formal IFC planner model with confidentiality/integrity lattice and `HIDE` primitive; evaluated on AgentDojo. |
| **ARM** `[15]` (Chinaei, `arXiv:2604.04035v1`, Apr 2026) | No (single-agent tool loop) | No (runtime provenance graph) | Not reported | No | Not reported | Runtime provenance graph over tool calls, field provenance, and counterfactual edges for denied actions (prevents causality laundering). |
| **MiniScope** `[113]` (Zhu et al., `arXiv:2512.11147v2`, Dec 2025) | No (single-agent delegate) | No (runtime contextual enforcement) | Not reported | **Yes** (automated permission-hierarchy discovery) | Not reported | Task-centric hierarchical permission discovery & contextual runtime authorization; reduces confirmation prompts. |
| **Parisel** `[62]` (`arXiv:2607.09744v1`, Jul 2026) | Yes (agent influence graph $G(\theta)$) | Partial (pairwise ultrametric blast radius $d(a,b)$) | Partial (Prop. A.1 ultrametric & Prop. 5.7 collusion monotonicity; no executable enforcement proof) | No | Not reported | Conceptual theory of least autonomy over organizational hierarchies; no executable reference monitor or empirical benchmark evaluation. |
| **Muruaga (APC)** `[59]` (`arXiv:2608.15888v1`, Aug 2026) | Yes (multi-agent delegation chain) | No (session-state runtime checks) | Yes (Blast Radius Monotonicity & Composition Soundness) | No | Not reported | Agentic Principal Chain tracks delegated authority & session budgets across principals with 6 runtime authorization checks. |
| **Moon & Varshney** `[56]` (`arXiv:2605.09045v2`, May 2026) | No (single framework boundary, PocketFlow) | No (runtime boundary policy) | Yes (machine-checked Dafny forward-simulation refinement) | No | Not reported | Deductive verification under havoc oracle semantics in Dafny; strongest single-framework mechanization, no multi-agent influence graph. |
| **CAPMAS** `[84]` (Veski et al., `arXiv:2609.06500v1`, Sep 2026) | Yes (multi-agent Macaroon delegation) | No (runtime token attenuation) | Not reported | Partial (contrastive semantic query scoping) | Not reported | Maps natural-language queries to bounded privilege sets and delegates offline Macaroon tokens with monotonic attenuation. |
| **SafeFlow** `[19]` (Dai et al., `arXiv:2607.25255`, Jul 2026) | Yes (dynamic multi-agent collaboration) | No (runtime semantic IFC) | Not reported | No | Not reported | Semantic taint attachment & propagation across dynamic multi-agent collaboration graphs to block fragmented malicious intent. |
| **Paul & Nandy** `[65]` (`arXiv:2609.22949v1`, Sep 2026) | Yes (6-agent threat model, 14 vectors) | No | Not reported | No | Not reported | Empirical taxonomy of 14 multi-agent injection vectors + 4 architectural defenses (signing, provenance, sanitization, role-scoped tools). |
| **Safin et al.** `[73]` (`arXiv:2609.17648v1`, Sep 2026) | Yes (4-agent LangGraph pipeline) | No (runtime signed tokens + oracle) | Not reported | No | Not reported | Empirical ablation of task-bound signed tokens & policy oracle separating Judgment Bypass Rate (100% JBR) from Unsafe Action Rate (0%). |
| **GUIDE (This paper)** | **Yes** (arbitrary compromised subset $A \subseteq V$ on fixed acyclic workflows) | **Yes** (workflow-wide static effect-reachability bound $\text{Reach}(A, J, \tau_{\text{adv}})$) | **Yes** (paper proofs of Thms. 1–2 & Props. 1–4 + bounded exhaustive check; **not** mechanized) | **Yes** (deterministic trace-driven lattice intersection over observed nominal calls) | **Partial** (oracle-trace replay on AgentDojo; static call-admissibility check on 15 held-out apps) | Explicitly qualifies: bound is conditional on complete mediation, accurate `ToolSpec`, acyclic DAG, and trusted monitor; excludes text-only harm & authorized-recipient malicious content. |

---

## 3. Bibliography Verification & Cleanup Audit (`ISS-033`)

All 116 references in `GUIDE_Manuscript_JIDMIS_Final.docx` were programmatically verified on **2026-11-19/20** (`version-2/scripts/stage6_verify_references.py`, `reference_verification.json`):
- **108 / 116** verified directly via Crossref DOI API, arXiv Atom API, PMLR/USENIX/GitHub/HuggingFace primary pages (title similarity $\ge 0.80$, year verified).
- **6 / 116** OpenReview-hosted conference papers (`[2]` TMLR 2026, `[5]` ICLR 2025, `[71]` ICLR 2024, `[82]` COLM 2025, `[100]` ICLR 2025, `[108]` ICLR 2025) verified via OpenAlex + primary web bibliographic records (OpenReview returned bot-challenge HTML to scripted HTTP).
- **1 / 116** classic textbook (`[16]` Cohen, 1988, *Statistical Power Analysis for the Behavioral Sciences*, 2nd ed.).
- **1 / 116 UNVERIFIABLE / DEAD DOI (`[69]`):** Rana, Kubbo, & Jayabalan (2017), *Privacy and Security Challenges Towards Cloud Based Access Control in Electronic Health Records*, DOI `10.36478/ajit.2017.274.281` returned **HTTP 404** on both Crossref and `doi.org`.
- **7 / 116 OFF-TOPIC / CITATION-PADDING ENTRIES TO REMOVE IN V2 (`ISS-033`):**
  1. `[69]` Rana et al. (2017) — Cloud EHR access control (also dead DOI 404).
  2. `[70]` Rashid et al. (2025) — OpenAI API text cryptography/steganography (*Fusion: Practice and Applications*).
  3. `[72]` Safavi, Abdulnabi, Rana, & Alizadeh (2025) — Explainable cybersecurity framework (ASSIC).
  4. `[81]` Tirtadjaja, Rana, & Shanmugam (2021) — Enterprise IT privileged accounts (ICDABI).
  5. `[83]` Tripathy, Mishra, Dash, & Rana (2025/2026) — Cooperative multi-agent knowledge management (Springer LNNS).
  6. `[101]` Yeow, Rana, & Abdul Majid (2024) — GPT-3.5 software requirement engineering (ICETSIS).
  7. `[105]` Zaidi, Salim, & Rana (2026) — Multi-agent deep learning in hybrid renewable energy (TIC).
  All 7 are removed from the V2 manuscript bibliography (reducing the bibliography from 116 to **109 verified, strictly relevant references**).
- **Note on preprint proportion:** Of the 109 retained references, `23` are arXiv preprints (`21.1%`), primarily fast-moving 2025–2026 multi-agent containment/IFC papers (`FIDES`, `Progent`, `MiniScope`, `ARM`, `CaMeLoT`, `Muruaga`, `Parisel`, `Moon & Varshney`, `CAPMAS`, `SafeFlow`, `Paul & Nandy`, `Safin et al.`, `AgentFlow`, `ContainmentBench`, `Narisetty et al.`, etc.); `83` (`76.1%`) are peer-reviewed conference/journal publications or books, and `3` (`2.8%`) are software/model citations (`LangGraph`, `CrewAI`, `ProtectAI DeBERTa`). Note that `[21]` CaMeL (`SaTML 2026`), `[85]` AgentSpec (`ICSE 2026`), `[45]` ACE (`NDSS 2026`), `[80]` SAGA (`NDSS 2026`), `[54]` BlindGuard (`ACL 2026`), `[91]` DataFilter (`SaTML 2026`), and `[92]` AttnTrace (`IEEE S&P 2026`) all cite their verified published proceedings versions!
