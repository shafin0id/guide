"""Build extraction.csv for every included record (protocol §5.7-5.8).

All includes get keyword-assisted codes from title+abstract (`extraction_basis=auto-keyword`). The core
set (closest to SQ2/SQ3; feeds Table 1 and the novelty decision) is coded by hand after reading the
abstract and, where marked, the full text (`extraction_basis=manual-abstract|manual-fulltext`). Manual
codes override auto codes. Quality (0-10) is scored only for the core set; 0 on an item means "not
evidenced in what was read", not "absent".
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

D = Path(__file__).resolve().parent.parent / "data"
OUT = D.parent

MECH = [("formal-verification", r"formal verif|model check|dafny|theorem|provabl|calculus|smt|z3|ltl|ctl\b"),
        ("static-analysis", r"static analys|dependency graph|attack graph|taint-style|bill of materials"),
        ("ifc", r"information[- ]flow|taint|label propagat|data[- ]flow"),
        ("access-control", r"access control|privilege|least[- ]privilege|permission|capabilit|authori[sz]|delegat.*token|macaroon|rbac|abac"),
        ("policy-gate", r"policy enforcement|runtime enforcement|reference monitor|policy engine|guardrail|firewall|gate"),
        ("sandbox", r"sandbox|isolation|isolat"),
        ("monitor-guard", r"monitor|anomal|detect"),
        ("provenance-audit", r"provenance|audit|traceab|tamper|signed|signature|attest|ledger"),
        ("routing", r"rout|orchestrat|delegat|hand-?off|task allocation|topolog"),
        ("training-defense", r"fine-tun|post-train|alignment train|reinforcement learning|rl\b"),
        ("benchmark", r"benchmark|evaluation framework|test suite|dataset"),
        ("attack", r"attack|exploit|red[- ]team|jailbreak|poison|hijack")]
THREAT = [("injection", r"inject"), ("compromised-agent", r"compromis|malicious agent|byzantine|faulty agent|insider"),
          ("tampering", r"tamper|forg|spoof"), ("memory-poisoning", r"memory poison|memory injection|poisoned memor"),
          ("tool-poisoning", r"tool poison|malicious tool|rug pull|skill")]
CTRL = [("routing", r"rout|orchestrat|delegat|task allocation"), ("handoff", r"hand-?off|message passing|inter-agent messag"),
        ("gate", r"policy|gate|enforce|authori[sz]|guard"), ("trace", r"trace|log|audit"),
        ("provenance", r"provenance|taint|information[- ]flow|label"), ("static-bound", r"static|pre-?deploy|before deploy|formal verif|blast radius|reachab")]

# Manual codes for the core set. Fields: mechanism, threat, controls, sq, static_bound, sound_wrt_runtime,
# k_parametric, synthesis, eval, models, n_runs, artefact, key_result, limitation, implication, quality, basis
M = {
 "R1153": ("static-analysis", "compromised-agent", "static-bound", "SQ3", "partial", "no", "per-agent reachability", "no",
           "none", "-", "illustrative example", "no", "Influence graph over write-read and A2A meetings; effective autonomy = actions of all reachable agents; compositional blast-radius metric; collusion predicate",
           "Explicitly no enforcement or noninterference theorem; no runtime; no empirical evaluation; no synthesis",
           "Closest conceptual prior art for static multi-agent reachability: GUIDE must cite and differentiate (effect-level BR(K) with runtime soundness + synthesis + live validation)", "2", "manual-fulltext"),
 "R1572": ("access-control", "injection;compromised-agent", "gate;trace;routing", "SQ1;SQ2;SQ3", "partial", "yes (paper proof; not mechanised)", "delegation depth", "no",
           "live-llm", "Claude Sonnet 4.6; Claude Haiku 4.5", "3,154 instances", "yes", "Blast Radius Monotonicity across delegation chains and Composition Soundness proved; compromised-model eval injects ground-truth attack call after first legitimate call: AgentDojo exfiltration 75-100% -> 0%",
           "Runtime budget/scope model, not a pre-deployment effect bound; proofs not machine-checked; one model family",
           "Same compromised-model method as GUIDE K1-K4: GUIDE's assumed-compromise protocol is not novel; position BR(K) as static and effect-level", "9", "manual-fulltext"),
 "R1622": ("formal-verification", "compromised-agent", "gate;static-bound", "SQ3", "partial", "yes (Dafny-mechanised refinement)", "all model outputs (havoc oracle)", "no",
           "none", "-", "verification case study (PocketFlow)", "unclear", "Containment layer verified to enforce boundary policy for every typed action the model can emit",
           "Single minimalist framework; not parametric in a subset K; no multi-agent influence; no synthesis",
           "Stronger soundness evidence than GUIDE's paper proof + property tests: state this as a GUIDE limitation", "4", "manual-abstract"),
 "R1242": ("formal-verification", "injection", "gate;provenance;static-bound", "SQ3", "partial", "yes (plan executed by CaMeL interpreter)", "no", "no",
           "live-llm", "n/c", "n/c", "n/c", "Generated plan translated to a transition system and model-checked against CTL policies (nuXmv) before any tool call",
           "Per-plan, per-query check; not a deployment-time bound over compromise sets",
           "Cite as plan-level static verification; contrasts with GUIDE's configuration-level bound", "5", "manual-abstract"),
 "R1222": ("static-analysis", "injection", "static-bound", "SQ3", "partial", "no", "no", "no", "none", "-", "5,399 agent programs",
           "n/c", "Agent Dependency Graph recovered from agent source code; 238 prompt-to-tool taint risks found",
           "Code-level dependency analysis; no compromise model; no runtime soundness", "Complementary: GUIDE analyses the policy+workflow configuration, not source code", "4", "manual-abstract"),
 "R0976": ("static-analysis", "injection", "static-bound", "SQ3", "partial", "no", "no", "no", "none", "-", "22 samples", "yes (pip)",
           "Dataflow + credential + config + privilege-risk checks on agent code; 40/42 vulnerabilities, 6 FP", "Small benchmark; no soundness",
           "Already cited in novelty.md as closest; keep", "4", "manual-abstract"),
 "R0799": ("static-analysis", "injection", "static-bound", "SQ3", "partial", "no", "attack-graph", "no", "none", "-", "2 case studies", "n/c",
           "MulVAL logic-based attack graphs for AI-agent applications", "Attack-graph reachability is not tied to an enforcing runtime",
           "Method-family prior art (attack graphs) for pre-deployment reachability", "3", "manual-abstract"),
 "R1162": ("static-analysis", "injection", "static-bound", "SQ3", "partial", "no", "no", "no", "none", "-", "1 case study", "n/c",
           "Asset-based impact + attack trees; quantifies how sandboxing and least privilege limit blast radius", "Risk assessment, no guarantee",
           "Shows 'blast radius' is used informally in the field", "2", "manual-abstract"),
 "R0756": ("benchmark", "injection", "gate", "SQ4", "no", "-", "-", "no", "live-llm", "n/c", "AgentDojo + 5 defenses", "yes",
           "Measures open privilege left by defenses (Progent, CaMeL, AC4A, ...): cannot be derived from ASR or utility",
           "Measurement, not a bound", "Supports GUIDE's sink-capability metric; cite in Discussion", "6", "manual-abstract"),
 "R0918": ("access-control", "injection", "gate", "SQ1", "no", "-", "-", "yes (permission hierarchies)", "simulated", "n/c", "synthetic dataset, 10 apps", "n/c",
           "Automatic least-privilege enforcement from reconstructed permission hierarchies; 1-6% latency overhead",
           "Single-agent tool calling", "Prior art for automatic least privilege: GUIDE's synthesis must be positioned against it", "5", "manual-abstract"),
 "R1183": ("access-control", "injection", "gate;trace", "SQ1", "no", "-", "-", "yes (learned from audit logs, PPO)", "live-llm", "n/c", "n/c", "n/c",
           "Learns minimum viable capability set per task type from audit logs", "Learned policy, no minimality guarantee",
           "Closest prior art to trace-driven least-privilege synthesis", "4", "manual-abstract"),
 "R1263": ("training-defense", "none", "gate", "SQ1;SQ4", "no", "-", "-", "envelopes predefined", "live-llm", "4B model", "n/c", "n/c",
           "Post-training teaches task-conditioned authority; excess-privilege scored against sufficient-authority envelopes",
           "Model-side, not an enforcement bound", "Related to least-privilege envelopes", "4", "manual-abstract"),
 "R0712": ("access-control", "compromised-agent;memory-poisoning;injection", "gate;handoff", "SQ2", "no", "-", "-", "no", "live-llm", "n/c", "3 seeds x 60 tasks", "n/c",
           "Compromised low-privilege agent reaches execution in every undefended trial; signed task-bound tokens + policy oracle: 100% judgment bypass but 0% unsafe actions; component ablation",
           "Single 4-agent LangGraph pipeline", "Removes GUIDE's containment finding as a contribution (A22); cite as replication target", "7", "manual-abstract"),
 "R0716": ("access-control", "injection;compromised-agent", "gate;handoff;provenance", "SQ1;SQ2", "no", "-", "-", "no", "live-llm", "n/c", "14 vectors x 6-agent system", "n/c",
           "67% of agents vulnerable to >=1 scope violation with prompt guardrails; defense architecture with signed messages, provenance tracking, privilege-scoped tools",
           "Workshop paper; single system", "Removes GUIDE's four-control integration claim (A22)", "5", "manual-abstract"),
 "R2511": ("access-control", "compromised-agent", "gate;handoff", "SQ1", "no", "-", "-", "semantic scoping (learned)", "live-llm", "n/c", "n/c", "n/c",
           "Contrastive semantic scoping to bounded privilege sets + Macaroon tokens with monotonic privilege reduction", "Learned scoping; no static bound",
           "Delegation/attenuation is covered prior art", "4", "manual-abstract"),
 "R1179": ("ifc", "compromised-agent;injection", "provenance;gate", "SQ1;SQ2", "no", "-", "-", "no", "live-llm", "n/c", "n/c", "n/c",
           "Semantic taints propagated through the collaboration graph; workflow-level validation before irreversible actions",
           "Runtime; semantic (model-judged) taints", "Multi-agent runtime IFC is covered prior art", "4", "manual-abstract"),
 "R1266": ("benchmark", "injection", "trace;gate", "SQ2;SQ4", "no", "-", "-", "no", "live-llm", "Qwen2.5-7B-Instruct", "17,640 records (7 conditions x 5 seeds)", "yes",
           "Stage-scoped containment metrics; no committed violation under taint-only or intent-ledger enforcement, but traces differ in 73.5% of pairs",
           "One main model", "Post-exposure containment measurement is covered prior art", "8", "manual-abstract"),
 "R2103": ("benchmark", "injection;compromised-agent", "-", "SQ2;SQ4", "no", "-", "-", "no", "live-llm", "10 backbone LLMs", "300 adversarial + 100 harmless", "n/c",
           "Multi-agent adversarial benchmark, six attack types, 211 tools", "Benchmark only", "Candidate external benchmark for future work", "6", "manual-abstract"),
 "R0751": ("ifc", "injection", "gate;provenance", "SQ1", "no", "-", "-", "no", "live-llm", "n/c", "AgentDojo", "yes",
           "Control/data-flow separation + capabilities; 77% of AgentDojo tasks with provable security vs 84% undefended", "Single trusted planner",
           "GUIDE's provenance guard is a weaker, heuristic instance", "7", "manual-abstract"),
 "R1169": ("ifc", "injection", "gate;provenance", "SQ1", "no", "-", "-", "no", "live-llm", "n/c", "AgentDojo", "yes",
           "Formal model of planners; confidentiality/integrity labels enforced deterministically", "Single planner", "As CaMeL", "7", "manual-abstract"),
 "R0748": ("access-control", "injection", "gate", "SQ1", "no", "-", "-", "LLM-generated policies", "live-llm", "n/c", "AgentDojo; ASB", "yes",
           "Symbolic privilege rules over tool names/args checked deterministically; LLM generates and updates policy", "Policy quality depends on the LLM",
           "GUIDE's gate is simpler than Progent", "7", "manual-abstract"),
 "R2095": ("policy-gate", "none", "gate", "SQ1", "no", "-", "-", "no", "live-llm", "n/c", "multiple domains", "n/c",
           "DSL of triggers/predicates/enforcement; prevents >90% unsafe executions (code agents)", "Rule authoring burden", "Runtime rule-gate prior art", "5", "manual-abstract"),
 "R1267": ("formal-verification", "injection", "provenance", "SQ3", "partial", "yes (calculus semantics)", "no", "no", "none", "-", "-", "n/c",
           "Lambda calculus with conversations and dynamic IFC labels; provenance defences provably sound", "Calculus-level, not a deployment tool",
           "Formal foundation to cite beside FIDES/CaMeL", "3", "manual-abstract"),
 "R2557": ("benchmark", "none", "handoff;trace", "SQ4", "no", "-", "-", "no", "live-llm", "32B open model; gpt-4.1-mini", "626 episodes", "n/c",
           "Policy-relevant facts attenuated at hand-off: 0% single-loop, 56% fixed pipeline, 85% orchestrator-subagent (32B); 3-6% for a stronger model",
           "Finance domain only", "Direct evidence for RQ1's hand-off problem; capability-dependence mirrors GUIDE's ceiling vs Groq gap", "6", "manual-abstract"),
 "R0242": ("handoff-integrity", "none", "handoff", "SQ1", "no", "-", "-", "no", "live-llm", "n/c", "n/c", "n/c",
           "Hand-off artefacts collapse boundary metadata (rules) while keeping facts", "n/c", "Supports structured hand-off design", "3", "manual-abstract"),
 "R2541": ("policy-gate", "none", "gate", "SQ4", "no", "-", "-", "no", "live-llm", "n/c", "15 + 20 + 40 runs, pre-registered", "n/c",
           "Pre-registered ablation of a verifier+deterministic acceptance stage; exact tests, Holm correction", "Offensive-security domain",
           "Methodological exemplar for pre-registration and ablation reporting", "7", "manual-abstract"),
}

COLS = ["id", "citation_key", "title", "year", "venue", "doi", "arxiv", "peer_reviewed", "mechanism", "threat",
        "controls", "sq", "static_bound", "sound_wrt_runtime", "k_parametric", "synthesis", "eval", "models",
        "n_runs", "artefact", "key_result", "limitation", "design_implication_for_GUIDE", "quality_score",
        "extraction_basis"]


def codes(text: str, table) -> str:
    return ";".join(k for k, p in table if re.search(p, text, re.I))


def key(r: dict) -> str:
    first = (r.get("authors") or "anon").split(";")[0].strip().split(" ")[-1].lower()
    word = re.sub(r"[^a-z]", "", (r["title"].split(":")[0].split(" ")[0] or "x").lower())
    return f"{re.sub(r'[^a-z]', '', first) or 'anon'}{r.get('year') or ''}{word}"


def main() -> None:
    scr = {r["id"]: r for r in csv.DictReader((OUT / "screening.csv").open())}
    recs = {json.loads(l)["id"]: json.loads(l) for l in (D / "records.jsonl").open()}
    for x in json.load((D / "snowball_screened_input.json").open()):
        recs[x["sid"]] = x
    rows = []
    for rid, s in scr.items():
        if s["decision"] != "include":
            continue
        r = recs[rid]
        text = f"{r['title']} {r.get('abstract') or ''}"
        venue = r.get("venue") or ""
        pr = "no" if (not venue or "arxiv" in venue.lower() or venue.lower() in ("openreview", "ssrn")) else "yes"
        row = {c: "" for c in COLS}
        row.update(id=rid, citation_key=key(r), title=r["title"], year=r.get("year"), venue=venue,
                   doi=r.get("doi", ""), arxiv=r.get("arxiv", ""), peer_reviewed=pr,
                   mechanism=codes(text, MECH) or "other", threat=codes(text, THREAT) or "none",
                   controls=codes(text, CTRL), eval="live-llm" if re.search(r"gpt|claude|llama|qwen|gemini|we evaluate|experiment", text, re.I) else "unclear",
                   extraction_basis="auto-keyword")
        if rid in M:
            v = M[rid]
            row.update(dict(zip(["mechanism", "threat", "controls", "sq", "static_bound", "sound_wrt_runtime",
                                 "k_parametric", "synthesis", "eval", "models", "n_runs", "artefact", "key_result",
                                 "limitation", "design_implication_for_GUIDE", "quality_score", "extraction_basis"], v)))
        rows.append(row)
    with (OUT / "extraction.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    print(f"extracted={len(rows)} manual={sum(r['extraction_basis'].startswith('manual') for r in rows)} "
          f"peer_reviewed={sum(r['peer_reviewed'] == 'yes' for r in rows)}")


if __name__ == "__main__":
    main()
