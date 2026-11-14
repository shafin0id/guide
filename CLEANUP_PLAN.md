# GUIDE repository cleanup plan (public release)

You are cleaning the GUIDE repository at `/Users/shafinoid/ITQAN/GitHub/guide` for a public academic and professional
release, then pushing it to `origin/main`. Follow the phases in order. Do not skip a verification step. If a step fails
and the fix is not obvious, stop and report instead of improvising.

## 0. Ground rules

- Never commit secrets. `.env` and `.env.gemini_keys` hold real API keys. They must stay untracked and must never be
  printed, copied into a file, or committed.
- Do not change any number in `experiments/`, any frozen protocol file, or any research logic in `src/`. This is a
  cleanup, not a re-analysis.
- Do not rewrite `README.md`. It was written and checked against the results. Only fix links in it if a path changes
  and a link breaks.
- Back up before deleting (Phase 1). The owner needs the private files later.
- Do not force-push. Do not rewrite git history unless Phase 10 is explicitly approved by the owner.
- Commit after each phase with a clear message, so each phase can be reverted on its own.
- Host memory is limited. Run tests once at the end, not after every phase.

## 1. Prepare and back up

```bash
cd /Users/shafinoid/ITQAN/GitHub/guide
git status
git fetch origin
git switch step3-protocol-v9
git switch -c cleanup/public-release
mkdir -p ~/ITQAN/GUIDE-private-archive
rsync -a --exclude .venv --exclude .venv-rw --exclude .git ./ ~/ITQAN/GUIDE-private-archive/
```

Check that `~/ITQAN/GUIDE-private-archive/docs/paper` and the two university folders exist in the backup before going on.

Facts already checked, for your context:
- `origin/main` and local `main` are at `8ce14d5`. `step3-protocol-v9` is 17 commits ahead and is a fast-forward of main.
- No API key appears in any tracked file or in git history. Keep it that way.
- About 7,700 files are tracked. About 6,000 of them are AgentDojo run logs under `experiments/results/step3/runs/`.

## 2. Stop tracking local and tool files

```bash
git rm -r --cached .kiro
git rm --cached "docs/paper/out/~\$nuscript-draft.docx"
```

Append to `.gitignore` (keep the existing lines):

```gitignore
# local tooling and environments
.kiro/
.venv-rw/
.hypothesis/
.mypy_cache/
.ruff_cache/
.env.gemini_keys
~$*
```

Run `git status --short` and confirm that `.env`, `.env.gemini_keys`, `.venv`, `.venv-rw` and `.kiro` do not appear.
Commit: `chore: stop tracking local tool settings and caches`.

## 3. Remove private and third-party documents

These are not the author's to publish, or they are drafts of a paper under journal review.

```bash
git rm -r "previously submitted to university"
git rm -r "supporting documents from supervisor"
git rm -r docs/paper
```

Also delete these untracked folders from the working tree. They are already in the backup.

```bash
rm -r "docs/paper"   # if anything untracked remains, for example "Final Submission [read only for ai]" and revision-v2 drafts
```

Commit: `chore: remove private university material and manuscript drafts`.

## 4. Remove internal planning and AI hand-off documents

Delete these files from `docs/`. They are working notes, run plans and prompts for AI tools, not documentation.

```text
docs/agentdojo-baseline-handoff-prompt.md
docs/agentdojo-baseline-run-plan.md
docs/agentdojo-handoff-prompt.md
docs/agentdojo-run-plan.md
docs/final-run-handoff-prompt.md
docs/final-run-plan.md
docs/handoff-prompt-complete-gemini-main.md
docs/paper-plan.md
docs/static-analysis-extensions-plan.md
docs/step3-plan.md
docs/novelty.md
docs/references-final.md
docs/submission-alignment.md
```

Move and rename:

```bash
mkdir -p docs/archive docs/protocols docs/results
git mv docs/research-audit.md docs/archive/research-audit.md
git mv docs/protocol-v9a.md docs/protocols/protocol-v9a.md
git mv docs/protocol-v9b.md docs/protocols/protocol-v9b.md
git mv docs/step3-results.md docs/results-v9.md
git mv docs/final-run-results.md docs/results/protocol-v8.md
git mv docs/static-analysis-extensions-results.md docs/results/protocol-v7.md
git mv references-final.bib docs/references.bib
git rm references.bib
```

Commit: `docs: remove internal plans and reorganise documentation`.

## 5. Rename the internal "step3" label to "v9"

"Step 3" was an internal work stage. Publicly the experiments are Protocol v9.

```bash
git mv scripts/step3 scripts/v9
git mv experiments/results/step3 experiments/results/v9
```

Then replace the path string `"step3"` with `"v9"` in exactly these files. Change only the path segment, not variable
names unless shown.

| File | Change |
|---|---|
| `src/guide_agentdojo/run_v9.py` | `/ "results" / "step3"` to `/ "results" / "v9"`, and rename the variable `STEP3` to `V9_RESULTS` everywhere in the file |
| `src/guide_agentdojo/spend.py` | `"step3" / "ledger.jsonl"` to `"v9" / "ledger.jsonl"` |
| `src/guide_realworld/run_rw.py` | `"step3" / "realworld"` to `"v9" / "realworld"` |
| `scripts/v9/analyze.py` | `"step3"` path to `"v9"`, and the generated title `Step 3 results summary (auto-generated by scripts/step3/analyze.py)` to `Protocol v9 results summary (auto-generated by scripts/v9/analyze.py)` |
| `scripts/v9/diag_m1.py`, `scripts/v9/exhaustive_bound.py`, `scripts/v9/w2_full.py`, `scripts/v9/w2_variants.py` | `"step3"` path segment to `"v9"` |
| `scripts/v9/verify_complete.py` | `S = "experiments/results/step3/"` to `S = "experiments/results/v9/"`, and `split("step3/")` to `split("v9/")` |
| `scripts/v9/v9.sh`, `scripts/v9/run_v9a.sh`, `scripts/v9/run_pi.sh` | `scripts/step3/` to `scripts/v9/` |
| `.gitignore` | `experiments/results/step3/ledger.jsonl` to `experiments/results/v9/ledger.jsonl` |

Delete one-off debugging and quota-workaround scripts:

```bash
git rm scripts/v9/debug_ag.py scripts/v9/debug_ag2.py scripts/v9/debug_tf.py scripts/v9/debug_think.py \
  scripts/v9/probe_detector.py scripts/v9/probe_frameworks.py scripts/v9/probe_gemini.py scripts/v9/progress.py \
  scripts/v9/run_gemini.sh scripts/v9/run_gemini2.sh scripts/v9/run_gemini3.sh scripts/v9/run_gemini_swap.sh
git rm -r --ignore-unmatch experiments/results/v9/runs/smoke experiments/results/v9/runs/smoke_old
```

Verify:

```bash
git grep -n "step3" -- src scripts tests .github pyproject.toml .gitignore    # must print nothing
PYTHONPATH=src .venv/bin/python scripts/v9/verify_complete.py                 # every "missing" count must be 0
```

If `verify_complete.py` reports a missing cell, the rename broke a path. Fix the path, do not touch the data.
Commit: `refactor: rename step3 working label to protocol v9`.

## 6. Remove manuscript-build tooling and failed-run leftovers

The manuscript is no longer in the repository, so its build scripts have nothing to build.

```bash
git rm scripts/paper/build_apa_refs.py scripts/paper/build_complete_manuscript.py scripts/paper/build_docx.py \
  scripts/paper/finalize_refs.py scripts/paper/make_reference_style.py scripts/paper/validate_manuscript.py \
  scripts/paper/verify_docx_numbers.py scripts/paper/generate_numbers.py
git rm -r scripts/final scripts/lit
```

Keep `scripts/paper/make_figures.py`, `scripts/paper/figures/`, `scripts/check_boundaries.py` and
`scripts/aggregate_protocol_v5.py`. Before deleting `scripts/final` and `generate_numbers.py`, run
`git grep -n "generate_numbers\|run_final\|scripts.final\|scripts/lit" -- src tests scripts .github` and confirm only
the deleted files refer to them. If a test imports them, keep the module and report it.

Remove failed or abandoned run artifacts. They are excluded from every reported result, and they stay in git history
at tag `paper-v1`.

```bash
git ls-files experiments | grep -E "\.failed-|abandoned" | xargs -I{} git rm "{}"
```

In `docs/experiments.md`, wherever these files are mentioned, add one sentence saying the excluded failed attempts
are preserved at git tag `paper-v1`. Do not change any number.
Commit: `chore: remove manuscript build tooling and excluded run artifacts`.

## 7. Clean the remaining documentation

For each kept file in `docs/` (including `docs/lit-review/*.md`, `docs/results/*.md`, `docs/results-v9.md` and
`docs/protocols/*.md`):

1. Fix every link and path that points to a moved or deleted file. Use
   `grep -rn "docs/\|step3\|manuscript-draft\|handoff\|run-plan" docs README.md REPRODUCE.md` to find them.
2. Remove text that is only internal working notes: mentions of AI coding assistants or their models, prompts, API
   budgets in CNY or USD, personal balance figures, "fill this in" placeholders such as `Executor / model: ___`, and
   lines like "Spec: docs/final-run-plan.md". Keep every research fact, number, deviation and limitation.
3. In `docs/results-v9.md`, remove the paragraph that tells the reader to revoke API keys and any sentence about free
   or paid Gemini keys beyond "the Gemini replication was limited to 20 pairs by the free-tier request quota".
4. Do not edit frozen protocol content in `docs/protocols/`, except for broken links.

Commit: `docs: remove internal notes and fix links`.

## 8. Update metadata and reproduction guide

`pyproject.toml`:
- `version = "0.4.0"`.
- `description = "GUIDE: an external reference monitor that bounds the blast radius of compromised agents in LLM multi-agent systems (research prototype)"`.
- Remove `python-docx` from the core `dependencies` list. Nothing in `src/` or `tests/` imports it after Phase 6.
  Check with `git grep -n "import docx\|from docx" -- src tests scripts` before removing.
- Move `matplotlib` from core `dependencies` to a new extra `figures = ["matplotlib>=3.10.9"]`, and add it to the
  `dev` extra too. Check with `git grep -n "matplotlib" -- src tests` first. If `src/` imports it, leave it as it is.
- Leave `agentdojo==0.1.35` and `cryptography` as they are.
- Add `guide-agentdojo-v9 = "guide_agentdojo.run_v9:main"` to `[project.scripts]` if it is missing.

Regenerate the lock file: `uv lock`.

`CITATION.cff`:
- `title: "GUIDE: An External Reference Monitor That Bounds the Blast Radius of Compromised Agents in LLM Multi-Agent Systems"`
- `version: "0.4.0"` and `date-released:` today's date.
- Keep the author and ORCID.

`REPRODUCE.md`. Rewrite it so it matches the published table and figure numbering below. For each item keep the
existing fields (protocol, inputs, command, outputs, API cost, git tag) and update paths for Phases 4 to 6. Remove
every section about building or verifying the Word manuscript, pandoc, `check_numbers`, and `docs/paper`. Update the
environment section to `git checkout main` and `uv sync --all-extras`, and add the `.venv-rw` set-up from `README.md`.

| Item | Content | Source |
|---|---|---|
| Table 1 | Comparison of security mechanisms | literature review |
| Table 2 | Research questions, objectives, hypotheses, evidence | design |
| Table 3 | Metrics and definitions | `docs/evaluation.md` |
| Table 4 | Deviations from the proposal | `docs/experiments.md` |
| Table 5 | Violation rate under assumed compromise, K1 to K4 | `experiments/results/v2-compromised/` |
| Table 6 | Assumed-compromise replay on AgentDojo | `experiments/results/compromise-replay-v8/` |
| Table 7 | Bound prediction versus runtime containment | `experiments/results/compromise-replay-v8/` |
| Table 8 | AgentDojo defended (v6) versus undefended (v6b) | `experiments/results/agentdojo-v6*/` |
| Table 9 | Utility-cost prediction confusion matrix | `experiments/results/final-v8/v7a_attributable_loss.json` |
| Table 10 | Structural census of 55 configurations | `experiments/results/topology-v8/` |
| Table 11 | Configuration mining funnel | `experiments/mining/` |
| Table 12 | Nominal performance across model families | `experiments/results/v2-main/`, `experiments/results/v5-main-*/` |
| Table 13 | Defenses on AgentDojo (Protocol v9a) | `experiments/results/v9/summary.md` |
| Table 14 | Framework applications (Protocol v9b) | `experiments/results/v9/realworld/main/rows.jsonl` |
| Figures 1 to 7, S1, S2 | Generated by `scripts/paper/make_figures.py` | `scripts/paper/figures/` |

Commit: `docs: update metadata and reproduction guide`.

## 9. Verify everything, then push

Run each check. All must pass.

```bash
uv sync --all-extras
uv run ruff check src tests scripts
uv run python scripts/check_boundaries.py
uv run mypy
uv run pytest -q
PYTHONPATH=src uv run python scripts/v9/verify_complete.py
PYTHONPATH=src uv run python scripts/v9/analyze.py > /dev/null && git diff --stat experiments/results/v9/summary.md
uv build
```

Expected results:
- `pytest`: all tests pass. If `tests/unit/test_blast_radius.py::test_property_coverage_is_not_vacuous` fails only
  when run alone or in a changed order, that is a known ordering fragility of a Hypothesis test, so report it and do not
  modify the test.
- `analyze.py` must not change any number in `summary.md`. Only the generated title line may differ.
- `ruff` errors in files you did not touch were already there. Fix only errors your changes introduced.

Secret scan. Every command must print nothing.

```bash
git grep -n -I -E "sk-[a-f0-9]{32}|AQ\.Ab8RN6|AIza[0-9A-Za-z_-]{30}|gsk_[A-Za-z0-9]{20}"
git ls-files | grep -E "(^|/)\.env$|\.env\.gemini_keys|\.kiro/"
```

Link check: `grep -rnoE "\]\(([^)]+\.md)\)" README.md REPRODUCE.md docs` and confirm every linked file exists.

Final structure check. `git ls-files | awk -F/ '{print $1}' | sort -u` should show only:
`.github .gitignore .env.example CITATION.cff LICENSE README.md REPRODUCE.md docs experiments pyproject.toml scripts src tests uv.lock`.

Delete this plan file, then merge and push:

```bash
git rm CLEANUP_PLAN.md
git commit -m "chore: remove cleanup plan"
git switch main
git merge --ff-only cleanup/public-release
git push origin main
git push origin --tags
```

If `--ff-only` fails because `origin/main` moved, stop and report. Do not force-push.

After the push, open the repository on GitHub and check that the README renders, including the logo block and the
badges, and that the CI workflow passes on `main`.

## 10. Optional: purge private files from history (owner approval required)

The removed university assignments and supervisor PDFs are still in git history, so anyone can recover them from older
commits. Removing them from history needs a history rewrite and a force push. This changes every commit hash and tag.
Do this only if the owner explicitly says "approved, rewrite history".

```bash
pip install git-filter-repo
git filter-repo --invert-paths \
  --path "previously submitted to university" \
  --path "supporting documents from supervisor" \
  --path docs/paper
git remote add origin https://github.com/shafin0id/guide.git
git push origin --force --all
git push origin --force --tags
```

## 11. Report back

Report to the owner:
- The commit list on `main` after the push.
- The output of the Phase 9 checks.
- Any file you kept that this plan said to delete, or deleted that it said to keep, and why.
- Any test, lint or link problem you could not fix.
- A reminder to revoke and regenerate every API key that was used during the project.
