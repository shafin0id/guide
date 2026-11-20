<div align="center">

<p>
  <img src="docs/guide-banner.svg" alt="GUIDE" width="540" />
</p>

<h3>GUIDE: An External Reference Monitor For Containing Compromised Agents In LLM-Based Multi-Agent Systems</h3>

<p>
  GUIDE is a research prototype for an external reference monitor and static<br />
  effect-reachability analysis of fixed acyclic multi-agent LLM workflows.
</p>

<p>
  <img src="https://img.shields.io/badge/status-research%20prototype-4F46E5?style=flat-square&labelColor=1E293B" alt="Status: Research Prototype" />
  <img src="https://img.shields.io/badge/python-3.12-2563EB?style=flat-square&logo=python&logoColor=white&labelColor=1E293B" alt="Python 3.12" />
  <a href="uv.lock"><img src="https://img.shields.io/badge/deps-uv.lock-7C3AED?style=flat-square&logo=uv&logoColor=white&labelColor=1E293B" alt="uv.lock" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-0D9488?style=flat-square&labelColor=1E293B" alt="License: Apache 2.0" /></a>
</p>

<p>
  <a href="#scope-and-limitations">Scope &amp; Limitations</a> &nbsp;&middot;&nbsp;
  <a href="#layout">Layout</a> &nbsp;&middot;&nbsp;
  <a href="#setup">Setup</a> &nbsp;&middot;&nbsp;
  <a href="REPRODUCE.md">Reproduce</a> &nbsp;&middot;&nbsp;
  <a href="audit/current-assessment.md">Current Assessment</a> &nbsp;&middot;&nbsp;
  <a href="audit/claim-scope-corrections.md">Claim Corrections</a>
</p>

</div>

---

## Scope and Limitations

<table>
  <thead>
    <tr>
      <th width="50%" align="left">Contribution</th>
      <th width="50%" align="left">Does Not Guarantee</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td valign="top">
        <ul>
          <li>A conditional workflow bound</li>
          <li>Trace-driven permission reduction</li>
          <li>An empirical account of the security–utility trade-off</li>
        </ul>
      </td>
      <td valign="top">
        <ul>
          <li>Safe content in authorized calls</li>
          <li>Deployment security for arbitrary frameworks</li>
          <li>Immunity to prompt injection</li>
        </ul>
      </td>
    </tr>
  </tbody>
</table>

> [!WARNING]
> **Known release limitations** (disclosed, not fixed, in this release):
> - Counterexamples to general synthesis preservation and optimality
> - Incomplete numeric argument modelling
> - A sensitivity-check gap for tools without column selection
> - Malformed-input exceptions
>
> See [claim corrections](audit/claim-scope-corrections.md).

---

## Layout

| Area | Path | Description |
| :--- | :--- | :--- |
| **Core** | [`src/guide/`](src/guide/) | Core policy enforcement, signing, routing and trace ledger. |
| **Research** | [`src/guide_research/`](src/guide_research/) | Blast-radius analysis, provenance checks and synthesis. |
| **Evaluation** | [`src/guide_agentdojo/`](src/guide_agentdojo/), [`src/guide_realworld/`](src/guide_realworld/), [`src/guide_bench/`](src/guide_bench/) | Evaluation adapters and tasks. |
| **Tests & Scripts** | [`tests/`](tests/), [`scripts/`](scripts/) | Regression tests and reproducible analyses. |
| **Experiments** | [`experiments/`](experiments/) | Historical raw data and mining inputs. |
| **Results** | [`results/`](results/) | Recorded offline and statistical analyses, with current checks under [`results/verification/`](results/verification/). |
| **Audit** | [`audit/`](audit/) | Claim-to-evidence records, assumptions and outstanding limitations. |
| **Dependencies** | [`environments/`](environments/), [`uv.lock`](uv.lock) | Recorded dependency information. |

> [!NOTE]
> The repository integrates the revised code directly; no separate version-2 workspace is required. Document-generation scripts and personal review drafts are excluded.

---

## Setup

### Recorded Development Resolution

For the recorded development dependency resolution, use **Python 3.12** and:

```sh
uv sync --frozen --extra dev --extra agentdojo
uv run --frozen --extra dev --extra agentdojo pytest -q
```

### Minimal Core and Framework Dependencies

A minimal core install is:

```sh
pip install .
```

Framework dependencies are separate; see [`environments/realworld-freeze.txt`](environments/realworld-freeze.txt). There is no `realworld` package extra.

> [!IMPORTANT]
> Read [REPRODUCE.md](REPRODUCE.md) and [the current assessment](audit/current-assessment.md) before interpreting results. Historical live outcomes predate the hardened implementation and must not be described as fresh live measurements of this release.
