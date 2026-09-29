
### misassigned (T=1000, 100 seeds; mean expected regret, 95% CI)

| Policy | total regret | regret after T/2 |
|---|---|---|
| static(first) | 150.0 [150.0, 150.0] | 75.0 [75.0, 75.0] |
| round_robin | 120.0 [120.0, 120.0] | 60.0 [60.0, 60.0] |
| bayes_ucb | 18.3 [15.7, 21.0] | 3.9 [3.0, 4.9] |
| bayes_ucb+penalty | 12.5 [9.6, 15.4] | 1.2 [0.2, 2.2] |
| bayes_ucb+discount0.99 | 61.2 [59.2, 63.1] | 30.3 [28.9, 31.7] |
| bayes_ucb+discount0.95 | 83.3 [81.8, 84.8] | 42.2 [41.2, 43.1] |

### drift (T=1000, 100 seeds; mean expected regret, 95% CI)

| Policy | total regret | regret after T/2 |
|---|---|---|
| static(first) | 275.0 [275.0, 275.0] | 275.0 [275.0, 275.0] |
| round_robin | 115.0 [115.0, 115.0] | 55.0 [55.0, 55.0] |
| bayes_ucb | 54.5 [53.1, 56.0] | 39.8 [37.8, 41.8] |
| bayes_ucb+penalty | 61.0 [59.1, 62.8] | 49.4 [46.5, 52.3] |
| bayes_ucb+discount0.99 | 41.8 [40.5, 43.2] | 12.2 [11.8, 12.7] |
| bayes_ucb+discount0.95 | 56.8 [55.5, 58.0] | 16.0 [15.6, 16.5] |
