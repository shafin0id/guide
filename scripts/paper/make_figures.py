"""Generate the paper's figures from verified numbers in docs/experiments.md and docs/formal_model.md.

Black-and-white / greyscale only, per user instruction. Runs single-process, closes each figure
immediately to keep memory low under tight host conditions. No invented data: every number below
is copied from the markdown tables already verified in docs/experiments.md.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os

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
MODEL_MARKER = {"DeepSeek": "o", "Gemini": "s", "Groq GPT-OSS-120B": "^"}

# ---------------------------------------------------------------------------
# Fig 4: Task success + intent fidelity by condition, per model (dot-whisker)
# Source: docs/experiments.md "Main Suite: Cross-Model Comparison"
# ---------------------------------------------------------------------------
main_suite = {
    "DeepSeek": {
        "B1": (0.989, 0.967, 1.000, 0.999),
        "B2": (1.000, 1.000, 1.000, 1.000),
        "P":  (0.989, 0.967, 1.000, 0.999),
        "GPLUS": (1.000, 1.000, 1.000, 1.000),
    },
    "Gemini": {
        "B1": (0.935, 0.797, 1.000, 0.989),
        "B2": (0.969, 0.895, 1.000, 0.995),
        "P":  (0.967, 0.891, 1.000, 0.994),
        "GPLUS": (0.968, 0.893, 1.000, 0.995),
    },
    "Groq GPT-OSS-120B": {
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
fig.suptitle("Fig. 4. Main-suite task success\nby condition and model (mean, 95% CI)", fontsize=7, y=0.995)
fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig(os.path.join(OUT, "fig4_main_suite_success.png"), dpi=600, bbox_inches="tight")
plt.close(fig)

# ---------------------------------------------------------------------------
# Fig 5: Containment heatmap under assumed compromise, per model
# Source: docs/experiments.md "Assumed-Compromise Suite: Containment Across Models"
# cell = violation rate (task success in parens is the complement; we plot violation rate)
# ---------------------------------------------------------------------------
compromise = {
    "DeepSeek": {
        "K1": {"B1": 0.00, "B2": 0.00, "P": 0.00, "GPLUS": 0.00},
        "K2": {"B1": 1.00, "B2": 1.00, "P": 0.00, "GPLUS": 0.00},
        "K3": {"B1": 1.00, "B2": 1.00, "P": 1.00, "GPLUS": 0.00},
        "K4": {"B1": 1.00, "B2": 1.00, "P": 0.00, "GPLUS": 0.00},
    },
    "Gemini": {
        "K1": {"B1": 0.00, "B2": 0.00, "P": 0.00, "GPLUS": 0.00},
        "K2": {"B1": 1.00, "B2": 1.00, "P": 0.00, "GPLUS": 0.00},
        "K3": {"B1": 1.00, "B2": 1.00, "P": 1.00, "GPLUS": 0.00},
        "K4": {"B1": 1.00, "B2": 1.00, "P": 0.00, "GPLUS": 0.00},
    },
    "Groq GPT-OSS-120B": {
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
fig.suptitle("Fig. 5. Violation rate under assumed compromise, by condition and model", fontsize=8)
fig.tight_layout(rect=[0, 0, 1, 0.90])
fig.savefig(os.path.join(OUT, "fig5_compromise_heatmap.png"), dpi=600)
plt.close(fig)

# ---------------------------------------------------------------------------
# Fig 7: Overhead (median wall time per condition, DeepSeek; framework-only time)
# Source: docs/experiments.md main suite table (median wall s) + overhead test section
# ---------------------------------------------------------------------------
wall_s = {"B1": 3.9, "B2": 4.2, "P": 4.3, "GPLUS": 4.5}
framework_ms = {"B1": 0.16, "B2": 0.23, "P": 1.68, "GPLUS": 1.69}

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(140 / 25.4, 55 / 25.4))
ax1.bar(range(len(CONDITIONS)), [wall_s[c] for c in CONDITIONS],
        color=[SHADE[c] for c in CONDITIONS], edgecolor="black",
        hatch=[HATCH[c] for c in CONDITIONS])
ax1.set_xticks(range(len(CONDITIONS))); ax1.set_xticklabels(CONDITIONS)
ax1.set_ylabel("median wall time (s)")
ax1.set_title("(a) end-to-end, DeepSeek", fontsize=7)
ax1.grid(axis="y", linestyle=":", linewidth=0.5, color="0.7")

ax2.bar(range(len(CONDITIONS)), [framework_ms[c] for c in CONDITIONS],
        color=[SHADE[c] for c in CONDITIONS], edgecolor="black",
        hatch=[HATCH[c] for c in CONDITIONS])
ax2.set_xticks(range(len(CONDITIONS))); ax2.set_xticklabels(CONDITIONS)
ax2.set_ylabel("framework-only time (ms)")
ax2.set_title("(b) scripted model, no provider latency", fontsize=7)
ax2.grid(axis="y", linestyle=":", linewidth=0.5, color="0.7")

fig.suptitle("Fig. 7. Overhead by condition: end-to-end vs. framework-only", fontsize=8)
fig.tight_layout(rect=[0, 0, 1, 0.90])
fig.savefig(os.path.join(OUT, "fig7_overhead.png"), dpi=600)
plt.close(fig)

# ---------------------------------------------------------------------------
# Fig 8: Degraded-agent sequence A12 (cumulative completed runs over 20 runs)
# Source: docs/experiments.md "A12 sequence" bullet
# B2 0/20; P(routing) 19/20 one warm-up failure then recovers; GPLUS 20/20;
# GPLUS-redispatch 19/20; GPLUS-routing(static routing, redispatch rescues) 20/20
# ---------------------------------------------------------------------------
import itertools

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
    "B2 (static, static)": dict(linestyle="-", marker="", color="0.75"),
    "P (routing, no re-dispatch)": dict(linestyle="--", marker="o", color="0.5", markevery=4),
    "GPLUS (routing + re-dispatch)": dict(linestyle="-", marker="^", color="0.0", markevery=4),
    "GPLUS-redispatch (routing only)": dict(linestyle="-.", marker="s", color="0.3", markevery=4),
    "GPLUS-routing (static + re-dispatch)": dict(linestyle=":", marker="D", color="0.15", markevery=4),
}
fig, ax = plt.subplots(figsize=(85 / 25.4, 65 / 25.4))
x = list(range(1, n + 1))
for label, cum in series.items():
    ax.plot(x, cum, label=label, linewidth=1, markersize=3, **STYLE[label])
ax.set_xlabel("run number (degraded agent present throughout)")
ax.set_ylabel("cumulative completed runs")
ax.set_xlim(1, n)
ax.set_ylim(0, n + 1)
ax.legend(fontsize=5, loc="upper left", framealpha=1)
ax.grid(linestyle=":", linewidth=0.5, color="0.7")
fig.suptitle("Fig. 8. Degraded-agent sequence (A12), 20 consecutive runs", fontsize=8)
fig.tight_layout(rect=[0, 0, 1, 0.92])
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

fig, ax = plt.subplots(figsize=(85 / 25.4, 60 / 25.4))
bars = ax.bar(range(len(labels)), values, color=["0.8", "0.6", "0.4", "0.15", "0.15"],
              edgecolor="black")
ax.set_yscale("log")
ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, fontsize=6)
ax.set_ylabel("admissible recipients (log scale)")
for i, (bar, v, unb) in enumerate(zip(bars, values, is_unbounded)):
    label = "unbounded\n(domain-wide)" if unb else str(v)
    ax.text(bar.get_x() + bar.get_width() / 2, v * 1.3, label, ha="center", fontsize=6)
fig.suptitle("Fig. 6. Admissible recipients for one sink (T15), by policy", fontsize=8)
fig.tight_layout(rect=[0, 0, 1, 0.90])
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
fig.suptitle("Fig. S2. Routing simulation regret, stationary vs. drift", fontsize=8)
fig.tight_layout(rect=[0, 0, 1, 0.90])
fig.savefig(os.path.join(OUT, "figS2_routing_regret.png"), dpi=600)
plt.close(fig)

# ---------------------------------------------------------------------------
# Fig 9: AgentDojo utility vs. containment (v6b vs. v6 benign utility, M1 containment)
# Source: docs/experiments.md Protocol v6, v6b, and v8 (M1)
# ---------------------------------------------------------------------------
suites = ["Banking", "Slack", "Travel", "Workspace", "Overall"]
v6b_util = [1.000, 0.952, 0.950, 0.850, 0.918]
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
ax.set_ylim(0, 1.12)
ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
ax.legend(fontsize=6, loc="upper right")
ax.grid(axis="y", linestyle=":", linewidth=0.5, color="0.7")

fig.suptitle("Fig. 9. AgentDojo benign utility (v6b undefended vs. v6 defended) and M1 containment", fontsize=8)
fig.tight_layout(rect=[0, 0, 1, 0.92])
fig.savefig(os.path.join(OUT, "fig9_agentdojo_utility_containment.png"), dpi=600)
plt.close(fig)

print("Figures written to", OUT)
for f in sorted(os.listdir(OUT)):
    print(" -", f)

