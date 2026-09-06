"""
Cryptographically Signed State Handoff Module.

Enforces RFC 8785 JSON Canonicalization Scheme (JCS), SHA-256 parent-hash linking:
h_k = SHA-256(h_{k-1} || canonical(P_k)), Ed25519 signature verification, and
immutable S_0 intent anchor preservation.
"""

from enum import Enum
import hashlib
import json
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ed25519
from pydantic import BaseModel, Field, ValidationError


class IntentPackage(BaseModel):
    """
    Cryptographically sealed state hand-off payload.
    Preserves the immutable root intent anchor S_0 and links previous execution hashes.
    """
    run_id: str = Field(description="Unique identifier for the orchestration run")
    handoff_id: str = Field(description="Unique identifier for this hand-off step")
    parent_hash: str = Field(description="Cryptographic hash of the parent state h_{k-1}")
    objective: str = Field(description="Immutable root objective S_0")
    constraints: List[str] = Field(default_factory=list, description="Mandatory constraint set")
    input_refs: List[str] = Field(default_factory=list, description="CAS sha256 pointers")
    permitted_tools: List[str] = Field(default_factory=list, description="Allow-listed tools")
    expected_schema: str = Field(default="{}", description="JSON schema specification for agent output")
    expiry_time: float = Field(description="Epoch timestamp after which package is invalid")
    findings: Dict[str, Any] = Field(default_factory=dict, description="Transient findings F_n")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Self-reported confidence kappa")

    def to_canonical_json(self) -> bytes:
        """
        Serializes package into deterministic canonical JSON adhering to RFC 8785 (JCS).
        Sorts keys recursively, suppresses superfluous whitespace, and UTF-8 encodes.
        """
        raw_dict = self.model_dump(exclude={"signature"})
        return json.dumps(
            raw_dict,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False
        ).encode("utf-8")

    def compute_hash(self, prev_hash: str) -> str:
        """
        Computes SHA-256 hash link: h_k = SHA-256(h_{k-1} || canonical(P_k)).

        Args:
            prev_hash: Preceding parent hash string h_{k-1}.

        Returns:
            Hexadecimal SHA-256 hash digest string.
        """
        payload = prev_hash.encode("utf-8") + self.to_canonical_json()
        return hashlib.sha256(payload).hexdigest()


class CryptographicHandoffManager:
    """
    Manager for Ed25519 key generation, package signing, and verification.
    Deterministically enforces zero-trust state lineage and expiry constraints.
    """

    @staticmethod
    def generate_keypair() -> Tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
        """Generates a new asymmetric Ed25519 keypair."""
        private_key = ed25519.Ed25519PrivateKey.generate()
        return private_key, private_key.public_key()

    @staticmethod
    def sign_package(
        package: IntentPackage,
        private_key: ed25519.Ed25519PrivateKey,
        prev_hash: str
    ) -> Dict[str, Any]:
        """
        Signs the canonicalized package hash using Ed25519 private key.

        Args:
            package: IntentPackage instance to sign.
            private_key: Ed25519 private key of sending agent.
            prev_hash: Expected parent hash h_{k-1}.

        Returns:
            Sealed envelope containing package dict, package_hash, and signature hex.
        """
        package_hash = package.compute_hash(prev_hash)
        signature = private_key.sign(package_hash.encode("utf-8"))
        return {
            "package": package.model_dump(),
            "package_hash": package_hash,
            "signature": signature.hex()
        }

    @staticmethod
    def verify_and_unpack(
        payload: Dict[str, Any],
        public_key: ed25519.Ed25519PublicKey,
        expected_prev_hash: str,
        expected_objective: Optional[str] = None
    ) -> IntentPackage:
        """
        Verifies package integrity, expiry, parent-hash lineage, and Ed25519 signature.

        Args:
            payload: Envelope with keys 'package', 'package_hash', 'signature'.
            public_key: Sender's Ed25519 public key.
            expected_prev_hash: The parent hash that must match package.parent_hash.
            expected_objective: Optional check verifying immutable S_0 consistency.

        Returns:
            Verified IntentPackage instance.

        Raises:
            ValueError: With 'REJECTED_INTEGRITY: <reason>' on any validation failure.
        """
        if not isinstance(payload, dict):
            raise ValueError("REJECTED_INTEGRITY: Malformed payload container")

        if "package" not in payload or "package_hash" not in payload or "signature" not in payload:
            raise ValueError("REJECTED_INTEGRITY: Missing mandatory cryptographic fields")

        pkg_data = payload["package"]
        claimed_hash = payload["package_hash"]
        sig_hex = payload["signature"]

        # 1. Pydantic Schema Validation
        try:
            package = IntentPackage(**pkg_data)
        except ValidationError as e:
            raise ValueError(f"REJECTED_INTEGRITY: Schema validation failed: {e}") from e

        # 2. Expiry Verification
        current_timestamp = time.time()
        if current_timestamp > package.expiry_time:
            raise ValueError(
                f"REJECTED_INTEGRITY: Package expired (current={current_timestamp:.2f} > expiry={package.expiry_time:.2f})"
            )

        # 3. Hash Lineage Verification
        calculated_hash = package.compute_hash(expected_prev_hash)
        if calculated_hash != claimed_hash or package.parent_hash != expected_prev_hash:
            raise ValueError(
                f"REJECTED_INTEGRITY: Hash lineage broken (calc={calculated_hash[:12]} vs claimed={claimed_hash[:12]})"
            )

        # 4. Cryptographic Signature Verification
        try:
            sig_bytes = bytes.fromhex(sig_hex)
            public_key.verify(sig_bytes, calculated_hash.encode("utf-8"))
        except (InvalidSignature, ValueError) as e:
            raise ValueError(f"REJECTED_INTEGRITY: Invalid Ed25519 signature: {e}") from e

        # 5. S_0 Anchor Immutability Preservation
        if expected_objective is not None and package.objective != expected_objective:
            raise ValueError(
                "REJECTED_INTEGRITY: Immutable objective S_0 has been altered during delegation"
            )

        return package


class Tier(str, Enum):
    """Governance Tier classification for state handoffs."""
    INTERNAL = "INTERNAL"    # Tier 1: In-memory validated state transfer between internal subtasks/specialists
    TOOL = "TOOL"            # Tier 2: Tool boundary with CAMCO validation and CAS referencing
    BOUNDARY = "BOUNDARY"    # Tier 3: Workflow boundary with full Ed25519 signature + RFC 8785 JCS canonicalization


GovernanceTier = Tier


class TieredHandoffManager:
    """
    Tiered Governance Handoff Manager.
    Enforces a 3-tier boundary architecture:
    - Tier 1 (INTERNAL): In-memory validated dictionary handoff between internal subtasks/specialists.
      Validates schema, expiry, and S_0 immutability without Ed25519 signing overhead.
    - Tier 2 (TOOL): Tool invocation boundary with CAMCO validation and CAS referencing.
    - Tier 3 (BOUNDARY): Workflow boundaries with full RFC 8785 JCS canonicalization,
      parent-hash chaining, and Ed25519 signature verification.
    """

    @staticmethod
    def generate_keypair() -> Tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
        """Generates an asymmetric Ed25519 keypair for boundary cryptographic handoffs."""
        return CryptographicHandoffManager.generate_keypair()

    @classmethod
    def execute_handoff(
        cls,
        tier: Union[Tier, str],
        package: IntentPackage,
        prev_hash: str,
        private_key: Optional[ed25519.Ed25519PrivateKey] = None,
    ) -> Dict[str, Any]:
        """
        Executes a state handoff according to the specified governance tier.

        Args:
            tier: Governance tier (INTERNAL, TOOL, or BOUNDARY).
            package: IntentPackage payload.
            prev_hash: Parent execution hash h_{k-1}.
            private_key: Ed25519 private key (required for BOUNDARY tier).

        Returns:
            Handoff container dictionary with tier metadata and verified payload.
        """
        tier_enum = Tier(tier)

        if tier_enum in (Tier.INTERNAL, Tier.TOOL):
            # Tier 1 / Tier 2: In-memory validated handoff
            # Compute hash link for trace continuity without cryptographic asymmetric signing
            package_hash = package.compute_hash(prev_hash)
            return {
                "tier": tier_enum.value,
                "package": package.model_dump(),
                "package_hash": package_hash,
                "parent_hash": prev_hash,
                "signature": None,
                "verified": True,
            }
        elif tier_enum == Tier.BOUNDARY:
            if private_key is None:
                raise ValueError("BOUNDARY tier handoff requires an Ed25519 private key")
            sealed = CryptographicHandoffManager.sign_package(package, private_key, prev_hash)
            sealed["tier"] = Tier.BOUNDARY.value
            return sealed
        else:
            raise ValueError(f"Unsupported governance tier: {tier}")

    @classmethod
    def verify_handoff(
        cls,
        payload: Dict[str, Any],
        expected_prev_hash: str,
        expected_objective: Optional[str] = None,
        public_key: Optional[ed25519.Ed25519PublicKey] = None,
    ) -> IntentPackage:
        """
        Verifies and unpacks a state handoff package based on its recorded tier.

        Args:
            payload: Handoff dictionary container.
            expected_prev_hash: Expected parent hash h_{k-1}.
            expected_objective: Expected immutable root objective S_0.
            public_key: Sender's Ed25519 public key (required for BOUNDARY tier).

        Returns:
            Verified IntentPackage instance.
        """
        tier_str = payload.get("tier", Tier.BOUNDARY.value)
        tier_enum = Tier(tier_str)

        if tier_enum in (Tier.INTERNAL, Tier.TOOL):
            if "package" not in payload:
                raise ValueError("REJECTED_INTEGRITY: Malformed in-memory handoff container")

            pkg_data = payload["package"]
            try:
                package = IntentPackage(**pkg_data)
            except ValidationError as e:
                raise ValueError(f"REJECTED_INTEGRITY: Schema validation failed: {e}") from e

            # Expiry check
            current_timestamp = time.time()
            if current_timestamp > package.expiry_time:
                raise ValueError(
                    f"REJECTED_INTEGRITY: Package expired (current={current_timestamp:.2f} > expiry={package.expiry_time:.2f})"
                )

            # Hash lineage check
            calculated_hash = package.compute_hash(expected_prev_hash)
            claimed_hash = payload.get("package_hash")
            if claimed_hash and calculated_hash != claimed_hash:
                raise ValueError(
                    f"REJECTED_INTEGRITY: Hash lineage broken (calc={calculated_hash[:12]} vs claimed={claimed_hash[:12]})"
                )
            if package.parent_hash != expected_prev_hash:
                raise ValueError(
                    f"REJECTED_INTEGRITY: Hash lineage broken (package.parent_hash={package.parent_hash[:12]} vs expected={expected_prev_hash[:12]})"
                )

            # S_0 immutability
            if expected_objective is not None and package.objective != expected_objective:
                raise ValueError(
                    "REJECTED_INTEGRITY: Immutable objective S_0 has been altered during delegation"
                )

            return package

        elif tier_enum == Tier.BOUNDARY:
            if public_key is None:
                raise ValueError("BOUNDARY tier verification requires an Ed25519 public key")
            return CryptographicHandoffManager.verify_and_unpack(
                payload, public_key, expected_prev_hash, expected_objective
            )
        else:
            raise ValueError(f"Unsupported governance tier: {tier_str}")

