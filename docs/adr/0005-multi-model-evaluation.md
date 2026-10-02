# ADR-0005: Multi-model evaluation (protocol-v5)

## Context

Protocol v1-v4 evaluated every condition (B1, B2, P, GPLUS and ablations) against exactly one
model family (DeepSeek, served as `deepseek-flash`). `docs/limitations.md` already lists this as
an explicit external-validity threat, and the supervisor's plan named "a 2nd/3rd model family" as
a next step.

## Decision

Re-run the frozen main suite (RQ3) and the assumed-compromise suite (RQ4/H1) against two additional
model families, changing only `--model/--base-url/--key-env` on the existing `guide_bench.run` CLI.
No task, checker, policy, or condition changes. This keeps the comparison exactly what the proposal's
model-invariance principle (§6, §8.2) requires: identical tasks/policies/settings, model swapped as
the only independent variable added.

**Models** (both free-tier, OpenAI-compatible, chosen and pilot-verified 2026-09-30):

| Model | Provider | Why this one | Verified free-tier issue |
|---|---|---|---|
| `openai/gpt-oss-120b` | Groq (`https://api.groq.com/openai/v1`) | Selected after `qwen/qwen3.8-27b` exhausted Groq's 200k TPD cap; does not trip Groq's tool-call guardrail on prompted JSON | 8,000 TPM limit managed via 3-key round-robin rotation and dynamic retry backoff |
| `gemini-3.5-flash-lite` | Google AI Studio, OpenAI-compat shim (`https://generativelanguage.googleapis.com/v1beta/openai`) | High-volume free tier completing 6/6 pilot tasks cleanly; flagship `gemini-3.8-flash` free tier was capped at 20 req/day | Requires `seed: None` (OpenAI-compat shim rejects seed with HTTP 400) |

**Retired / Rejected candidates (with evidence, not guessed):**
* `qwen/qwen3.8-27b` (Groq) -- initially selected, but hit Groq's 200,000 tokens/day cap during the main suite run; abandoned and archived in `experiments/results/v5-main-groq-qwen.abandoned-qwen-tpd-exhausted/`.
* `openai/gpt-oss-20b` (Groq) -- confirmed via direct request replay: Groq's server-side heuristic
  detects GUIDE's prompted `tool_calls` JSON in the assistant text and raises
  `{"code":"tool_use_failed","message":"Tool choice is none, but model called a tool"}`, because GUIDE
  does NOT use the native OpenAI `tools=[...]` parameter (by design -- the policy gate inspects a
  `ProposedCall` parsed from prompted JSON, independent of any native function-calling API; see
  `guide.agent.PROTOCOL`). Changing GUIDE's protocol to use native tool-calling *only for Groq* would
  break model-invariance across conditions and is out of scope. `openai/gpt-oss-120b` did not trigger
  this guardrail in the same test (evidence in `docs/experiments.md` Protocol v5), so this is
  model-specific on Groq's side, not endpoint-wide.
* `gemini-2.5-flash` -- HTTP 404, deprecated for this API key as of 2026-09-30 (Google's own error
  names `gemini-3.8-flash` as the replacement).
* `gemini-3.8-flash` -- works correctly (confirmed: `model_ids` reports it, JSON mode honoured), but
  its free-tier daily quota (20 req/day, measured empirically, see above) is too small to run even the
  pilot in one day. Kept as a documented fallback if `flash-lite`'s quota also proves insufficient.
* `gemini-2.0-flash-lite`, `gemini-2.5-flash-lite` -- both HTTP 404, deprecated for this API key
  (Google's error names `gemini-3.5-flash-lite` as the current replacement).

## Disclosed deviation from strict setting-identity

`ModelSettings.seed` is set to `None` (omitted from the request body) for the Gemini condition only.
Gemini's OpenAI-compatibility layer rejects the `seed` parameter outright
(`HTTP 400 "Unknown name \"seed\": Cannot find field."`, confirmed by direct request replay,
2026-09-30) -- it is not in Google's documented OpenAI-compat parameter table. DeepSeek and Groq both
honour `seed`. This is the ONE settings field that differs across models in protocol-v5, it is
disclosed here and in the manifest for every Gemini run, and it does not touch `temperature`,
`max_tokens`, or `json_mode`, which stay identical across all three model families.

## What stays fixed (the actual model-invariance guarantee)

Tasks, constraints, checkers, policies, conditions (B1/B2/P/GPLUS), `temperature=0.0`,
`max_tokens=4096`, `json_mode=True`, task/condition/repetition randomisation seed (2026), suite
definitions, and scoring code. Only the model, base URL, key, and (Gemini only) the `seed` field
change. Each run's manifest records `model_requested` and the provider-reported `model_ids_observed`,
exactly as for DeepSeek in protocol-v1..v4.

## Consequences

* Free-tier limits are the binding constraint, and they differ in KIND across providers: Groq's
  `qwen/qwen3.8-27b` is limited by output tokens/minute (~1,000 OTPM, measured), so pacing/backoff
  (already built into `OpenAICompatibleProvider`) eventually gets through. Gemini's `-flash-lite` is
  limited by requests/DAY (the flagship `-flash` measured at 20/day; `-flash-lite`'s exact cap is
  unmeasured but materially higher per the pilot), so a run that outpaces the daily quota cannot be
  fixed by retrying -- if it happens mid-suite, the correct response is to resume the next day (the
  runner already supports resume-by-key via `results.jsonl`), not to retry harder. This is a resource
  constraint of the free tier, not a change to the protocol, and it is why a full 360-run main suite per
  model takes materially longer in wall-clock time than the DeepSeek runs did.
* Any model-specific failure (malformed JSON, truncation, refusal) is scored and reported exactly like
  a DeepSeek failure -- no special-casing, no exclusion, per `pref.scientific_integrity`.
* Fair-benchmarking framing for peer review: this is **not** a claim that GUIDE was "tested against
  CrewAI/LangGraph/AutoGen on multiple models." It is the SAME single-framework, four-condition
  ablation (B1/B2/P/GPLUS), repeated with the model held to a different free-tier LLM each time. A21/A1
  in `docs/submission-alignment.md` already withdrew the claim that any third-party framework's code was
  executed; nothing here reopens that. External validity is what changes: "does this null result / this
  containment finding hold for a different model family," which is exactly the open item A16 flagged.
