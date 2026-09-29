# Architecture

GUIDE has three layers with one-way dependencies: **Core ← Research ← Bench**. Core never imports
Research or Bench (checked in CI, `scripts/check_boundaries.py`).

```
src/
  guide/              GUIDE Core — stable, provider-agnostic primitives (public API = guide/__init__.py)
    types.py          ToolCall, ToolResult, Sensitivity, Trust, Usage, ChatMessage
    errors.py         GuideError hierarchy (IntegrityError = proposal REJECTED_INTEGRITY)
    providers.py      ModelProvider protocol; OpenAICompatibleProvider; ScriptedProvider (test double)
    tools.py          ToolSpec/OperationSpec metadata (write effect, external sink, control params,
                      column sensitivity); Tool protocol; ToolRegistry
    policy.py         Policy (declarative) + PolicyEngine protocol + RulePolicyEngine (allow/bound/deny)
    handoff.py        IntentPackage, canonical JSON, ContentStore, KeyRing (per-principal Ed25519), seal/open
    trace.py          TraceLedger (hash-linked, redacting), EventSink protocol, JsonlSink
    routing.py        Router protocol; StaticRouter; BayesUCBRouter (+ optional discount / failure penalty)
    workflow.py       Step, Workflow (DAG, Kahn), TaskSpec
    agent.py          AgentSpec; JSON reply protocol + strict parser
    runtime.py        Runtime + RuntimeConfig: the single orchestration engine
  guide_research/     GUIDE Research — experimental mechanisms under evaluation
    provenance.py     ProvenanceGuard (H1): control arguments of side-effecting calls must be
                      supported by trusted content
  guide_bench/        GUIDE Bench — reproducible evaluation
    env.py            sandbox enterprise tools + fault hooks        tasks.py  18 proposal tasks
    adversarial.py    12 robustness cases                           faults.py model/transport faults
    conditions.py     B1, B2, P, GPLUS, ablations                   scoring.py condition-blind checks
    run.py            randomised, resumable runner + manifest       stats.py  bootstrap, Wilcoxon, Holm
    integrity.py      mutation experiment (H3)                      routing_sim.py bandit simulation (H4)
```

## Execution flow (one run)

```
TaskSpec(objective S0, constraints, output schema, Workflow)
  └─ Runtime.run
       ├─ observers.observe(S0 + constraints, TRUSTED); trace run.start (genesis = H(run_id, S0, policy digest))
       └─ for step in topological order:
            route()         Router.select(domain/role, candidates)                      → trace route
            handoff()       TRANSCRIPT | STRUCTURED | SIGNED:
                              SIGNED: IntentPackage(parent=head, sender, receiver, S0, constraints,
                                      input_refs=CAS refs of dependency outputs, permitted_tools, schema, expiry)
                                      seal (sender's key) → Transport.deliver → open_sealed
                                      (schema, lineage, receiver, link hash, signature, expiry)  → trace
                                      failure ⇒ run halts: rejected_integrity (fail closed)
            agent loop      ≤ max_agent_turns tool turns, ≤ max_repairs re-asks on malformed JSON
              propose call → validate() PolicyEngine.evaluate → ALLOW | BOUND(revised call) | DENY
                           → tool.invoke (exceptions isolated) → observers.observe(result, UNTRUSTED)
                           → trace policy.decision + tool.result (digests, not raw data)
            on step failure: optional re-dispatch to the next-best agent (redispatch_on_failure)
            Router.update(success, self-reported confidence)
       └─ trace run.end; RunRecord(status, final output, calls, usage, trace kinds, trace_intact)
```

## Key contracts

| Contract | Guarantee | Explicit non-guarantee |
|---|---|---|
| `PolicyEngine.evaluate` runs before any tool code | a DENY never reaches the tool; BOUND executes only the revised call | semantic safety of allowed calls |
| Decisions use `ToolSpec` metadata | proposer-declared attributes cannot create permissions | correctness of tool metadata (operator responsibility) |
| `open_sealed` | tampering, spoofed sender, replay at another chain position, misdelivery and expiry are rejected | factual correctness of package content |
| `TraceLedger.verify` | any edit to an event breaks the chain from that event onward | protection against an attacker who rewrites the whole chain (anchor the head externally) |
| Providers | a completion or a `ProviderError`; never a fabricated reply | determinism of hosted models at temperature 0 |

## Extension points (how a user plugs in their own components)

* **Model**: implement `ModelProvider.complete(messages, settings) -> ModelResponse`.
* **Tool**: implement `Tool` with a `ToolSpec`; declare `write_effect`, `external`, `control_params`, and
  column sensitivity so the gate can reason about it.
* **Policy**: implement `PolicyEngine`; compose by wrapping (as `ProvenanceGuard` wraps `RulePolicyEngine`).
* **Routing**: implement `Router`.
* **Observability**: implement `EventSink.emit(TraceEvent)` (e.g. OpenTelemetry exporter).
* **Transport**: implement `Transport.deliver` (e.g. a message queue between processes).
* **Key custody**: subclass `KeyRing` for KMS/HSM-backed signing.

## Known architectural limits (see docs/limitations.md)

Steps execute sequentially (stages are computed but not run concurrently); keys and trace are in-process;
the runtime is synchronous; there is no human-escalation hook yet (a DENY is returned to the agent);
multi-tenancy and RBAC over principals are not modelled beyond per-step tool delegation.
