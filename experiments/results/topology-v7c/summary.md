# Protocol v7c: blast-radius-minimal agent topology — summary

Configs analysed: 19 of 19 (0 skipped: too large for exhaustive partition enumeration)

## Q1 — transcript wash-out
Median WBR_1 reduction from best TRANSCRIPT partition vs. original structure: **0.000** (n=19).
Hypothesis was 'little reduction' — under TRANSCRIPT, compromising one agent influences every later step regardless of topology.

## Q2 — least agents for the floor (SIGNED + least-privilege, k=1)
| config | n_steps | m at floor | floor WBR_1 |
|---|---|---|---|
| support-01-langgraph-linear | 2 | 1 | 1.000 |
| support-02-langgraph-branch | 3 | 1 | 1.000 |
| support-03-crewai-sequential | 2 | 1 | 1.000 |
| support-04-crewai-hierarchical | 3 | 1 | 1.000 |
| support-05-autogen-groupchat | 2 | 1 | 1.000 |
| sql-01-langgraph-linear | 2 | 1 | 0.000 |
| sql-02-langgraph-branch | 3 | 1 | 1.000 |
| sql-03-crewai-sequential | 2 | 1 | 1.000 |
| sql-04-crewai-hierarchical | 3 | 1 | 1.000 |
| sql-05-autogen-groupchat | 2 | 1 | 1.000 |
| itsm-01-langgraph-linear | 2 | 1 | 1.000 |
| itsm-02-crewai-hierarchical | 3 | 1 | 1.000 |
| itsm-03-autogen-groupchat | 2 | 1 | 1.000 |
| docs-01-langgraph-branch | 3 | 1 | 1.000 |
| docs-02-crewai-sequential | 2 | 1 | 1.000 |
| docs-03-autogen-groupchat | 2 | 1 | 1.000 |
| code-01-langgraph-linear | 2 | 1 | 1.000 |
| code-02-crewai-hierarchical | 3 | 1 | 1.000 |
| code-03-autogen-groupchat | 2 | 1 | 1.000 |

## Q3 — irreducible floor (no partition/mode/policy reaches WBR_1 = 0)
| config | min achievable WBR_1 |
|---|---|
| support-01-langgraph-linear | 1.000 |
| support-02-langgraph-branch | 1.000 |
| support-03-crewai-sequential | 1.000 |
| support-04-crewai-hierarchical | 1.000 |
| support-05-autogen-groupchat | 1.000 |
| sql-02-langgraph-branch | 1.000 |
| sql-03-crewai-sequential | 1.000 |
| sql-04-crewai-hierarchical | 1.000 |
| sql-05-autogen-groupchat | 1.000 |
| itsm-01-langgraph-linear | 1.000 |
| itsm-02-crewai-hierarchical | 1.000 |
| itsm-03-autogen-groupchat | 1.000 |
| docs-01-langgraph-branch | 1.000 |
| docs-02-crewai-sequential | 1.000 |
| docs-03-autogen-groupchat | 1.000 |
| code-01-langgraph-linear | 1.000 |
| code-02-crewai-hierarchical | 1.000 |
| code-03-autogen-groupchat | 1.000 |

## Q4 — decomposition (median WBR_1 across configs)
| condition | median WBR_1 |
|---|---|
| (i) original structure, nominal policy, TRANSCRIPT | 1.000 |
| (ii) least-privilege policy only | 1.000 |
| (iii) + SIGNED hand-off | 1.000 |
| (iv) + best partition | 1.000 |
