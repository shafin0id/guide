# Protocol v9 results (Protocols v9a, v9b, v9c, v9g, exhaustive check)

Auto-generated tables: `experiments/results/v9/summary.md` (script `scripts/v9/analyze.py`). Protocol freezes are git tags
`protocol-v9a-frozen`, `protocol-v9b-frozen`, `protocol-v9c-frozen`, `protocol-v9g-frozen`. Model: DeepSeek-V4.1-Flash
(`deepseek-flash`, non-thinking, temperature 0; the v6 model name was retired, so all conditions were re-run).

## Supervisor items covered

| Item | Evidence | Headline result |
|---|---|---|
| 1, 7 real apps, parallel/branching/cyclic | 15 apps built with LangGraph 1.2.21, CrewAI 1.15.41, AutoGen 0.7.5; 5 topologies each; 720 runs | Compromised-reader attack success 25.6% (23/90) undefended; strict 0/90, cred 0/90, flexI_cred 6/90 (6.7%). Undefended success depends on the topology (6/6 in selector and parallel-task apps, 0/6 in several others). |
| 2, 10 benign utility, trade-off | 4 enforcement variants plus 4 baselines, all 97 AgentDojo tasks, 3 repetitions for GUIDE variants | none 95.9%; strict 62.9% (Slack 28.6%); flexI_cred 78.4% (Slack 66.7%, p=0.0007 vs strict). cred keeps strict's utility and adds containment (full grid 559/588 vs 543/588). flexI_cred containment 522/588 (88.8%). |
| 3 stronger attacks | weak agent; `direct`, `important_instructions`, GUIDE-aware text attack, 5-round LLM adaptive attacker | Undefended attack success is low on this model: direct 9.0%, important_instructions 2.5%, GUIDE-aware 1.0%, adaptive 0/30. GUIDE conditions 0.5-1.0%. Where an undefended baseline exists (direct, real-world relay) the improvement is measurable. A vulnerable model (Gemini) block is scheduled. |
| 4 baselines under identical conditions | tool_filter, spotlighting, repeat_user_prompt, PI detector in the same loop | direct attack: none 9.0%, strict 0.5%, tool_filter 1.0%, pi_detector 1.5%, spotlighting 4.5%, repeat 4.0%. Utility: tool_filter 86.6%, spotlighting 95.9%, pi_detector 57.7%, strict 62.9%, flexI_cred 78.4%. CaMeL not run (see limitations). |
| 5 containment | 949 pairs; full-grid replay per variant | 588 of 949 pairs contain at least one attacker sink call; the other 361 have read-only goals, so nothing to contain. The 45 uncontained (strict): 16 banking `update_password` (no control parameter), 20+1 travel calendar/email (legitimate recipient, attacker content), 5 Slack DM to a listed user, 3 workspace `delete_file` id "13" (substring match). cred closes the 16; 29 remain. |
| 6 theory | exhaustive check, zero API cost | 594,516 influence cases (all DAGs up to 5 steps) with 0 oracle mismatches and 0 monotonicity violations; 1,966,080 gate evaluations (250,880 executed, 1,715,200 denied) with 0 soundness and 0 exactness violations. Valid for the enumerated space only. |
| 8 prediction on unseen tasks | static rule on the 15 held-out apps | 69 attacker sink calls: 0 soundness violations (nothing executed that was predicted blocked); 84.1% agreement; 11 over-approximations (call denied although predicted admissible, because the agent had not performed the lookup). |
| 9 statistics | Wilson CIs, exact McNemar, Cohen's h, 3 repetitions | repetition disagreement per task: 1-2 of 97 tasks per condition. |
| 11, 12 reproducibility | pinned model id, settings, per-row ledger, frozen tags; `scripts/v9/` | `.env` is not committed; `docs/protocols/protocol-v9*.md` list all settings. |

## Limitations to state in the paper
- Attack success is low even undefended on DeepSeek-V4.1-Flash (weak agent, standard attacks). Defence-vs-defence security differences are therefore mostly shown by the `direct` attack (9.0% undefended, n=200) and by the assumed-compromised-reader relay (25.6%, n=90). A more susceptible model is evaluated only in a small Gemini block (free-tier quota).
- Real-world apps are framework-example-style applications with sandboxed tools and author-written tasks, not third-party production systems. The compromised reader is an assumed adversary (the formal model's), not an emergent one.
- Strict and cred cost real utility whenever a legitimate control value comes from a tool output instead of the user's prompt (Slack 28.6%, real-world benign 26.7-30.0%). flexI_cred recovers part of it by admitting identifiers from enumeration tools for internal sinks, at the price of 6/90 relay successes on apps whose attacker target is a listed identifier.
- Content-bearing sinks (calendar event bodies, DMs, emails) are not constrained by control-value provenance; this accounts for most residual uncontained pairs.
- `tool_filter` was re-implemented after the first version was found to be broken (provider ignores tool schemas when `tool_choice=none`); first-version rows are discarded and disclosed. PI-detector inputs are truncated to the model's 512-token window (speed fix). Infrastructure fixes after freeze: YAML sanitising of attacker text, last-message handling, detector truncation.
- Not done: CaMeL/Progent quantitative comparison; static re-mining of third-party repos (clones were deleted; extractor rewrite out of budget); mechanised formal proof.
- Gemini block (v9g, completed): Gemini 3.1 Flash-Lite, default agent, `important_instructions`, 20 pairs, 4 conditions; the Gemini replication was limited to 20 pairs by the free-tier request quota. Attack success: none 15/20, strict 1/20, cred 1/20, flexI_cred 1/20. Utility under attack: 12, 10, 10, 11 of 20. n=20, so intervals are wide; pi_detector and the other baselines were not run on Gemini. Cells left over from the aborted larger plan (v9g-2) are in the same rows file and are not part of the frozen matrix.
