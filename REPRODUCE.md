# Reproducing GUIDE

**Current scope correction:** Universal synthesis preservation and least-element optimality are not established; numeric authority is not exact at argument level, and sensitivity/input robustness gaps remain. See [claim-scope-corrections.md](audit/claim-scope-corrections.md). These are disclosed limitations, not code fixes.


## Environment

Use a fresh Python 3.12 environment; do not copy a virtual environment from another laptop.

```sh
uv sync --frozen --extra dev --extra agentdojo
uv run --frozen --extra dev --extra agentdojo pytest -q
uv run --frozen --extra dev --extra agentdojo ruff check src tests scripts
uv run --frozen --extra dev --extra agentdojo mypy
uv run --frozen --extra dev --extra agentdojo python scripts/check_boundaries.py
```

`uv.lock` records the imported development resolution. This final review used a separate compatibility environment where necessary; see `results/verification/` for the actual outcome and package versions. A successful compatibility run does not certify a fresh frozen-lock installation.

## Model-free analyses

Run these from the repository root in the environment above. They require no provider keys or paid model calls, although installing packages requires network access.

```sh
python scripts/v9/exhaustive_bound.py B
python -m guide_agentdojo.bound
python scripts/run_offline_ablations.py
```

The final command writes `results/offline/component_audit.json`, keeping the imported `stage7d_ablations.json` intact. It executes policy-transformed arguments and measures benign-call admissibility, not task success. Tool execution errors can affect observation state; lack of denial alone does not prove objective completion. Retrospective split labels do not establish untouched held-out evaluation.

Other historical re-aggregation commands may overwrite their designated summary files: preserve the supplied data first. `experiments/results/` contains historical provider runs, while `results/reproduction/` contains imported audit outputs. Their original paths and timestamps are provenance, not promises that every external source is still available.

## Limits

- Five transcripts underlying the 1,575-run replay aggregate are missing. This aggregate cannot be independently regenerated.
- Historical live runs need provider access to repeat; aliases and model behavior may have changed. The current hardening has not been evaluated in fresh live runs.
- No official CaMeL, Progent or FIDES head-to-head evaluation was completed.
- The future live protocol was incomplete and is not distributed as an executed or frozen confirmatory study.
- Static bounds assume accurate effect metadata, complete mediation, fixed acyclic workflows and a trusted monitor. Framework guard adapters do not exercise all core controls.
- Mined example counts do not estimate production prevalence. Reference metadata checks do not establish every cited technical claim.

See the manuscript and `audit/current-assessment.md` for the corresponding claim restrictions.
