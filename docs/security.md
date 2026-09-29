# Security model

GUIDE is a research prototype. Nothing here is a security certification (proposal §6).

## Trust boundaries

| Principal / content | Trust | Notes |
|---|---|---|
| Task principal (objective S₀, constraints) | trusted | the only source that can authorise *where* side effects land (provenance guard) |
| Policy (`Policy`) and tool metadata (`ToolSpec`) | trusted, operator-authored | the gate reasons only from these |
| Agents (LLM outputs) | **untrusted** | an agent's reasons, self-declared attributes or instructions never create permissions |
| Tool outputs, documents, retrieved data | **untrusted** | may contain injected instructions |
| Hand-off channel | untrusted transport | sealed packages; tampering ⇒ run halts |
| Other agents' messages | untrusted, attributable | signatures prove *who* sent a package, not that it is true |

## Threats → controls → evidence

| Threat | Control | Evidence | Residual risk |
|---|---|---|---|
| Unauthorised tool/operation (incl. injected destructive writes) | rule gate: allow-list, per-step delegation, write/external deny | adversarial A05/A06; integration tests | wrong tool metadata; tools with hidden side effects |
| Restricted data exposure | column-sensitivity bounding (data minimisation before the model sees data) | main + A02/A07 | restricted data from sources without column metadata; model memory of prior runs (none here) |
| Parameter abuse (huge limits) | projection onto numeric bounds | unit tests | bounds must be configured |
| Sink steering by injection (exfiltration) | recipient-domain allow-list (core); provenance guard (research) | A03 (external), A04 (internal mailbox) | paraphrased/encoded destinations; destinations legitimately taken from data |
| Hand-off tampering / replay / misdelivery / spoofing | per-principal Ed25519, hash chain, receiver + expiry checks | integrity suite (10 mutation classes); A08 | key compromise; in-process key storage |
| Compromised peer agent (valid signature, false content) | none cryptographic; downstream gate still limits actions | A07 | content-level manipulation of the deliverable |
| Audit tampering | hash-linked trace with digests (no raw sensitive data) | unit tests | whole-chain rewrite by a host-level attacker (anchor head externally) |
| Model failure / malformed output | bounded repair, fail-closed step failure, optional re-dispatch | A11, A12 sequence, main | repeated malformed output across all agents |
| Tool outage / transient failure | error surfaced to agent; no fabrication | A09, A10 | the agent may still guess (measured: `not_fabricated` checks) |
| Silent evaluation corruption | condition-blind scoring, no provider fallback | regression tests | — |
| Secrets in logs | trace redaction of secret-like keys; provider keys read from env, never logged | unit test | secrets placed in free-text fields |

## Auditability: answering the administrator's questions from a trace

| Question | Where it is answered |
|---|---|
| What did the agents do? | `model.call`, `step.output` (digest), `tool.result` events per step |
| Why did they do it? | the agent's model output (retained in run transcripts); decisions record `rule` + `reason` |
| Which policy allowed it? | `policy.decision` (`rule`, `reason`) + policy digest bound into the genesis hash |
| Which tool executed it? | `tool.result` (`tool`, `operation`, `ok`, data digest) |
| What data did they access? | `policy.decision` args digest, BOUND reason (columns removed), content-store refs in hand-offs |
| What happened on failure? | `model.malformed`, `step.failed`, `handoff.rejected`, `provider.error`, run status |
| Can the action be reversed? | not provided: write effects are denied by default; rollback is future work |
| Can the decision path be verified? | `TraceLedger.verify()`; hand-off link hashes chain across steps |

## Not provided (explicit)

Authentication of human principals, RBAC/multi-tenancy, KMS-backed keys, sandboxing of tool code,
rollback/compensation for write effects, human-in-the-loop escalation, network egress controls, defence
against adaptive attackers who optimise against the provenance guard, rate limiting.

## Reporting vulnerabilities

Open a private security advisory on the repository; do not file public issues for undisclosed vulnerabilities.
