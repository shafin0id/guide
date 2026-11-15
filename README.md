<div align="center">

```text
 ██████╗ ██╗   ██╗██╗██████╗ ███████╗
██╔════╝ ██║   ██║██║██╔══██╗██╔════╝
██║  ███╗██║   ██║██║██║  ██║█████╗
██║   ██║██║   ██║██║██║  ██║██╔══╝
╚██████╔╝╚██████╔╝██║██████╔╝███████╗
 ╚═════╝  ╚═════╝ ╚═╝╚═════╝ ╚══════╝
   ▓▓ agent ▓▓ ──▶ [ ▒▒ monitor ▒▒ ] ──▶ ▓▓ tools ▓▓
```

**Governed, Uncertainty-aware, Intent-pinned Delegation Enforcer**

An external reference monitor that bounds the blast radius of compromised agents in LLM multi-agent systems.

![Python](https://img.shields.io/badge/python-3.10%20to%203.12-blue)
![License](https://img.shields.io/badge/license-Apache--2.0-green)
![Status](https://img.shields.io/badge/status-research%20prototype-orange)

</div>

---

## What GUIDE is

Prompt injection is hard to stop inside a model's reasoning loop. In a multi-agent pipeline, one injected agent can steer
downstream agents into running tools it could not call itself. GUIDE does not try to make agents resist injection. It
assumes any agent can be compromised and sits between the agents and their tools, so every proposed tool call and
delegation is checked before it runs.

GUIDE has two parts.

1. **A runtime reference monitor** with four controls:
   - Bayes-UCB routing over per-agent success evidence, with re-dispatch on step failure.
   - Signed, hash-linked hand-offs with a per-principal Ed25519 key for each agent.
   - A policy gate that allows, bounds or denies each tool call before any tool code runs.
   - A provenance guard that refuses a control argument, such as an email recipient, unless it can be traced to the
     trusted task text. A hash-linked trace ledger records every decision.
2. **A static blast-radius analysis** that computes, before deployment, every effect a given set of compromised agents can
   cause. It also synthesizes least-privilege policies from nominal traces and predicts which benign tasks enforcement
   will block.

GUIDE is research code from an MSc dissertation at Asia Pacific University of Technology and Innovation. It is not a
production security product and carries no security certification.

## Main results

All numbers come from the files under `experiments/results/` and are reproduced by the commands in
[`REPRODUCE.md`](REPRODUCE.md). Unless stated otherwise the model is DeepSeek 4.1 Flash.

| Question | Result |
|---|---|
| Is the static bound sound? | No violation in 1,575 replayed runs (2,051 tool calls). A bounded exhaustive check (full configured combinations through four steps, reduced combinations at five) found no mismatch in 594,516 influence cases and no soundness or exactness violation in 1,966,080 gate evaluations. |
| Does runtime enforcement contain a compromised agent? | On AgentDojo, an assumed-compromise replay contained 543 of 588 in-scope task-injection pairs (92.3%). The `cred` variant raises this to 559 of 588 (95.1%). |
| Can the utility cost be predicted before deployment? | The static predictor flagged 29 of the 30 benign AgentDojo tasks that enforcement later lost (96.9% accuracy). |
| What does enforcement cost? | Benign utility fell from 95.9% to 62.9% under strict enforcement. The directory-aware `flexI_cred` variant recovers 78.4%. |
| How does it compare with existing defenses? | Against the AgentDojo `direct` attack on 200 pairs with a deliberately vulnerable agent prompt, success fell from 9.0% undefended to 0.5% under GUIDE. Tool filtering reached 1.0%, the PI detector 1.5%, spotlighting 4.5% and prompt repetition 4.0%, all under the same model and agent loop. |
| Does it hold in framework-built applications? | In 15 applications built with LangGraph, CrewAI and AutoGen, a compromised reader agent reached its goal in 23 of 90 undefended runs and in none under strict enforcement. |
| Does it hold on a more vulnerable model? | On Gemini 3.1 Flash-Lite, attack success fell from 15 of 20 undefended pairs to 1 of 20 under GUIDE. |
| Does splitting work across agents help? | In a linear chain it cannot lower the worst-case reach. In a census of 55 workflow configurations, 49 (89.1%) were linear chains, so least privilege is the lever that works. |

### Limitations

- Live attacks rarely succeeded on DeepSeek 4.1 Flash even without a defense, so most live comparisons have low power.
- The framework applications and internal suites were written by the author with sandboxed tools. They are not
  third-party production systems. Framework adapters evaluate the gate and provenance controls, not the core runtime’s signed hand-offs or router.
- The bound covers acyclic workflows only, and calls whose control value appears in the user's request are admitted
  even when their content is harmful.
- CaMeL and Progent were not run under the same conditions.
- The soundness proofs were checked by hand, by property tests and by the bounded exhaustive check, not by a theorem prover.

## Repository layout

```text
src/
  guide/              core monitor: routing, signed hand-offs, policy gate, trace (needs only cryptography; httpx and scipy are optional)
  guide_research/     provenance guard, its v9 variants, static blast-radius analysis, topology theory
  guide_bench/        task suites, conditions, fault injection, statistics, config mining
  guide_agentdojo/    AgentDojo adapter, assumed-compromise replay, cost predictor, v9 runner, adaptive attacker
  guide_realworld/    15 LangGraph, CrewAI and AutoGen applications with sandboxed tools
tests/                unit, integration, security, regression and performance tests
scripts/
  check_boundaries.py layer rule check (core <- research <- bench)
  v9/                 Protocol v9 run, analysis and completeness scripts
experiments/          frozen raw results and summaries for every protocol
docs/                 architecture, formal model, evaluation, experiment log, protocols, literature review, finished figures and manuscript
```

The layer rule is enforced in CI. The core package imports nothing from the research or benchmark packages.

## Install

GUIDE uses [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/shafin0id/guide.git
cd guide
uv sync --all-extras
```

The framework applications use a separate environment, because LangGraph, CrewAI and AutoGen pin dependencies that
conflict with AgentDojo:

```bash
uv venv .venv-rw --python 3.12
uv pip install --python .venv-rw/bin/python langgraph==1.2.21 crewai==1.15.41 \
  autogen-agentchat==0.7.5 "autogen-ext[openai]==0.7.5" langchain-openai openai python-dotenv cryptography
```

Live runs need API keys. Copy `.env.example` to `.env` and fill in the keys you use. `.env` is git-ignored.

## Quick start

```bash
uv run pytest -q                                   # test suite, no network
uv run python scripts/check_boundaries.py          # layer rule
PYTHONPATH=src uv run python -m guide_agentdojo.compromise_replay   # 949-pair assumed-compromise replay, no API cost
PYTHONPATH=src uv run python scripts/v9/exhaustive_bound.py A       # exhaustive influence check, no API cost
PYTHONPATH=src uv run python scripts/v9/exhaustive_bound.py B       # exhaustive gate check, no API cost
PYTHONPATH=src uv run python scripts/v9/analyze.py                  # rebuild the Protocol v9 summary tables
PYTHONPATH=src uv run python scripts/v9/verify_complete.py          # check that every v9 cell completed
```

Every result table and the finished figures, with their protocol, inputs, outputs and API cost, are listed in [`REPRODUCE.md`](REPRODUCE.md).

## Research method

Every evaluation protocol was frozen in git before its run, and each freeze is a tag (`protocol-v1` to `protocol-v8`,
`protocol-v9a-frozen`, `protocol-v9b-frozen`, `protocol-v9c-frozen`, `protocol-v9g-frozen`). Scoring is deterministic
and blind to the condition label. Negative results are kept, including the ceiling effect on nominal tasks and the low
live attack success on DeepSeek. The final manuscript uses a narrative related-work review; its scope is explained in [`docs/lit-review/`](docs/lit-review/).

An earlier version of this project (tag `baseline-v0`) reported benchmark numbers that came from the evaluation code
instead of the system. Those numbers were withdrawn, and the audit is in [`docs/archive/research-audit.md`](docs/archive/research-audit.md).

## Documentation

| Document | Content |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | Package structure and data flow |
| [`docs/formal_model.md`](docs/formal_model.md) | Formal model, theorems and propositions |
| [`docs/evaluation.md`](docs/evaluation.md) | Conditions, suites and metrics |
| [`docs/experiments.md`](docs/experiments.md) | Experiment log for Protocols v1 to v8 |
| [`docs/results-v9.md`](docs/results-v9.md) | Protocol v9 results |
| [`docs/protocols/`](docs/protocols/) | Frozen Protocol v9 specifications |
| [`docs/limitations.md`](docs/limitations.md) | Known limitations and bypasses |
| [`docs/security.md`](docs/security.md) | Threat model and security notes |

The checked submission manuscript and supplementary material are in [the submission folder](docs/paper/revision-v2/Final%20by%20Supervisor/). Finished figure files are in [`docs/figures/`](docs/figures/).

## Citation

A manuscript describing GUIDE is being prepared for journal submission. Until it is published, please cite the software using
[`CITATION.cff`](CITATION.cff).

## Author

Shafin Ahmad ([ORCID 0009-0008-7351-1609](https://orcid.org/0009-0008-7351-1609)), supervised by Ts. Dr. Maythem
Kamal Abbas, Asia Pacific University of Technology and Innovation, Kuala Lumpur, Malaysia.

## License

[Apache License 2.0](LICENSE).
