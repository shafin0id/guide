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
| Signed messages + provenance tracking + privilege-scoped tools per role, evaluated together in a multi-agent system | Paul & Nandy, "Beyond Single-Model Injection", ICML 2026 AIWILD workshop (arXiv:2609.22949 ✓) | **Removes GUIDE's "integration" claim.** |
| Compromised agent contained by structural authorization (signed task-bound tokens + policy oracle) even when its judgment fails; component ablation | Safin et al., IEEE CARS 2026 (arXiv:2609.17648 ✓) | **Removes GUIDE's empirical containment finding as a contribution** (GUIDE's K1–K4 results replicate it). |
| Capability tokens with monotonic privilege reduction across agents (Macaroons) + semantic scoping of privileges | CAPMAS, Veski, Guerraoui & Froelicher (arXiv:2609.06500 ✓); AIP (arXiv:2603.24775 ✓); South et al. (arXiv:2501.09674 ✓) | Delegation/attenuation is covered. |
| Semantic taints propagated through a multi-agent collaboration graph, validated before irreversible actions | SafeFlow (arXiv:2607.25255 ✓); also APPA recoverable IFC (arXiv:2607.24625 ✓), ARM causality laundering (arXiv:2604.04035 ✓) | Multi-agent runtime IFC is covered. |
| Post-exposure containment benchmarks | ContainmentBench (arXiv:2607.23999 ✓); TAMAS (arXiv:2511.05269 ✓) | Measuring containment is covered. |
| Four controls integrated in one orchestration layer, evaluated with a common protocol and ablations | all of the above | **Not novel** (superseded Sept 2026). |

## 1b. Positioned contribution (protocol-v3)

**Static worst-case blast-radius bounding and least-privilege synthesis for deterministic multi-agent runtimes**
(`docs/formal_model.md`, `src/guide_research/blast_radius.py`).

Every work above either enforces at run time or *measures* containment by attacking a running system. The contribution
here computes, **before deployment** and without running any model, a bound BR(K) on every effect a compromised
agent set K can cause (tool, operation, admissible destinations, exposed columns). It covers influence through
context, shared state, injectable tools and the transport. It comes with:

1. a soundness theorem, proved on paper and property-tested against the real gate and runtime: no execution produces
   an adversary-dependent effect outside BR(K);
2. exactness for direct compromise: every predicted effect was realised by a live adaptive attacker (39/39);
3. least-privilege synthesis from nominal traces that is minimal in the policy lattice, provably shrinks BR(K), and
   kept 100 % utility on held-out and live runs;
4. analysis findings, i.e. bugs the bound exposed that testing had not: substring provenance admits 692 recipients
   including a different mailbox (realised 3/3), and data arguments are unconstrained (F1–F4).

**Novelty status (systematic review, 2026-10-01; `docs/lit-review/literature-review.md` §5.5, §7).**
Partial overlap. Parisel, *A Theory of Least Autonomy in AI* (arXiv:2607.09744) gives a static influence
graph over agents with conservative "effective autonomy" reachability and a blast-radius metric, but no
enforcement theorem, runtime, synthesis or evaluation. Muruaga, *Bounded Agents* (arXiv:2608.15888)
proves runtime blast-radius monotonicity along delegation chains and uses the same compromised-model
evaluation as K1–K4. Moon & Varshney, *Containment Verification* (arXiv:2605.09045) mechanise in Dafny
that one framework contains every model output (stronger soundness evidence than ours, but not
parametric in K and without synthesis). Least-privilege synthesis has prior art in MiniScope
(arXiv:2512.11147) and Aethelgard (arXiv:2604.11839), neither claiming lattice minimality. The
contribution is therefore stated as an **extension** of these works: an effect-level, compromise-
parametric bound proved sound against the enforcing gate and runtime, live-validated, with
lattice-minimal synthesis. Agent Audit (arXiv:2603.22853) remains relevant as code-level static
analysis. The IAM-policy analogue is SMT-based reasoning about AWS access policies (Backes et al.,
FMCAD 2018), prior art for the *method family*. Re-run the static-analysis search before submission.

## 2. What the evidence actually supports (see docs/experiments.md)

1. On nominal tasks with a capable model, none of the controls improved success or fidelity (null result, practical-significance criterion not met). Their overhead was small: ≈3 % median wall time, ≈1.5 ms of framework time per run.
2. Under assumed compromise, the ablations attribute containment to specific mechanisms. The rule gate contained restricted-data exposure, external exfiltration and destructive writes. The provenance guard alone contained in-domain sink steering, and it depends on the gate. Signing turned in-transit tampering into a fail-closed halt. The model resisted every textual injection, so injection *resistance* was not measurable.
3. Per-principal keys are necessary for attribution (spoofing detection 0 % → 100 %).
4. Adaptive routing and re-dispatch each removed the degraded-agent failure mode (static assignment 0/20, routing 19/20, both 20/20).

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
