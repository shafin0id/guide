# Protocol v8 (M2): Proposition 4 and Absolute Reach

## Absolute Reach Across 19 Own Configs

| Condition | Median Abs WBR₁ | Median Nom-Normalised WBR₁ | Reduction from (i) |
|---|---|---|---|
| (i) Nominal, TRANSCRIPT | 2.0 | 1.000 | — |
| (ii) Least privilege | 1.0 | 0.500 | 1.0 sinks (50.0%) |
| (iii) + SIGNED hand-off | 1.0 | 0.500 | 1.0 sinks (50.0%) |
| (iv) + Best partition | 1.0 | 0.500 | 1.0 sinks (50.0%) |

## Structural Census (55 Acyclic Configs)

*Note: 1 mined config (`zhongyu09/openchatbi:openchatbi/text2sql/sql_graph.py`) is cyclic and excluded from DAG blast-radius scoring.*

| Set | N | is_chain | Dominating Source (all steps) | Floor = 1 under SIGNED (Prop 4) |
|---|---|---|---|---|
| Own | 19 | 19/19 (100.0%) | 19/19 (100.0%) | 19/19 (100.0%) |
| Mined (scored) | 36 | 30/36 (83.3%) | 36/36 (100.0%) | 2/36 (5.6%) |
| **Total** | **55** | **49/55 (89.1%)** | **55/55 (100.0%)** | **21/55 (38.2%)** |
