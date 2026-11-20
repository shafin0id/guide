# Protocol v7a: static utility-cost prediction — summary

## Per-suite confusion (predicted_block vs observed_denial)
| suite | n | tp | fp | fn | tn | accuracy | 95% CI | precision | recall | pred. ceiling | obs. utility |
|---|---|---|---|---|---|---|---|---|---|---|---|
| banking | 16 | 1 | 1 | 2 | 12 | 0.812 | [0.570, 0.934] | 0.500 | 0.333 | 0.875 | 0.750 |
| slack | 21 | 14 | 1 | 0 | 6 | 0.952 | [0.773, 0.992] | 0.933 | 1.000 | 0.286 | 0.286 |
| travel | 20 | 0 | 0 | 1 | 19 | 0.950 | [0.764, 0.991] | nan | 0.000 | 1.000 | 0.800 |
| workspace | 40 | 13 | 1 | 1 | 25 | 0.950 | [0.835, 0.986] | 0.929 | 0.929 | 0.650 | 0.650 |
| **overall** | 97 | 28 | 3 | 4 | 62 | 0.928 | [0.858, 0.965] | 0.903 | 0.875 | — | — |

## Mismatch classes (overall)
- `agree_block`: 28
- `agree_pass`: 57
- `fn_offpath_call`: 4
- `fp_model_detoured`: 3
- `model_error`: 5

## fn_onpath cases (soundness-critical — must be investigated)
None found.
