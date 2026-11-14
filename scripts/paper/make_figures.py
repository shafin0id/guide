"""Generate the paper's figures from verified numbers in docs/experiments.md and docs/formal_model.md.

Black-and-white / greyscale only, per user instruction. Runs single-process, closes each figure
immediately to keep memory low under tight host conditions. No invented data: every number below
is copied from the markdown tables already verified in docs/experiments.md.
"""
import matplotlib

matplotlib.use("Agg")
import os

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

OUT = os.path.join(os.path.dirname(__file__), "figures")
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({
    "font.size": 8,
    "font.family": "sans-serif",
    "axes.edgecolor": "black",
    "axes.labelcolor": "black",
    "text.color": "black",
    "xtick.color": "black",
    "ytick.color": "black",
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
})

CONDITIONS = ["B1", "B2", "P", "GPLUS"]
# greyscale fill shades per condition (lighter -> darker), markers differ per model
SHADE = {"B1": "0.85", "B2": "0.65", "P": "0.45", "GPLUS": "0.15"}
HATCH = {"B1": "", "B2": "//", "P": "xx", "GPLUS": ""}
MODEL_MARKER = {"DeepSeek 4.1 Flash": "o", "Gemini 3.5 Flash-Lite": "s", "OpenAI GPT-OSS-120B (Groq)": "^"}

# ---------------------------------------------------------------------------
# Fig 1: GUIDE external reference monitor, controls and data flow
# ---------------------------------------------------------------------------
def make_fig1():
    import matplotlib.patches as patches
    fig, ax = plt.subplots(figsize=(150 / 25.4, 75 / 25.4), dpi=600)
    ax.set_xlim(0, 150)
    ax.set_ylim(0, 75)
    ax.axis("off")

    outer_box = patches.FancyBboxPatch((32, 10), 86, 60, boxstyle="square,pad=0",
                                      linewidth=1.2, edgecolor="#222222", facecolor="#FAFAFA", linestyle="--")
    ax.add_patch(outer_box)
    ax.text(34, 67, "GUIDE: external reference monitor", fontsize=7.5, fontweight="bold", color="#222222")

    def draw_box(x, y, w, h, title, subtitle=None, facecolor="#F0F0F0", edgecolor="#333333"):
        box = patches.FancyBboxPatch((x, y), w, h, boxstyle="square,pad=0",
                                    linewidth=0.8, edgecolor=edgecolor, facecolor=facecolor)
        ax.add_patch(box)
        if subtitle:
            ax.text(x + w / 2, y + h / 2 + 2.2, title, fontsize=6.8, fontweight="bold", ha="center", va="center", color="#111111")
            ax.text(x + w / 2, y + h / 2 - 2.5, subtitle, fontsize=5.5, ha="center", va="center", color="#444444")
        else:
            ax.text(x + w / 2, y + h / 2, title, fontsize=6.8, fontweight="bold", ha="center", va="center", color="#111111")

    def draw_arrow(x1, y1, x2, y2, label=None, label_pos=None):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", lw=0.9, color="#222222"))
        if label and label_pos:
            ax.text(label_pos[0], label_pos[1], label, fontsize=5.2, ha="center", va="center", color="#333333",
                    bbox=dict(boxstyle="square,pad=0.1", fc="white", ec="none"))

    draw_box(2, 52, 24, 12, "User task", "natural language")
    draw_box(36, 52, 26, 12, "Control 1", "Bayes-UCB routing")
    draw_box(68, 52, 26, 12, "Control 2", "signed hand-off package")
    draw_box(68, 30, 26, 12, "Control 4", "provenance guard")
    draw_box(36, 30, 26, 12, "Control 3", "SMT policy gate")
    draw_box(36, 14, 58, 10, "Trace ledger", "hash-linked record; success estimates feed Control 1")
    draw_box(124, 52, 24, 12, "Agent loop", "untrusted model", facecolor="#FFFFFF")
    draw_box(2, 31, 24, 10, "Tool code", "runs only if allowed", facecolor="#E8E8E8")
    draw_box(2, 14, 24, 10, "Call denied", "never reaches tool", facecolor="#E0E0E0")

    draw_arrow(26, 58, 36, 58, "task", (31, 60.5))
    draw_arrow(62, 58, 68, 58, "agent", (65, 60.5))
    draw_arrow(94, 58, 124, 58, "hand-off", (109, 60.5))
    draw_arrow(130, 52, 94, 40, "proposed tool call", (116, 48))
    draw_arrow(68, 36, 62, 36, "traced", (65, 38.5))
    draw_arrow(36, 36, 26, 36, "allow / bound", (31, 38.5))
    draw_arrow(36, 32, 26, 20, "deny", (30, 27))
    draw_arrow(81, 30, 81, 24, None, None)
    draw_arrow(49, 30, 49, 24, None, None)

    fig.subplots_adjust(left=0.01, right=0.99, top=0.98, bottom=0.08)
    fig.savefig(os.path.join(OUT, "fig1_reference_monitor_design.png"), dpi=600)
    plt.close(fig)

make_fig1()

# ---------------------------------------------------------------------------
# Fig 4: Task success + intent fidelity by condition, per model (dot-whisker)
# Source: docs/experiments.md "Main Suite: Cross-Model Comparison"
# ---------------------------------------------------------------------------
main_suite = {
    "DeepSeek 4.1 Flash": {
        "B1": (0.989, 0.967, 1.000, 0.999),
        "B2": (1.000, 1.000, 1.000, 1.000),
        "P":  (0.989, 0.967, 1.000, 0.999),
        "GPLUS": (1.000, 1.000, 1.000, 1.000),
    },
    "Gemini 3.5 Flash-Lite": {
        "B1": (0.935, 0.797, 1.000, 0.989),
        "B2": (0.969, 0.895, 1.000, 0.995),
        "P":  (0.967, 0.891, 1.000, 0.994),
        "GPLUS": (0.968, 0.893, 1.000, 0.995),
    },
    "OpenAI GPT-OSS-120B (Groq)": {
        "B1": (0.409, 0.238, 0.590, 0.643),
        "B2": (0.390, 0.211, 0.575, 0.667),
        "P":  (0.297, 0.158, 0.447, 0.595),
        "GPLUS": (0.318, 0.152, 0.512, 0.632),
    },
}

fig, axes = plt.subplots(3, 1, figsize=(90 / 25.4, 160 / 25.4), sharex=True)
for ax, (model, data) in zip(axes, main_suite.items()):
    for i, cond in enumerate(CONDITIONS):
        mean, lo, hi, fid = data[cond]
        ax.errorbar(i, mean, yerr=[[mean - lo], [hi - mean]], fmt=MODEL_MARKER[model],
                    color="black", markerfacecolor=SHADE[cond], markeredgecolor="black",
                    capsize=3, markersize=6, linewidth=1)
    ax.set_xticks(range(len(CONDITIONS)))
    ax.set_xticklabels(CONDITIONS)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("task success")
    ax.set_title(model, fontsize=8, loc="left")
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax.grid(axis="y", linestyle=":", linewidth=0.5, color="0.7")
axes[-1].set_xlabel("condition")
fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig(os.path.join(OUT, "fig4_main_suite_success.png"), dpi=600, bbox_inches="tight")
plt.close(fig)

# ---------------------------------------------------------------------------
# Fig 5: Containment heatmap under assumed compromise, per model
# Source: docs/experiments.md "Assumed-Compromise Suite: Containment Across Models"
# cell = violation rate (task success in parens is the complement; we plot violation rate)
# ---------------------------------------------------------------------------
compromise = {
    "DeepSeek 4.1 Flash": {
        "K1": {"B1": 0.00, "B2": 0.00, "P": 0.00, "GPLUS": 0.00},
        "K2": {"B1": 1.00, "B2": 1.00, "P": 0.00, "GPLUS": 0.00},
        "K3": {"B1": 1.00, "B2": 1.00, "P": 1.00, "GPLUS": 0.00},
        "K4": {"B1": 1.00, "B2": 1.00, "P": 0.00, "GPLUS": 0.00},
    },
    "Gemini 3.5 Flash-Lite": {
        "K1": {"B1": 0.00, "B2": 0.00, "P": 0.00, "GPLUS": 0.00},
        "K2": {"B1": 1.00, "B2": 1.00, "P": 0.00, "GPLUS": 0.00},
        "K3": {"B1": 1.00, "B2": 1.00, "P": 1.00, "GPLUS": 0.00},
        "K4": {"B1": 1.00, "B2": 1.00, "P": 0.00, "GPLUS": 0.00},
    },
    "OpenAI GPT-OSS-120B (Groq)": {
        "K1": {"B1": 0.00, "B2": 0.00, "P": 0.00, "GPLUS": 0.00},
        "K2": {"B1": 1.00, "B2": 1.00, "P": 0.00, "GPLUS": 0.00},
        "K3": {"B1": 1.00, "B2": 1.00, "P": 1.00, "GPLUS": 0.00},
        "K4": {"B1": 1.00, "B2": 1.00, "P": 0.00, "GPLUS": 0.00},
    },
}
cases = ["K1", "K2", "K3", "K4"]
fig, axes = plt.subplots(1, 3, figsize=(175 / 25.4, 55 / 25.4))
for ax, model in zip(axes, compromise.keys()):
    grid = [[compromise[model][k][c] for c in CONDITIONS] for k in cases]
    im = ax.imshow(grid, cmap="Greys", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(CONDITIONS))); ax.set_xticklabels(CONDITIONS)
    ax.set_yticks(range(len(cases))); ax.set_yticklabels(cases)
    ax.set_title(model, fontsize=7)
    for yi in range(len(cases)):
        for xi in range(len(CONDITIONS)):
            v = grid[yi][xi]
            ax.text(xi, yi, f"{v:.2f}", ha="center", va="center",
                     color="white" if v > 0.5 else "black", fontsize=7)
fig.tight_layout(rect=[0, 0, 1, 0.90])
fig.savefig(os.path.join(OUT, "fig5_compromise_heatmap.png"), dpi=600)
plt.close(fig)

# ---------------------------------------------------------------------------
# Fig 7: Overhead (median wall time per condition, DeepSeek 4.1 Flash; monitor-only time)
# Source: docs/experiments.md main suite table (median wall s) + overhead test section
# ---------------------------------------------------------------------------
wall_s = {"B1": 3.9, "B2": 4.2, "P": 4.3, "GPLUS": 4.5}
monitor_ms = {"B1": 0.16, "B2": 0.23, "P": 1.68, "GPLUS": 1.69}

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(140 / 25.4, 55 / 25.4))
ax1.bar(range(len(CONDITIONS)), [wall_s[c] for c in CONDITIONS],
        color=[SHADE[c] for c in CONDITIONS], edgecolor="black",
        hatch=[HATCH[c] for c in CONDITIONS])
ax1.set_xticks(range(len(CONDITIONS))); ax1.set_xticklabels(CONDITIONS)
ax1.set_ylabel("median wall time (s)")
ax1.set_title("(a) end-to-end, DeepSeek 4.1 Flash", fontsize=7)
ax1.grid(axis="y", linestyle=":", linewidth=0.5, color="0.7")

ax2.bar(range(len(CONDITIONS)), [monitor_ms[c] for c in CONDITIONS],
        color=[SHADE[c] for c in CONDITIONS], edgecolor="black",
        hatch=[HATCH[c] for c in CONDITIONS])
ax2.set_xticks(range(len(CONDITIONS))); ax2.set_xticklabels(CONDITIONS)
ax2.set_ylabel("monitor-only time (ms)")
ax2.set_title("(b) scripted model, no provider latency", fontsize=7)
ax2.grid(axis="y", linestyle=":", linewidth=0.5, color="0.7")

fig.tight_layout(rect=[0, 0, 1, 0.90])
fig.savefig(os.path.join(OUT, "fig7_overhead.png"), dpi=600)
plt.close(fig)

# ---------------------------------------------------------------------------
# Fig 8: Degraded-agent sequence A12 (cumulative completed runs over 20 runs)
# Source: docs/experiments.md "A12 sequence" bullet
# B2 0/20; P(routing) 19/20 one warm-up failure then recovers; GPLUS 20/20;
# GPLUS-redispatch 19/20; GPLUS-routing(static routing, redispatch rescues) 20/20
# ---------------------------------------------------------------------------

def cumulative(fail_at_runs, n=20):
    """fail_at_runs: set of 1-indexed run numbers that fail (do not complete)."""
    cum = []
    total = 0
    for i in range(1, n + 1):
        if i not in fail_at_runs:
            total += 1
        cum.append(total)
    return cum

n = 20
series = {
    "B2 (static, static)": cumulative(set(range(1, n + 1))),  # 0/20: static always picks the broken agent -> fails every run
    "P (routing, no re-dispatch)": cumulative({1}),  # 19/20: one warm-up failure, then routing avoids it
    "GPLUS (routing + re-dispatch)": cumulative(set()),  # 20/20
    "GPLUS-redispatch (routing only)": cumulative({1}),  # 19/20
    "GPLUS-routing (static + re-dispatch)": cumulative(set()),  # 20/20, rescued every time
}
STYLE = {
    "B2 (static, static)": dict(linestyle="-", marker="x", color="0.55", markevery=(1, 4)),
    "P (routing, no re-dispatch)": dict(linestyle="--", marker="o", color="0.45", markevery=(0, 4)),
    "GPLUS (routing + re-dispatch)": dict(linestyle="-", marker="^", color="0.0", markevery=(0, 4)),
    "GPLUS-redispatch (routing only)": dict(linestyle="-.", marker="s", color="0.25", markevery=(2, 4)),
    "GPLUS-routing (static + re-dispatch)": dict(linestyle=":", marker="D", color="0.15", markevery=(2, 4)),
}
fig, ax = plt.subplots(figsize=(95 / 25.4, 68 / 25.4))
x = list(range(1, n + 1))
for label, cum in series.items():
    ax.plot(x, cum, label=label, linewidth=1.1, markersize=3.2, **STYLE[label])
ax.set_xlabel("run number (degraded agent present throughout)")
ax.set_ylabel("cumulative completed runs")
ax.set_xlim(0.5, n + 0.5)
ax.set_ylim(-1.2, n + 1.5)
ax.legend(fontsize=5.2, loc="upper left", framealpha=1)
ax.grid(linestyle=":", linewidth=0.5, color="0.7")
fig.tight_layout(rect=[0, 0, 1, 0.96])
fig.savefig(os.path.join(OUT, "fig8_degraded_agent_sequence.png"), dpi=600)
plt.close(fig)

# ---------------------------------------------------------------------------
# Fig 6: Blast radius bound sizes (sink capability / recipient count) per condition
# Source: docs/experiments.md Protocol v3 "Bound sizes (T15, K = reporters ∪ retrievers)"
# B2: 2 sinks, unbounded recipients; P: 1 sink, unbounded in-domain; GPLUS(substring): 692
# recipients; GPLUS-token and P-LP: exactly 1.
# Shown as a bar chart on a log scale of admitted-recipient count (unbounded shown as a capped bar
# with an annotation, since "unbounded" has no finite value to plot).
# ---------------------------------------------------------------------------
labels = ["B2", "P", "GPLUS\n(substring)", "GPLUS-token", "P-LP"]
# use a large finite stand-in only for visualising "unbounded" bars; annotate as such, not invented data
UNBOUNDED_DISPLAY = 10000
values = [UNBOUNDED_DISPLAY, UNBOUNDED_DISPLAY, 692, 1, 1]
is_unbounded = [True, True, False, False, False]

fig, ax = plt.subplots(figsize=(105 / 25.4, 66 / 25.4))
bars = ax.bar(range(len(labels)), values, width=0.58, color=["0.8", "0.6", "0.4", "0.15", "0.15"],
              edgecolor="black")
ax.set_yscale("log")
ax.set_ylim(0.5, 120000)
ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, fontsize=6.5)
ax.set_ylabel("admissible recipients (log scale)")
for bar, v, unb in zip(bars, values, is_unbounded):
    label = "unbounded\n(domain)" if unb else str(v)
    ax.text(bar.get_x() + bar.get_width() / 2, v * 1.35, label, ha="center", va="bottom", fontsize=5.8)
fig.tight_layout(rect=[0, 0, 1, 0.96])
fig.savefig(os.path.join(OUT, "fig6_blast_radius_bound_sizes.png"), dpi=600)
plt.close(fig)

# ---------------------------------------------------------------------------
# Fig S2: Routing simulation regret (stationary, drift)
# Source: docs/experiments.md "Routing simulation (H4...)"
# ---------------------------------------------------------------------------
scenarios = ["stationary", "drift (post-drift)"]
algo_vals = {
    "static": (150.0, 275.0),
    "Bayes-UCB": (18.3, 54.5),
    "discount 0.99": (61.2, 41.8),
    "+penalty": (12.5, 61.0),
}
fig, ax = plt.subplots(figsize=(85 / 25.4, 60 / 25.4))
width = 0.2
x = range(len(scenarios))
for i, (algo, vals) in enumerate(algo_vals.items()):
    offs = [xi + (i - 1.5) * width for xi in x]
    ax.bar(offs, vals, width=width, label=algo, color=["0.85", "0.6", "0.35", "0.1"][i], edgecolor="black")
ax.set_xticks(list(x)); ax.set_xticklabels(scenarios, fontsize=7)
ax.set_ylabel("mean regret")
ax.legend(fontsize=6)
fig.tight_layout(rect=[0, 0, 1, 0.90])
fig.savefig(os.path.join(OUT, "figS2_routing_regret.png"), dpi=600)
plt.close(fig)

# ---------------------------------------------------------------------------
# Fig 9: AgentDojo utility vs. containment (v6b vs. v6 benign utility, M1 containment)
# Source: docs/experiments.md Protocol v6, v6b, and v8 (M1)
# ---------------------------------------------------------------------------
suites = ["Banking", "Slack", "Travel", "Workspace", "Overall"]
v6b_util = [0.938, 0.952, 0.800, 0.950, 0.918]  # from agentdojo-v6b-undefended/*/summary_none.json
v6_util  = [0.750, 0.286, 0.800, 0.650, 0.619]
m1_cont  = [0.889, 0.940, 0.825, 0.988, 0.923]

fig, ax = plt.subplots(figsize=(140 / 25.4, 65 / 25.4))
w = 0.25
xs = list(range(len(suites)))

bars1 = ax.bar([x - w for x in xs], v6b_util, width=w, label="v6b benign utility (undefended)",
               color="0.85", edgecolor="black")
bars2 = ax.bar(xs, v6_util, width=w, label="v6 benign utility (defended)",
               color="0.55", edgecolor="black", hatch="//")
bars3 = ax.bar([x + w for x in xs], m1_cont, width=w, label="M1 containment (assumed compromise)",
               color="0.15", edgecolor="black")

ax.set_xticks(xs)
ax.set_xticklabels(suites, fontsize=7)
ax.set_ylabel("rate")
ax.set_ylim(0, 1.30)
ax.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
ax.legend(fontsize=6, loc="upper center", ncol=2, frameon=True)
ax.grid(axis="y", linestyle=":", linewidth=0.5, color="0.7")

fig.tight_layout(rect=[0, 0, 1, 0.96])
fig.savefig(os.path.join(OUT, "fig9_agentdojo_utility_containment.png"), dpi=600)
plt.close(fig)

# ---------------------------------------------------------------------------
# Fig S1: PRISMA 2020 literature selection flow diagram
# Source: docs/lit-review/prisma-counts.json
# ---------------------------------------------------------------------------
def make_figS1_prisma():
    import json

    import matplotlib.patches as patches
    counts_path = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "lit-review", "prisma-counts.json")
    with open(counts_path, encoding="utf-8") as f:
        c = json.load(f)

    fig, ax = plt.subplots(figsize=(155 / 25.4, 125 / 25.4), dpi=600)
    ax.set_xlim(0, 155)
    ax.set_ylim(0, 125)
    ax.axis("off")

    def box(x, y, w, h, title, detail="", fc="#F4F4F4"):
        p = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6", linewidth=0.8, edgecolor="#222222", facecolor=fc)
        ax.add_patch(p)
        if detail:
            ax.text(x + w / 2, y + h * 0.64, title, fontsize=6.5, fontweight="bold", ha="center", va="center", color="#111111")
            ax.text(x + w / 2, y + h * 0.30, detail, fontsize=5.6, ha="center", va="center", color="#333333")
        else:
            ax.text(x + w / 2, y + h / 2, title, fontsize=6.5, fontweight="bold", ha="center", va="center", color="#111111")

    def arrow(x1, y1, x2, y2):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", lw=0.8, color="#222222"))

    # Main vertical chain (left) and exclusions (right)
    mw, mh = 86, 12
    ew, eh = 56, 12
    mx, ex = 4, 96
    ys = [110, 92, 74, 56, 38, 20, 3]

    box(mx, ys[0], mw, mh,
        f"Records identified (n = {c['identified_database']:,})",
        "OpenAlex, arXiv, Semantic Scholar (6 strings x 3 sources)")
    box(mx, ys[1], mw, mh,
        f"Unique records after deduplication (n = {c['unique']:,})",
        "Deduplicated by DOI, arXiv ID, and normalized title")
    box(ex, ys[1], ew, mh,
        f"Duplicates removed (n = {c['duplicates_removed']:,})", "", fc="#FAFAFA")

    box(mx, ys[2], mw, mh,
        f"Passed deterministic pre-filter (n = {c['title_screened']:,})",
        "Requires LLM term + agent term (+7 rescued in recall audit)")
    pr = c["prefilter_reasons"]
    box(ex, ys[2], ew, mh,
        f"Pre-filter excluded (n = {c['prefilter_excluded']:,})",
        f"E6: {pr['E6']}, E3: {pr['E3']}, E1: {pr['E1']}, E2: {pr['E2']}", fc="#FAFAFA")

    box(mx, ys[3], mw, mh,
        f"Passed title screening (n = {c['abstract_assessed']:,})",
        "Single primary screener against I1-I3 / E1-E6")
    tr = c["title_reasons"]
    box(ex, ys[3], ew, mh,
        f"Title excluded (n = {c['title_excluded']:,})",
        f"E6: {tr['E6']}, E3: {tr['E3']}, E1: {tr['E1']}, E2: {tr['E2']}", fc="#FAFAFA")

    box(mx, ys[4], mw, mh,
        f"Included from databases (n = {c['included_database']:,})",
        "Abstract assessment completed")
    ar = c["abstract_reasons"]
    box(ex, ys[4], ew, mh,
        f"Abstract excluded (n = {c['abstract_excluded']:,})",
        f"E3: {ar['E3']}, E6: {ar['E6']}, E5: {ar['E5']}", fc="#FAFAFA")

    box(mx, ys[5], mw, mh,
        f"Snowballing additions (n = {c['included_snowball']:,})",
        f"1 round on 43 core works: {c['snowball_identified']} identified -> {c['included_snowball']} included")
    box(ex, ys[5], ew, mh,
        f"Snowball excluded (n = {c['snowball_prefilter_excluded'] + c['snowball_title_excluded']:,})",
        f"Pre-filter: {c['snowball_prefilter_excluded']}, Title: {c['snowball_title_excluded']}", fc="#FAFAFA")

    box(mx, ys[6], mw, mh,
        f"Total studies included (n = {c['included_total']:,})",
        "607 database + 114 snowballing (26 core works hand-coded)", fc="#E8E8E8")

    for i in range(len(ys) - 1):
        arrow(mx + mw / 2, ys[i], mx + mw / 2, ys[i + 1] + mh)
    for y in ys[1:6]:
        arrow(mx + mw, y + mh / 2, ex, y + mh / 2)

    fig.tight_layout(pad=0.3)
    fig.savefig(os.path.join(OUT, "figS1_prisma_flow.png"), dpi=600)
    plt.close(fig)

make_figS1_prisma()

print("Figures written to", OUT)
for f in sorted(os.listdir(OUT)):
    print(" -", f)

