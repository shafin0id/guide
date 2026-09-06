"""
CAMCO Pre-Execution External Policy Gate Module.

Implements deterministic action tuple interception and Euclidean convex projection:
u* = argmin_{v in C} ||u - v||_2^2 for runtime parameters.
Enforces zero-trust boundaries returning ALLOW, BOUNDED, or DENIED_BY_POLICY.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


class PolicyDecision(str, Enum):
    """Standard policy decisions emitted by CAMCO gate."""
    ALLOW = "ALLOW"
    BOUNDED = "BOUNDED"
    DENY = "DENY"
    DENIED_BY_POLICY = "DENIED_BY_POLICY"


@dataclass
class PolicyEvaluationResult:
    decision: PolicyDecision
    validated_params: Dict[str, Any]
    is_blocked: bool
    error: Optional[str] = None


@dataclass
class ActionProposal:
    """Action proposal for open-domain tool use evaluation."""
    agent_id: str
    tool_name: str
    tool_arguments: Dict[str, Any]
    permitted_tools: List[str]
    data_sensitivity: str = "PUBLIC"
    is_write_effect: bool = False
    target_resource: str = "default"


@dataclass(frozen=True)
class ActionRecord:
    """
    Standardized 5-element execution tuple characterizing external action requests.
    tau = [Tool, Operation, Resource_Class, Data_Sensitivity, Write_Effect]
    """
    tool: str
    operation: str
    resource_class: str
    data_sensitivity: str
    write_effect: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool": self.tool,
            "operation": self.operation,
            "resource_class": self.resource_class,
            "data_sensitivity": self.data_sensitivity,
            "write_effect": self.write_effect,
        }


class CAMCOPolicyGate:
    """
    Out-of-process pre-execution policy enforcement gate.
    Evaluates requested action tuples and runtime arguments against active enterprise policies.
    """

    SENSITIVITY_HIERARCHY: Dict[str, int] = {
        "PUBLIC": 1,
        "INTERNAL": 2,
        "CONFIDENTIAL": 3,
        "RESTRICTED": 4,
    }

    def __init__(self, policy_rules: Optional[Dict[str, Any]] = None):
        """
        Initializes CAMCO policy gate with compliance configuration.

        Args:
            policy_rules: Dictionary containing:
                - permitted_tools (List[str])
                - allow_write (bool)
                - max_data_sensitivity (str: PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED)
                - max_query_limit (int)
                - forbidden_operations (List[str])
                - boundary_tolerance_epsilon (float)
        """
        rules = policy_rules or {}
        self.permitted_tools: List[str] = list(
            rules.get("permitted_tools", ["procurement_db", "incident_log_store", "email_service"])
        )
        self.allow_write: bool = bool(rules.get("allow_write", False))
        self.max_data_sensitivity: str = str(rules.get("max_data_sensitivity", "PUBLIC")).upper()
        self.max_query_limit: int = int(rules.get("max_query_limit", 100))
        self.forbidden_operations: List[str] = [
            op.upper() for op in rules.get("forbidden_operations", ["DROP", "DELETE", "TRUNCATE", "SHUTDOWN"])
        ]
        self.boundary_tolerance_epsilon: float = float(rules.get("boundary_tolerance_epsilon", 0.0))

    def project_limit(self, requested_limit: float) -> Tuple[int, float]:
        """
        Computes 1D Euclidean minimum-distance projection onto permissible closed interval C = [1, max_limit]:
        u* = argmin_{v in [1, L_max]} (u - v)^2

        Returns:
            Tuple of (projected_limit, euclidean_distance).
        """
        u = float(requested_limit)
        lower_bound = 1.0
        upper_bound = float(self.max_query_limit)

        projected = min(max(lower_bound, u), upper_bound)
        distance = abs(u - projected)
        return int(projected), distance

    def validate_and_project(
        self,
        action: ActionRecord,
        params: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Evaluates proposed action against convex permissible set C.

        Returns:
            Tuple of (decision, result_parameters_or_error)
            Decisions:
                'ALLOW'   - Action fully compliant, parameters unmodified.
                'BOUNDED' - Action admissible after Euclidean projection.
                'DENY'    - Policy violation; returns DENIED_BY_POLICY description.
        """
        eval_params = dict(params) if params else {}

        # Rule 1: Tool Allow-list Interception
        if action.tool not in self.permitted_tools:
            return "DENY", {
                "error": f"DENIED_BY_POLICY: Tool '{action.tool}' is not in permitted list {self.permitted_tools}"
            }

        # Rule 2: Forbidden Operation Blocking
        if action.operation.upper() in self.forbidden_operations:
            return "DENY", {
                "error": f"DENIED_BY_POLICY: Operation '{action.operation}' is strictly prohibited"
            }

        # Rule 3: Write Operations on Read-Only Policy
        if action.write_effect and not self.allow_write:
            return "DENY", {
                "error": "DENIED_BY_POLICY: Write operations are strictly prohibited under active read-only policy"
            }

        # Rule 4: Data Sensitivity Clearance Enforcement
        action_sens = action.data_sensitivity.upper()
        action_rank = self.SENSITIVITY_HIERARCHY.get(action_sens, 4)
        clearance_rank = self.SENSITIVITY_HIERARCHY.get(self.max_data_sensitivity, 1)

        if action_rank > clearance_rank:
            return "DENY", {
                "error": (
                    f"DENIED_BY_POLICY: Action data sensitivity '{action_sens}' (rank {action_rank}) "
                    f"exceeds maximum allowed clearance '{self.max_data_sensitivity}' (rank {clearance_rank})"
                )
            }

        # Rule 5: Convex Euclidean Projection on Query Limits
        if "limit" in eval_params:
            try:
                requested_limit = float(eval_params["limit"])
                projected_limit, distance = self.project_limit(requested_limit)

                if distance > 0.0:
                    # Boundary tolerance check: if distance exceeds epsilon_max, DENY immediately
                    if self.boundary_tolerance_epsilon > 0.0 and distance > self.boundary_tolerance_epsilon:
                        return "DENY", {
                            "error": (
                                f"DENIED_BY_POLICY: Parameter projection distance {distance:.2f} "
                                f"exceeds boundary tolerance epsilon_max ({self.boundary_tolerance_epsilon:.2f})"
                            )
                        }

                    bounded_params = eval_params.copy()
                    bounded_params["limit"] = projected_limit
                    bounded_params["_projection_note"] = (
                        f"Projected limit from {int(requested_limit)} to {projected_limit} "
                        f"(Euclidean distance={distance:.2f})"
                    )
                    return "BOUNDED", bounded_params
            except (ValueError, TypeError):
                return "DENY", {
                    "error": "DENIED_BY_POLICY: Parameter 'limit' must be numeric"
                }

        return "ALLOW", eval_params

    def action_to_coordinate(
        self,
        action: ActionRecord,
        params: Optional[Dict[str, Any]] = None
    ) -> np.ndarray:
        """
        Maps the 5-element execution tuple tau into a continuous coordinate u in R^5:
        u = [tool_code, op_code, resource_code, sensitivity_rank, write_effect_flag].
        """
        tool_code = float(hash(action.tool) % 1000) / 1000.0
        op_code = float(hash(action.operation) % 1000) / 1000.0
        res_code = float(hash(action.resource_class) % 1000) / 1000.0
        sens_rank = float(self.SENSITIVITY_HIERARCHY.get(action.data_sensitivity.upper(), 4))
        write_flag = 1.0 if action.write_effect else 0.0
        return np.array([tool_code, op_code, res_code, sens_rank, write_flag], dtype=float)

    def project_vector(self, u: np.ndarray, target_convex_bounds: Optional[np.ndarray] = None) -> Tuple[np.ndarray, float]:
        """
        Computes continuous Euclidean minimum-distance projection:
        u* = argmin_{v in C} ||u - v||_2^2.

        Returns:
            Tuple of (projected_vector, euclidean_distance).
        """
        if target_convex_bounds is None:
            # Default bounds: [0..1, 0..1, 0..1, 1..max_sens, 0..allow_write]
            max_sens = float(self.SENSITIVITY_HIERARCHY.get(self.max_data_sensitivity, 1))
            max_write = 1.0 if self.allow_write else 0.0
            lower = np.array([0.0, 0.0, 0.0, 1.0, 0.0])
            upper = np.array([1.0, 1.0, 1.0, max_sens, max_write])
        else:
            lower = target_convex_bounds[0]
            upper = target_convex_bounds[1]

        projected = np.clip(u, lower, upper)
        dist = float(np.linalg.norm(u - projected))
        return projected, dist

    def validate(
        self,
        action: ActionRecord,
        params: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """Convenience alias for validate_and_project."""
        return self.validate_and_project(action, params)

    def evaluate(self, proposal: ActionProposal) -> PolicyEvaluationResult:
        """
        Evaluates an ActionProposal against CAMCO zero-trust policy rules.
        """
        # If proposal provides permitted_tools, enforce tool allow-list
        if proposal.permitted_tools is not None:
            if proposal.tool_name not in proposal.permitted_tools:
                return PolicyEvaluationResult(
                    decision=PolicyDecision.DENY,
                    validated_params=proposal.tool_arguments,
                    is_blocked=True,
                    error=f"Tool '{proposal.tool_name}' not in permitted tools: {proposal.permitted_tools}"
                )

        # Check write effect
        if proposal.is_write_effect and not self.allow_write:
            return PolicyEvaluationResult(
                decision=PolicyDecision.DENY,
                validated_params=proposal.tool_arguments,
                is_blocked=True,
                error="Write operations prohibited by policy"
            )

        # Check sensitivity
        prop_sens = self.SENSITIVITY_HIERARCHY.get(proposal.data_sensitivity.upper(), 4)
        max_sens = self.SENSITIVITY_HIERARCHY.get(self.max_data_sensitivity, 1)
        if prop_sens > max_sens:
            return PolicyEvaluationResult(
                decision=PolicyDecision.DENY,
                validated_params=proposal.tool_arguments,
                is_blocked=True,
                error=f"Data sensitivity '{proposal.data_sensitivity}' exceeds clearance '{self.max_data_sensitivity}'"
            )

        return PolicyEvaluationResult(
            decision=PolicyDecision.ALLOW,
            validated_params=proposal.tool_arguments,
            is_blocked=False,
            error=None
        )

