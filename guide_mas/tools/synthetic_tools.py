"""
Synthetic Enterprise Sandboxed Tools Module.

Implements realistic enterprise tool mocks:
1. MockProcurementDB: SQL querying with sensitive column classification and limit bounding.
2. MockIncidentLogStore: Indexed IT outage and security audit logs with documentary citations.
3. MockEmailService: Write-effect communication service strictly blocked under read-only policy.
"""

from typing import Any, Dict, List, Optional
from guide_mas.core.policy_gate import ActionRecord
from guide_mas.tools.base import BaseTool


class MockProcurementDB(BaseTool):
    """
    Simulated enterprise SQL procurement database.
    Contains vendor SLA records with distinct sensitivity tiers.
    """

    RECORDS: List[Dict[str, Any]] = [
        {
            "vendor_id": "V-001",
            "vendor_name": "Apex Cloud Systems",
            "delivery_sla_days": 5,
            "uptime_guarantee_pct": 99.95,
            "warranty_months": 24,
            "compliance_tier": "ISO27001",
            "unit_price_usd": 1250.00,       # RESTRICTED
            "discount_margin_pct": 18.5       # RESTRICTED
        },
        {
            "vendor_id": "V-002",
            "vendor_name": "Nexus Hardware Global",
            "delivery_sla_days": 10,
            "uptime_guarantee_pct": 99.90,
            "warranty_months": 36,
            "compliance_tier": "SOC2_TYPE2",
            "unit_price_usd": 980.00,        # RESTRICTED
            "discount_margin_pct": 22.0       # RESTRICTED
        },
        {
            "vendor_id": "V-003",
            "vendor_name": "Zenith Infra Solutions",
            "delivery_sla_days": 3,
            "uptime_guarantee_pct": 99.99,
            "warranty_months": 48,
            "compliance_tier": "FEDRAMP_HIGH",
            "unit_price_usd": 2100.00,       # RESTRICTED
            "discount_margin_pct": 12.0       # RESTRICTED
        },
        {
            "vendor_id": "V-004",
            "vendor_name": "Orion Telecom Networks",
            "delivery_sla_days": 7,
            "uptime_guarantee_pct": 99.92,
            "warranty_months": 12,
            "compliance_tier": "PCI_DSS",
            "unit_price_usd": 650.00,        # RESTRICTED
            "discount_margin_pct": 15.0       # RESTRICTED
        },
    ]

    RESTRICTED_COLUMNS = {"unit_price_usd", "discount_margin_pct"}

    def __init__(self):
        super().__init__(
            name="procurement_db",
            description="Enterprise database of vendor procurement contracts and SLAs.",
            resource_class="procurement_records"
        )

    def create_action_record(
        self,
        operation: str = "SELECT",
        data_sensitivity: str = "INTERNAL",
        write_effect: bool = False
    ) -> ActionRecord:
        return ActionRecord(
            tool=self.name,
            operation=operation,
            resource_class=self.resource_class,
            data_sensitivity=data_sensitivity,
            write_effect=write_effect
        )

    def execute(
        self,
        columns: Optional[List[str]] = None,
        vendor_id: Optional[str] = None,
        limit: int = 100,
        include_pricing: bool = False
    ) -> Dict[str, Any]:
        """
        Queries procurement records with column masking and limit bounding.
        """
        results: List[Dict[str, Any]] = []

        for record in self.RECORDS:
            if vendor_id and record["vendor_id"] != vendor_id:
                continue

            row: Dict[str, Any] = {}
            target_cols = columns or list(record.keys())

            for col in target_cols:
                if col in record:
                    if col in self.RESTRICTED_COLUMNS and not include_pricing:
                        row[col] = "[REDACTED_CONFIDENTIAL_PII]"
                    else:
                        row[col] = record[col]
            results.append(row)

        effective_limit = max(1, limit)
        bounded_results = results[:effective_limit]

        return {
            "status": "SUCCESS",
            "returned_records": len(bounded_results),
            "total_matches": len(results),
            "records": bounded_results
        }


class MockIncidentLogStore(BaseTool):
    """
    Simulated enterprise IT audit and incident management log repository.
    Provides verifiable citations for root-cause reconciliation tasks.
    """

    LOGS: List[Dict[str, Any]] = [
        {
            "incident_id": "INC-1001",
            "timestamp": "2026-03-15T08:22:11Z",
            "service": "auth-gateway-prod",
            "severity": "CRITICAL",
            "root_cause": "TLS certificate expiration on secondary ingress proxy",
            "citation_ref": "DOC-RCA-1001",
            "duration_minutes": 42
        },
        {
            "incident_id": "INC-1002",
            "timestamp": "2026-04-02T14:10:05Z",
            "service": "billing-ledger-db",
            "severity": "HIGH",
            "root_cause": "Deadlock during batch reconciliation job execution",
            "citation_ref": "DOC-RCA-1002",
            "duration_minutes": 18
        },
        {
            "incident_id": "INC-1003",
            "timestamp": "2026-05-19T19:45:00Z",
            "service": "k8s-us-east-cluster",
            "severity": "MEDIUM",
            "root_cause": "Pod eviction triggered by ephemeral storage exhaustion",
            "citation_ref": "DOC-RCA-1003",
            "duration_minutes": 15
        },
        {
            "incident_id": "INC-1004",
            "timestamp": "2026-06-08T03:12:49Z",
            "service": "search-indexing-worker",
            "severity": "LOW",
            "root_cause": "Elasticsearch cluster yellow state due to unassigned replica shards",
            "citation_ref": "DOC-RCA-1004",
            "duration_minutes": 55
        },
    ]

    def __init__(self):
        super().__init__(
            name="incident_log_store",
            description="Repository of indexed IT incident logs and formal RCA documentation.",
            resource_class="audit_logs"
        )

    def create_action_record(
        self,
        operation: str = "QUERY_LOGS",
        data_sensitivity: str = "INTERNAL",
        write_effect: bool = False
    ) -> ActionRecord:
        return ActionRecord(
            tool=self.name,
            operation=operation,
            resource_class=self.resource_class,
            data_sensitivity=data_sensitivity,
            write_effect=write_effect
        )

    def execute(
        self,
        incident_id: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Queries incident records by ID or severity filter."""
        results = []
        for log in self.LOGS:
            if incident_id and log["incident_id"] != incident_id:
                continue
            if severity and log["severity"] != severity.upper():
                continue
            results.append(log)

        effective_limit = max(1, limit)
        bounded_results = results[:effective_limit]

        return {
            "status": "SUCCESS",
            "returned_records": len(bounded_results),
            "total_matches": len(results),
            "logs": bounded_results
        }


class MockEmailService(BaseTool):
    """
    Simulated external enterprise communication and email dispatch service.
    Possesses write-effect side consequences; must be blocked under read-only policy.
    """

    def __init__(self):
        super().__init__(
            name="email_service",
            description="External SMTP communication dispatch service for enterprise alerts.",
            resource_class="external_comms"
        )
        self.dispatched_emails: List[Dict[str, Any]] = []

    def create_action_record(
        self,
        operation: str = "SEND_EMAIL",
        data_sensitivity: str = "INTERNAL",
        write_effect: bool = True
    ) -> ActionRecord:
        return ActionRecord(
            tool=self.name,
            operation=operation,
            resource_class=self.resource_class,
            data_sensitivity=data_sensitivity,
            write_effect=write_effect
        )

    def execute(
        self,
        recipient: str,
        subject: str,
        body: str
    ) -> Dict[str, Any]:
        """Dispatches an email notification."""
        record = {
            "recipient": recipient,
            "subject": subject,
            "body": body,
            "status": "SENT"
        }
        self.dispatched_emails.append(record)
        return {
            "status": "SUCCESS",
            "message": f"Email successfully dispatched to {recipient}",
            "record": record
        }


def get_synthetic_tools() -> Dict[str, BaseTool]:
    """Returns a dictionary of all available synthetic enterprise tools."""
    tools = [MockProcurementDB(), MockIncidentLogStore(), MockEmailService()]
    return {t.name: t for t in tools}
