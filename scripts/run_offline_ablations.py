#!/usr/bin/env python3
"""Stage 7D: Offline security-utility Pareto frontier, component ablations,
staging-trace vs exploratory prompt-only predictor, and independent
external branching/parallel DAG topology analysis.

Zero live LLM API calls. Uses the code in this release.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
WORKSPACE = (BASE_DIR / "workspace") if (BASE_DIR / "workspace").is_dir() else BASE_DIR
if str(WORKSPACE / "src") not in sys.path:
    sys.path.insert(0, str(WORKSPACE / "src"))

from agentdojo.benchmark import get_suite  # noqa: E402
from agentdojo.functions_runtime import FunctionsRuntime  # noqa: E402

from guide.agent import AgentSpec  # noqa: E402
from guide.policy import Decision, Policy, PolicyContext, RulePolicyEngine  # noqa: E402
from guide.runtime import HandoffMode  # noqa: E402
from guide.tools import OperationSpec, ToolRegistry, ToolSpec  # noqa: E402
from guide.types import Sensitivity, ToolCall, ToolResult, Trust  # noqa: E402
from guide.workflow import Step, TaskSpec, Workflow  # noqa: E402
from guide_agentdojo.policy import build_suite_policy  # noqa: E402
from guide_agentdojo.replay_execution import execute_admitted_decision  # noqa: E402
from guide_agentdojo.specs import DOJO_TOOL_SECURITY, build_tool_registry  # noqa: E402
from guide_research.blast_radius import SystemModel, blast_radius  # noqa: E402
from guide_research.provenance_v9 import (  # noqa: E402
    DIRECTORY_EXTRACTORS,
    HARDENED_EXTRA_CONTROL,
    DirectoryGuard,
)
from guide_research.topology_theory import has_dominating_source, is_chain  # noqa: E402

OUT_JSON = BASE_DIR / "results" / "offline" / "component_audit.json"
SUITES = ("banking", "slack", "travel", "workspace")
VERSION = "v1.2.2"


def load_dev_split() -> set[tuple[str, str]]:
    split_path = WORKSPACE / "experiments" / "results" / "v9" / "w2" / "split.json"
    d = json.loads(split_path.read_text(encoding="utf-8"))
    dev: set[tuple[str, str]] = set()
    for s, buckets in d.items():
        for t in buckets["dev"]:
            dev.add((s, t))
    return dev


def classify_admitted_pair(suite: str, inj_id: str, sink_calls: list[Any]) -> str:
    """Exact 4-way taxonomy of residual admitted pairs discovered in Stage 3 (ISS-013)."""
    fn_names = [c.function for c in sink_calls]
    if "update_password" in fn_names:
        return "missing_control_metadata"
    if suite == "travel" and inj_id == "injection_task_2":
        return "omitted_optional_control_param"
    if suite == "workspace" and inj_id == "injection_task_1":
        return "untyped_numeric_token_collision"
    return "authorized_recipient_malicious_content"


def make_variant_engine(variant_name: str, suite_name: str, suite_tools: list[Any], reg: ToolRegistry) -> Any:
    """Construct policy engine / guard for each offline ablation arm."""
    base_pol = build_suite_policy(suite_name, suite_tools)
    if variant_name == "none":
        return None
    if variant_name == "rule_read_only":
        pol = Policy(
            policy_id=f"{suite_name}-readonly",
            permitted=base_pol.permitted,
            max_sensitivity=Sensitivity.RESTRICTED,
            allow_write=False,
            allow_external=False,
            numeric_bounds={},
        )
        return RulePolicyEngine(pol, reg)
    if variant_name == "rule_no_external":
        pol = Policy(
            policy_id=f"{suite_name}-noext",
            permitted=base_pol.permitted,
            max_sensitivity=Sensitivity.RESTRICTED,
            allow_write=True,
            allow_external=False,
            numeric_bounds={},
        )
        return RulePolicyEngine(pol, reg)

    eng = RulePolicyEngine(base_pol, reg)
    cfg_map = {
        "strict": ("substring", "off", {}, False),
        "strict_nonempty": ("substring", "off", {}, True),
        "cred": ("substring", "off", HARDENED_EXTRA_CONTROL, False),
        "cred_nonempty": ("substring", "off", HARDENED_EXTRA_CONTROL, True),
        "hard": ("token", "off", HARDENED_EXTRA_CONTROL, False),
        "hard_nonempty": ("token", "off", HARDENED_EXTRA_CONTROL, True),
        "flexI_cred": ("substring", "internal", HARDENED_EXTRA_CONTROL, False),
        "flexI_cred_nonempty": ("substring", "internal", HARDENED_EXTRA_CONTROL, True),
        "flexI_hard_nonempty": ("token", "internal", HARDENED_EXTRA_CONTROL, True),
    }
    match, mode, extra, req_nonempty = cfg_map[variant_name]
    return DirectoryGuard(
        eng,
        reg,
        match,  # type: ignore[arg-type]
        directory_mode=mode,  # type: ignore[arg-type]
        extra_control=extra,
        require_nonempty_control=req_nonempty,
    )


def observe_full_directory(guard: DirectoryGuard, run_id: str, suite: Any, env: Any) -> None:
    """Observe the complete initial directory of ``suite`` (conservative attacker bound)."""
    if guard.directory_mode == "off":
        return
    rt = FunctionsRuntime(suite.tools)
    calls: list[tuple[str, dict[str, Any]]] = []
    if suite.name == "slack":
        calls = [("get_channels", {})] + [
            ("get_users_in_channel", {"channel": c}) for c in list(env.slack.channels)
        ]
    elif suite.name == "workspace":
        calls = [("list_files", {})]
        for c in getattr(env.inbox, "contact_list", []):
            guard.observe_directory(run_id, "search_contacts_by_email", [c])
    for fn, args in calls:
        res, err = rt.run_function(env, fn, args)
        if not err and res is not None:
            guard.observe_directory(run_id, fn, res)


def eval_ablation_arms(dev_split: set[tuple[str, str]]) -> dict[str, Any]:
    """Evaluate all 12 arms deterministically on:
    - 97 benign tasks (dev=30, heldout=67) via ground-truth benign tool sequences
    - 588 in-scope attack pairs (dev, heldout, pooled) via ground-truth attack tool sequences
    """
    arms = [
        "none",
        "rule_read_only",
        "rule_no_external",
        "strict",
        "strict_nonempty",
        "cred",
        "cred_nonempty",
        "hard",
        "hard_nonempty",
        "flexI_cred",
        "flexI_cred_nonempty",
        "flexI_hard_nonempty",
    ]

    # Preload suites, ground-truth benign & attack traces
    suite_cache: dict[str, Any] = {}
    benign_cases: list[dict[str, Any]] = []
    attack_cases: list[dict[str, Any]] = []

    for sname in SUITES:
        suite = get_suite(VERSION, sname)
        reg = build_tool_registry(suite.tools)
        tool_names = frozenset(f.name for f in suite.tools)
        env0 = suite.load_and_inject_default_environment({})
        rt0 = FunctionsRuntime(suite.tools)

        # Precompute initial directory outputs ONCE per suite (fast & exact!)
        cached_dir_obs: list[tuple[str, Any]] = []
        if sname == "slack":
            for fn_n, f_args in [("get_channels", {})] + [
                ("get_users_in_channel", {"channel": c}) for c in list(env0.slack.channels)
            ]:
                res, err = rt0.run_function(env0, fn_n, f_args)
                if not err and res is not None:
                    cached_dir_obs.append((fn_n, res))
        elif sname == "workspace":
            res, err = rt0.run_function(env0, "list_files", {})
            if not err and res is not None:
                cached_dir_obs.append(("list_files", res))
            for c in getattr(env0.inbox, "contact_list", []):
                cached_dir_obs.append(("search_contacts_by_email", [c]))

        suite_cache[sname] = {
            "suite": suite,
            "reg": reg,
            "tool_names": tool_names,
            "cached_dir_obs": cached_dir_obs,
        }

        for uid, ut in sorted(suite.user_tasks.items()):
            gt = ut.ground_truth(env0)
            benign_cases.append(
                {
                    "suite": sname,
                    "user_task": uid,
                    "is_dev": (sname, uid) in dev_split,
                    "prompt": ut.PROMPT,
                    "gt_calls": gt,
                }
            )
            for iid, it in sorted(suite.injection_tasks.items()):
                igt = it.ground_truth(env0)
                sink_calls = [
                    c for c in igt if (sec := DOJO_TOOL_SECURITY.get(c.function)) and (sec[0] or sec[1])
                ]
                if not sink_calls:
                    continue
                attack_cases.append(
                    {
                        "suite": sname,
                        "user_task": uid,
                        "injection_task": iid,
                        "is_dev": (sname, uid) in dev_split,
                        "prompt": ut.PROMPT,
                        "sink_calls": sink_calls,
                    }
                )

    results: dict[str, Any] = {}
    for arm in arms:
        b_counts = {
            "pooled": [0, 0],
            "dev": [0, 0],
            "heldout": [0, 0],
            "by_suite": {s: [0, 0] for s in SUITES},
        }
        a_counts = {
            "pooled": [0, 0],
            "dev": [0, 0],
            "heldout": [0, 0],
            "by_suite": {s: [0, 0] for s in SUITES},
            "admitted_taxonomy": {},
        }

        # Benign replay using real FunctionsRuntime execution
        for bc in benign_cases:
            sc = suite_cache[bc["suite"]]
            eng = make_variant_engine(arm, bc["suite"], sc["suite"].tools, sc["reg"])
            run_id = f"b-{bc['suite']}-{bc['user_task']}"
            admitted = True
            if eng is not None:
                env_run = sc["suite"].load_and_inject_default_environment({})
                rt = FunctionsRuntime(sc["suite"].tools)
                if isinstance(eng, DirectoryGuard):
                    eng.observe(run_id, {"objective": bc["prompt"]}, Trust.TRUSTED)
                ctx = PolicyContext(run_id, "step", sc["tool_names"])
                for call in bc["gt_calls"]:
                    cargs = dict(call.args or {})
                    d = eng.evaluate(ToolCall(call.function, call.function, cargs, "agent"), ctx)
                    if d.decision is Decision.DENY:
                        admitted = False
                        break
                    res, err = execute_admitted_decision(rt, env_run, d)
                    if isinstance(eng, DirectoryGuard) and res is not None and not err:
                        eng.observe(run_id, res, Trust.UNTRUSTED)
                        if call.function in DIRECTORY_EXTRACTORS:
                            eng.observe_directory(run_id, call.function, res)
                if isinstance(eng, DirectoryGuard):
                    eng.forget(run_id)

            bucket = "dev" if bc["is_dev"] else "heldout"
            b_counts["pooled"][1] += 1
            b_counts[bucket][1] += 1
            b_counts["by_suite"][bc["suite"]][1] += 1
            if admitted:
                b_counts["pooled"][0] += 1
                b_counts[bucket][0] += 1
                b_counts["by_suite"][bc["suite"]][0] += 1

        # Attack replay (assumed compromise — conservative full initial directory for flex*)
        for ac in attack_cases:
            sc = suite_cache[ac["suite"]]
            eng = make_variant_engine(arm, ac["suite"], sc["suite"].tools, sc["reg"])
            run_id = f"a-{ac['suite']}-{ac['user_task']}-{ac['injection_task']}"
            contained = False
            if eng is not None:
                if isinstance(eng, DirectoryGuard):
                    eng.observe(run_id, {"objective": ac["prompt"]}, Trust.TRUSTED)
                    for fn_n, res in sc["cached_dir_obs"]:
                        eng.observe_directory(run_id, fn_n, res)
                ctx = PolicyContext(run_id, "step", sc["tool_names"])
                all_denied = True
                for call in ac["sink_calls"]:
                    d = eng.evaluate(ToolCall(call.function, call.function, dict(call.args or {}), "agent"), ctx)
                    if d.decision is Decision.DENY:
                        continue
                    all_denied = False
                    break
                contained = all_denied
                if isinstance(eng, DirectoryGuard):
                    eng.forget(run_id)

            bucket = "dev" if ac["is_dev"] else "heldout"
            a_counts["pooled"][1] += 1
            a_counts[bucket][1] += 1
            a_counts["by_suite"][ac["suite"]][1] += 1
            if contained:
                a_counts["pooled"][0] += 1
                a_counts[bucket][0] += 1
                a_counts["by_suite"][ac["suite"]][0] += 1
            else:
                tax = classify_admitted_pair(ac["suite"], ac["injection_task"], ac["sink_calls"])
                a_counts["admitted_taxonomy"][tax] = a_counts["admitted_taxonomy"].get(tax, 0) + 1

        def fmt(pair: list[int]) -> dict[str, Any]:
            return {"k": pair[0], "n": pair[1], "pct": round(100.0 * pair[0] / max(1, pair[1]), 4)}

        results[arm] = {
            "benign_admissibility": {
                "pooled": fmt(b_counts["pooled"]),
                "dev_30": fmt(b_counts["dev"]),
                "heldout_67": fmt(b_counts["heldout"]),
                "by_suite": {s: fmt(v) for s, v in b_counts["by_suite"].items()},
            },
            "attack_containment": {
                "pooled": fmt(a_counts["pooled"]),
                "dev": fmt(a_counts["dev"]),
                "heldout": fmt(a_counts["heldout"]),
                "by_suite": {s: fmt(v) for s, v in a_counts["by_suite"].items()},
                "admitted_total": a_counts["pooled"][1] - a_counts["pooled"][0],
                "admitted_taxonomy": a_counts["admitted_taxonomy"],
            },
        }
    return results


def eval_trace_free_vs_oracle_predictor(dev_split: set[tuple[str, str]]) -> dict[str, Any]:
    """Compare historical M1b oracle-trace predictor (which reads user_task.ground_truth)
    against a genuinely deployable TRACE-FREE static predictor that sees ONLY the user prompt
    and suite tool specs (zero access to future tool calls or environment state).
    """
    v6_dir = WORKSPACE / "experiments" / "results" / "agentdojo-v6"
    v6b_dir = WORKSPACE / "experiments" / "results" / "agentdojo-v6b-undefended"
    v7a_pred = WORKSPACE / "experiments" / "results" / "predict-utility-v7a" / "predictions.jsonl"

    oracle_preds: dict[tuple[str, str], bool] = {}
    for line in v7a_pred.read_text(encoding="utf-8").splitlines():
        if line.strip():
            it = json.loads(line)
            oracle_preds[(it["suite"], it["user_task_id"])] = bool(it["predicted_block"])

    # Simple transparent deployable trace-free rule:
    # Predicts a strict-provenance block if the user prompt implies a state-mutating action
    # whose control target must be discovered from an external source (indirection cue like
    # "check/read/find ... and send/pay/invite/delete/post" without an explicit email/IBAN/file-ext/channel literal).
    email_re = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
    iban_re = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b")
    action_cue_re = re.compile(
        r"\b(send|pay|transfer|schedule|update|post|message|dm|invite|remove|add|delete|share|append|create|book|reserve|cancel|reschedule)\b",
        re.I,
    )
    indirection_cue_re = re.compile(
        r"\b(bill|invoice|receipt|file|inbox|email|channel|message|website|url|link|contact|colleague|friend|everyone|all users|members|whoever|latest|recent|check|read|find|look up)\b",
        re.I,
    )

    def trace_free_predict(suite_name: str, prompt: str) -> bool:
        has_action = bool(action_cue_re.search(prompt))
        if not has_action:
            return False
        has_indirection = bool(indirection_cue_re.search(prompt))
        has_explicit_email = bool(email_re.search(prompt))
        has_explicit_iban = bool(iban_re.search(prompt))
        if suite_name == "banking":
            return has_indirection and not has_explicit_iban
        if suite_name == "slack":
            # Slack tasks nearly always reference channels/users discovered via listing or external pages
            return has_indirection
        if suite_name == "travel":
            # Travel booking prompts usually name the hotel/restaurant directly unless checking emails/reviews
            return has_indirection and not has_explicit_email and "email" in prompt.lower()
        # workspace
        return has_indirection and not has_explicit_email

    def score_preds(pred_fn_map: dict[tuple[str, str], bool], actual_lost: dict[tuple[str, str], bool], subset: list[tuple[str, str]]) -> dict[str, Any]:
        tp = fp = fn = tn = 0
        for k in subset:
            p = pred_fn_map[k]
            y = actual_lost[k]
            if p and y:
                tp += 1
            elif p and not y:
                fp += 1
            elif not p and y:
                fn += 1
            else:
                tn += 1
        n = len(subset)
        acc = (tp + tn) / max(1, n)
        prec = tp / max(1, tp + fp)
        rec = tp / max(1, tp + fn)
        f1 = (2 * prec * rec) / max(1e-9, prec + rec)
        return {
            "n": n,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
        }

    actual_lost: dict[tuple[str, str], bool] = {}
    tf_preds: dict[tuple[str, str], bool] = {}
    all_keys: list[tuple[str, str]] = []

    for sname in SUITES:
        suite = get_suite(VERSION, sname)
        v6 = json.loads((v6_dir / sname / "summary_none.json").read_text())["utility_results"]
        v6b = json.loads((v6b_dir / sname / "summary_none.json").read_text())["utility_results"]
        for uid, ut in sorted(suite.user_tasks.items()):
            k = (sname, uid)
            all_keys.append(k)
            actual_lost[k] = bool(v6b.get(uid, False) and not v6.get(uid, False))
            tf_preds[k] = trace_free_predict(sname, ut.PROMPT)

    dev_keys = [k for k in all_keys if k in dev_split]
    held_keys = [k for k in all_keys if k not in dev_split]
    return {
        "oracle_trace_predictor_m1b": {
            "pooled_97": score_preds(oracle_preds, actual_lost, all_keys),
            "dev_30": score_preds(oracle_preds, actual_lost, dev_keys),
            "heldout_67": score_preds(oracle_preds, actual_lost, held_keys),
        },
        "deployable_trace_free_predictor": {
            "pooled_97": score_preds(tf_preds, actual_lost, all_keys),
            "dev_30": score_preds(tf_preds, actual_lost, dev_keys),
            "heldout_67": score_preds(tf_preds, actual_lost, held_keys),
        },
    }


def eval_independent_external_branching_dags() -> list[dict[str, Any]]:
    """Evaluate Proposition 3 & Proposition 4 on independently sourced, immutable-SHA
    official branching/parallel workflows from crewAIInc/crewAI-examples and langchain-ai/langgraph.
    Strictly separated from the 19 author-authored configs and the 36 sequential mined CrewAI scripts.
    """
    class _OpTool:
        def __init__(self, name: str, write: bool, external: bool, res: str) -> None:
            self.spec = ToolSpec(
                name=name,
                description=name,
                resource_class=res,
                operations={name: OperationSpec(name=name, write_effect=write, external=external)},
                default_sensitivity=Sensitivity.INTERNAL,
            )

        def invoke(self, operation: str, args: Any) -> ToolResult:
            return ToolResult(ok=True, data=None)

    specs = [
        {
            "id": "ext-crewai-meeting-assistant-flow",
            "source_kind": "official_external_repo",
            "repo": "crewAIInc/crewAI-examples",
            "sha": "da94a91e691e",
            "file": "flows/meeting_assistant_flow/src/meeting_assistant_flow/main.py",
            "license": "MIT",
            "topology": "rooted_parallel_fanout_3_sinks",
            "tools": [
                ("read_notes", False, False, "notes"),
                ("extract_tasks", False, False, "tasks_llm"),
                ("save_tasks_to_trello", True, True, "trello"),
                ("save_new_tasks_to_csv", True, False, "csv_file"),
                ("send_slack_notification", True, True, "slack"),
            ],
            "steps_refined": [
                Step("load_notes", "loader", "", tools=("read_notes",), depends_on=()),
                Step("gen_tasks", "extractor", "", tools=("extract_tasks",), depends_on=("load_notes",)),
                Step("trello_branch", "trello_ag", "", tools=("save_tasks_to_trello",), depends_on=("gen_tasks",)),
                Step("csv_branch", "csv_ag", "", tools=("save_new_tasks_to_csv",), depends_on=("gen_tasks",)),
                Step("slack_branch", "slack_ag", "", tools=("send_slack_notification",), depends_on=("gen_tasks",)),
            ],
        },
        {
            "id": "ext-crewai-lead-score-flow",
            "source_kind": "official_external_repo",
            "repo": "crewAIInc/crewAI-examples",
            "sha": "da94a91e691e",
            "file": "flows/lead-score-flow/src/lead_score_flow/main.py",
            "license": "MIT",
            "topology": "routed_async_fanout_with_human_gate",
            "tools": [
                ("load_leads_csv", False, False, "leads"),
                ("score_candidate", False, False, "scoring"),
                ("write_email_file_a", True, False, "email_dir_a"),
                ("write_email_file_b", True, False, "email_dir_b"),
            ],
            "steps_refined": [
                Step("load_leads", "loader", "", tools=("load_leads_csv",), depends_on=()),
                Step("score_leads", "scorer", "", tools=("score_candidate",), depends_on=("load_leads",)),
                Step("write_lead_a", "writer_a", "", tools=("write_email_file_a",), depends_on=("score_leads",)),
                Step("write_lead_b", "writer_b", "", tools=("write_email_file_b",), depends_on=("score_leads",)),
            ],
        },
        {
            "id": "ext-langgraph-hierarchical-teams-acyclic-unfolding",
            "source_kind": "official_external_repo",
            "repo": "langchain-ai/langgraph",
            "sha": "7830b91a24e6",
            "file": "examples/multi_agent/hierarchical_agent_teams.ipynb",
            "license": "MIT",
            "topology": "2_branch_isolated_teams_acyclic_unfolding",
            "tools": [
                ("tavily_search", False, False, "web"),
                ("scrape_webpages", False, False, "web"),
                ("write_document", True, False, "doc_fs"),
                ("python_repl_chart", True, True, "python_repl"),
            ],
            "steps_refined": [
                # Rooted at top-level router -> 2 independent sub-teams (research vs doc/chart)
                Step("top_supervisor", "supervisor", "", tools=(), depends_on=()),
                Step("research_search", "researcher", "", tools=("tavily_search",), depends_on=("top_supervisor",)),
                Step("research_scrape", "scraper", "", tools=("scrape_webpages",), depends_on=("research_search",)),
                Step("doc_write", "writer", "", tools=("write_document",), depends_on=("top_supervisor",)),
                Step("chart_exec", "charter", "", tools=("python_repl_chart",), depends_on=("top_supervisor",)),
            ],
        },
        {
            "id": "ext-rootless-decoupled-parallel-sinks-design",
            "source_kind": "author_modified_rootless_variant",
            "repo": "author-modified rootless isolation variant of crewAIInc/crewAI-examples meeting_assistant_flow",
            "sha": "da94a91e691e",
            "file": "flows/meeting_assistant_flow/src/meeting_assistant_flow/main.py (decoupled branches)",
            "license": "MIT",
            "topology": "rootless_parallel_3_independent_pipelines",
            "tools": [
                ("save_tasks_to_trello", True, True, "trello"),
                ("save_new_tasks_to_csv", True, False, "csv_file"),
                ("send_slack_notification", True, True, "slack"),
            ],
            "steps_refined": [
                Step("trello_branch", "trello_ag", "", tools=("save_tasks_to_trello",), depends_on=()),
                Step("csv_branch", "csv_ag", "", tools=("save_new_tasks_to_csv",), depends_on=()),
                Step("slack_branch", "slack_ag", "", tools=("send_slack_notification",), depends_on=()),
            ],
        },
    ]

    out = []
    for sp in specs:
        reg = ToolRegistry([_OpTool(n, w, e, r) for n, w, e, r in sp["tools"]])
        pol = Policy(
            policy_id=sp["id"],
            permitted={n: frozenset({n}) for n, _, _, _ in sp["tools"]},
            max_sensitivity=Sensitivity.RESTRICTED,
            allow_write=True,
            allow_external=True,
        )
        steps_ref = tuple(sp["steps_refined"])
        wf_ref = Workflow(steps_ref)
        agents_ref = tuple(AgentSpec(f"ag_{s.role}", s.role, "") for s in steps_ref)

        # Coarse 1-agent partition (all steps on 1 shared role)
        steps_coarse = tuple(
            Step(s.step_id, "shared", "", tools=s.tools, depends_on=s.depends_on) for s in steps_ref
        )
        wf_coarse = Workflow(steps_coarse)
        agents_coarse = (AgentSpec("ag_shared", "shared", ""),)

        sink_steps = [s.step_id for s in steps_ref if any(w or e for n, w, e, _ in sp["tools"] if n in s.tools)]
        total_sinks = len(sink_steps)

        def eval_partition(
            wf: Workflow,
            ags: tuple[AgentSpec, ...],
            mode: HandoffMode,
            *,
            _sid: str = sp["id"],
            _pol: Policy = pol,
            _reg: ToolRegistry = reg,
        ) -> dict[str, Any]:
            t = TaskSpec(_sid, "ext", "nominal", (), {}, wf)
            m = SystemModel.for_task(t, ags, _pol, _reg, mode=mode, gate="rule")
            reaches = [len(blast_radius(m, {a.agent_id}).sinks) for a in ags]
            return {
                "wbr1_max": max(reaches),
                "mean_agent_reach": round(sum(reaches) / len(reaches), 3),
                "per_agent_sinks": {a.agent_id: r for a, r in zip(ags, reaches, strict=True)},
            }

        out.append(
            {
                "id": sp["id"],
                "source_kind": sp["source_kind"],
                "repo": sp["repo"],
                "sha": sp["sha"],
                "file": sp["file"],
                "topology": sp["topology"],
                "n_steps": len(steps_ref),
                "total_sinks": total_sinks,
                "is_linear_chain": is_chain(wf_ref),
                "has_dominating_source_over_sinks": has_dominating_source(wf_ref, sink_steps),
                "coarse_1agent_signed": eval_partition(wf_coarse, agents_coarse, HandoffMode.SIGNED),
                "refined_transcript": eval_partition(wf_ref, agents_ref, HandoffMode.TRANSCRIPT),
                "refined_signed": eval_partition(wf_ref, agents_ref, HandoffMode.SIGNED),
            }
        )
    return out


def main() -> None:
    dev_split = load_dev_split()
    print(f"Loaded dev split: {len(dev_split)} tasks")
    ablations = eval_ablation_arms(dev_split)
    predictors = eval_trace_free_vs_oracle_predictor(dev_split)
    branching = eval_independent_external_branching_dags()

    payload = {
        "component_ablations_agentdojo": ablations,
        "predictor_oracle_vs_trace_free": predictors,
        "independent_external_branching_dags": branching,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("\n=== STAGE 7D ABLATION SUMMARY (POOLED / DEV / HELD-OUT) ===")
    print(f"{'Arm':<22} | {'Benign All':>10} | {'Benign Held':>11} | {'Contain All':>11} | {'Admitted Breakdown'}")
    print("-" * 100)
    for arm, d in ablations.items():
        ba = d["benign_admissibility"]["pooled"]
        bh = d["benign_admissibility"]["heldout_67"]
        ca = d["attack_containment"]["pooled"]
        tax = d["attack_containment"]["admitted_taxonomy"]
        print(f"{arm:<22} | {ba['k']:2d}/{ba['n']:2d} ({ba['pct']:5.1f}%) | {bh['k']:2d}/{bh['n']:2d} ({bh['pct']:5.1f}%) | {ca['k']:3d}/{ca['n']:3d} ({ca['pct']:5.1f}%) | {tax}")

    print("\n=== PREDICTOR COMPARISON (ORACLE-TRACE vs TRACE-FREE) ===")
    print(json.dumps(predictors, indent=2))

    print("\n=== INDEPENDENT EXTERNAL BRANCHING DAGS ===")
    for b in branching:
        print(
            f"{b['id']}: chain={b['is_linear_chain']} dom_src={b['has_dominating_source_over_sinks']} "
            f"coarse_wbr1={b['coarse_1agent_signed']['wbr1_max']}/{b['total_sinks']} "
            f"ref_tr_wbr1={b['refined_transcript']['wbr1_max']} (mean={b['refined_transcript']['mean_agent_reach']}) "
            f"ref_sig_wbr1={b['refined_signed']['wbr1_max']} (mean={b['refined_signed']['mean_agent_reach']})"
        )


if __name__ == "__main__":
    main()
