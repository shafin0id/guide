# Results: `experiments/results/v2-main`

Runs analysed: 360; harness errors: 0.

## Per condition (mean, 95% task-cluster bootstrap CI)

| Condition | runs | task success | intent fidelity | violation rate | completed | trace compl. | median tokens [IQR] | median wall s [IQR] | model calls |
|---|---|---|---|---|---|---|---|---|---|
| P | 90 | 0.989 [0.967, 1.000] | 0.999 [0.996, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 3424 [2569, 4000] | 4.3 [3.6, 6.1] | 4.1 |
| B1 | 90 | 0.989 [0.967, 1.000] | 0.999 [0.996, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 0.000 | 3610 [2584, 4636] | 3.9 [3.5, 5.9] | 4.2 |
| B2 | 90 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 0.000 | 3288 [2592, 3917] | 4.2 [3.5, 6.1] | 4.1 |
| GPLUS | 90 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 3404 [2542, 3861] | 4.5 [3.6, 5.8] | 4.1 |

## Paired task-level comparisons (Wilcoxon signed-rank, Pratt; Holm-adjusted per metric)

| Comparison | metric | tasks | non-zero | mean diff | W | p | p (Holm) | note |
|---|---|---|---|---|---|---|---|---|
| P vs B1 | task_success | 18 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| P vs B2 | task_success | 18 | 1 | -0.011 | 0.0 | 0.3173 | 0.6346 | fewer than 6 non-zero differences; low power |
| GPLUS vs P | task_success | 18 | 1 | +0.011 | 0.0 | 0.3173 | 0.6346 | fewer than 6 non-zero differences; low power |
| GPLUS vs B2 | task_success | 18 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| P vs B1 | intent_fidelity | 18 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| P vs B2 | intent_fidelity | 18 | 1 | -0.001 | 0.0 | 0.3173 | 0.6346 | fewer than 6 non-zero differences; low power |
| GPLUS vs P | intent_fidelity | 18 | 1 | +0.001 | 0.0 | 0.3173 | 0.6346 | fewer than 6 non-zero differences; low power |
| GPLUS vs B2 | intent_fidelity | 18 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| P vs B1 | violation | 18 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| P vs B2 | violation | 18 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| GPLUS vs P | violation | 18 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| GPLUS vs B2 | violation | 18 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |

## Proposal practical-significance criterion (P vs B2)

- best gain in success/fidelity: -0.001 (threshold +0.10)
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
| T14 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T15 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T16 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T17 | 0.8 / 0.0 | 0.8 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T18 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
