# Results: `experiments/pilot/pilot-3`

Runs analysed: 48; harness errors: 0.

## Per condition (mean, 95% task-cluster bootstrap CI)

| Condition | runs | task success | intent fidelity | violation rate | completed | trace compl. | median tokens [IQR] | median wall s [IQR] | model calls |
|---|---|---|---|---|---|---|---|---|---|
| P | 12 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 3271 [2444, 3726] | 4.2 [3.5, 6.1] | 4.2 |
| B1 | 12 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 0.000 | 3524 [2416, 3668] | 4.4 [3.1, 5.6] | 4.3 |
| B2 | 12 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 0.000 | 3346 [2625, 3527] | 4.8 [3.7, 6.2] | 4.3 |
| GPLUS | 12 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 3176 [2458, 4168] | 4.6 [3.8, 6.0] | 4.3 |

## Paired task-level comparisons (Wilcoxon signed-rank, Pratt; Holm-adjusted per metric)

| Comparison | metric | tasks | non-zero | mean diff | W | p | p (Holm) | note |
|---|---|---|---|---|---|---|---|---|
| P vs B1 | task_success | 6 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| P vs B2 | task_success | 6 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| GPLUS vs P | task_success | 6 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| GPLUS vs B2 | task_success | 6 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| P vs B1 | intent_fidelity | 6 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| P vs B2 | intent_fidelity | 6 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| GPLUS vs P | intent_fidelity | 6 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| GPLUS vs B2 | intent_fidelity | 6 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| P vs B1 | violation | 6 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| P vs B2 | violation | 6 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| GPLUS vs P | violation | 6 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| GPLUS vs B2 | violation | 6 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |

## Proposal practical-significance criterion (P vs B2)

- best gain in success/fidelity: +0.000 (threshold +0.10)
- violation reduction: n/a (B2 has none) (threshold 50%)
- median wall-time ratio P/B2: 0.88 (threshold 1.30)
- **criterion met: False**

## Per task: success / violation rate

| Task | P | B1 | B2 | GPLUS |
|---|---|---|---|---|
| T01 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T05 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T07 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T11 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T13 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T18 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
