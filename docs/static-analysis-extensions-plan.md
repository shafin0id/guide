# Static-Analysis Extensions Plan (Protocol v7a / v7b / v7c)

Status: **NOT STARTED.** Single source of truth for three static, zero-API-cost
analyses that strengthen GUIDE's multi-agent contribution. Written to be executed
by a different agent (Sonnet) and produce the same outputs the planning agent
would have produced. Every choice that could vary between executors (paths,
function names, metric definitions, tie-breaks, sampling queries, classifier
rules) is fixed here. If something in this file turns out to be impossible as
written, STOP, record why in §8, and choose the closest alternative. Disclose it;
never improvise silently.

Binding rules (`pref.scientific_integrity`): no fabricated numbers; freeze each
protocol in git (tag) before its main run; keep negative and null results; report
every mismatch; never tune a rule after seeing its agreement with the data.

---

## 0. Why these three, and the framing they serve

GUIDE is framed as a **reference monitor for LLM multi-agent systems**: under
assumed compromise it computes a **sound static blast-radius bound** for any
compromised subset of agents, synthesises least privilege, and enforces the bound
at the tool-call boundary. It is not an orchestration framework and does not
compete with LangGraph, CrewAI or AutoGen.

Single-agent tool-call enforcement is a crowded field (CaMeL, Progent, FIDES,
ARM, MiniScope). The less crowded part is the **multi-agent** bound. The three
tasks make that part carry the paper:

| ID | Task | Question it answers | New claim if it works |
|---|---|---|---|
| v7a | Static utility-cost prediction | Can the bound predict, before any run, which benign tasks GUIDE will block? | The bound is a pre-deployment decision tool, not only a proof. |
| v7b | Real-world MAS mining | How large is the blast radius of multi-agent systems people actually publish? | An empirical finding about the field, and external validity for the current self-authored 19-config study. |
| v7c | Blast-radius-minimal agent topology | Which split of steps across agents minimises worst-case blast radius when k agents are compromised? | A design result that only exists for multi-agent systems. |

Execution order: **v7a → v7c → v7b.** v7a and v7c use data already in the repo.
v7b is the largest task and has a network dependency.

Repo facts the executor needs (all verified 2026-10-02):
- Analyser: `src/guide_research/blast_radius.py` provides `SystemModel`, `authority`,
  `influenced`, `blast_radius`, `ValueSet`, `Capability`, `ObservedCall` and
  `synthesize_least_privilege`. Formal definitions and the soundness proof are in
  `docs/formal_model.md`.
- Provenance helpers: `src/guide_research/provenance.py` provides `corpus_of`,
  `supported` and `tokens_of`.
- AgentDojo adapter: `src/guide_agentdojo/` (`specs.py` has `DOJO_TOOL_SECURITY`
  and `build_tool_registry`; `policy.py` has `build_suite_policy`; `pipeline.py`
  has `GuideGplusPipeline`; `bound.py` holds the existing suite audit). It is
  pinned to `agentdojo==0.1.35`, benchmark `v1.2.2`.
- Pipeline trust corpus: the pipeline calls
  `guard.observe(run_id, {"objective": query}, Trust.TRUSTED)` with
  `query = user_task.PROMPT`. The trusted corpus is therefore exactly
  `corpus_of({"objective": PROMPT})`.
- Protocol v6 raw traces live at
  `experiments/results/agentdojo-v6/<suite>/guide-gplus-local/<suite>/<user_task_id>/none/none.json`.
  Each file has the keys `messages`, `utility`, `security` and `user_task_id`. A
  denial appears as a `role=="tool"` message whose `error` starts with
  `DENIED_BY_POLICY (`. Ignore `banking/guide-gplus/`, which holds old smoke
  output.
- Self-authored structural configs: `src/guide_bench/real_world/configs.py`
  (`load_configs()` returns `RealWorldConfig` objects with the fields
  `config_id, domain, pattern, task, agents, policy, registry, nominal_calls`).
  The existing audit is `src/guide_bench/real_world/audit.py`, with results in
  `docs/experiments.md` ("18/19 over-privileged"). Use whatever count
  `load_configs()` actually returns and report it. The audit's own docstring says
  18 and the results table says 19.
- `HandoffMode` has three values: `TRANSCRIPT`, `STRUCTURED` and `SIGNED`. In
  `influenced()`, `STRUCTURED` and `SIGNED` behave identically unless
  `transport_adversary=True`, so this plan compares only `TRANSCRIPT` with
  `SIGNED`.
- Use the project venv (`.venv/bin/python`, `uv run`). The host is memory-tight,
  so run targeted tests only (`uv run pytest tests/unit/<file> -q`), not the full
  suite, except once at the very end.

---

## 1. v7a — Predicting GUIDE's utility cost from the bound (no API)

### 1.1 Idea
Every AgentDojo user task ships a reference solution,
`user_task.ground_truth(pre_environment) -> list[FunctionCall]`. For each benign
task, ask the **static bound** whether every ground-truth call is admissible under
GPLUS: `gate="rule+provenance"`, `provenance_match="substring"`, and the trusted
corpus built from the task prompt alone. If some call is not admissible, predict
that GUIDE will block the task. Then compare the predictions with what actually
happened in the v6 traces.

### 1.2 Predictor (FROZEN definition, do not change after §1.4 step 3)
For suite `s` in `["banking","slack","travel","workspace"]` and every
`user_task` in `get_suite("v1.2.2", s).user_tasks`:
1. `env = suite.load_and_inject_default_environment({})`;
   `gt = user_task.ground_truth(env)`. If this raises, record
   `predict_status="gt_error"` with the exception text, and exclude the task from
   the metrics but count it.
2. `registry = build_tool_registry(suite.tools)`;
   `policy = build_suite_policy(s, suite.tools)`.
3. Build a single-step model **directly with the dataclass constructor**, not with
   `SystemModel.for_task`. `for_task` adds a `constraints` key to the corpus,
   which the pipeline does not do.
   ```python
   step = Step(step_id="agent-step", role="agent", instruction="", tools=tuple(f.name for f in suite.tools))
   model = SystemModel(workflow=Workflow((step,)), agents=(AgentSpec("agent-1","agent","agent"),),
                       policy=policy, registry=registry,
                       trusted_corpus=corpus_of({"objective": user_task.PROMPT}),
                       mode=HandoffMode.SIGNED, gate="rule+provenance", provenance_match="substring")
   caps = {(c.tool, c.operation): c for c in authority(model, step)}
   ```
   Match the `Step`, `Workflow` and `AgentSpec` constructor signatures to
   `src/guide/workflow.py` and `src/guide/agent.py`. The existing
   `src/guide_agentdojo/bound.py` shows working usage.
4. Each call `fc` in `gt` is **blocked** if `(fc.function, fc.function)` is not in
   `caps`, or if `not caps[key].admits(dict(fc.args))`. Record the first blocking
   parameter and its value (for a missing capability, record the parameter as
   `missing_capability`).
5. `predicted_block = any(call blocked)`.

Only the bound's own admissibility (`Capability.admits`) decides. No heuristics
and no model calls.

### 1.3 Observed outcomes (from the v6 traces)
For each benign trace, record three things:
- `observed_denial`: whether any tool message has an `error` starting with
  `DENIED_BY_POLICY`;
- `observed_utility`: the trace's `utility` value;
- `denied_calls`: a list of (function, rule, first 120 characters of the error).

Check that you found exactly 97 benign traces (16, 21, 20 and 40 per suite). If
any trace is missing, report it and do not substitute anything for it.

### 1.4 Steps
1. Write `src/guide_agentdojo/predict.py` with
   `predict_suite(suite_name) -> list[dict]`, `load_observed(results_dir, suite_name) -> dict[task_id, dict]`
   and `main()`. `main()` writes:
   - `experiments/results/predict-utility-v7a/predictions.jsonl`, one row per
     task: `suite, user_task_id, predict_status, predicted_block, blocking_function, blocking_param, blocking_value, observed_denial, observed_utility, denied_calls, mismatch_class`;
   - `summary.json`;
   - `summary.md`.
2. Write `tests/unit/test_predict_utility.py`, which tests the predictor only, not
   agreement with the data:
   - (a) a banking ground-truth call whose recipient IBAN is in the prompt is
     admitted;
   - (b) a call whose recipient appears only in environment data is blocked;
   - (c) the corpus equals `corpus_of({"objective": PROMPT})`.

   Run the tests until they pass.
3. **Freeze**: commit the predictor and its tests, then
   `git tag protocol-v7a`. Only after the tag, run `main()` against the v6 data.
4. Compute the metrics in §1.5. After the tag, do not change the predictor. If a
   bug is found, fix it as `protocol-v7a.1`, report both versions' numbers, and
   disclose the fix.

### 1.5 Metrics (all pre-registered)
- A confusion matrix of `predicted_block` against `observed_denial`, per suite and
  overall, with precision, recall and accuracy. Add a Wilson 95% interval for
  accuracy (reuse `guide_bench.stats` if it has a Wilson helper; otherwise
  implement Wilson in `predict.py`).
- A confusion matrix of `predicted_block` against `not observed_utility`.
- The predicted utility ceiling per suite, `1 - mean(predicted_block)`, next to
  the observed v6 benign utility.
- `mismatch_class`. Assign exactly one class per task:
  - `agree_block`: predicted block, observed denial;
  - `agree_pass`: no predicted block, no observed denial;
  - `fp_model_detoured`: predicted block, no denial, because the model found a
    different path;
  - `fn_offpath_call`: no predicted block, but a denial occurred on a call that
    is not in the ground truth;
  - `fn_onpath`: no predicted block, but a denial occurred on a ground-truth call.
    This indicates a bound/runtime disagreement, and every instance must be
    investigated and explained, because it bears on the soundness claim.

  Separately, flag `model_error` for tasks with no denial and
  `observed_utility == False`. These are model failures, not a GUIDE cost.
- **Optional, only if `experiments/results/agentdojo-v6b-undefended/` exists and
  its completeness has been verified.** Define the GUIDE-attributable loss as
  tasks that succeed undefended and fail defended. Report how well
  `predicted_block` predicts that loss. If the folder does not exist, write
  "pending v6b" and stop there.

### 1.6 Honest framing to carry into the results
The predictor was specified after the v6 data existed but before agreement was
computed. It is frozen by `protocol-v7a`, and it only uses the bound's own
admissibility check. State this plainly ("post-hoc analysis with a rule fixed
before evaluation"). Ground truth is one solution path, so false positives caused
by model detours are expected and must be reported, not hidden.

---

## 2. v7c — Blast-radius-minimal agent topology (no API)

### 2.1 Idea
Keep each configuration's steps and nominal calls fixed. Vary three things:
1. which agent runs which steps (a set partition of the steps; one partition
   block = one agent);
2. the hand-off mode (`TRANSCRIPT` or `SIGNED`);
3. the policy (the config's nominal policy, or `synthesize_least_privilege` from
   its `nominal_calls`).

Minimise the worst-case blast radius when k agents are compromised, and trace the
frontier of agent count against blast radius.

### 2.2 Definitions (FROZEN)
- For config `c`, let `Sinks*(c)` be the set of distinct `(tool, operation)`
  pairs with `write_effect or external` in the union of `authority` over all
  steps under the nominal policy and the original structure. Configs with
  `|Sinks*| = 0` are excluded from the ratios and counted.
- `D(BR)` is the set of distinct `(tool, operation)` pairs in `BR.sinks`.
- **Worst-case blast-radius fraction**:
  `WBR_k(c, P, mode, pol) = max over agent sets K, |K| = k, of |D(blast_radius(model, K))| / |Sinks*(c)|`.
  Compute it for `k = 1` and `k = 2`, the latter only when the partition has at
  least 2 blocks.
- **Model construction for partition P**: block `i` gets the role `r{i}` and the
  agent `AgentSpec(f"a{i}", f"r{i}", "")`. Each step keeps its id, tools,
  instruction and `depends_on`, and its `role` is set to its block's role (use
  `dataclasses.replace`). Use `gate="rule"`, matching the existing audit's
  `_model`, and `transport_adversary=False`.
- Least-privilege policy: `synthesize_least_privilege(model_original, [ObservedCall(*nc) for nc in cfg.nominal_calls])`.
  Use both its `.policy` and its `.workflow`, whose per-step tool delegation is
  trimmed. Re-apply the partition roles to `.workflow`'s steps.
- **Enumeration**: all set partitions of the step list, generated in canonical
  restricted-growth-string order. When several partitions tie, report the
  lexicographically smallest restricted growth string. If a config has more than
  10 steps (Bell(10) = 115,975), record that it was skipped. Do not sample.
- **Frontier**: for each block count `m = 1..n_steps`, record
  `min WBR_k over partitions with m blocks`, the argmin's restricted growth
  string, and the number of partitions that tie. Do this per (mode, policy).

### 2.3 Proposition to verify, and how
**Refinement monotonicity**: if partition `P'` refines `P`, then for fixed mode,
policy and k, `WBR_k(P') <= WBR_k(P)`.

Proof sketch: any k agents of `P'` cover steps that are contained in the steps
covered by some k agents of `P`. The direct steps are therefore a subset, and
`influenced` is a least fixpoint of monotone rules, so `Infl` and `BR` are subsets
too.

Steps:
1. Write a property test that checks the inequality on every (config, refining
   pair) reachable by splitting one block in two, for all partitions of configs
   with at most 6 steps.
2. If any counterexample appears, record it in full. It would mean the model
   or the proof sketch is wrong, which matters for the paper. Do not drop it.
3. Add the proposition and its proof to `docs/formal_model.md` as a new numbered
   proposition, marked "verified by property test (protocol-v7c)".

### 2.4 Pre-registered descriptive questions (answer each from the data)
- **Q1 (transcript wash-out):** under `TRANSCRIPT`, how much does the best
  partition reduce `WBR_1` compared with the original structure? The hypothesis is
  "little": in transcript mode, compromising one agent influences every later step.
- **Q2 (least agents for the floor):** under `SIGNED` with the least-privilege
  policy, what is the smallest `m` that reaches the per-config minimum `WBR_1`, and
  how does it compare with `n_steps`?
- **Q3 (irreducible floor):** for which configs does no partition, mode or policy
  push `WBR_1` below a positive floor? Identify the cause from the `reasons` in
  `blast_radius`: a state flow through a shared `resource_class`, or a single step
  that holds several sinks.
- **Q4 (decomposition):** report the median `WBR_1` across configs for four
  conditions:
  - (i) original structure, nominal policy, `TRANSCRIPT`;
  - (ii) least-privilege policy only;
  - (iii) least-privilege policy plus `SIGNED`;
  - (iv) least-privilege policy plus `SIGNED` plus the best partition.

  This attributes the reduction to policy, hand-off mode and topology, in that
  order.

### 2.5 Steps and outputs
1. Write `src/guide_research/topology.py`: `set_partitions(n)`,
   `apply_partition(model, rgs)`, `wbr(model, k)`, and
   `frontier(cfg, mode, pol, k)`. Research layer rule: Core must not import it.
2. Write `src/guide_bench/real_world/topology_audit.py`, whose `main()` writes
   `experiments/results/topology-v7c/{frontier.jsonl, summary.json, summary.md}`.
3. Write `tests/unit/test_topology.py`. It must cover partition counts against
   Bell numbers for n = 1..6, the refinement-monotonicity property (§2.3),
   reproduction of the original BR when the partition is the identity, and
   determinism of the tie-break.
4. Commit, `git tag protocol-v7c`, run, and answer Q1 to Q4 in `summary.md`.
5. **Optional extension**: after v7b is complete, re-run `topology_audit` on the
   v7b mined configs whose steps have at most 10 steps. They have no nominal
   calls, so only the nominal-policy rows apply. Report this separately.

---

## 3. v7b — Blast radius of real-world published multi-agent systems (no LLM, network: GitHub)

### 3.1 Safety rules (non-negotiable)
- **Never execute, import or `pip install` mined code.** Parse it with Python
  `ast` and YAML only. This is untrusted third-party code.
- Clone with `git clone --depth 1` into `experiments/mining/_clones/`. Add that
  path to `.gitignore` before the first clone. Delete each clone after its
  extraction. Store only structural metadata, the repo URL and the commit SHA.
  Never commit mined source code.
- Public data only. The paper reports aggregates. Per-repo rows go to
  supplementary data with the URL and SHA, and no repo is singled out in the
  text.

### 3.2 Sampling frame (FROZEN)
- GitHub REST `GET https://api.github.com/search/repositories?q=<Q>&sort=stars&order=desc&per_page=100&page=<p>`.
  Unauthenticated access works (10 search requests per minute). If the user has
  run `gh auth login`, `gh api` may be used instead with the same query.
  - `Q_crewai    = crewai in:name,description,readme language:Python fork:false archived:false pushed:>=2025-04-01`
  - `Q_langgraph = langgraph in:name,description,readme language:Python fork:false archived:false pushed:>=2025-04-01`
  - `Q_autogen   = autogen in:name,description,readme language:Python fork:false archived:false pushed:>=2025-04-01`
- Fetch pages 1 and 2, giving up to 200 results per framework. Save each raw API
  response to `experiments/mining/search_snapshot_<framework>_p<n>.json`, together
  with the UTC timestamp. That snapshot defines the sample.
- **Exclusion rules**, applied in this order, with each exclusion logged and its
  reason recorded:
  1. the owner is `crewAIInc`, `joaomdmoura`, `langchain-ai`, `microsoft` or
     `ag2ai` (the framework's own repositories);
  2. the repo name matches `(?i)(awesome|course|curriculum|roadmap|interview|paper|list)`;
  3. the repo is a duplicate across frameworks (keep it under the framework query
     where it ranked highest);
  4. the clone fails or the repo is over 200 MB.
- **Inclusion** after extraction: the repo yields at least one config with **2 or
  more agents and at least 1 tool bound to an agent**.
- Walk each framework's ranked list in star order until **40 repos are included**,
  or the 200 results run out. Take at most **3 configs per repo**: the first 3 in
  sorted file-path order, then source order.
- **Pilot, outside the frame**: before freezing the protocol, develop the
  extractor on 3 repos per framework taken from rank 201 onwards (page 3). Pilot
  repos are never part of the sample.
- Report the PRISMA-style funnel per framework: retrieved, excluded by each rule,
  cloned, parsed, included, and the number of configs.

### 3.3 Extraction (static, per framework)
Each config is recorded as
`{framework, repo, sha, file, agents:[{name, role, tools:[tool_id]}], steps:[{id, agent, tools, depends_on}], process, unresolved:[...]}`.
- **CrewAI**:
  - In Python, read `Agent(role=..., tools=[...])`, `Task(description=..., agent=<var>, tools=[...], context=[...])`
    and `Crew(agents=[...], tasks=[...], process=Process.sequential|hierarchical)`.
  - In YAML, read `config/agents.yaml` and `config/tasks.yaml` together with
    `@agent` / `@task` / `@crew` decorated methods in a `@CrewBase` class.
  - Steps are the tasks in list order. A step's tools are its agent's tools plus
    its task's tools. `depends_on` is the task's `context`, or the previous task
    for sequential crews.
  - For hierarchical crews, prepend a `manager` step with no tools that every
    task depends on.
- **LangGraph**:
  - Read `StateGraph(...)`, `.add_node(name, fn_or_agent)`, `.add_edge(a, b)`,
    `.add_conditional_edges(src, fn, mapping_or_list)`, `ToolNode([...])`,
    `create_react_agent(model, tools=[...])` and `<llm>.bind_tools([...])` inside
    a node function defined in the same file.
  - Steps are nodes other than `START`/`END`. `depends_on` is the set of incoming
    edges; conditional edges contribute every listed target.
  - Tools at a node come from `ToolNode` or a react agent, or from `bind_tools`
    when they can be resolved in the same module. Anything else goes into
    `unresolved`.
  - Each node counts as one agent.
- **AutoGen** (0.2 and 0.4+):
  - Read `AssistantAgent(name, ..., tools=[...])`,
    `register_function(f, caller=A, executor=B)` and `UserProxyAgent(..., code_execution_config=<not False>)`.
    In the last case, add a tool `code_executor` to that agent.
  - Read `GroupChat(agents=[...])`, `RoundRobinGroupChat([...])`,
    `SelectorGroupChat([...])` and `Swarm([...])`.
  - Steps are the agents in list order, and each step depends on the previous one.
- **Resolution**: resolve names within the same file, plus one level of imports
  from the same repo. Anything unresolved is listed in `unresolved`, never
  guessed. Report the share of configs with any unresolved item.

### 3.4 Tool classification (FROZEN, one rule set for every repo)
Order of precedence:
1. **Known-tool table** (exact class or function name):
   - external and write: `PythonREPLTool`, `PythonREPL`, `ShellTool`,
     `CodeInterpreterTool`, `code_executor`, `E2BCodeInterpreter`,
     `GmailSendMessage`, `SlackSendMessage`, `SendEmail*`;
   - write: `FileWriterTool`, `WriteFileTool`, `FileManagementToolkit`,
     `QuerySQLDataBaseTool`, `SQLDatabaseToolkit`, `GithubToolkit`;
   - read: `SerperDevTool`, `TavilySearchResults`, `TavilySearch`,
     `DuckDuckGoSearchRun`, `WebsiteSearchTool`, `ScrapeWebsiteTool`,
     `FileReadTool`, `DirectoryReadTool`, `WikipediaQueryRun`, `ArxivQueryRun`,
     `YahooFinanceNewsTool`.
2. **Keyword rule** for every other tool. Split the tool name (snake_case and
   camelCase) plus the first line of its docstring, if it can be resolved
   statically, into lowercase tokens.
   - External if any token is in
     `{send, email, mail, slack, tweet, publish, notify, webhook, sms, share, upload, post}`.
   - Otherwise write if any token is in
     `{write, save, create, update, delete, remove, insert, commit, execute, exec, run, deploy, modify, edit, move, rename, append, drop, push}`.
   - Otherwise read.
   Record the token that triggered the classification.
3. Web search and scraping count as read, which undercounts search-query
   exfiltration channels. All counts are therefore a **lower bound**. State this.

Build the registry as one `ToolSpec` per tool id, with one operation whose name
is the tool id, its `write_effect` and `external` flags from the classification,
no control parameters, and `resource_class = tool id`. With `resource_class` set
to the tool id, a state flow only occurs when two agents share the same tool.
The policy permits everything, and `gate="none"`, because that is how these
systems are deployed.

### 3.5 Metrics (pre-registered)
Primary mode is `TRANSCRIPT`, because all three frameworks share accumulated
messages or state by default. The counterfactual is `STRUCTURED`, scoped to the
dependency edges, and shows what scoped hand-offs would buy.

- **M1**: the share of configs where some single compromised agent's blast radius
  contains at least one sink.
- **M2 (cross-agent reach, the multi-agent-specific finding)**: the share of
  configs where some agent **with zero sinks of its own** reaches at least one
  sink through propagation.
- **M3**: `WBR_1`, as defined in §2.2 but on the mined config. Report the median
  and the interquartile range (IQR), excluding configs with no sinks and
  reporting their count.
- **M4**: M1 to M3 under `STRUCTURED`, and the change from `TRANSCRIPT`.
- **M5**: the share of configs with a code-execution tool (`code_executor`, a
  REPL or a shell tool).
- **Amplification**: per agent, `|D(BR({A}))| / max(1, own sinks)`. Report the
  median.

Report every metric per framework and pooled. Give proportions with Wilson 95%
intervals. Compare frameworks descriptively only; if a significance test is
used, it must be Fisher's exact test, Holm-corrected.

### 3.6 Extraction validation
Use `random.Random(7)` to select 10% of the included configs (at least 10). For
each one, re-read its source files and check the agents, the tools per agent, the
edges and the classification of each tool. Record the share that is structurally
exact, and the per-field error counts, in `experiments/mining/validation.md`.

If structural accuracy is below 90%, fix the extractor as `protocol-v7b.1`,
re-run everything, and report the accuracy of both versions. Never fix the
extractor silently.

### 3.7 Steps and outputs
1. Write `src/guide_bench/mining/{search.py, extract_crewai.py, extract_langgraph.py, extract_autogen.py, classify.py, to_model.py, audit.py}`,
   plus tests in `tests/unit/test_mining_*.py`. The tests must use small inline
   source strings written for the tests, never cloned code.
2. Run the pilot (§3.2) to debug the extractor. Then commit,
   `git tag protocol-v7b`, and only after the tag fetch the frozen snapshot and
   run the extraction.
3. Write the outputs to
   `experiments/mining/{funnel.json, configs.jsonl, results.jsonl, summary.json, summary.md, validation.md}`.
4. Clean up `experiments/mining/_clones/` and confirm that it is empty.

---

## 4. Reporting back (all three tasks)

Do **not** edit `docs/paper/manuscript-draft.md`. Do the following:
0. Create **`docs/static-analysis-extensions-results.md`**, a new standalone
   results record and the single place a reader can audit all three tasks. Keep
   this plan file as the spec, and only tick its §8 status boxes. Fill in the
   results file as each task completes, not at the end. It must contain:
   - per task: the git tag and commit, run date, exact commands run, input data
     paths, output file paths, final tables, answers to the pre-registered
     questions, every mismatch class with counts, and every deviation with its
     reason;
   - a "Soundness-critical items" section listing every v7a `fn_onpath` case,
     every v7c monotonicity counterexample and the v7b extraction accuracy (write
     "none found" explicitly when a list is empty);
   - a "What this can and cannot claim" section copied from §7, then updated
     with any limits found during the run;
   - a test-suite line: command, pass/fail counts, and date.
   Every number in it must trace to a file under `experiments/results/` or
   `experiments/mining/`. Never write a number that has no source file.
1. Add a `## Protocol v7: static-analysis extensions` section to `docs/experiments.md`
   with subsections v7a, v7c and v7b. Each subsection contains its tag and commit,
   its table, its pre-registered questions answered, every deviation, and every
   mismatch class with counts.
2. Add rows A31 (v7a), A32 (v7c) and A33 (v7b) to `docs/submission-alignment.md`,
   saying what was added beyond the submitted proposal and why.
3. Update §8 of this file with the final status, the actual run dates and every
   deviation.
4. Run the full test suite once at the end and report the pass count. The
   previous count was 104.
5. Reply with three short tables, one per task, then a list of any `fn_onpath`
   cases (v7a), any monotonicity counterexamples (v7c) and the extraction accuracy
   (v7b). These are the soundness-critical items.

## 5. Stop conditions
- v7a: stop if fewer than 97 benign traces are found; report the gap, never
  substitute.
- v7c: stop and report if the monotonicity test finds a counterexample before
  computing any frontier. The analysis can continue only after the user decides.
- v7b: stop if the GitHub API is unreachable or rate-limited for more than 30
  minutes, or if fewer than 15 configs are included for any framework after 200
  results. Report what was obtained; do not widen the queries without
  disclosing it.
- Any task: if the memory posture becomes critical, pause, run nothing in
  parallel, and resume serially.

## 6. Effort estimate (no API cost)
- v7a: about 2 to 3 hours.
- v7c: about 3 to 4 hours, with seconds to minutes of compute.
- v7b: about 1 to 2 days. The extractor is most of the work, and the network time
  is small.

## 7. What each result can and cannot claim
- v7a supports "the static bound predicts which benign AgentDojo tasks the
  enforcing runtime will block, with accuracy X". It is AgentDojo-specific, uses a
  single solution path, and is post-hoc with a frozen rule.
- v7c supports design guidance for this analyser's model and these configs. It
  does not claim optimality for real frameworks' runtime semantics.
- v7b gives a lower bound on reachable sinks under a stated static model of
  public repos. It is not a claim about each framework's own security, and not
  about production deployments the study cannot see.

## 8. Status log (executor updates in place)
- [x] v7a predictor + tests, tag `protocol-v7a` (commit fd8acff)
- [x] v7a results + mismatch analysis (overall accuracy 0.928, 0 fn_onpath cases)
- [x] v7c topology + monotonicity test, tag `protocol-v7c` (commit 49d3bdc, 0 counterexamples)
- [x] v7c frontier + Q1–Q4
- [x] v7b pilot, tag `protocol-v7b` (commit 234b7ce; pilot found + fixed a real
      extractor gap on 9 rank-201+ repos before tagging)
- [x] v7b snapshot, extraction, validation, metrics (commits 6e946bc, 34be9a8
      for two disclosed pre-main-run fixes; §5 stop condition triggered for
      langgraph n=1 and autogen n=0 — reported, queries NOT widened)
- [x] `docs/experiments.md` + `docs/submission-alignment.md` updated (Protocol v7
      section added to experiments.md; rows A31/A32/A33 added to submission-alignment.md;
      Proposition 3 added to docs/formal_model.md with its property-test citation)
- [ ] Full test suite passed (count: ___)
- Deviations:
  - v7c: all 19 real-world configs turned out to be **strictly linear dependency chains**
    (every step depends only on its immediate predecessor — the "branch"/"hierarchical"
    labels describe the framework idiom reproduced, not an actual DAG with independent
    branches). Consequence: WBR_1 = 1.0 for 18/19 configs under EVERY condition tested,
    including least-privilege + SIGNED + best partition (the one exception, `sql-01`,
    has zero write/external operations at all under its least-privilege policy, so its
    floor is 0.0 for a different reason — no sinks exist, not a topology/mode effect).
    Root cause confirmed structurally (not a code bug): under Definition 2 rule C, a
    linear chain's downstream steps are always `influenced` by an upstream compromise
    via the dependency edge itself, in BOTH transcript and signed mode (signed hand-off
    blocks transport tampering, not a legitimately-produced malicious hand-off from a
    compromised but honest-protocol upstream agent). This is disclosed in full in
    `docs/static-analysis-extensions-results.md` and is itself a negative result worth
    reporting, not a defect to hide (`pref.scientific_integrity`). It sharpens Q1–Q4: the
    floor in this config set is set by chain length and sink placement, not by partition
    count, because there is no actual branch point to exploit. This was not anticipated
    when §2 was frozen, but no definition or metric was changed after seeing the data —
    only the §2.4 narrative framing is affected, not the frozen computation.
  - v7b: §5 stop condition triggered for langgraph (1 included repo of 90 candidates)
    and autogen (0 of 70) — well below the 15-config floor. Per §5, queries were NOT
    widened; the shortfall is reported as a genuine finding about the sampling frame
    (spot-checked: top "autogen"-matching repos mention AutoGen but do not construct
    a GroupChat/Swarm; langgraph's candidate pool was heavily depleted by
    duplicate-across-frameworks exclusions). crewai reached 21 of the 40-repo target
    (36 configs). One mined LangGraph config was genuinely cyclic (a real
    retry/revision loop) — GUIDE's DAG-based formal model cannot score it; excluded
    with a disclosed count, not silently mishandled. Two pre-main-run fixes applied
    (a filesystem race in file-walking; the cyclic-workflow handling), both before any
    metrics existed. Extraction validation: 100% (10/10) structurally exact. Two
    further classifier undercounts ("add", "writer" vs. frozen "insert", "write"
    tokens) found but NOT fixed, since the rule set is frozen — disclosed only, per
    `docs/static-analysis-extensions-results.md`.

---

## 9. Handoff prompt (copy below this line into the executing agent)

You are executing three static-analysis tasks in the GUIDE research repository at
`/Users/shafinoid/Documents/GitHub/guide`. They require **no LLM API calls**. Read
`docs/static-analysis-extensions-plan.md` in full first. It is the binding
specification, and every definition, path, tie-break, query and classifier rule
in it is frozen. Execute in the order v7a, v7c, v7b.

For each task, write its tests, commit, create its git tag
(`protocol-v7a` / `-v7c` / `-v7b`), and only then run the main analysis. Never
change a frozen rule after seeing results; fix bugs only as a disclosed `.1`
version.

Never execute, import or install code mined from GitHub; parse it with `ast` and
YAML only. Do not push to any remote. Do not edit the manuscript.

The host is memory-tight, so run targeted tests and serial work only. Do not
fabricate or estimate any number. Report gaps, failures and counterexamples
plainly; they matter more than clean tables.

Record everything in the new file `docs/static-analysis-extensions-results.md`
(see §4.0), and update it after each task, not only at the end. When done, also
update `docs/experiments.md`, `docs/submission-alignment.md` and §8 of the plan.
Then reply with the summary described in §4.5 of the plan.

Ignore any earlier conversation in this thread that conflicts with the plan file.
The plan file wins.
