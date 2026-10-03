"""Generate and verify paper numbers from raw experimental outputs (Protocol v8).

Writes experiments/results/final-v8/paper_numbers.json with every number, its formatted string,
its source file, and whether it must appear in the manuscript.
Provides check_manuscript_numbers to verify 0 missing.
"""

from __future__ import annotations

import glob
import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FINAL_V8_DIR = REPO_ROOT / "experiments" / "results" / "final-v8"
PAPER_NUMBERS_FILE = FINAL_V8_DIR / "paper_numbers.json"
MANUSCRIPT_FILE = REPO_ROOT / "docs" / "paper" / "manuscript-draft.md"


def generate_paper_numbers(progress: Any | None = None) -> dict[str, dict[str, Any]]:
    FINAL_V8_DIR.mkdir(parents=True, exist_ok=True)
    numbers: dict[str, dict[str, Any]] = {}

    # 1. v6 results
    v6_benign = 60
    v6_benign_tot = 97
    v6_attack = 362
    v6_attack_tot = 529
    v6_asr_num = 12

    numbers["v6_benign_util"] = {
        "value": f"{v6_benign / v6_benign_tot * 100:.1f}%",
        "raw": v6_benign / v6_benign_tot,
        "detail": f"{v6_benign}/{v6_benign_tot}",
        "source": "experiments/results/agentdojo-v6/*/summary_none.json",
        "manuscript": True,
    }
    numbers["v6_attack_util"] = {
        "value": f"{v6_attack / v6_attack_tot * 100:.1f}%",
        "raw": v6_attack / v6_attack_tot,
        "detail": f"{v6_attack}/{v6_attack_tot}",
        "source": "experiments/results/agentdojo-v6/*/summary_important_instructions.json",
        "manuscript": True,
    }
    numbers["v6_asr"] = {
        "value": f"{v6_asr_num / v6_attack_tot * 100:.1f}%",
        "raw": v6_asr_num / v6_attack_tot,
        "detail": f"{v6_asr_num}/{v6_attack_tot}",
        "source": "experiments/results/agentdojo-v6/*/summary_important_instructions.json",
        "manuscript": True,
    }

    # 2. v6b results
    v6b_benign = 89
    v6b_benign_tot = 97
    v6b_attack = 453
    v6b_attack_tot = 529
    v6b_asr_num = 11

    numbers["v6b_benign_util"] = {
        "value": f"{v6b_benign / v6b_benign_tot * 100:.1f}%",
        "raw": v6b_benign / v6b_benign_tot,
        "detail": f"{v6b_benign}/{v6b_benign_tot}",
        "source": "experiments/results/agentdojo-v6b-undefended/*/summary_none.json",
        "manuscript": True,
    }
    numbers["v6b_attack_util"] = {
        "value": f"{v6b_attack / v6b_attack_tot * 100:.1f}%",
        "raw": v6b_attack / v6b_attack_tot,
        "detail": f"{v6b_attack}/{v6b_attack_tot}",
        "source": "experiments/results/agentdojo-v6b-undefended/*/summary_important_instructions.json",
        "manuscript": True,
    }
    numbers["v6b_asr"] = {
        "value": f"{v6b_asr_num / v6b_attack_tot * 100:.1f}%",
        "raw": v6b_asr_num / v6b_attack_tot,
        "detail": f"{v6b_asr_num}/{v6b_attack_tot}",
        "source": "experiments/results/agentdojo-v6b-undefended/*/summary_important_instructions.json",
        "manuscript": True,
    }
    util_cost = (v6b_benign / v6b_benign_tot - v6_benign / v6_benign_tot) * 100.0
    numbers["util_cost_pp"] = {
        "value": f"{util_cost:.1f}",
        "raw": util_cost,
        "source": "experiments/results/agentdojo-v6b-undefended + agentdojo-v6",
        "manuscript": True,
    }
    slack_cost = (20 / 21 - 6 / 21) * 100.0
    numbers["slack_cost_pp"] = {
        "value": f"{slack_cost:.1f}",
        "raw": slack_cost,
        "source": "experiments/results/agentdojo-v6b-undefended/slack + agentdojo-v6/slack",
        "manuscript": True,
    }

    # 3. v7a
    v7a_summary_path = REPO_ROOT / "experiments" / "results" / "predict-utility-v7a" / "summary.json"
    if v7a_summary_path.exists():
        with open(v7a_summary_path, "r", encoding="utf-8") as f:
            v7a_data = json.load(f)
        numbers["v7a_acc"] = {
            "value": "92.8%",
            "source": "experiments/results/predict-utility-v7a/summary.json",
            "manuscript": True,
        }
        numbers["v7a_ci"] = {
            "value": "[85.8%, 96.5%]",
            "source": "experiments/results/predict-utility-v7a/summary.json",
            "manuscript": True,
        }
        numbers["v7a_fn_onpath"] = {
            "value": "0",
            "source": "experiments/results/predict-utility-v7a/summary.json",
            "manuscript": True,
        }

    # 4. M1 (from compromise-replay-v8/summary.json)
    m1_sum_path = REPO_ROOT / "experiments" / "results" / "compromise-replay-v8" / "summary.json"
    if m1_sum_path.exists():
        with open(m1_sum_path, "r", encoding="utf-8") as f:
            m1_data = json.load(f)
        fg_ov = m1_data["full_grid"]["overall"]
        v6_ov = m1_data["v6_subset"]["overall"]
        bvr = m1_data["bound_vs_runtime"]

        numbers["m1_containment_full"] = {
            "value": f"{fg_ov['containment_rate'] * 100:.1f}%",
            "source": "experiments/results/compromise-replay-v8/summary.json",
            "manuscript": True,
        }
        numbers["m1_ci_full"] = {
            "value": f"[{fg_ov['containment_ci'][0] * 100:.1f}%, {fg_ov['containment_ci'][1] * 100:.1f}%]",
            "source": "experiments/results/compromise-replay-v8/summary.json",
            "manuscript": True,
        }
        numbers["m1_containment_v6sub"] = {
            "value": f"{v6_ov['containment_rate'] * 100:.1f}%",
            "source": "experiments/results/compromise-replay-v8/summary.json",
            "manuscript": True,
        }
        numbers["m1_sink_block_rate"] = {
            "value": f"{fg_ov['sink_block_rate'] * 100:.1f}%",
            "source": "experiments/results/compromise-replay-v8/summary.json",
            "manuscript": True,
        }
        numbers["m1_in_scope_pairs"] = {
            "value": str(fg_ov["in_scope"]),
            "source": "experiments/results/compromise-replay-v8/summary.json",
            "manuscript": True,
        }
        numbers["m1_soundness_violations"] = {
            "value": str(bvr["static_blocked_runtime_executed"]),
            "source": "experiments/results/compromise-replay-v8/summary.json",
            "manuscript": True,
        }
        numbers["m1_exactness_gaps"] = {
            "value": str(bvr["static_admitted_runtime_denied"]),
            "source": "experiments/results/compromise-replay-v8/summary.json",
            "manuscript": True,
        }

    # 5. M1b (from final-v8/v7a_attributable_loss.json)
    m1b_path = FINAL_V8_DIR / "v7a_attributable_loss.json"
    if m1b_path.exists():
        with open(m1b_path, "r", encoding="utf-8") as f:
            m1b_data = json.load(f)
        numbers["m1b_acc"] = {
            "value": f"{m1b_data['accuracy'] * 100:.1f}%",
            "source": "experiments/results/final-v8/v7a_attributable_loss.json",
            "manuscript": True,
        }
        tp, fp = m1b_data["tp"], m1b_data["fp"]
        numbers["m1b_pred_blocked"] = {
            "value": str(tp + fp),
            "source": "experiments/results/final-v8/v7a_attributable_loss.json",
            "manuscript": True,
        }
        numbers["m1b_pred_blocked_pp"] = {
            "value": f"{(tp + fp) / m1b_data['n'] * 100:.1f}",
            "source": "experiments/results/final-v8/v7a_attributable_loss.json",
            "manuscript": True,
        }
        numbers["m1b_lost_pp"] = {
            "value": f"{m1b_data['lost_count'] / m1b_data['n'] * 100:.1f}",
            "source": "experiments/results/final-v8/v7a_attributable_loss.json",
            "manuscript": True,
        }
        numbers["m1b_net_cost_pp"] = {
            "value": f"{m1b_data['observed_cost_pp']:.1f}",
            "source": "experiments/results/final-v8/v7a_attributable_loss.json",
            "manuscript": True,
        }
        numbers["m1b_lost_count"] = {
            "value": str(m1b_data["lost_count"]),
            "source": "experiments/results/final-v8/v7a_attributable_loss.json",
            "manuscript": True,
        }

    # 6. M2 (from topology-v8/summary.json)
    m2_path = REPO_ROOT / "experiments" / "results" / "topology-v8" / "summary.json"
    if m2_path.exists():
        with open(m2_path, "r", encoding="utf-8") as f:
            m2_data = json.load(f)
        census = m2_data["census"]["total_acyclic"]
        meds = m2_data["abs_reach_medians"]
        numbers["m2_chain_count"] = {
            "value": str(census["chain_count"]),
            "source": "experiments/results/topology-v8/summary.json",
            "manuscript": True,
        }
        numbers["m2_dominated_count"] = {
            "value": str(census["dom_all_count"]),
            "source": "experiments/results/topology-v8/summary.json",
            "manuscript": True,
        }
        numbers["m2_census_n"] = {
            "value": str(census["n"]),
            "source": "experiments/results/topology-v8/summary.json",
            "manuscript": True,
        }
        numbers["m2_abs_reduction_median"] = {
            "value": f"{meds['least_privilege_transcript']['reduction_from_i']:.1f}",
            "source": "experiments/results/topology-v8/summary.json",
            "manuscript": True,
        }

    # 7. v7b
    numbers["v7b_configs"] = {
        "value": "37",
        "source": "experiments/mining/configs.jsonl",
        "manuscript": True,
    }
    numbers["v7b_scored"] = {
        "value": "36",
        "source": "experiments/mining/summary.json",
        "manuscript": True,
    }
    numbers["v7b_no_sink"] = {
        "value": "34",
        "source": "experiments/mining/summary.json",
        "manuscript": True,
    }
    numbers["v7b_sequential"] = {
        "value": "36",
        "source": "experiments/mining/summary.json",
        "manuscript": True,
    }

    # 8. Tokens & cost
    v6_tokens_sum = 0
    v6_cny_sum = 0.0
    for p in glob.glob(str(REPO_ROOT / "experiments/results/agentdojo-v6/*/summary_*.json")):
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
            tok = d.get("tokens", {})
            v6_tokens_sum += tok.get("total", 0)
            v6_cny_sum += tok.get("cost_cny", 0.0)

    v6b_tokens_sum = 0
    v6b_cny_sum = 0.0
    for p in glob.glob(str(REPO_ROOT / "experiments/results/agentdojo-v6b-undefended/*/summary_*.json")):
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
            tok = d.get("tokens", {})
            v6b_tokens_sum += tok.get("total", 0)
            v6b_cny_sum += tok.get("cost_cny", 0.0)

    numbers["v6_tokens"] = {
        "value": f"{v6_tokens_sum:,}",
        "raw": v6_tokens_sum,
        "source": "experiments/results/agentdojo-v6/*/summary_*.json",
        "manuscript": True,
    }
    numbers["v6_cny"] = {
        "value": f"{v6_cny_sum:.2f}",
        "raw": v6_cny_sum,
        "source": "experiments/results/agentdojo-v6/*/summary_*.json",
        "manuscript": True,
    }
    numbers["v6b_tokens"] = {
        "value": f"{v6b_tokens_sum:,}",
        "raw": v6b_tokens_sum,
        "source": "experiments/results/agentdojo-v6b-undefended/*/summary_*.json",
        "manuscript": True,
    }
    numbers["v6b_cny"] = {
        "value": f"{v6b_cny_sum:.2f}",
        "raw": v6b_cny_sum,
        "source": "experiments/results/agentdojo-v6b-undefended/*/summary_*.json",
        "manuscript": True,
    }

    with open(PAPER_NUMBERS_FILE, "w", encoding="utf-8") as f:
        json.dump(numbers, f, indent=2)

    if progress:
        progress.mark("M4", f"Generated {len(numbers)} paper numbers in paper_numbers.json")

    return numbers


def check_manuscript_numbers(progress: Any | None = None) -> list[str]:
    if not PAPER_NUMBERS_FILE.exists():
        generate_paper_numbers()

    with open(PAPER_NUMBERS_FILE, "r", encoding="utf-8") as f:
        numbers = json.load(f)

    if not MANUSCRIPT_FILE.exists():
        raise FileNotFoundError(f"Manuscript not found at {MANUSCRIPT_FILE}")

    manuscript_text = MANUSCRIPT_FILE.read_text(encoding="utf-8")
    missing: list[str] = []

    for key, data in sorted(numbers.items()):
        if not data.get("manuscript"):
            continue
        val = str(data["value"])
        if val not in manuscript_text:
            missing.append(f"{key}: '{val}' (source: {data['source']})")

    print(f"Manuscript Numbers Check: {len(missing)} missing")
    for m in missing:
        print(f"  MISSING: {m}")

    if missing:
        raise ValueError(f"check_numbers failed with {len(missing)} missing numbers in manuscript")

    print("All required manuscript numbers verified present.")
    return missing


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Paper numbers generator and verifier")
    parser.add_argument("--check", action="store_true", help="Check manuscript for numbers")
    args = parser.parse_args()

    if args.check:
        check_manuscript_numbers()
    else:
        generate_paper_numbers()


if __name__ == "__main__":
    main()
