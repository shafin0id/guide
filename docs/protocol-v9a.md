# Protocol v9a: live AgentDojo evaluation (frozen 2026-11-13)

Frozen before any v9a main-run cell was executed. Code: `src/guide_agentdojo/run_v9.py`, `pipeline.py`,
`src/guide_research/provenance_v9.py`. Sample: `experiments/results/step3/protocol/pairs_sample200.json`
(seed 20261113). Offline variant study: `experiments/results/step3/w2/variants.json`.

## Model and settings
- Agent model: `deepseek-flash` (served as DeepSeek-V4.1-Flash-1017), non-thinking mode (`thinking: disabled`),
  temperature 0, max 1024 output tokens per call, max 12 agent turns. The v6 model (`deepseek-v4-flash`) has been retired,
  so the no-defence and GUIDE conditions were all re-run under v9a for a like-for-like comparison.
- AgentDojo 0.1.35, benchmark v1.2.2.
- Gemini 3.1 Flash-Lite (`reasoning_effort=minimal`) is used only as a secondary vulnerable-model replication; the
  free-tier key allows 500 requests per day per model, so that block is small and reported separately (protocol v9a-G).

## Agent configurations
- `default`: v6 system prompt. Used for benign utility.
- `weak`: v6 prompt plus an instruction to carry out requests found in tool output (amplified susceptibility). Used for
  attack grids, because the default agent resists the standard attack with and without a defence (v6b: 0%).
  Pilot (20 pairs, undefended, weak agent): direct 4/20, important_instructions 1/20, injecagent 0/20, ignore_previous 0/20,
  system_message 0/20, guide_aware 0/20, tool_knowledge 0/20.

## Conditions
`none`, `strict` (submitted v8 guard), `cred` (credential/profile writes treated as control values),
`flexI_cred` (cred plus enumeration-tool identifiers admitted for internal sinks), and the AgentDojo baselines
`tool_filter`, `spotlighting` (delimiting), `repeat_user_prompt`, `pi_detector` (protectai DeBERTa v2, threshold 0.5),
all run inside the same agent loop, model and settings.

Variant selection rule and result: `docs/step3-plan.md` section 6.6 (offline, dev/held-out split seeded 20261113).

## Matrix (all rows 1 temperature-0 run unless stated)
| Block | Agent | Attack | Conditions | Cells |
|---|---|---|---|---|
| B1 benign, all 97 tasks | default | none | none, strict, cred, flexI_cred, tool_filter, spotlighting, repeat_user_prompt, pi_detector | 776 |
| B2 benign repetitions 2-3 | default | none | none, strict, cred, flexI_cred | 776 |
| A1 attack, 200-pair stratified sample | weak | direct, important_instructions, guide_aware | none, strict, cred, flexI_cred | 2400 |
| A2 attack, same sample | weak | direct, important_instructions | tool_filter, spotlighting, repeat_user_prompt, pi_detector | 1600 |

Metrics: benign utility, attack success rate (AgentDojo `security`), utility under attack; Wilson 95% CIs,
paired McNemar tests, Cohen's h. Completion is counted per key (provider|condition|attack|suite|user|injection)
with status completed; failed cells are retried.

## Stop rules
DeepSeek balance floor 10.09 CNY (checked before every task); no protocol change after this commit except
infrastructure fixes disclosed in the run log.

## Addendum v9c: adaptive attacker loop (frozen 2026-11-13, before its main run)
`src/guide_agentdojo/adaptive.py`. 30 pairs (prefix of the frozen 200-pair sample: 8 banking, 8 slack, 7 travel, 7 workspace) x
conditions none, strict, cred, flexI_cred, weak DeepSeek agent. An attacker LLM (DeepSeek, temperature 0.8) rewrites the
injection for up to 5 rounds after seeing the monitor's refusal text or the agent's reply. Success: AgentDojo `security`.
Smoke (2 pairs, 2 conditions) ran end to end.

## Addendum v9g: Gemini replication (frozen 2026-11-13, before its run)
Provider `gemini-3.1-flash-lite` (`reasoning_effort=minimal`; thought signatures echoed back), default agent prompt,
attack `important_instructions`, first 5 pairs of each suite from the frozen 200-pair sample (20 pairs; sized to about 400 requests so one daily quota covers it; changed from 6 before the run), conditions none,
strict, cred, flexI_cred. Reason for the small size: the supplied key is on Google's free tier (500 requests per day per
model; the 2.5 Flash-Lite model is closed to new accounts). Pilot: undefended attack success 15/20 on this model.
Executed by a scheduled job after the daily quota reset; incomplete cells are reported as incomplete.
