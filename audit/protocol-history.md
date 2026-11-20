> Historical audit record imported from the separate development workspace. Its paths identify that workspace, and its completion labels are not independent certification. See current-assessment.md for the submitted release.

# Stage 3 — Protocol Chronology & Prospective-Registration Audit

Recorded: 2026-11-19 UTC  
Method: Inspected every git tag (`git for-each-ref --sort=creatordate`), commit timestamps, `manifest.json` fields, and `experiments/results/v9/ledger.jsonl` UTC timestamps.

## 1. Tag & Commit Timeline

| Tag / Commit | Type | Timestamp (+0800 / UTC) | Scope & Audit Verdict |
|---|---|---|---|
| `baseline-v0` (`ccc53f3`) | annotated tag | 2026-09-29 21:52:05 +0800 | Pre-rebuild baseline whose fabricated/harness-filled results were withdrawn (`docs/archive/research-audit.md`). |
| `protocol-v1` (`e9c378d` -> `4cbac31`) | annotated tag | 2026-09-29 22:27:56 +0800 | Froze `docs/evaluation.md` and `src/` rebuild prior to v1 runs (note manifests record `git.dirty=true` due to untracked analysis scripts). |
| `protocol-v2` (`b640698` -> `cf515c9`) | annotated tag | 2026-09-29 22:51:56 +0800 | Disclosed post-v1 amendment (D1 context order, D2 local JSON repair, D3 K1–K4 assumed compromise). |
| `protocol-v3` (`0efde6f`) | annotated tag | 2026-09-30 00:06:51 +0800 | Tag commit message reads `"Blast-radius analysis validated"` — **tagged AFTER validation, not prospectively before runs**. |
| `protocol-v4` (`00c3b5a` -> `19d8025`) | annotated tag | 2026-09-30 00:49:03 +0800 | Tag commit message reads `"Real-world configuration study validated"` — **tagged AFTER running the 19-config study**. |
| `review-protocol-v1` (`46636a2`) | lightweight tag | 2026-10-01 23:49:06 +0800 | Historical SLR protocol; underlying CSV screening/extraction records later lost (`ISS-003`). |
| `protocol-v6` (`99495de` -> `92f60e6`) | annotated tag | 2026-10-02 19:02:37 +0800 | Preceded v6 main runs (`token_usage.jsonl` Phase 1 starts `2026-10-02T11:04:26Z` = `19:04:26 +0800`; Phase 0 smoke ran earlier at `05:10Z`). Note `protocol-v6b` is cited in `REPRODUCE.md:187` but **no git tag `protocol-v6b` exists** (nor `protocol-v5`)! |
| `protocol-v7a` (`fd8acff`) | lightweight tag | 2026-10-02 23:55:32 +0800 | Static predictor run on already-collected v6 traces (rule frozen prior to computing agreement, post-hoc analysis of existing traces). |
| `protocol-v7c` (`49d3bdc`) | lightweight tag | 2026-10-02 23:57:31 +0800 | Topology refinement monotonicity & 19-config audit. |
| `protocol-v7b` (`234b7ce`) | lightweight tag | 2026-10-03 00:10:41 +0800 | Followed by two disclosed pre-metric bugfix commits (`6e946bc` broken symlink, `34be9a8` cyclic LangGraph exclusion). |
| `protocol-v8` (`e1736ed`) | lightweight tag | 2026-10-03 02:27:11 +0800 | M1 compromise replay, M1b, M2 topology theory. |
| `paper-v1` (`958b56a`) | lightweight tag | 2026-10-03 15:32:43 +0800 | First full manuscript build (pre-v9). |
| `protocol-v9a-frozen` (`1f95ffa`) | lightweight tag | 2026-11-13 21:27:59 +0800 (`13:27:59Z`) | **Chronology check**: `ledger.jsonl` records **1,294 calls BEFORE `13:27:59Z`** (starting `11:59:20Z`: DeepSeek & Gemini pilots/probes) and **28,581 calls AFTER `13:27:59Z`**. Main DeepSeek v9a grid ran AFTER the freeze, EXCEPT three disclosed post-freeze infrastructure fixes (`tool_filter` v2 re-implementation, `pi_detector` 512-token truncation mid-run, last-message handling). |
| `protocol-v9b-frozen` (`f8fc18c`) | lightweight tag | 2026-11-13 22:03:25 +0800 (`14:03:25Z`) | Preceded main 720-run framework execution (`rw:*` ledger entries occur after `14:03Z`). |
| `protocol-v9c-frozen` (`caf8643`) | lightweight tag | 2026-11-13 22:06:23 +0800 (`14:06:23Z`) | Preceded main 30-pair adaptive loop; 21 initial runs failed with YAML `ParserError`/`ScannerError` before post-freeze YAML-sanitization fix, then all 120 cells completed cleanly. |
| `protocol-v9g-frozen` (`98b4ae8`) | lightweight tag | 2026-11-14 00:47:35 +0800 (`16:47:35Z`) | **Nuance**: Tag `protocol-v9g-frozen` was actually placed on Addendum `v9g-2` (the aborted 80-pair funded Gemini expansion), NOT on `v9g-3` (`9158ba7`, 7 minutes later at `00:54:41 +0800`), which reverted to the 20-pair free-tier plan! Furthermore, `protocol-v9a.md:56` already noted `"Pilot: undefended attack success 15/20 on this model"` BEFORE `v9g-frozen`, and the final reported `none` block also got `15/20` — raising the possibility that the 20 pairs overlapped the pilot (non-disjoint pilot/evaluation). |

## 2. Key Chronology Discrepancies Affecting Claims

1. **Missing advertised tags**: `REPRODUCE.md` cites git tags `protocol-v5` and `protocol-v6b`, neither of which exists in `git tag -l`.
2. **Post-run vs pre-run tags**: `protocol-v3` and `protocol-v4` were tagged AFTER validation (not strictly prospective pre-registration). The manuscript sentence `"All the evaluation protocols were frozen into version control prior to the respective runs"` (`P0120`) is **overbroad** and must be qualified accurately.
3. **Variant-selection rule contradiction (`ISS-014`)**: `w2_variants.py` was frozen before v9a main runs, and its pre-registered rule selected **`strict`**, NOT `flexI_cred` (which missed the `-2 pp` dev containment floor by `-3.9 pp`). Running `flexI_cred` live was a manual Pareto-exploration choice, NOT the output of the frozen selection rule.
4. **Mid-run infrastructure mutations in v9a/v9c/v9g**: `tool_filter` v1 (466 rows discarded, replaced by v2), `pi_detector` (truncated to 512 tokens mid-run), adaptive YAML sanitization (21 failed rows retried), and Gemini `PerDay` stop-rule patch (`90e1b56`). All are disclosed, but must be reflected honestly when describing protocol adherence (exploratory/amended vs strictly pre-registered confirmatory).
