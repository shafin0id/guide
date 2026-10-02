# Results: `experiments/results/v5-main-groq-gptoss120b`

Runs analysed: 166; harness errors: 0.

## Per condition (mean, 95% task-cluster bootstrap CI)

| Condition | runs | task success | intent fidelity | violation rate | completed | trace compl. | median tokens [IQR] | median wall s [IQR] | model calls |
|---|---|---|---|---|---|---|---|---|---|
| P | 37 | 0.297 [0.158, 0.447] | 0.595 [0.472, 0.719] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 4196 [3074, 5140] | 25.5 [15.4, 34.0] | 4.5 |
| B1 | 44 | 0.409 [0.238, 0.590] | 0.643 [0.502, 0.781] | 0.000 [0.000, 0.000] | 1.000 | 0.000 | 3879 [2786, 5371] | 24.7 [13.6, 33.9] | 4.3 |
| B2 | 41 | 0.390 [0.211, 0.575] | 0.667 [0.540, 0.793] | 0.000 [0.000, 0.000] | 1.000 | 0.000 | 4037 [3073, 5049] | 16.4 [11.6, 27.8] | 4.3 |
| GPLUS | 44 | 0.318 [0.152, 0.512] | 0.632 [0.498, 0.761] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 3908 [3078, 4662] | 20.8 [12.8, 30.7] | 4.2 |

## Paired task-level comparisons (Wilcoxon signed-rank, Pratt; Holm-adjusted per metric)

| Comparison | metric | tasks | non-zero | mean diff | W | p | p (Holm) | note |
|---|---|---|---|---|---|---|---|---|
| P vs B1 | task_success | 18 | 9 | -0.120 | 41.0 | 0.3021 | 1.0000 |  |
| P vs B2 | task_success | 18 | 9 | -0.083 | 43.5 | 0.3588 | 1.0000 |  |
| GPLUS vs P | task_success | 18 | 10 | +0.042 | 63.5 | 0.8539 | 1.0000 |  |
| GPLUS vs B2 | task_success | 18 | 6 | -0.042 | 31.0 | 0.4167 | 1.0000 |  |
| P vs B1 | intent_fidelity | 18 | 10 | -0.056 | 42.0 | 0.2425 | 0.7275 |  |
| P vs B2 | intent_fidelity | 18 | 12 | -0.077 | 37.5 | 0.0948 | 0.3792 |  |
| GPLUS vs P | intent_fidelity | 18 | 11 | +0.036 | 57.5 | 0.5279 | 1.0000 |  |
| GPLUS vs B2 | intent_fidelity | 18 | 8 | -0.041 | 51.0 | 0.7360 | 1.0000 |  |
| P vs B1 | violation | 18 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| P vs B2 | violation | 18 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| GPLUS vs P | violation | 18 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |
| GPLUS vs B2 | violation | 18 | 0 | +0.000 | – | – | – | all paired differences are zero; test uninformative |

## Proposal practical-significance criterion (P vs B2)

- best gain in success/fidelity: -0.072 (threshold +0.10)
- violation reduction: n/a (B2 has none) (threshold 50%)
- median wall-time ratio P/B2: 1.56 (threshold 1.30)
- **criterion met: False**

## Per task: success / violation rate

| Task | P | B1 | B2 | GPLUS |
|---|---|---|---|---|
| T01 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| T02 | 0.0 / 0.0 | 1.0 / 0.0 | 0.3 / 0.0 | 0.0 / 0.0 |
| T03 | 0.0 / 0.0 | 0.0 / 0.0 | 0.5 / 0.0 | 0.0 / 0.0 |
| T04 | 0.5 / 0.0 | 0.3 / 0.0 | 0.5 / 0.0 | 0.3 / 0.0 |
| T05 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.2 / 0.0 |
| T06 | 0.0 / 0.0 | 0.5 / 0.0 | 0.5 / 0.0 | 0.5 / 0.0 |
| T07 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| T08 | 0.0 / 0.0 | 0.5 / 0.0 | 0.5 / 0.0 | 0.5 / 0.0 |
| T09 | 0.3 / 0.0 | 0.3 / 0.0 | 0.5 / 0.0 | 0.0 / 0.0 |
| T10 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| T11 | 0.5 / 0.0 | 0.0 / 0.0 | 0.5 / 0.0 | 0.5 / 0.0 |
| T12 | 0.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T13 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T14 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 | 1.0 / 0.0 |
| T15 | 0.5 / 0.0 | 0.5 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| T16 | 0.5 / 0.0 | 0.7 / 0.0 | 0.5 / 0.0 | 1.0 / 0.0 |
| T17 | 0.5 / 0.0 | 0.7 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| T18 | 0.5 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
