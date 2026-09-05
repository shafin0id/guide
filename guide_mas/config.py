"""
GUIDE Framework Configuration Module.

Enforces immutable architectural invariants, foundational model invariance,
cryptographic standards, and enterprise sensitivity hierarchies.
"""

from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SensitivityLevel(str, Enum):
    """Hierarchical enterprise data sensitivity classification."""
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


SENSITIVITY_RANK: Dict[SensitivityLevel, int] = {
    SensitivityLevel.PUBLIC: 1,
    SensitivityLevel.INTERNAL: 2,
    SensitivityLevel.CONFIDENTIAL: 3,
    SensitivityLevel.RESTRICTED: 4,
}


class TaskDomain(str, Enum):
    """Enterprise workflow benchmark task domains."""
    CONSTRAINED_SYNTHESIS = "constrained_synthesis"
    EVIDENCE_RECONCILIATION = "evidence_reconciliation"
    POLICY_PLANNING = "policy_planning"


class ComplexityTier(str, Enum):
    """Constraint complexity tier."""
    LOW = "LOW"        # 4 atomic constraints
    MEDIUM = "MEDIUM"  # 6 atomic constraints
    HIGH = "HIGH"      # 8 atomic constraints


class ModelInvarianceConfig(BaseModel):
    """
    Non-negotiable Model Invariance Rule configuration.
    Enforces identical foundation model parameters across Conditions B1, B2, and P.
    """
    model_name: str = "gpt-4o"
    temperature: float = 0.0
    max_tokens: int = 2048
    seed: int = 42
    max_retries: int = 3
    timeout_seconds: float = 30.0
    context_window_limit: int = 128000


class CryptographicConfig(BaseModel):
    """Cryptographic signature and canonicalization specifications."""
    signature_algorithm: str = "Ed25519"
    hash_algorithm: str = "SHA-256"
    canonicalization_standard: str = "RFC 8785 (JCS)"
    default_expiry_ttl_seconds: float = 300.0  # 5 minutes validity


class RoutingConfig(BaseModel):
    """Bayesian Upper Confidence Bound (Bayes-UCB) routing parameters."""
    warmup_pulls: int = 1
    anomaly_kappa_threshold: float = 0.80
    anomaly_beta_penalty: float = 5.0
    default_prior_alpha: float = 1.0
    default_prior_beta: float = 1.0


class PolicyGateConfig(BaseModel):
    """CAMCO Pre-Execution Policy Gate default rule boundaries."""
    max_query_limit: int = 100
    allow_write: bool = False
    max_data_sensitivity: SensitivityLevel = SensitivityLevel.PUBLIC
    permitted_tools: List[str] = Field(
        default_factory=lambda: ["procurement_db", "incident_log_store", "email_service"]
    )


class StorageConfig(BaseModel):
    """Content-addressable storage configuration."""
    base_storage_dir: Path = Path("/tmp/guide_storage")
    ledger_storage_dir: Path = Path("/tmp/guide_ledger")


class GUIDEConfig(BaseSettings):
    """Master configuration class for the GUIDE multi-agent framework."""
    env: str = "production"
    debug: bool = False
    random_seed: int = 42

    model: ModelInvarianceConfig = Field(default_factory=ModelInvarianceConfig)
    crypto: CryptographicConfig = Field(default_factory=CryptographicConfig)
    routing: RoutingConfig = Field(default_factory=RoutingConfig)
    policy: PolicyGateConfig = Field(default_factory=PolicyGateConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)

    model_config = SettingsConfigDict(
        arbitrary_types_allowed=True,
        env_prefix="GUIDE_"
    )


_GLOBAL_CONFIG: Optional[GUIDEConfig] = None


def get_config() -> GUIDEConfig:
    """Retrieves or initializes the global singleton GUIDE configuration."""
    global _GLOBAL_CONFIG
    if _GLOBAL_CONFIG is None:
        _GLOBAL_CONFIG = GUIDEConfig()
    return _GLOBAL_CONFIG


def set_config(config: GUIDEConfig) -> None:
    """Overrides the global configuration (primarily used during evaluation setups)."""
    global _GLOBAL_CONFIG
    _GLOBAL_CONFIG = config
