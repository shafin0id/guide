"""
Unit tests for CAMCOPolicyGate and ActionRecord.

Verifies:
1. Tool allow-list enforcement (rejects unauthorized tools with DENIED_BY_POLICY).
2. Read-only boundary enforcement (blocks write-effect operations when allow_write=False).
3. Data sensitivity clearance hierarchy (rejects RESTRICTED when clearance is INTERNAL).
4. Euclidean minimum-distance projection: clamps query limit to permissible upper bound (BOUNDED).
5. Forbidden operation blocking (e.g. DROP, DELETE).
6. Execution allowance for fully compliant action requests (ALLOW).
"""

import pytest
from guide_mas.core.policy_gate import ActionRecord, CAMCOPolicyGate


@pytest.fixture
def standard_gate():
    """Standard enterprise policy gate fixture."""
    return CAMCOPolicyGate({
        "permitted_tools": ["procurement_db", "incident_log_store"],
        "allow_write": False,
        "max_data_sensitivity": "INTERNAL",
        "max_query_limit": 100,
        "forbidden_operations": ["DROP", "DELETE", "TRUNCATE", "SHUTDOWN"]
    })


def test_allowed_compliant_action(standard_gate):
    """Verifies that a compliant read action returns ALLOW."""
    action = ActionRecord(
        tool="procurement_db",
        operation="SELECT",
        resource_class="procurement_records",
        data_sensitivity="INTERNAL",
        write_effect=False
    )
    decision, params = standard_gate.validate_and_project(action, {"vendor_id": "V-001", "limit": 25})
    assert decision == "ALLOW"
    assert params["limit"] == 25


def test_unpermitted_tool_denied(standard_gate):
    """Verifies that an unauthorized tool is blocked deterministically."""
    action = ActionRecord(
        tool="unauthorized_external_scraper",
        operation="FETCH",
        resource_class="web_pages",
        data_sensitivity="PUBLIC",
        write_effect=False
    )
    decision, res = standard_gate.validate_and_project(action, {})
    assert decision == "DENY"
    assert "Tool 'unauthorized_external_scraper' is not in permitted list" in res["error"]


def test_write_operation_blocked_on_readonly(standard_gate):
    """Verifies that write_effect=True is blocked under read-only policy."""
    action = ActionRecord(
        tool="procurement_db",
        operation="INSERT",
        resource_class="procurement_records",
        data_sensitivity="INTERNAL",
        write_effect=True
    )
    decision, res = standard_gate.validate_and_project(action, {})
    assert decision == "DENY"
    assert "Write operations are strictly prohibited" in res["error"]


def test_sensitivity_clearance_violation(standard_gate):
    """Verifies that requesting RESTRICTED data under INTERNAL clearance is denied."""
    action = ActionRecord(
        tool="procurement_db",
        operation="SELECT",
        resource_class="procurement_records",
        data_sensitivity="RESTRICTED",
        write_effect=False
    )
    decision, res = standard_gate.validate_and_project(action, {"columns": ["unit_price_usd"]})
    assert decision == "DENY"
    assert "exceeds maximum allowed clearance" in res["error"]


def test_euclidean_projection_limit_bounding(standard_gate):
    """Verifies that limit=500 is projected onto permissible set [1, 100] resulting in BOUNDED decision."""
    action = ActionRecord(
        tool="procurement_db",
        operation="SELECT",
        resource_class="procurement_records",
        data_sensitivity="INTERNAL",
        write_effect=False
    )
    decision, params = standard_gate.validate_and_project(action, {"limit": 500})
    assert decision == "BOUNDED"
    assert params["limit"] == 100
    assert "_projection_note" in params
    assert "Euclidean distance=400.00" in params["_projection_note"]


def test_forbidden_operation_blocked(standard_gate):
    """Verifies that prohibited SQL DDL verbs (e.g. DROP) are denied immediately."""
    action = ActionRecord(
        tool="procurement_db",
        operation="DROP",
        resource_class="procurement_records",
        data_sensitivity="INTERNAL",
        write_effect=False
    )
    decision, res = standard_gate.validate_and_project(action, {})
    assert decision == "DENY"
    assert "Operation 'DROP' is strictly prohibited" in res["error"]


def test_boundary_tolerance_epsilon_denial():
    """Verifies that when projection distance exceeds boundary_tolerance_epsilon, action is DENIED."""
    strict_gate = CAMCOPolicyGate({
        "permitted_tools": ["procurement_db"],
        "max_data_sensitivity": "INTERNAL",
        "max_query_limit": 100,
        "boundary_tolerance_epsilon": 50.0  # Max allowable projection distance is 50
    })
    action = ActionRecord(
        tool="procurement_db",
        operation="SELECT",
        resource_class="procurement_records",
        data_sensitivity="INTERNAL",
        write_effect=False
    )
    # limit=200 has distance 100 > epsilon=50 -> must be DENIED!
    decision, res = strict_gate.validate_and_project(action, {"limit": 200})
    assert decision == "DENY"
    assert "exceeds boundary tolerance epsilon_max" in res["error"]

    # limit=130 has distance 30 <= epsilon=50 -> BOUNDED
    decision2, res2 = strict_gate.validate_and_project(action, {"limit": 130})
    assert decision2 == "BOUNDED"
    assert res2["limit"] == 100


def test_vector_coordinate_projection(standard_gate):
    """Verifies 5D continuous coordinate mapping and projection."""
    action = ActionRecord(
        tool="procurement_db",
        operation="SELECT",
        resource_class="procurement_records",
        data_sensitivity="RESTRICTED",
        write_effect=True
    )
    coord = standard_gate.action_to_coordinate(action)
    assert len(coord) == 5
    assert coord[3] == 4.0  # RESTRICTED rank
    assert coord[4] == 1.0  # write_effect

    projected, dist = standard_gate.project_vector(coord)
    assert len(projected) == 5
    assert dist > 0.0
    # On standard_gate with INTERNAL (2) and allow_write=False (0), sensitivity & write are projected
    assert projected[3] == 2.0
    assert projected[4] == 0.0
