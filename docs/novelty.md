# Novelty analysis

Rule applied: a mechanism is "novel" only if no prior work found implements it in substance. Sources
marked ✓ were checked online on 2026-09-29; others are from the submitted literature review.

## 1. Component-by-component

| GUIDE element | Closest prior work | Verdict |
|---|---|---|
| Beta-posterior Bayes-UCB agent routing | Kaufmann, Cappé & Garivier (AISTATS 2012); discounted bandits for drift (Garivier & Moulines, ALT 2011) | Standard algorithm, standard application. Not novel. |
| Confidence-weighted failure penalty ("trust freeze") | none specific; heuristic | Not a contribution: in simulation it helps only in the stationary case and hurts under drift (routing results). |
| Signed, hash-linked hand-off packages | tamper-evident logging (Crosby & Wallach, USENIX Sec 2009); provenance (Cheney et al. 2009); agent-interaction provenance (arXiv:2508.02866 ✓) | Engineering application of known primitives. Not novel. |
| Pre-execution rule gate (allow/bound/deny) | Progent — DSL privilege control over tool calls, deterministic (arXiv:2504.11703 ✓); AgentSpec — runtime enforcement rules (arXiv:2503.18666 ✓); policy projection (Pasupuleti et al., ICAISET 2026) | Not novel. GUIDE's gate is simpler than Progent. |
| Provenance guard (control args must come from trusted content) | CaMeL — capabilities + data-flow policies at tool calls (Debenedetti et al., arXiv:2503.18813 ✓); FIDES — integrity/confidentiality labels propagated through tool calls, enforced before sensitive tools, shipped in Microsoft Agent Framework (Costa et al., arXiv:2505.23643 ✓; Microsoft Agent Framework docs ✓) | **Not novel.** A simplified, heuristic (substring-based) instance of information-flow control that FIDES/CaMeL do more rigorously. |
| Re-dispatch on step failure | standard retry/failover | Not novel. |
| Four controls integrated in one orchestration layer, evaluated with a common protocol and ablations | Proposal §7 claims no study was found doing this; MAS-specific prompt-injection architectures are appearing (arXiv:2609.22949 ✓, Sept 2026 — must be reviewed before any claim) | **Possibly a modest contribution**, only as *evaluated integration*, and only if the final systematic review (proposal §7) still finds no equivalent study. |

## 2. What the evidence actually supports (see docs/experiments.md)

1. On nominal tasks with a capable model, none of the controls improved success or fidelity (null result, practical-significance criterion not met). Their overhead was small (≈3 % median wall time).
2. Under attack and fault conditions, specific controls prevented specific failures, and the ablations show which: the gate for writes and data exposure, signing for in-transit tampering, the provenance guard for in-domain sink steering.
3. Per-principal keys are necessary for attribution (spoofing 0 % → 100 % detected).

That is an empirical systems/DSR contribution. It is suitable for the MSc dissertation. On its own it is **not** a
Q1-level novelty claim.

## 3. Claims removed or weakened

All README v2.4 claims listed in `docs/research-audit.md` §8, plus: "RFC 8785 JCS" (now: canonical JSON with a restricted value domain), "Euclidean convex projection over the action tuple" (now: interval projection for numeric args + subset projection for columns), "provable O(ln T) regret" for this system (now: no guarantee; simulation only), "out-of-process gate" (it is in-process).

## 4. Routes to a defensible research contribution (hypotheses, not claims)

Ordered by expected value/feasibility:

1. **Cross-agent label integrity.** FIDES/CaMeL assume one trusted planner. In a multi-agent pipeline, an intermediate agent that is compromised can *launder* taint: re-emit untrusted content as its own output. Research question: can provenance labels be bound into signed hand-offs so that a downstream gate can prove which fields derive from untrusted data, even when intermediate agents are adversarial? Needs: a formal model, an implementation, evaluation on AgentDojo adapted to multi-agent pipelines, adaptive attacks. Check arXiv:2609.22949 and arXiv:2508.08127 first.
2. **Standard-benchmark evaluation of the integrated controls.** AgentDojo (utility + attack success under injection; supports custom pipelines, arXiv:2406.13352 ✓) and τ-bench (policy-following with pass^k consistency), across ≥3 model families, with ablations. Converts the internal-suite findings into externally comparable evidence.
3. **Integrity-aware routing.** Use hand-off rejections, policy denials and malformed outputs as reward signals; study robust or discounted bandits against adversarial or degrading agents with real LLM agents (not only simulation).
4. **Protocol verification.** Model the hand-off protocol (lineage, expiry, receiver binding, per-principal keys) in ProVerif/Tamarin and prove the stated integrity properties.
