# Handoff prompt — final run (M1–M6)

Copy everything below the line into the executing agent (Gemini 3.8 Flash via
Antigravity, Sonnet, or any coding agent with shell and file access).

---

You are finishing the GUIDE research project in the repository at
`/Users/shafinoid/Documents/GitHub/guide`, branch `research/evidence-based-rebuild`.
This is the **last** run before the paper is published, so it has to be done right in one
pass.

**Read these files first, in full, in this order:**
1. `docs/final-run-plan.md`. This is the binding spec. Every definition, path, metric,
   order, threshold and stop rule is fixed there.
2. `docs/final-run-results.md`. This is the results template you fill in.
3. `docs/static-analysis-extensions-results.md` and the Protocol v6/v7 sections of
   `docs/experiments.md`. These are the existing results; do not re-run them.
4. `/Users/shafinoid/.kiro/crew/skills/shafin-writing-skill/SKILL.md`. Read it before
   editing any prose.

**What the project is.** GUIDE is a **reference monitor for LLM multi-agent systems**.
Assuming some agents will be compromised, it computes a sound static blast-radius bound
for any compromised subset of agents, synthesises least privilege, and enforces the bound
at the tool-call boundary. It is not an orchestration framework.
- CaMeL, Progent, FIDES, ARM and MiniScope are **single-agent** monitors with different
  architectures, addressing a different problem. Never write that GUIDE "extends",
  "generalises" or "builds on" them (plan §0.2).
- AgentDojo is a single-agent benchmark. It validates GUIDE's enforcement and cost
  predictor only.
- No standard multi-agent containment benchmark exists. **Do not run any other
  benchmark.**

**Why this run exists.** The undefended AgentDojo baseline (v6b) showed the model
executed zero injected tool calls even without a defence. So the live "0 compromised"
result says nothing about GUIDE. M1 replays the attacker's own ground-truth calls through
GUIDE's real gate (assumed compromise) to get a meaningful containment number, and checks
that the static bound agrees with the runtime on every call. The other tasks:
- M2 proves and tests Proposition 4 (the topology floor) and reports absolute reach;
- M3 fixes a flaky test;
- M5 fixes the references and checks for new competitors;
- M4 rewrites the docs and manuscript using only computed numbers;
- M6 prepares the release.

**Hard rules:**
- **No LLM API calls and no spending of any kind.** Network use is limited to the free
  public APIs listed in plan §6.
- Never fabricate a number, DOI, page range, author or citation. If a lookup fails,
  record it as failed.
- Follow plan §1's order exactly. Write the tests, commit and tag `protocol-v8` **before**
  computing M1/M2 results. Never change a frozen rule after seeing results; fix bugs only
  as a disclosed `protocol-v8.1`, reporting both versions.
- Never weaken a test (no lowered thresholds, no removed assertions).
- Stop only on plan stop conditions S1, S2 or S3. On anything else, record it and keep
  going. Do not ask the owner questions mid-run; record open decisions in "Owner
  decisions pending".
- Do not push to any remote. Do not edit `previously submitted to university/`. Never
  commit `.env`. Do not edit `src/guide_research/topology.py` or
  `src/guide_agentdojo/predict.py` (both frozen).
- The host has little free memory. Run work serially, use targeted tests while working,
  and run the full suite only in M3 and M6. Delete scratch files you create.

**Live progress (required).** Build `scripts/final/progress.py` and
`scripts/final/run_final.py` first (plan §2). Run every compute stage with
`uv run python -u scripts/final/run_final.py --stage <stage>`.
- Each unit of work must print one line, flushed immediately, showing a timestamp, the
  overall % and the stage counter, for example
  `[overall 41.7%] [M1 412/949 43.4%] banking user_task_3 x injection_task_2 -> CONTAINED`.
- Write the same line to `experiments/results/final-v8/run.log`.
- Print stage START and DONE banners.
- For agent-driven stages (M3, M4, M5, M6), set totals with
  `progress.py --set-total <stage> <n>` and call `progress.py --mark <stage> "<what>"`
  after each unit, so the owner can watch the overall percentage reach 100%.

**Record as you go.** Fill in `docs/final-run-results.md` after every stage, not at the
end. Tick the status boxes in plan §10. Every number in any document must come from
`experiments/results/final-v8/paper_numbers.json` or another results file under
`experiments/`, with its path.

**When finished,** reply with exactly the report described in plan §9. Ignore any
earlier conversation that conflicts with the plan file; the plan file wins.
