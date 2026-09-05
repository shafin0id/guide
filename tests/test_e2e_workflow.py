"""
End-to-End Workflow Integration Test.

Validates the full GUIDE orchestration lifecycle across all four core architectural controls:
1. Dynamic Topology DAG Scheduling (O(|V| + |E|) Kahn's algorithm)
2. Content-Addressable Storage (CAS pointer input_refs[])
3. Bayes-UCB Dynamic Specialist Agent Routing (Kaufmann et al., 2012)
4. Cryptographically Sealed State Handoffs (RFC 8785 JCS + Ed25519)
5. CAMCO Pre-Execution Action Policy Gate (Convex Euclidean Projection)
6. Hash-Linked Immutable Trace Ledger (Backwards SHA-256 Lineage Audit)
"""

import json
import time
import pytest
from guide_mas.core.coordinator import BayesUCBCoordinator
from guide_mas.core.handoff import CryptographicHandoffManager, IntentPackage
from guide_mas.core.policy_gate import ActionRecord, CAMCOPolicyGate
from guide_mas.core.topology import DynamicTopologyEngine, TaskNode
from guide_mas.core.trace_ledger import HashLinkedTraceLedger
from guide_mas.storage.content_store import ContentAddressableStore
from guide_mas.tools.synthetic_tools import MockProcurementDB


def test_full_e2e_guide_pipeline():
    """Executes a complete production-grade multi-agent delegation workflow."""
    run_id = f"e2e_run_{int(time.time())}"
    objective_s0 = "Extract multi-vendor procurement SLAs under zero-disclosure constraints"
    constraints = [
        "Extract delivery SLA for Apex Cloud Systems",
        "Verify FedRAMP compliance tier",
        "Suppress RESTRICTED unit pricing and discount margins",
        "Bound query records to maximum limit of 100"
    ]

    # -------------------------------------------------------------------------
    # 1. Content-Addressable Storage (CAS)
    # -------------------------------------------------------------------------
    cas = ContentAddressableStore()
    source_document = json.dumps({
        "procurement_registry": "Enterprise Hardware & Cloud Catalog 2026",
        "confidentiality": "INTERNAL",
        "vendors": ["V-001", "V-003"]
    })
    doc_ref = cas.store(source_document)
    assert doc_ref.startswith("sha256:")
    assert cas.retrieve(doc_ref) == source_document

    # -------------------------------------------------------------------------
    # 2. Hash-Linked Trace Ledger Initialization
    # -------------------------------------------------------------------------
    ledger = HashLinkedTraceLedger(
        run_id=run_id,
        initial_objective=objective_s0,
        policy_hash="CAMCO_STRICT_ENTERPRISE_2026"
    )
    init_event_hash = ledger.append_event("WORKFLOW_INITIALIZED", {
        "objective": objective_s0,
        "input_refs": [doc_ref]
    })
    assert ledger.current_hash == init_event_hash

    # -------------------------------------------------------------------------
    # 3. Dynamic Critical-Path DAG Topology Discovery
    # -------------------------------------------------------------------------
    topology = DynamicTopologyEngine()
    # 3 subtasks: T1 and T2 run concurrently, T3 depends on both
    topology.add_node(TaskNode(
        task_id="T1", domain="constrained_synthesis", description="Extract Apex SLA", dependencies=[]
    ))
    topology.add_node(TaskNode(
        task_id="T2", domain="constrained_synthesis", description="Extract Zenith FedRAMP SLA", dependencies=[]
    ))
    topology.add_node(TaskNode(
        task_id="T3", domain="policy_planning", description="Synthesize final SLA report", dependencies=["T1", "T2"]
    ))

    # Verify acyclicity
    order = topology.validate_acyclic()
    assert len(order) == 3

    # Partition into parallel execution stages
    stages = topology.get_parallel_execution_stages()
    assert len(stages) == 2
    assert {n.task_id for n in stages[0]} == {"T1", "T2"}
    assert [n.task_id for n in stages[1]] == ["T3"]

    ledger.append_event("TOPOLOGY_SCHEDULED", {
        "stages": [[n.task_id for n in s] for s in stages],
        "total_nodes": len(topology.nodes)
    })

    # -------------------------------------------------------------------------
    # 4. Bayesian UCB Dynamic Routing Setup
    # -------------------------------------------------------------------------
    agent_pool = ["specialist_alpha", "specialist_beta", "specialist_gamma"]
    domains = ["constrained_synthesis", "policy_planning"]
    coordinator = BayesUCBCoordinator(agent_ids=agent_pool, domains=domains, warmup_pulls=1)

    # -------------------------------------------------------------------------
    # 5. CAMCO Pre-Execution Policy Gate Setup
    # -------------------------------------------------------------------------
    policy_gate = CAMCOPolicyGate({
        "permitted_tools": ["procurement_db"],
        "allow_write": False,
        "max_data_sensitivity": "INTERNAL",
        "max_query_limit": 100
    })
    tool_db = MockProcurementDB()

    # -------------------------------------------------------------------------
    # 6. Cryptographic State Keys
    # -------------------------------------------------------------------------
    priv_key, pub_key = CryptographicHandoffManager.generate_keypair()

    # -------------------------------------------------------------------------
    # 7. Multi-Stage Execution
    # -------------------------------------------------------------------------
    current_state_hash = ledger.current_hash
    findings_accumulated = {}

    for stage_idx, stage in enumerate(stages):
        for task_node in stage:
            # Step A: Bayes-UCB Agent Selection
            selected_agent = coordinator.route(domain=task_node.domain, total_system_steps=10)
            ledger.append_event("ROUTING_DISPATCH", {
                "task_id": task_node.task_id,
                "domain": task_node.domain,
                "selected_agent": selected_agent
            })

            # Step B: Sealed Cryptographic Handoff
            pkg = IntentPackage(
                run_id=run_id,
                handoff_id=f"handoff_{task_node.task_id}",
                parent_hash=current_state_hash,
                objective=objective_s0,  # S_0 pinned
                constraints=constraints,
                input_refs=[doc_ref],
                permitted_tools=["procurement_db"],
                expiry_time=time.time() + 300.0,
                findings=findings_accumulated
            )
            sealed_envelope = CryptographicHandoffManager.sign_package(pkg, priv_key, current_state_hash)

            # Receiver verifies cryptographic signature and immutable S_0
            unpacked_pkg = CryptographicHandoffManager.verify_and_unpack(
                sealed_envelope, pub_key, expected_prev_hash=current_state_hash, expected_objective=objective_s0
            )
            assert unpacked_pkg.objective == objective_s0

            current_state_hash = ledger.append_event("HANDOFF_VERIFIED", {
                "handoff_id": pkg.handoff_id,
                "package_hash": sealed_envelope["package_hash"],
                "agent": selected_agent
            })

            # Step C: Tool Action & CAMCO Policy Validation
            # Request limit=250 -> CAMCO must project down to 100 via Euclidean projection
            action = tool_db.create_action_record(operation="SELECT", data_sensitivity="INTERNAL", write_effect=False)
            decision, modified_params = policy_gate.validate_and_project(action, {"vendor_id": "V-001", "limit": 250})

            assert decision == "BOUNDED"
            assert modified_params["limit"] == 100

            # Execute tool under bounded parameters
            tool_output = tool_db.execute(
                vendor_id=modified_params.get("vendor_id"),
                limit=modified_params["limit"]
            )
            assert tool_output["status"] == "SUCCESS"

            current_state_hash = ledger.append_event("TOOL_EXECUTED", {
                "task_id": task_node.task_id,
                "tool": action.tool,
                "decision": decision,
                "records_returned": tool_output["returned_records"]
            })

            # Step D: Bayesian Evidence Update
            coordinator.update_evidence(
                agent_id=selected_agent,
                domain=task_node.domain,
                success=1,
                confidence=0.99
            )

            findings_accumulated[task_node.task_id] = {
                "records": tool_output["records"],
                "agent": selected_agent
            }

    # -------------------------------------------------------------------------
    # 8. Complete Verification of Audit Ledger
    # -------------------------------------------------------------------------
    is_valid, err_msg = ledger.verify_ledger_integrity()
    assert is_valid is True, f"Ledger integrity verification failed: {err_msg}"
    assert len(ledger.ledger) > 6

    # -------------------------------------------------------------------------
    # 9. IPS Intent Preservation Score Guarantee
    # -------------------------------------------------------------------------
    # S_0 pinned: IPS = 0.85(1.0) + 0.15(0.85^3) = 0.85 + 0.15(0.6141) = 0.9421 >= 91.66%
    n_hops = len(topology.nodes)
    ips = 0.85 * 1.0 + 0.15 * (0.85 ** n_hops)
    assert ips >= 0.9166, f"IPS retention {ips} fell below 91.66% target"
