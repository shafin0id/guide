# Formal model: static blast-radius bounds for a deterministic multi-agent runtime

Scope: the GUIDE runtime (`src/guide/runtime.py`), gate (`src/guide/policy.py`), provenance guard
(`src/guide_research/provenance.py`) and analyser (`src/guide_research/blast_radius.py`). Every definition below names
the code that implements it. The analyser is tested for agreement with the real gate
(`tests/unit/test_blast_radius.py`, property-based) and was validated on live executions (§7).

## 1. System

A deployment is Σ = ⟨W, A, ρ, R, P, T, m, g⟩.

* **Workflow** W = (S, Dep, r, Tools). S is a finite set of steps. Dep(s) ⊆ S are its dependencies (acyclic),
  r(s) its role, and Tools(s) its delegated tool names. ≺ is the fixed linearisation `Workflow.order()`
  (Kahn's algorithm, ties broken by declaration order). Steps execute sequentially in ≺.
* **Agents** A with roles ρ : A → Roles. Cand(s) = {a ∈ A : ρ(a) = r(s)}.
* **Tool metadata** R (`ToolSpec`). For each tool t:
  * Ops(t), its operations;
  * for each op o: write flag w(t,o), external flag x(t,o), and control parameters CP(t,o);
  * resource class res(t);
  * column sensitivity λ_t : Cols(t) → 𝕃, where 𝕃 = PUBLIC < INTERNAL < CONFIDENTIAL < RESTRICTED;
  * columns parameter cp(t) ∈ Names ∪ {⊥};
  * default sensitivity d(t).
* **Policy** P = ⟨Perm, λ̄, W?, X?, B, D, Rc, CA⟩: permitted operations Perm : Tools ⇀ 2^Ops, clearance λ̄, write/external
  flags, numeric bounds B, recipient domains D, exact recipients Rc, and column allow-lists CA.
* **Trusted corpus** T = `corpus_of({objective, constraints})`: the lower-cased string leaves of the task header,
  joined by newlines. This is exactly the content the runtime passes to observers as TRUSTED (`Runtime.run`). Tool
  results are observed only as UNTRUSTED (`Runtime._execute`).
* **Hand-off mode** m ∈ {transcript, structured, signed}. **Gate** g ∈ {∅, rule, rule+prov_μ}, where μ ∈ {sub, tok}.

**Calls and effects.** A proposed call is c = ⟨t, o, args⟩. The runtime executes a (possibly revised) call ĉ. The
*effect* of executing ĉ at step s is α(ĉ, s) = ⟨s, t, o, ĉ.args, X(ĉ)⟩. X(ĉ) ⊆ Cols(t) is the set of columns the call
can place into an agent context: ĉ.args[cp(t)] if that argument is present and non-empty, otherwise Cols(t)
(`_exposed`). A **sink** effect has w ∨ x.

## 2. Runtime semantics (the facts the proof uses)

* **(R1) Single execution point.** Tool code runs only in `Runtime._execute` (`registry.get(t).invoke`).
* **(R2) Decision function.** With g ≠ ∅, `_execute` first computes δ_g(c, s) = `engine.evaluate(c, PolicyContext(…,
  step_tools))` and executes only when δ ≠ DENY, using the revised call δ.call. With g = ∅, it executes c only if
  t ∈ step_tools and o ∈ Ops(t).
* **(R3) Delegated tools.** step_tools = Tools(s) in transcript and structured modes. In signed mode it is
  `accepted.permitted_tools` from `open_sealed`.
* **(R4) Context.**
  * transcript: header, plus all outputs and tool results of steps before s in ≺.
  * structured and signed: header, plus the outputs of Dep(s). In signed mode these are dereferenced from verified
    content-store references.
  * In every mode, the step's own tool results.
* **(R5) Determinism.** δ_g depends only on (c, Tools(s), P, R, T). It does not depend on the proposing agent, its
  stated reasons, its context or the run history.

## 3. Authority

A *capability* κ = ⟨s, t, o, Φ, C⟩ admits (args, X) iff Φ(args) ∧ (X ⊆ C) (`Capability.admits`).
Let norm(v) = str(v).strip().lower() and dom(v) = the part of str(v) after its last '@', lower-cased.

**Definition 1 (Authority)** Auth_g(s) (`authority`):

* g = ∅: {⟨s, t, o, ⊤, Cols(t)⟩ : t ∈ Tools(s), o ∈ Ops(t)}.
* g = rule: all ⟨s, t, o, Φ, C⟩ with t ∈ Tools(s), o ∈ Perm(t), (w ⇒ W?) and (x ⇒ X?), where:
  * Φ(args) = x ⇒ [(D ≠ ∅ ⇒ dom(args.recipient) ∈ D) ∧ (Rc ≠ ∅ ⇒ norm(args.recipient) ∈ Rc)];
  * if cp(t) ≠ ⊥: C = {c : λ_t(c) ≤ λ̄ ∧ (t ∈ dom CA ⇒ c ∈ CA(t))}, and C must be non-empty;
  * otherwise: C = Cols(t), and d(t) ≤ λ̄ is required.
* g = rule+prov_μ: as for rule, with Φ strengthened for sinks:
  Φ ∧ [(w ∨ x) ⇒ ∀p ∈ CP(t,o) ∀v ∈ elems(args.p): norm(v) = ε ∨ supp_μ(norm(v), T)].
  Here supp_sub(v, T) ⇔ v is a substring of T, and supp_tok(v, T) ⇔ v ∈ Tok(T) (`supported`, `tokens_of`).

**Lemma 1 (Gate correspondence).** For all c and s:

* (a) *Soundness:* if δ_g(c, s) = ĉ ≠ DENY, then some κ ∈ Auth_g(s) with key ⟨s, ĉ.t, ĉ.o⟩ admits (ĉ.args, X(ĉ)).
* (b) *Exactness:* if some κ ∈ Auth_g(s) admits c.args, c is well-formed (known columns, numeric bounded arguments,
  and requested columns intersecting C), then δ_g(c, s) ≠ DENY.

*Proof.* Case analysis over the branches of `RulePolicyEngine.evaluate`, in code order:

1. unknown tool or operation;
2. Perm;
3. delegation (Tools(s));
4. write flag;
5. external flag, domain D, exact list Rc;
6. column bounding (unknown columns ⇒ DENY; otherwise args[cp] := requested ∩ C, DENY if empty) or the d(t) check;
7. numeric clamping.

Each DENY branch corresponds to one failed conjunct of Definition 1, and every non-DENY path satisfies all of them.
Bounding rewrites only args[cp] (to a subset of C, so X(ĉ) ⊆ C) and numeric arguments, which Φ does not mention.
Control parameters and the recipient are never rewritten, so Φ(c.args) = Φ(ĉ.args). For rule+prov, `ProvenanceGuard`
returns the inner DENY unchanged. Otherwise, for sinks, it denies exactly when some element violates supp_μ over T;
by the corpus remark in §1, the guard's trusted text equals T. ∎

Both directions are property-tested against the real gate: 1,500 generated cases per run with a coverage assertion
over every rule (`test_property_auth_is_exact_wrt_real_gate`, `test_property_coverage_is_not_vacuous`).

**Lemma 2 (Delegation integrity).** In every accepted hand-off, step_tools = Tools(s).
*Proof.* Transcript and structured modes use `step.tools` directly (R3). In signed mode, `open_sealed` accepts only if
link_hash = H(parent ‖ canonical(package)) and the claimed sender's Ed25519 signature on link_hash verifies. The
runtime sealed permitted_tools = Tools(s), so accepting a different value requires a forgery (A2). ∎

**Theorem 1 (Step containment).** For every deployment Σ, every behaviour of all agents (including all agents
compromised), and every execution trace τ: every executed call ĉ at step s has α(ĉ, s) admitted by Auth_g(s).
*Proof.* Induction on the number of executed calls in τ. The base case is trivial. Inductive step: by (R1) the next
executed call comes from `_execute` at some step s. By Lemma 2 the tool set used is Tools(s). If g = ∅, execution
requires t ∈ Tools(s) and o ∈ Ops(t), which is Definition 1 for g = ∅. Otherwise ĉ = δ_g(c, s) ≠ DENY, and Lemma 1(a)
applies. Agent behaviour only chooses c, which Lemma 1 quantifies over universally. ∎

Theorem 1 needs no assumption about agents: authority is agent-independent.

## 4. Adversary and influence

**Adversary** 𝒜 = ⟨K, J, τ_adv⟩. It controls:
* every model output of each agent in K ⊆ A (arbitrary strings on every turn);
* the content of results returned by tools in J;
* if τ_adv, the hand-off transport (it may read, modify or drop messages).

Honest agents (A ∖ K) are arbitrary, possibly randomised, functions of their view. No correctness is assumed.

**Assumptions.**
* A1 — Complete mediation: agents cannot invoke tools except by proposing calls to the runtime (R1).
* A2 — Ed25519 is EUF-CMA secure, and private keys are not available to the adversary (they live in the runtime's
  `KeyRing`; agents never hold keys).
* A3 — Honest agents with the same role are interchangeable: same output distribution given the same view. This holds
  in the bench (same model, same persona). It is needed only because router state may be adversary-influenced.
* A4 — Tools satisfy their `ToolSpec`: only operations with w change state, and only state of res(t); only operations
  with x send data out; reads return only the columns in args[cp(t)] when cp(t) ≠ ⊥.
* A5 — The runtime, gate, policy, registry and keyring form the trusted computing base. The analysis covers a single
  run on a fresh environment. Cross-run persistence (shared databases, memory) is out of scope.

**Definition 2 (Influence)** (`influenced`). Infl(𝒜) is the least set closed under:

* **D** (direct): Cand(s) ∩ K ≠ ∅ ⇒ s ∈ Infl. Direct(K) denotes these steps.
* **J** (injection): Tools(s) ∩ J ≠ ∅ ⇒ s ∈ Infl.
* **X** (transport): τ_adv ∧ m ≠ signed ⇒ s ∈ Infl.
* **C** (context): if m = transcript, (∃s′ ≺ s with s′ ∈ Infl) ⇒ s ∈ Infl; otherwise (∃s′ ∈ Dep(s) ∩ Infl) ⇒ s ∈ Infl.
* **St** (state): (∃s′ ≺ s, s′ ∈ Infl, ∃κ ∈ Auth_g(s′) with w(κ) and res(κ) ∈ res(Tools(s))) ⇒ s ∈ Infl.

The rules are monotone, so the least fixpoint exists and is reached in at most |S| rounds.

**Definition 3 (Blast radius).** BR(𝒜) = ⋃_{s ∈ Infl(𝒜)} Auth_g(s) (`blast_radius`).

**Theorem 2 (Soundness of the blast-radius bound).** For every Σ satisfying A1–A5, every adversary 𝒜, and every
execution τ, couple τ with the adversary-free execution τ₀ that uses the same honest randomness. Then:

1. every call executed at a step s ∈ Infl(𝒜) is admitted by BR(𝒜);
2. for every s ∉ Infl(𝒜), either the run halted before s completed in τ, or the executed effects at s in τ equal
   those in τ₀. Equality is exact when the router picks the same candidate, and in distribution otherwise (A3).

Consequently, every effect whose occurrence or arguments depend on the adversary lies in BR(𝒜). The adversary can
remove effects (halting, failing steps), but outside BR(𝒜) it cannot add or change any.

*Proof.* Part 1 follows immediately from Theorem 1 and Definition 3.

Part 2 is by induction over ≺. The hypothesis: for every s′ ≺ s with s′ ∉ Infl, the view and outputs of s′ in τ
equal those in τ₀. Fix s ∉ Infl for which the run in τ did not halt before s completed.

* **Context.** In transcript mode, rule C makes every s′ ≺ s non-influenced, so their outputs and tool results agree
  by hypothesis. In structured and signed modes, rule C gives Dep(s) ∩ Infl = ∅, so the dependency outputs agree.
  The header is task-fixed.
* **Transport.** If τ_adv and m ≠ signed, rule X gives s ∈ Infl, a contradiction. If m = signed, any modification of
  the wire makes `open_sealed` reject (Lemma 2, A2). The run then halts, which the statement allows. So the accepted
  content equals the sealed content, which the runtime built from agreeing inputs.
* **Tool results at s.** For t ∈ Tools(s): t ∉ J (else rule J). By A4, t's state changes only through executed write
  effects on res(t) by earlier steps. Those of non-influenced steps agree by hypothesis. An influenced s′ could write
  res(t) only through a capability in Auth_g(s′) (Theorem 1), but then rule St would give s ∈ Infl, a contradiction.
  So the results agree.
* **Executing agent.** Cand(s) ∩ K = ∅ (else rule D), so the agent is honest. Router state may differ because
  influenced steps update it, but any selected candidate is honest and interchangeable (A3). Re-dispatch is triggered
  only by the step's own view, which agrees.
* **Conclusion.** The view of s agrees, so its proposals agree (exactly or in distribution). δ_g is deterministic
  (R5), so the executed effects agree. ∎

**Corollary 1 (Harm surface).** Eff(τ) ⊆ BR(𝒜) ∪ Eff_{S∖Infl}(τ₀). A deployment whose adversary-free behaviour is
acceptable can therefore be audited before deployment by inspecting BR(𝒜) alone.

**Lemma 3 (Monotonicity).**
* 𝒜 ⊑ 𝒜′ (componentwise ⊆) ⇒ Infl(𝒜) ⊆ Infl(𝒜′) and BR(𝒜) ⊆ BR(𝒜′).
* P ⊑ P′ in the policy lattice ⇒ Auth_g^P(s) ⊆ Auth_g^{P′}(s). The lattice orders Perm, CA, Rc, D and Tools(s) by
  ⊆, and λ̄, the flags and the numeric upper bounds by ≤. For D and Rc, "empty" means unrestricted, i.e. top.

*Proof.* Every rule and every conjunct of Definition 1 is monotone. The first part is property-tested
(`test_property_monotone_in_compromised_set`). ∎

**Proposition 1 (Tightness for direct compromise).** For s ∈ Direct(K), every κ ∈ Auth_g(s) is realisable by an
adversary whose agent is selected for s: propose a well-formed call admitted by κ, which executes by Lemma 1(b).
Hence BR restricted to Direct(K) is exact. On Infl ∖ Direct, BR over-approximates: realising it requires honest
agents to be manipulated.

**Proposition 3 (Refinement monotonicity, protocol-v7c)**. Fix a workflow's step set, mode m, policy P and k. Let
Π′ refine Π (every block of Π′ is a subset of some block of Π — i.e. Π′ reassigns the same steps to a finer-grained
set of agents, splitting one or more of Π's agents into several). Then for every k:

WBR_k(Π′, m, P) ≤ WBR_k(Π, m, P)

where WBR_k is the worst-case blast-radius fraction over every size-k subset of agents (`guide_research.topology.wbr`).

*Proof sketch.* Any k agents under Π′ are each a subset of the steps some single agent of Π would hold (refinement
only ever splits a Π-block, never merges across blocks). The set of steps directly compromised by k agents of Π′ is
therefore contained in the set of steps some k agents of Π could directly compromise. `influenced` (Definition 2)
is the least fixpoint of monotone rules over the compromised set — the same argument as Lemma 3's first part, but
holding the compromised STEP set fixed and varying which AGENT boundary it is viewed through — so Infl and
therefore BR can only shrink or stay the same, never grow, as the agent partition is refined. ∎

Verified by property test (`test_refinement_monotonicity`, protocol-v7c): every (coarse, fine) partition pair
reachable by splitting one block in two, over every real-world config with ≤ 6 steps, k ∈ {1,2}, both TRANSCRIPT and
SIGNED mode, 200 Hypothesis examples — zero counterexamples. See `docs/results/protocol-v7.md` §v7c
for the disclosed caveat that this proposition is about the WORST-CASE FRACTION over a fixed workflow's partition
space; it does not by itself guarantee a lower floor is reachable when every step in a config shares the same
downstream sink (observed in 18 of 19 self-authored configs, which are linear chains with no independent branch to
exploit). WBR is normalised by Sinks* under the same policy, so a least-privilege policy that removes some sinks but not all can leave WBR₁ = 1 while still lowering the absolute reach. Report absolute reach (§4.3) for policy comparisons.

Notation: Π_⊥ is the finest partition (one agent per step); for a step s, Infl_s =
Infl({a_s}) under Π_⊥ (this includes context and state-flow rules); R(s) = the set of
distinct (tool, operation) sinks in ⋃_{t ∈ Infl_s} Auth_g(t); Sinks* is the set of distinct (tool, operation) write/external pairs reachable by any single agent under policy P (`guide_research.topology.total_sinks_star`).

**Proposition 4 (Topology floor).** For a fixed workflow, mode m and policy P with
Sinks* ≠ ∅:
- (a) min over partitions Π of WBR₁(Π) = max_s |R(s)| / |Sinks*|, attained by Π_⊥.
- (b) If m = transcript, then min_Π WBR₁(Π) = 1.
- (c) If m ∈ {structured, signed} and some step r reaches every step that holds a sink
  along `depends_on` edges, then min_Π WBR₁(Π) = 1.
- Corollary: in a sequential chain (each step depends on its predecessor), WBR₁ = 1 under
  every mode and every partition whenever any sink remains. Splitting agents and signing
  hand-offs cannot lower the worst case; only removing sinks from authority (policy or
  delegation) changes the reach.

*Proof.*
- (a) Π_⊥ refines every partition, so Proposition 3 gives WBR₁(Π_⊥) ≤ WBR₁(Π) for all Π.
  Under Π_⊥, the single agents are exactly the steps.
- (b) Let s₀ be the first step in execution order. Rule C in transcript mode makes every
  later step influenced once s₀ is, so Infl_{s₀} = S and R(s₀) = Sinks*.
- (c) Rule C in structured and signed mode propagates along every `depends_on` edge, so
  Infl_r contains every sink-holding step.
∎

## 5. Least-privilege synthesis

Given observed executed nominal calls O = {⟨s, t, o, args⟩} (`synthesize_least_privilege`), define P* and W*:

* Tools*(s) = {t : ⟨s, t, ·, ·⟩ ∈ O};
* Perm*(t) = {o : ⟨·, t, o, ·⟩ ∈ O};
* W? = ∃ observed write; X? = ∃ observed external;
* Rc* = {norm(args.recipient) : external calls}; D* = dom(Rc*);
* CA*(t) = ⋃ X(args) for tools with cp(t) ≠ ⊥;
* λ̄* = max of the observed column sensitivities, and of d(t) for tools without cp;
* upper numeric bounds = the observed maxima (never above P's).

**Proposition 2.** If every call in O is admitted by Auth^P, then:
* (a) every call in O executes under ⟨P*, W*⟩;
* (b) ⟨P*, W*⟩ is the least element of the policy lattice with property (a);
* (c) BR_{P*}(𝒜) ⊆ BR_P(𝒜).

*Proof.* (a) Each conjunct of Definition 1 is satisfied by construction, and Lemma 1(b) turns admission into
execution. (b) Removing any element from any component leaves some observed call unadmitted. (c) Lemma 3. If some
call in O is not admitted by Auth^P, synthesis raises an error: least privilege only removes permissions. ∎

(a) and (b) are tested by removing each permission dimension (`test_least_privilege_permits_all_observed_and_is_minimal`).
Generalisation beyond O is an empirical question (§7).

## 6. Complexity

* Auth_g(s) costs O(Σ_{t∈Tools(s)} |Ops(t)| + |Cols(t)|).
* The fixpoint takes at most |S| rounds of O(|S|²) work, so O(|S|³) in the worst case; it is linear-time per round
  for the DAGs used here.
* Enumerating admissible recipients under substring provenance costs O(|T| · occurrences of "@d" in T).

## 7. Empirical validation (protocol-v3; details in docs/experiments.md)

| Check | Data | Result |
|---|---|---|
| Theorem 1 (step containment) on recorded runs | 1,575 runs (v1/v2 main, adversarial, compromised): 2,051 executed calls | 0 violations |
| Theorem 2(1) on recorded attacks | v2-compromised: 300 executed calls at influenced steps; 55 harmful effects | 0 violations; 55/55 harmful effects predicted |
| Live adaptive attacker, 7 direct attacks + 1 transitive, 5 configurations × 3 reps | 120 runs | 0 soundness violations; 75/75 predicted-blocked runs had no harmful effect; direct tightness 39/39 = 1.00; transitive tightness 0/6 = 0.00 |
| Least privilege, held-out replay | train reps 1–3, test reps 4–5 (44 calls) | 0/44 denied |
| Least privilege, live utility | 18 tasks × 2 reps | 36/36 success, 0 denials |

## 8. Findings produced by the analysis

* **F1 (substring provenance is weak).** Under rule+prov_sub, T15's bound admits 692 distinct recipient strings, e.g.
  board@corp.example, a different mailbox that happens to be a substring of change-board@corp.example. The live
  attacker realised it 3/3. prov_tok and least privilege reduce the bound to exactly one recipient, and both blocked it 3/3.
* **F2 (unbounded column tools).** When a tool has column metadata but no columns parameter, the gate checks only d(t).
  Such a tool can expose RESTRICTED columns under an INTERNAL clearance. No bench tool triggers this, and the analyser
  models it soundly (C = Cols(t)). It is a design gap in the gate.
* **F3 (data arguments are unconstrained).** An exfiltrating body sent to a legitimate recipient (M4) is inside the
  bound, and was realised, under every configuration. The bound makes explicit that control-argument policies cannot
  stop content leakage.
* **F4 (transitive over-approximation).** Infl ∖ Direct was realised in 0/6 runs with this model. The bound is exact
  for direct compromise and conservative beyond it.

## 9. Limits of the guarantee

The guarantee holds only under A1–A5, and only for one run.
* It says nothing about content leakage through data arguments (F3), side channels, denial-feedback inference
  (arXiv:2604.04035), availability, or honest-agent mistakes at non-influenced steps.
* The signed-mode statements hold except with the adversary's (negligible) Ed25519 forgery probability.
* The proof is on paper and checked by tests. A machine-checked proof (e.g. in Lean or Coq over a model of the runtime)
  is future work.
