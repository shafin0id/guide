# Results: `experiments/results/main-rescored`

Runs analysed: 360; harness errors: 0.

## Per condition (mean, 95% task-cluster bootstrap CI)

| Condition | runs | task success | intent fidelity | violation rate | completed | trace compl. | median tokens [IQR] | median wall s [IQR] | model calls |
|---|---|---|---|---|---|---|---|---|---|
| P | 90 | 0.967 [0.911, 1.000] | 0.979 [0.944, 1.000] | 0.000 [0.000, 0.000] | 0.967 | 1.000 | 3206 [2601, 4192] | 4.7 [3.9, 6.1] | 4.2 |
| B1 | 90 | 0.967 [0.911, 1.000] | 0.974 [0.933, 1.000] | 0.000 [0.000, 0.000] | 0.967 | 0.000 | 3550 [2610, 5682] | 4.2 [3.6, 7.1] | 4.3 |
| B2 | 90 | 0.967 [0.911, 1.000] | 0.978 [0.942, 1.000] | 0.000 [0.000, 0.000] | 0.967 | 0.000 | 3350 [2533, 4128] | 4.5 [3.8, 6.3] | 4.2 |
| GPLUS | 90 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 3130 [2586, 4263] | 4.8 [3.9, 6.3] | 4.3 |

## Paired task-level comparisons (Wilcoxon signed-rank, Pratt; Holm-adjusted per metric)

| Comparison | metric | tasks | non-zero | mean diff | W | p | p (Holm) | note |
|---|---|---|---|---|---|---|---|---|
| P vs B1 | task_success | 18 | 3 | +0.000 | 18.0 | 0.6109 | 1.0000 | fewer than 6 non-zero differences; low power |
| P vs B2 | task_success | 18 | 2 | +0.000 | 17.5 | 1.0000 | 1.0000 | fewer than 6 non-zero differences; low power |
| GPLUS vs P | task_success | 18 | 2 | +0.033 | 0.0 | 0.1575 | 0.6299 | fewer than 6 non-zero differences; low power |
| GPLUS vs B2 | task_success | 18 | 2 | +0.033 | 0.0 | 0.1575 | 0.6299 | fewer than 6 non-zero differences; low power |
| P vs B1 | intent_fidelity | 18 | 3 | +0.005 | 18.0 | 0.6109 | 1.0000 | fewer than 6 non-zero differences; low power |
| P vs B2 | intent_fidelity | 18 | 2 | +0.000 | 17.0 | 0.9678 | 1.0000 | fewer than 6 non-zero differences; low power |
| GPLUS vs P | intent_fidelity | 18 | 2 | +0.021 | 0.0 | 0.1575 | 0.6299 | fewer than 6 non-zero differences; low power |
| GPLUS vs B2 | intent_fidelity | 18 | 2 | +0.022 | 0.0 | 0.1575 | 0.6299 | fewer than 6 non-zero differences; low power |
| P vs B1 | violation | 18 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| P vs B2 | violation | 18 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| GPLUS vs P | violation | 18 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| GPLUS vs B2 | violation | 18 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |

## Proposal practical-significance criterion (P vs B2)

- best gain in success/fidelity: +0.000 (threshold +0.10)
- violation reduction: n/a (B2 has none) (threshold 50%)
- median wall-time ratio P/B2: 1.03 (threshold 1.30)
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
| T14 | 1.0 / 0.0 | 0.8 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T15 | 0.8 / 0.0 | 0.6 / 0.0 | 0.6 / 0.0 | 1.0 / 0.0 |
| T16 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T17 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T18 | 0.6 / 0.0 | 1.0 / 0.0 | 0.8 / 0.0 | 1.0 / 0.0 |
