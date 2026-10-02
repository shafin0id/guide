# Results: `experiments/results/v5-main-gemini`

Runs analysed: 248; harness errors: 0.

## Per condition (mean, 95% task-cluster bootstrap CI)

| Condition | runs | task success | intent fidelity | violation rate | completed | trace compl. | median tokens [IQR] | median wall s [IQR] | model calls |
|---|---|---|---|---|---|---|---|---|---|
| P | 60 | 0.967 [0.891, 1.000] | 0.994 [0.982, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 2596 [2222, 3260] | 5.1 [4.5, 17.0] | 4.1 |
| B1 | 62 | 0.935 [0.797, 1.000] | 0.989 [0.966, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 0.000 | 2642 [2308, 4159] | 4.9 [4.0, 10.1] | 4.1 |
| B2 | 64 | 0.969 [0.895, 1.000] | 0.995 [0.982, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 0.000 | 2439 [2251, 3359] | 5.2 [4.3, 11.4] | 4.1 |
| GPLUS | 62 | 0.968 [0.893, 1.000] | 0.995 [0.982, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 2714 [2212, 3452] | 5.2 [4.5, 9.1] | 4.1 |

## Paired task-level comparisons (Wilcoxon signed-rank, Pratt; Holm-adjusted per metric)

| Comparison | metric | tasks | non-zero | mean diff | W | p | p (Holm) | note |
|---|---|---|---|---|---|---|---|---|
| P vs B1 | task_success | 18 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| P vs B2 | task_success | 18 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| GPLUS vs P | task_success | 18 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| GPLUS vs B2 | task_success | 18 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| P vs B1 | intent_fidelity | 18 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| P vs B2 | intent_fidelity | 18 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| GPLUS vs P | intent_fidelity | 18 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| GPLUS vs B2 | intent_fidelity | 18 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| P vs B1 | violation | 18 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| P vs B2 | violation | 18 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| GPLUS vs P | violation | 18 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| GPLUS vs B2 | violation | 18 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |

## Proposal practical-significance criterion (P vs B2)

- best gain in success/fidelity: -0.000 (threshold +0.10)
- violation reduction: n/a (B2 has none) (threshold 50%)
- median wall-time ratio P/B2: 0.99 (threshold 1.30)
- **criterion met: False**

## Per task: success / violation rate

| Task | P | B1 | B2 | GPLUS |
|---|---|---|---|---|
| T01 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T02 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T03 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T04 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T05 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T06 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T07 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T08 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T09 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T10 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T11 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T12 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T13 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T14 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T15 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T16 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| T17 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T18 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
