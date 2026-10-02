# Protocol v7b: real-world MAS mining — summary

## PRISMA-style funnel
- **crewai**: retrieved=200, excluded={'excluded_name_pattern': 29, 'framework_own_repo': 2, 'over_200mb': 12}, cloned=154 (failures=3), included_repos=21, configs=36
- **langgraph**: retrieved=200, excluded={'excluded_name_pattern': 27, 'framework_own_repo': 13, 'over_200mb': 27, 'duplicate_across_frameworks': 43}, cloned=87 (failures=3), included_repos=1, configs=1
- **autogen**: retrieved=200, excluded={'over_200mb': 15, 'framework_own_repo': 9, 'duplicate_across_frameworks': 78, 'excluded_name_pattern': 28}, cloned=70 (failures=0), included_repos=0, configs=0

Total configs mined: 37

## Metrics — TRANSCRIPT hand-off
| framework | n | M1 (single-agent->sink) | M2 (zero-own-sink agent reaches) | M3 median WBR1 | M5 code-exec |
|---|---|---|---|---|---|
| crewai | 36 | 0.056 (0.015369986664161854, 0.18144657208647252) | 0.028 (0.004920407139810455, 0.14169718653273855) | 1.000 (n_excl=34) | 0.000 |
| langgraph | 0 | nan (0.0, 0.0) | nan (0.0, 0.0) | nan (n_excl=0) | nan |
| autogen | 0 | nan (0.0, 0.0) | nan (0.0, 0.0) | nan (n_excl=0) | nan |
| pooled | 36 | 0.056 (0.015369986664161854, 0.18144657208647252) | 0.028 (0.004920407139810455, 0.14169718653273855) | 1.000 (n_excl=34) | 0.000 |

## Metrics — STRUCTURED hand-off
| framework | n | M1 (single-agent->sink) | M2 (zero-own-sink agent reaches) | M3 median WBR1 | M5 code-exec |
|---|---|---|---|---|---|
| crewai | 36 | 0.056 (0.015369986664161854, 0.18144657208647252) | 0.028 (0.004920407139810455, 0.14169718653273855) | 1.000 (n_excl=34) | 0.000 |
| langgraph | 0 | nan (0.0, 0.0) | nan (0.0, 0.0) | nan (n_excl=0) | nan |
| autogen | 0 | nan (0.0, 0.0) | nan (0.0, 0.0) | nan (n_excl=0) | nan |
| pooled | 36 | 0.056 (0.015369986664161854, 0.18144657208647252) | 0.028 (0.004920407139810455, 0.14169718653273855) | 1.000 (n_excl=34) | 0.000 |
