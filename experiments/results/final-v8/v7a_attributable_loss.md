# Protocol v8 (M1b): GUIDE-Attributable Utility Loss

## Confusion Matrix (Predicted Block vs Lost Utility)

| | Lost Utility (v6b=True, v6=False) | Not Lost | Total |
|---|---|---|---|
| **Predicted Block** | 29 (TP) | 2 (FP) | 31 |
| **Not Predicted** | 1 (FN) | 65 (TN) | 66 |
| **Total** | 30 | 67 | 97 |

## Performance Metrics

- **Accuracy**: 96.9% (95% CI [91.3%, 98.9%])
- **Precision**: 93.5% (29/31)
- **Recall**: 96.7% (29/30)
- **Lost Tasks Count**: 30 / 97 (30.9%)

## Utility Cost Comparison

- **Predicted Cost**: 29.9 pp (`mean(predicted_block * v6b_utility)`)
- **Observed Cost**: 29.9 pp (`v6b benign utility - v6 benign utility`)
