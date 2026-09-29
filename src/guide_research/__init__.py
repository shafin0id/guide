"""GUIDE Research: experimental RMCE mechanisms under evaluation.

Depends on ``guide`` (core); core never imports from here. A mechanism graduates into core
only after it is supported by the experiments recorded in docs/experiments.md.
"""

from guide_research.provenance import ProvenanceGuard

__all__ = ["ProvenanceGuard"]
