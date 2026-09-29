"""Real-world configuration study (Task 5 / protocol-v4).

IMPORTANT SCOPE NOTE (read before citing these results):

This module does NOT parse or execute LangGraph, CrewAI, or AutoGen source code. It curates
18 synthetic workflow configurations -- expressed directly in GUIDE's own types (`guide.workflow`,
`guide.tools`, `guide.policy`) -- that reproduce the *structural pattern* each framework is known
for from its own documentation:

  * LangGraph  -- a StateGraph of tool-bearing nodes, shared mutable state, edges = data flow.
  * CrewAI     -- a manager/hierarchical or sequential list of agents, each with its own tool list.
  * AutoGen    -- a group chat where every participant can see every message (full transcript
                  broadcast) and any participant may be selected to act next.

`configs.py` documents, per configuration, which structural feature it reproduces and cites the
framework concept by name. No live LangGraph/CrewAI/AutoGen installation, execution, or benchmark
data is involved anywhere in this module -- this is a *generalisation study* of the static
analyser (`guide_research.blast_radius`) over hand-authored configurations in that structural
style, not an empirical study of those frameworks' shipped code. See docs/experiments.md
"Protocol v4" for the same caveat next to the numbers it produces.
"""
