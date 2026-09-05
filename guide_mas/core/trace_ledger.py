"""
Hash-Linked Trace Ledger Module.

Maintains an immutable, append-only JSONL audit ledger with SHA-256 backwards pointer chaining.
Genesis block is anchored to: h_0 = SHA-256(Run_ID || S_0 || Policy_Hash).
Enforces tamper-evident backward lineage and comprehensive mathematical verification.
"""

import copy
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


class HashLinkedTraceLedger:
    """
    Append-only trace ledger providing non-repudiation and cryptographic auditability
    for multi-agent coordination, routing decisions, policy validations, and tool outputs.
    """

    def __init__(
        self,
        run_id: str,
        initial_objective: str,
        policy_hash: str = "GENESIS_POLICY_V1"
    ):
        """
        Initializes ledger and computes genesis hash h_0.

        Args:
            run_id: Unique orchestration run identifier.
            initial_objective: Immutable root task objective S_0.
            policy_hash: Hash or signature of active compliance policies.
        """
        self.run_id = run_id
        self.initial_objective = initial_objective
        self.policy_hash = policy_hash
        self.ledger: List[Dict[str, Any]] = []

        # Genesis Hash computation matching Section 2.4
        genesis_payload = f"{run_id}:{initial_objective}:{policy_hash}".encode("utf-8")
        self.genesis_hash: str = hashlib.sha256(genesis_payload).hexdigest()
        self.current_hash: str = self.genesis_hash

    def append_event(self, event_type: str, details: Dict[str, Any]) -> str:
        """
        Appends an event node to the ledger, computing the next cryptographic hash link.
        h_k = SHA-256(h_{k-1} || canonical(Event_k))

        Args:
            event_type: Category of event (e.g., 'ROUTING', 'HANDOFF', 'POLICY_GATE', 'TOOL_EXEC').
            details: Event metadata and operational findings.

        Returns:
            The newly computed node hash h_k.
        """
        event_node: Dict[str, Any] = {
            "run_id": self.run_id,
            "parent_hash": self.current_hash,
            "timestamp": time.time(),
            "event_type": event_type,
            "details": details
        }

        # Canonical serialization of node payload (excluding node_hash itself)
        serialized_bytes = json.dumps(
            event_node,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=str
        ).encode("utf-8")

        new_hash = hashlib.sha256(self.current_hash.encode("utf-8") + serialized_bytes).hexdigest()
        event_node["node_hash"] = new_hash

        self.ledger.append(event_node)
        self.current_hash = new_hash
        return new_hash

    def append_trace(self, event_type: str, details: Dict[str, Any]) -> str:
        """Alias for append_event to maintain nomenclature consistency with Section 3."""
        return self.append_event(event_type, details)

    def verify_ledger_integrity(self) -> Tuple[bool, Optional[str]]:
        """
        Performs full cryptographic audit of ledger backwards lineage from genesis to tip.

        Returns:
            Tuple of (is_valid, error_description_if_invalid).
        """
        expected_parent = self.genesis_hash

        for idx, node in enumerate(self.ledger):
            # 1. Check parent pointer linkage
            if node.get("parent_hash") != expected_parent:
                return False, (
                    f"Broken hash chain at node {idx}: claimed parent {node.get('parent_hash')[:12]} "
                    f"does not match expected {expected_parent[:12]}"
                )

            # 2. Recompute node hash
            node_copy = dict(node)
            claimed_node_hash = node_copy.pop("node_hash", None)
            if not claimed_node_hash:
                return False, f"Missing node_hash at ledger index {idx}"

            serialized_bytes = json.dumps(
                node_copy,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                default=str
            ).encode("utf-8")

            recomputed_hash = hashlib.sha256(
                expected_parent.encode("utf-8") + serialized_bytes
            ).hexdigest()

            if recomputed_hash != claimed_node_hash:
                return False, (
                    f"Tampered content at node {idx}: recomputed hash {recomputed_hash[:12]} "
                    f"differs from claimed hash {claimed_node_hash[:12]}"
                )

            expected_parent = claimed_node_hash

        return True, None

    def export_ledger(self) -> List[Dict[str, Any]]:
        """Exports ledger as deep copy of event nodes to preserve in-memory immutability."""
        return copy.deepcopy(self.ledger)

    def to_jsonl(self, filepath: Optional[Union[str, Path]] = None) -> str:
        """
        Serializes entire ledger to JSONL string and optionally persists to disk.

        Args:
            filepath: Optional destination path.

        Returns:
            JSONL formatted string.
        """
        lines = [json.dumps(node, sort_keys=True) for node in self.ledger]
        jsonl_str = "\n".join(lines) + ("\n" if lines else "")

        if filepath:
            out_path = Path(filepath)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(jsonl_str, encoding="utf-8")

        return jsonl_str
