"""
Unit tests for HashLinkedTraceLedger.

Verifies:
1. Deterministic genesis hash h_0 initialization: SHA-256(Run_ID || S_0 || Policy_Hash).
2. Hash chain evolution: h_k = SHA-256(h_{k-1} || canonical(Event_k)).
3. Full backward lineage audit verification on untouched ledger (returns True).
4. Detection of tampered event payloads or altered parent pointers.
5. JSONL serialization and export.
"""

import hashlib
import json
import pytest
from guide_mas.core.trace_ledger import HashLinkedTraceLedger


def test_genesis_hash_computation():
    """Verifies that genesis hash h_0 matches the SHA-256 formulation in Section 2.4."""
    run_id = "run_audit_001"
    objective = "Verify financial ledger integrity"
    policy_hash = "POLICY_V1"

    ledger = HashLinkedTraceLedger(run_id=run_id, initial_objective=objective, policy_hash=policy_hash)

    expected_payload = f"{run_id}:{objective}:{policy_hash}".encode("utf-8")
    expected_genesis = hashlib.sha256(expected_payload).hexdigest()

    assert ledger.genesis_hash == expected_genesis
    assert ledger.current_hash == expected_genesis


def test_event_chaining_and_integrity_verification():
    """Verifies event appending and successful full ledger traversal verification."""
    ledger = HashLinkedTraceLedger(run_id="run_chain", initial_objective="Audit test")

    h1 = ledger.append_event("ROUTING", {"agent": "agent_synthesis", "arm_score": 0.94})
    h2 = ledger.append_event("POLICY_VALIDATE", {"tool": "procurement_db", "decision": "ALLOW"})
    h3 = ledger.append_event("EXECUTION_RESULT", {"status": "SUCCESS"})

    assert len(ledger.ledger) == 3
    assert ledger.ledger[0]["parent_hash"] == ledger.genesis_hash
    assert ledger.ledger[1]["parent_hash"] == h1
    assert ledger.ledger[2]["parent_hash"] == h2
    assert ledger.current_hash == h3

    is_valid, err = ledger.verify_ledger_integrity()
    assert is_valid is True
    assert err is None


def test_tampered_event_detection():
    """Verifies that mutating an event in the ledger is caught by cryptographic audit."""
    ledger = HashLinkedTraceLedger(run_id="run_tamper", initial_objective="Tamper test")
    ledger.append_event("EVENT_1", {"data": "authentic_value"})
    ledger.append_event("EVENT_2", {"data": "second_value"})

    # Adversary alters first node's data in-place
    ledger.ledger[0]["details"]["data"] = "falsified_value"

    is_valid, err = ledger.verify_ledger_integrity()
    assert is_valid is False
    assert "Tampered content at node 0" in (err or "")


def test_broken_hash_parent_pointer_detection():
    """Verifies that altering a parent hash pointer breaks the chain audit."""
    ledger = HashLinkedTraceLedger(run_id="run_pointer", initial_objective="Pointer test")
    ledger.append_event("NODE_A", {"status": "A"})
    ledger.append_event("NODE_B", {"status": "B"})

    # Corrupt parent pointer of node 1
    ledger.ledger[1]["parent_hash"] = "0" * 64

    is_valid, err = ledger.verify_ledger_integrity()
    assert is_valid is False
    assert "Broken hash chain at node 1" in (err or "")


def test_jsonl_export():
    """Verifies clean JSONL output format."""
    ledger = HashLinkedTraceLedger(run_id="run_jsonl", initial_objective="JSONL test")
    ledger.append_event("EV_1", {"step": 1})
    ledger.append_event("EV_2", {"step": 2})

    jsonl_output = ledger.to_jsonl()
    lines = [line for line in jsonl_output.strip().split("\n") if line]
    assert len(lines) == 2

    node1 = json.loads(lines[0])
    node2 = json.loads(lines[1])
    assert node1["event_type"] == "EV_1"
    assert node2["event_type"] == "EV_2"
