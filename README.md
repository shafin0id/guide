# GUIDE

GUIDE is a research prototype for an external reference monitor and static effect-reachability analysis of fixed acyclic multi-agent LLM workflows.

The contribution is a conditional workflow bound, trace-driven permission reduction, and an empirical account of the security–utility trade-off. It does not guarantee safe content in authorized calls, deployment security for arbitrary frameworks, or immunity to prompt injection.

Known release limitations include counterexamples to general synthesis preservation and optimality, incomplete numeric argument modelling, a sensitivity-check gap for tools without column selection, and malformed-input exceptions. These are disclosed, not fixed, in this release. See [claim corrections](audit/claim-scope-corrections.md).

## Layout

- `src/guide/`: core policy enforcement, signing, routing and trace ledger.
- `src/guide_research/`: blast-radius analysis, provenance checks and synthesis.
- `src/guide_agentdojo/`, `src/guide_realworld/`, `src/guide_bench/`: evaluation adapters and tasks.
- `tests/` and `scripts/`: regression tests and reproducible analyses.
- `experiments/`: historical raw data and mining inputs.
- `results/`: recorded offline and statistical analyses, with current checks under `results/verification/`.
- `audit/`: claim-to-evidence records, assumptions and outstanding limitations.
- `environments/` and `uv.lock`: recorded dependency information.

The repository integrates the revised code directly; no separate version-2 workspace is required. Document-generation scripts and personal review drafts are excluded.

## Setup

For the recorded development dependency resolution, use Python 3.12 and:

```sh
uv sync --frozen --extra dev --extra agentdojo
uv run --frozen --extra dev --extra agentdojo pytest -q
```

A minimal core install is `pip install .`. Framework dependencies are separate; see `environments/realworld-freeze.txt`. There is no `realworld` package extra.

Read [REPRODUCE.md](REPRODUCE.md) and [the current assessment](audit/current-assessment.md) before interpreting results. Historical live outcomes predate the hardened implementation and must not be described as fresh live measurements of this release.
