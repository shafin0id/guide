> Historical audit record imported from the separate development workspace. Its paths identify that workspace, and its completion labels are not independent certification. See current-assessment.md for the submitted release.

# Stage 5 — Baseline Fairness, Experimental Hygiene, and Threat-Model Comparison Audit

Generated: 2026-11-20 UTC  
Evidence sources: `version-2/workspace/src/guide_agentdojo/baselines.py`, `pipeline.py`, `run_v9.py`, `version-2/results/reproduction/v9_matrix_audit.json`, `version-2/results/sensitivity/stage5_stats_audit.json`

---

## 1. Summary Verdict on Baseline Comparability

The Protocol v9 baseline comparison (`tool_filter`, `spotlighting`, `repeat_user_prompt`, `pi_detector` vs `none`, `strict`, `cred`, `flexI_cred`) ran inside the same `AgentPipeline` loop with matched task keys, model alias, temperature (`0`), and token/turn budgets. However, **five concrete fairness caveats** must be documented and accounted for in the V2 manuscript:

1. **`pi_detector` 512-token truncation (`ISS-032`):** After protocol freeze, `pi_detector` (DeBERTa-v3 prompt-injection classifier) was truncated to its 512-token window (`max_length=512, truncation=True`) as a runtime fix. Auditing all `2,634` AgentDojo v6b tool-output messages confirms **`157/2,634 (6.0%)` exceed 2,000 characters (~500 tokens)**, with lengths up to **`28,561` characters (~7,140 tokens)**. Injections placed past token 512 (especially in long inbox/drive/calendar listings) are invisible to the truncated classifier, biasing `pi_detector` toward higher ASR and/or asymmetric detection behavior relative to chunked/sliding-window deployment.
2. **`tool_filter` v1 invalidation and v2 re-run:** The initial `tool_filter` implementation (`466` rows across benign/direct/important_instructions) failed because the DeepSeek endpoint ignored tool definitions when `tool_choice="none"`. Re-implementing `tool_filter` (`impl=2`) as a pre-execution LLM call filtering the active tool list resolved the API incompatibility; all `466` broken v1 rows were discarded and all `497` cells (`97 + 200 + 200`) were re-executed cleanly. Notably, `tool_filter` (`impl=2`) achieved **`86.6%` benign utility** (`83.6%` held-out) and **`1.0%` direct ASR (`2/200`)**, which is **statistically indistinguishable in security from `strict` (`1/200`, $p_{\text{Holm}} = 1.00$)** while achieving **+23.7 pp higher benign utility** (`+13.4 pp` on held-out tasks)! The V1 manuscript under-emphasized how strongly `tool_filter` dominated the utility–security trade-off on this live benchmark.
3. **Uninformative `v9c` Adaptive Attacker & Low Undefended ASR (`ISS-032`):**
   - `v9c` (`30` pairs, 5-round LLM adaptive attacker): **`none` scored `0/30` ASR**, so `strict`/`cred`/`flexI_cred` scoring `0/30` provides **zero statistical evidence of defense effectiveness** against adaptive attacks. V2 must classify `v9c` as an **uninformative null test** (not evidence of adaptive resilience!).
   - `v9a` `important_instructions` (`none` `5/200 = 2.5%`) and `guide_aware` (`none` `2/200 = 1.0%`): floor-compressed undefended baselines leave virtually zero statistical power to distinguish defenses.
   - `v9g` Gemini (`n=20` pairs): Gemini 3.1 Flash-Lite was demonstrably vulnerable (`15/20 = 75.0%` undefended -> `1/20 = 5.0%` under GUIDE), **but none of the 4 external baselines (`tool_filter`, `spotlighting`, `repeat_user_prompt`, `pi_detector`) completed the 20-pair Gemini matrix** (aborted at `3–6` rows during `v9g-2`). Consequently, there is **no high-ASR live baseline comparison** against external defenses in the historical dataset.
4. **Absence of Closest Architectural Baselines (`CaMeL`, `Progent`, `FIDES`, `AgentSpec`):** All 4 executed baselines are prompt/classifier/tool-list defenses from AgentDojo rather than capability/information-flow reference monitors (`CaMeL`, `Progent`). Comparing a deterministic provenance monitor primarily against prompt-level heuristics (`spotlighting`, `repeat_user_prompt`) and a truncated classifier (`pi_detector`) leaves the closest architectural competitors unbenchmarked empirically. (Addressed directly in Stage 7B feasibility + offline comparison!)
5. **Control-Boundary Asymmetry in `guide_agentdojo` & `guide_realworld`:** As proven in Stage 4 (`audit/code-theorem-map.md`), both live benchmark adapters configure `RulePolicyEngine` permissively (`allow_write=True`, `allow_external=True`, `RESTRICTED` clearance, all tools) and omit Ed25519 signing/routing. Therefore, live comparisons evaluate **only `ProvenanceGuard`/`DirectoryGuard`** (not the full multi-agent rule-policy + signing + routing stack).

---

## 2. Per-Baseline Verification Matrix

| Baseline | Implementation (`baselines.py` / `pipeline.py`) | Validated? | Benign Utility (Held-out 67 / Pooled 97) | Direct ASR (`n=200`) | Key Fairness Notes |
|---|---|---|---:|---:|---|
| `none` | Unmodified AgentDojo loop | Yes | 94.0% / 95.9% | 9.0% (18/200) | Clean reference; low natural ASR on DeepSeek even with weak prompt |
| `strict` (GUIDE) | `ProvenanceGuard` strict mode (permissive `RulePolicy`) | Yes (`ISS-021` caveats) | 70.1% / 62.9% | 0.5% (1/200) | Admits omitted optional control params & untyped numeric tokens; heavy utility penalty when control values come from tool outputs |
| `cred` (GUIDE) | `strict` + credential-tool gate (`update_password`) | Yes | 68.7% / 62.9% | 1.0% (2/200) | Extra live hit (`slack\|user_task_11\|inj1`) vs `strict` is LLM nondeterminism on admitted Alice recipient |
| `flexI_cred` (GUIDE) | `cred` + `DirectoryGuard` (internal-sink directory allowlist) | Yes (**exploratory**, `ISS-014`) | 80.6% / 78.4% | 0.5% (1/200) | Failed pre-registered `-2 pp` dev containment floor; held-out utility gain vs `strict` is $p = 0.0654$ (n.s.) |
| `tool_filter` (`impl=2`) | Separate pre-execution LLM prompt filtering tool list | Yes (466 v1 rows discarded) | 83.6% / 86.6% | 1.0% (2/200) | Statistically tied with `strict` on Direct ASR ($p_{\text{Holm}}=1.00$), +23.7 pp pooled / +13.4 pp held-out benign utility; adds 1 LLM call per task |
| `spotlighting` | Delimiter/datamarking wrapper around tool outputs | Yes | 95.5% / 95.9% | 4.5% (9/200) | Zero utility loss; significantly weaker than `strict` on Direct ASR ($p_{\text{Holm}}=0.0313$) |
| `repeat_user_prompt` | Appends original user instruction after every tool output | Yes | 92.5% / 94.8% | 4.0% (8/200) | Minimal utility loss; significantly weaker than `strict` on Direct ASR ($p_{\text{Holm}}=0.0469$) |
| `pi_detector` | Local DeBERTa-v3 classifier on tool outputs | **Truncated at 512 tokens (`ISS-032`)** | 59.7% / 57.7% | 1.5% (3/200) | 6.0% of tool messages exceed 512 tokens; severe false-positive utility drop (`57.7%`), statistically tied with `strict` on Direct ASR ($p_{\text{Holm}}=1.00$) |

---

## 3. Implications for Paper Claims

1. **Do NOT claim GUIDE dominates all baselines on live AgentDojo:** On `v9a` direct attack, `tool_filter` achieves statistically indistinguishable ASR (`1.0%` vs `0.5%`, $p_{\text{Holm}}=1.00$) with substantially higher benign utility (`86.6%` vs `62.9%` `strict`, `78.4%` `flexI_cred`). GUIDE's distinct advantage over `tool_filter` is **not** live DeepSeek ASR, but (a) **deterministic, model-free worst-case containment under assumed compromise** (`92.3%–95.1%` vs `tool_filter`'s vulnerability whenever the legitimate task already requires the sink tool, e.g., banking transfers or email/DM tasks) and (b) **static pre-execution effect-reachability bounds**.
2. **Explicitly classify `v9c` adaptive evaluation as uninformative** (because `none` scored `0/30`).
3. **Explicitly disclose `pi_detector`'s 512-token truncation** (`6.0%` of tool outputs truncated, max `28,561` chars) as a threat to internal validity for that baseline.
4. **Explicitly acknowledge the absence of live high-ASR external baseline comparisons** (Gemini `v9g` ran only GUIDE variants vs `none`, `n=20`) and the **absence of live CaMeL/Progent runs** (addressed structurally and offline in Stage 7B).
