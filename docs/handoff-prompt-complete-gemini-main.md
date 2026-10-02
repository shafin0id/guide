# Handoff prompt — complete the GUIDE protocol-v5 Gemini main suite

Paste everything below this line into the other AI tool, as-is.

---

You are operating in an existing repository at `/Users/shafinoid/Documents/GitHub/guide` (a research codebase for an MSc project, GUIDE/RMCE). You have full shell/file access to this machine. Your ONLY job is to finish one specific, narrow data-collection gap — do not touch anything else, do not refactor code, do not re-run anything that is already complete.

## Current state (verified by direct inspection of the JSONL files, not trusted from any prior report)

Four datasets exist under `/Users/shafinoid/Documents/GitHub/guide/experiments/results/`:

1. `v5-main-groq-gptoss120b/results.jsonl` — **DONE, do not touch.** 144/144 target cells completed (4 conditions × 18 tasks × 2 reps), 0 failures.
2. `v5-compromised-groq-gptoss120b/results.jsonl` — **DONE, do not touch.** 32/32 target cells completed (4 conditions × 4 tasks × 2 reps), 0 failures. (NOTE: `v5-compromised-groq-qwen/` is a separate, abandoned directory from a dead model — ignore it entirely, do not run or clean it.)
3. `v5-compromised-gemini/results.jsonl` — **DONE, do not touch.** 32/32 target cells completed, 0 failures.
4. `v5-main-gemini/results.jsonl` — **NOT DONE. This is your task.** The file has 215 total rows (because old rep-3/4/5 rows from an earlier, abandoned 360-run design are still sitting in it), but only 111 of the 144 required (condition, task, rep≤2) cells are actually `status: completed`. 33 cells are missing. Some of those 33 are `status: failed` rows already in the file; some were never attempted at all.

The 33 missing (condition, task, rep) cells are exactly:
```
B1,T01,1  B1,T01,2  B1,T02,2  B1,T05,1  B1,T09,1  B1,T11,1  B1,T14,1  B1,T15,1  B1,T17,1  B1,T18,2
B2,T01,1  B2,T04,2  B2,T06,1  B2,T06,2  B2,T07,1  B2,T15,1  B2,T15,2  B2,T17,2  B2,T18,2
GPLUS,T09,2  GPLUS,T11,1  GPLUS,T11,2  GPLUS,T12,2  GPLUS,T13,2  GPLUS,T14,1  GPLUS,T15,2  GPLUS,T18,1  GPLUS,T18,2
P,T03,1  P,T05,2  P,T09,1  P,T12,1  P,T16,2
```
(Key format in the file is `TASK|CONDITION|REP`, e.g. `T01|B1|1` — adjust string matching accordingly; the triples above are given as (condition, task, rep).)

## Why this gap exists (read before touching anything)

`guide_bench.run`'s resume-by-key logic treats **any** key already present in `results.jsonl` as "done" — including rows with `status: failed`. This means simply re-running the command does nothing: it sees the failed keys as already attempted and submits zero new work, exits instantly, and looks like a stall. **You must prune failed rows out of the results file (and the matching `transcripts.jsonl` rows, same keys) before relaunching**, or no retry will happen.

Do NOT delete or touch any `status: completed` rows. Do NOT delete rep-3/4/5 rows either — they are harmless leftover data, not part of the 144 target, and removing them is unnecessary extra risk. Only remove rows where `status == "failed"` AND the rep is 1 or 2.

## Exact steps

1. **Confirm environment first.** The Groq/Gemini API keys live in `/Users/shafinoid/Documents/GitHub/guide/.env` (root), NOT in `src/guide-bench/.env` (that one only has a DeepSeek key — this split caused real confusion before, don't repeat it). Check `GEMINI_API_KEY` is set there and has headroom:
   ```bash
   cd /Users/shafinoid/Documents/GitHub/guide
   grep GEMINI_API_KEY .env
   ```
   Gemini free tier (`gemini-3.5-flash-lite`) has historically shown a **daily request quota**, not a per-minute one — if the current key is exhausted you will see every call fail with `HTTP 429` and the response body will say `quota exceeded` with a daily reset. If that happens, STOP, do not retry blindly, and report back to the user that a fresh key is needed — do not attempt key rotation/chaining automatically; that was explicitly rejected as policy by the project owner (quota evasion). Ask for a new key if the current one is dead.

2. **Prune only the failed rep≤2 rows** (use the Python snippet below exactly — it is scoped to leave completed rows and rep>2 rows untouched):
   ```bash
   cd /Users/shafinoid/Documents/GitHub/guide/experiments/results/v5-main-gemini
   python3 -c "
import json

def keep(line):
    r = json.loads(line)
    k = r.get('key', '')
    parts = k.split('|')
    if len(parts) != 3:
        return True  # malformed key, leave alone, don't guess
    task, cond, rep = parts
    try:
        rep = int(rep)
    except ValueError:
        return True
    if r.get('status') == 'failed' and rep <= 2:
        return False  # drop it so it can be retried
    return True

for fname in ('results.jsonl', 'transcripts.jsonl'):
    kept = []
    with open(fname) as f:
        for line in f:
            line = line.rstrip('\n')
            if not line:
                continue
            if keep(line):
                kept.append(line)
    with open(fname, 'w') as f:
        f.write('\n'.join(kept) + '\n')
    print(fname, 'rows kept:', len(kept))
"
   ```

3. **Relaunch the run, targeting exactly 2 reps, same model/settings as the completed 111 cells** (`gemini-3.5-flash-lite`, `--model-seed none` — Gemini's OpenAI-compat shim rejects a real seed value, this is a known, already-disclosed deviation, do not change it):
   ```bash
   cd /Users/shafinoid/Documents/GitHub/guide/src/guide_bench
   nohup guide-bench --suite main --reps 2 \
     --model gemini-3.5-flash-lite --model-seed none \
     --out-dir ../../experiments/results/v5-main-gemini \
     --env-file ../../.env \
     > ../../experiments/results/v5-main-gemini/run.log 2>&1 &
   echo "launched PID $!"
   ```
   (If the actual CLI flag names differ from what's shown — check `guide-bench --help` or read `src/guide_bench/run.py`'s `argparse` setup first; don't guess flag names, confirm them.)

4. **Poll for completion**, checking real completion status, not just row count (this project has twice mistaken a padded row count for a finished run — do not repeat that):
   ```bash
   cd /Users/shafinoid/Documents/GitHub/guide/experiments/results/v5-main-gemini
   python3 -c "
import json
cells = set()
with open('results.jsonl') as f:
    for line in f:
        r = json.loads(line)
        if r.get('status') != 'completed':
            continue
        k = r.get('key', '')
        parts = k.split('|')
        if len(parts) != 3:
            continue
        task, cond, rep = parts
        rep = int(rep)
        if rep <= 2:
            cells.add((cond, task, rep))
print('completed rep<=2 cells:', len(cells), '/ 144')
"
   ```
   Repeat this check every few minutes (Gemini's daily quota means this may take hours or need to resume tomorrow — do not force it or spam retries past 429 daily-cap responses).

5. **Stop condition:** when the check in step 4 reports exactly 144, you are done. Do not run more reps, do not change the target. Report the final count back to the user plainly.

## Hard constraints — do not violate these

- Do not touch `v5-main-groq-gptoss120b/`, `v5-compromised-groq-gptoss120b/`, or `v5-compromised-gemini/` — they are finished and verified.
- Do not touch `v5-compromised-groq-qwen/` or `v5-main-groq-qwen.abandoned-qwen-tpd-exhausted/` — dead, abandoned, out of scope.
- Do not modify `src/guide/providers.py`, `src/guide_bench/run.py`, or any other source file unless a command fails for a reason that requires a code fix (e.g. a missing CLI flag) — if so, make the smallest possible fix, run the existing test suite (`pytest` from repo root, or whatever the project's actual test command is — check for a `Makefile`/`pyproject.toml` first) and confirm all tests still pass before using the changed code for real data collection.
- Do not attempt to rotate, chain, or round-robin multiple API keys automatically. If a key is quota-exhausted, stop and ask the user for a new one.
- Do not re-run or "clean up" anything outside `v5-main-gemini/`.
- When you report back, report **actual completed-cell counts verified by a script**, not raw line counts in the JSONL file — this exact distinction has caused repeated false "done" reports in this project.

## When finished

Report: final completed-cell count (should be 144/144), any failures encountered and their HTTP status/reason, whether a key swap was needed, and confirm no other dataset or file was modified.
