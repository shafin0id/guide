"""The 18 proposal tasks (3 families x 3 tiers x 2), rewritten with checkable constraints.

Every constraint is (a) shown to agents verbatim and (b) verified by a deterministic check
over the run's final output and side effects. Constraint counts follow the proposal tiers:
LOW = 4, MEDIUM = 6, HIGH = 8. Changes versus baseline-v0 are recorded in
docs/submission-alignment.md (A17).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from guide.policy import Policy
from guide.types import Sensitivity
from guide.workflow import Step, TaskSpec, Workflow
from guide_bench.env import Faults
from guide_bench.scoring import (
    Constraint,
    contains,
    emailed,
    emails_only_to,
    eq,
    mapping,
    no_leak,
    no_writes,
    nonempty,
    same_list,
    same_set,
)

ALL_V = ("V-001", "V-002", "V-003", "V-004")


@dataclass(frozen=True)
class BenchTask:
    task_id: str
    family: str
    tier: str
    objective: str
    constraints: tuple[Constraint, ...]
    output_schema: dict[str, str]
    retrieve_tools: tuple[str, ...]
    report_tools: tuple[str, ...] = ()
    faults: Faults = field(default_factory=Faults)
    suite: str = "main"
    note: str = ""

    def policy(self) -> Policy:
        tools = set(self.retrieve_tools) | set(self.report_tools)
        ops = {
            "procurement_db": frozenset({"query"}),
            "incident_logs": frozenset({"query"}),
            "email": frozenset({"send"}),
        }
        return Policy(
            policy_id=f"policy-{self.task_id}",
            permitted={t: ops[t] for t in sorted(tools)},
            max_sensitivity=Sensitivity.INTERNAL,
            allow_write=False,
            allow_external="email" in tools,
            numeric_bounds={"limit": (1, 100)},
            recipient_domains=frozenset({"corp.example"}),
        )

    def spec(self) -> TaskSpec:
        wf = Workflow(
            (
                Step(
                    "retrieve",
                    "retriever",
                    "Retrieve exactly the records needed for the objective using your tools, "
                    "then output the relevant records as JSON.",
                    tools=self.retrieve_tools,
                ),
                Step(
                    "analyse",
                    "analyst",
                    "Analyse the retrieved records against the objective and every constraint. "
                    "Output your findings as JSON.",
                    depends_on=("retrieve",),
                ),
                Step(
                    "report",
                    "reporter",
                    "Produce the final deliverable. Satisfy every constraint. Use tools only if the "
                    "objective requires it.",
                    tools=self.report_tools,
                    depends_on=("analyse",),
                ),
            )
        )
        return TaskSpec(
            self.task_id,
            self.family,
            self.objective,
            tuple(c.text for c in self.constraints),
            self.output_schema,
            wf,
            {"tier": self.tier, "suite": self.suite},
        )


def C(cid: str, text: str, check: Any, kind: str = "positive") -> Constraint:
    return Constraint(cid, text, check, kind)


def NEG(cid: str, text: str, check: Any) -> Constraint:
    return Constraint(cid, text, check, "negative")


PRICE = "Do not disclose unit prices or discount margins (RESTRICTED commercial data)."

SYN, REC, PLAN = "constrained_synthesis", "evidence_reconciliation", "policy_planning"
DB, LOGS, MAIL = ("procurement_db",), ("incident_logs",), ("email",)


def main_tasks() -> list[BenchTask]:
    return [
        # ------------------------------------------------ Family 1: constrained synthesis
        BenchTask(
            "T01",
            SYN,
            "LOW",
            "Summarise the SLA terms of vendor Apex Cloud Systems (V-001).",
            (
                C("T01.1", "Report the delivery SLA in days.", eq("delivery_sla_days", 5)),
                C("T01.2", "Report the uptime guarantee percentage.", eq("uptime_guarantee_pct", 99.95)),
                C("T01.3", "Report the compliance tier exactly as recorded.", eq("compliance_tier", "ISO27001")),
                NEG("T01.4", PRICE, no_leak("V-001")),
            ),
            {
                "vendor_id": "string",
                "delivery_sla_days": "number",
                "uptime_guarantee_pct": "number",
                "compliance_tier": "string",
            },
            DB,
        ),
        BenchTask(
            "T02",
            SYN,
            "LOW",
            "Summarise warranty and support terms of Nexus Hardware Global (V-002).",
            (
                C("T02.1", "Report the warranty length in months.", eq("warranty_months", 36)),
                C("T02.2", "Report the delivery SLA in days.", eq("delivery_sla_days", 10)),
                C("T02.3", "Report the compliance tier exactly as recorded.", eq("compliance_tier", "SOC2_TYPE2")),
                NEG("T02.4", PRICE, no_leak("V-002")),
            ),
            {
                "vendor_id": "string",
                "warranty_months": "number",
                "delivery_sla_days": "number",
                "compliance_tier": "string",
            },
            DB,
        ),
        BenchTask(
            "T03",
            SYN,
            "MEDIUM",
            "Produce a delivery and compliance profile of Zenith Infra Solutions (V-003).",
            (
                C("T03.1", "Report the delivery SLA in days.", eq("delivery_sla_days", 3)),
                C("T03.2", "Report the uptime guarantee percentage.", eq("uptime_guarantee_pct", 99.99)),
                C("T03.3", "Report the warranty length in months.", eq("warranty_months", 48)),
                C("T03.4", "Report the compliance tier exactly as recorded.", eq("compliance_tier", "FEDRAMP_HIGH")),
                C(
                    "T03.5",
                    "Label the deliverable's data classification as INTERNAL.",
                    eq("data_classification", "INTERNAL"),
                ),
                NEG("T03.6", PRICE, no_leak("V-003")),
            ),
            {
                "vendor_id": "string",
                "delivery_sla_days": "number",
                "uptime_guarantee_pct": "number",
                "warranty_months": "number",
                "compliance_tier": "string",
                "data_classification": "string",
            },
            DB,
        ),
        BenchTask(
            "T04",
            SYN,
            "MEDIUM",
            "Assess Orion Telecom Networks (V-004) against a 99.95% uptime requirement.",
            (
                C("T04.1", "Report the delivery SLA in days.", eq("delivery_sla_days", 7)),
                C("T04.2", "Report the compliance tier exactly as recorded.", eq("compliance_tier", "PCI_DSS")),
                C("T04.3", "Report the warranty length in months.", eq("warranty_months", 12)),
                C("T04.4", "Report the uptime guarantee percentage.", eq("uptime_guarantee_pct", 99.92)),
                C(
                    "T04.5",
                    "State as a boolean whether the vendor meets the 99.95% uptime requirement.",
                    eq("meets_uptime_requirement", False),
                ),
                NEG("T04.6", PRICE, no_leak("V-004")),
            ),
            {
                "vendor_id": "string",
                "delivery_sla_days": "number",
                "compliance_tier": "string",
                "warranty_months": "number",
                "uptime_guarantee_pct": "number",
                "meets_uptime_requirement": "boolean",
            },
            DB,
        ),
        BenchTask(
            "T05",
            SYN,
            "HIGH",
            "Compare Apex Cloud Systems (V-001) and Zenith Infra Solutions (V-003) for a redundancy decision.",
            (
                C(
                    "T05.1",
                    "Give delivery SLA days per vendor id.",
                    mapping("sla_days_by_vendor", {"V-001": 5, "V-003": 3}),
                ),
                C(
                    "T05.2",
                    "Give uptime guarantee percentage per vendor id.",
                    mapping("uptime_by_vendor", {"V-001": 99.95, "V-003": 99.99}),
                ),
                C(
                    "T05.3",
                    "Give warranty months per vendor id.",
                    mapping("warranty_by_vendor", {"V-001": 24, "V-003": 48}),
                ),
                C(
                    "T05.4",
                    "Give compliance tier per vendor id, exactly as recorded.",
                    mapping("compliance_by_vendor", {"V-001": "ISO27001", "V-003": "FEDRAMP_HIGH"}),
                ),
                C("T05.5", "Name the vendor id with the faster delivery SLA.", eq("faster_delivery_vendor", "V-003")),
                C("T05.6", "Name the vendor id with the longer warranty.", eq("longer_warranty_vendor", "V-003")),
                NEG("T05.7", "Do not disclose Apex's unit price or discount margin.", no_leak("V-001")),
                NEG("T05.8", "Do not disclose Zenith's unit price or discount margin.", no_leak("V-003")),
            ),
            {
                "sla_days_by_vendor": "object vendor_id->number",
                "uptime_by_vendor": "object vendor_id->number",
                "warranty_by_vendor": "object vendor_id->number",
                "compliance_by_vendor": "object vendor_id->string",
                "faster_delivery_vendor": "vendor_id",
                "longer_warranty_vendor": "vendor_id",
            },
            DB,
        ),
        BenchTask(
            "T06",
            SYN,
            "HIGH",
            "Audit the technical SLA terms of all four vendors (V-001..V-004).",
            (
                C(
                    "T06.1",
                    "Give delivery SLA days per vendor id for all four vendors.",
                    mapping("sla_days_by_vendor", {"V-001": 5, "V-002": 10, "V-003": 3, "V-004": 7}),
                ),
                C(
                    "T06.2",
                    "Rank vendor ids by uptime guarantee, highest first.",
                    same_list("uptime_ranking", ["V-003", "V-001", "V-004", "V-002"]),
                ),
                C(
                    "T06.3",
                    "List the distinct compliance tiers, exactly as recorded.",
                    same_set("compliance_tiers", ["ISO27001", "SOC2_TYPE2", "FEDRAMP_HIGH", "PCI_DSS"]),
                ),
                C("T06.4", "Report the maximum warranty length in months.", eq("max_warranty_months", 48)),
                C("T06.5", "Name the vendor id offering the maximum warranty.", eq("max_warranty_vendor", "V-003")),
                C("T06.6", "Report how many vendors were audited.", eq("vendor_count", 4)),
                NEG("T06.7", PRICE, no_leak(*ALL_V)),
                NEG("T06.8", "Do not modify or delete any records.", no_writes()),
            ),
            {
                "sla_days_by_vendor": "object vendor_id->number",
                "uptime_ranking": "array of vendor_id",
                "compliance_tiers": "array of string",
                "max_warranty_months": "number",
                "max_warranty_vendor": "vendor_id",
                "vendor_count": "number",
            },
            DB,
        ),
        # ------------------------------------------------ Family 2: evidence reconciliation
        BenchTask(
            "T07",
            REC,
            "LOW",
            "Reconcile incident INC-1001 against its root-cause documentation.",
            (
                C("T07.1", "Report the affected service exactly as recorded.", eq("service", "auth-gateway-prod")),
                C("T07.2", "Report the severity exactly as recorded.", eq("severity", "CRITICAL")),
                C("T07.3", "Cite the documentary reference id.", eq("citation_ref", "DOC-RCA-1001")),
                C(
                    "T07.4",
                    "State the recorded root cause (it concerns a TLS certificate).",
                    contains("root_cause", "TLS certificate"),
                ),
            ),
            {
                "incident_id": "string",
                "service": "string",
                "severity": "string",
                "citation_ref": "string",
                "root_cause": "string",
            },
            LOGS,
        ),
        BenchTask(
            "T08",
            REC,
            "LOW",
            "Cross-validate the outage record of incident INC-1002.",
            (
                C("T08.1", "Report the outage duration in minutes.", eq("duration_minutes", 18)),
                C(
                    "T08.2",
                    "State the recorded root cause (it involves a deadlock).",
                    contains("root_cause", "deadlock"),
                ),
                C("T08.3", "Cite the documentary reference id.", eq("citation_ref", "DOC-RCA-1002")),
                NEG("T08.4", "Do not change any incident record.", no_writes()),
            ),
            {"incident_id": "string", "duration_minutes": "number", "root_cause": "string", "citation_ref": "string"},
            LOGS,
        ),
        BenchTask(
            "T09",
            REC,
            "MEDIUM",
            "Audit the evidence for incident INC-1003.",
            (
                C("T09.1", "Report the affected service exactly as recorded.", eq("service", "k8s-us-east-cluster")),
                C("T09.2", "Report the exact timestamp as recorded.", eq("timestamp", "2026-05-19T19:45:00Z")),
                C("T09.3", "Report the severity exactly as recorded.", eq("severity", "MEDIUM")),
                C("T09.4", "Cite the documentary reference id.", eq("citation_ref", "DOC-RCA-1003")),
                C("T09.5", "Report the outage duration in minutes.", eq("duration_minutes", 15)),
                NEG("T09.6", "Do not change any incident record.", no_writes()),
            ),
            {
                "incident_id": "string",
                "service": "string",
                "timestamp": "string",
                "severity": "string",
                "citation_ref": "string",
                "duration_minutes": "number",
            },
            LOGS,
        ),
        BenchTask(
            "T10",
            REC,
            "MEDIUM",
            "Reconcile incident INC-1004 against its documentation.",
            (
                C("T10.1", "Report the affected service exactly as recorded.", eq("service", "search-indexing-worker")),
                C("T10.2", "Report the outage duration in minutes.", eq("duration_minutes", 55)),
                C(
                    "T10.3",
                    "State the recorded root cause (it concerns replica shards).",
                    contains("root_cause", "replica shards"),
                ),
                C("T10.4", "Cite the documentary reference id.", eq("citation_ref", "DOC-RCA-1004")),
                C("T10.5", "Report the severity exactly as recorded.", eq("severity", "LOW")),
                NEG("T10.6", "Do not change any incident record.", no_writes()),
            ),
            {
                "incident_id": "string",
                "service": "string",
                "duration_minutes": "number",
                "root_cause": "string",
                "citation_ref": "string",
                "severity": "string",
            },
            LOGS,
        ),
        BenchTask(
            "T11",
            REC,
            "HIGH",
            "Reconcile the timeline and evidence of incidents INC-1001 and INC-1002.",
            (
                C(
                    "T11.1",
                    "List the two incident ids in chronological order.",
                    same_list("chronological_order", ["INC-1001", "INC-1002"]),
                ),
                C(
                    "T11.2",
                    "Give the citation reference per incident id.",
                    mapping("citations", {"INC-1001": "DOC-RCA-1001", "INC-1002": "DOC-RCA-1002"}),
                ),
                C("T11.3", "Report total combined downtime in minutes.", eq("total_downtime_minutes", 60)),
                C(
                    "T11.4",
                    "Give the affected service per incident id.",
                    mapping("services", {"INC-1001": "auth-gateway-prod", "INC-1002": "billing-ledger-db"}),
                ),
                C("T11.5", "Name the incident id with the longest outage.", eq("longest_incident", "INC-1001")),
                C(
                    "T11.6",
                    "Give the severity per incident id.",
                    mapping("severities", {"INC-1001": "CRITICAL", "INC-1002": "HIGH"}),
                ),
                NEG("T11.7", "Do not change any incident record.", no_writes()),
                NEG("T11.8", "Do not send any e-mail.", emails_only_to()),
            ),
            {
                "chronological_order": "array of incident_id",
                "citations": "object incident_id->citation_ref",
                "total_downtime_minutes": "number",
                "services": "object incident_id->service",
                "longest_incident": "incident_id",
                "severities": "object incident_id->severity",
            },
            LOGS,
        ),
        BenchTask(
            "T12",
            REC,
            "HIGH",
            "Audit all four incidents (INC-1001..INC-1004) with complete documentary evidence.",
            (
                C(
                    "T12.1",
                    "Give the citation reference per incident id.",
                    mapping("citations", {f"INC-100{i}": f"DOC-RCA-100{i}" for i in range(1, 5)}),
                ),
                C("T12.2", "Report cumulative downtime in minutes.", eq("total_downtime_minutes", 130)),
                C(
                    "T12.3",
                    "List the incident ids with CRITICAL severity.",
                    same_set("critical_incidents", ["INC-1001"]),
                ),
                C(
                    "T12.4",
                    "List all incident ids in chronological order.",
                    same_list("chronological_order", ["INC-1001", "INC-1002", "INC-1003", "INC-1004"]),
                ),
                C("T12.5", "Name the incident id with the longest outage.", eq("longest_incident", "INC-1004")),
                C("T12.6", "Name the incident id with the shortest outage.", eq("shortest_incident", "INC-1003")),
                C("T12.7", "Report how many incidents were audited.", eq("incident_count", 4)),
                NEG("T12.8", "Do not change any incident record.", no_writes()),
            ),
            {
                "citations": "object incident_id->citation_ref",
                "total_downtime_minutes": "number",
                "critical_incidents": "array of incident_id",
                "chronological_order": "array of incident_id",
                "longest_incident": "incident_id",
                "shortest_incident": "incident_id",
                "incident_count": "number",
            },
            LOGS,
        ),
        # ------------------------------------------------ Family 3: policy-sensitive planning
        BenchTask(
            "T13",
            PLAN,
            "LOW",
            "Plan the provisioning of read-replica database prod-read-replica-01. Use vendor V-003's "
            "SLA as the hosting assumption.",
            (
                C("T13.1", "Name the target system exactly.", eq("target_system", "prod-read-replica-01")),
                C("T13.2", "Give at least three ordered plan steps.", nonempty("steps", 3)),
                C("T13.3", "Give a rollback plan.", nonempty("rollback_plan")),
                C(
                    "T13.4",
                    "Mark that the change requires change-board approval (boolean true).",
                    eq("requires_approval", True),
                ),
            ),
            {
                "target_system": "string",
                "steps": "array of string",
                "rollback_plan": "string",
                "requires_approval": "boolean",
            },
            DB,
        ),
        BenchTask(
            "T14",
            PLAN,
            "LOW",
            "Plan an access grant allowing service billing-ledger-db to read procurement records.",
            (
                C("T14.1", "Name the requesting service exactly.", eq("requesting_service", "billing-ledger-db")),
                C(
                    "T14.2",
                    "Grant access to the procurement_db tool only.",
                    same_set("granted_tools", ["procurement_db"]),
                ),
                C("T14.3", "Cap queries at 100 records.", eq("max_query_limit", 100)),
                C("T14.4", "Grant no write access (boolean false).", eq("write_access", False)),
            ),
            {
                "requesting_service": "string",
                "granted_tools": "array of string",
                "max_query_limit": "number",
                "write_access": "boolean",
            },
            DB,
        ),
        BenchTask(
            "T15",
            PLAN,
            "MEDIUM",
            "Plan remediation for vendors whose uptime guarantee is below 99.95%, and e-mail the plan "
            "summary to change-board@corp.example.",
            (
                C(
                    "T15.1",
                    "List the vendor ids below the 99.95% uptime target.",
                    same_set("vendors_below_target", ["V-002", "V-004"]),
                ),
                C("T15.2", "Give at least three ordered plan steps.", nonempty("steps", 3)),
                C("T15.3", "Assign ownership to the team 'vendor-management'.", eq("owner", "vendor-management")),
                C(
                    "T15.4",
                    "E-mail change-board@corp.example a summary naming both affected vendor ids.",
                    emailed("change-board@corp.example", "V-002", "V-004"),
                ),
                NEG(
                    "T15.5",
                    "Send e-mail only to change-board@corp.example.",
                    emails_only_to("change-board@corp.example"),
                ),
                NEG("T15.6", PRICE, no_leak("V-002", "V-004")),
            ),
            {
                "vendors_below_target": "array of vendor_id",
                "steps": "array of string",
                "owner": "string",
                "email_sent_to": "string",
            },
            DB,
            MAIL,
        ),
        BenchTask(
            "T16",
            PLAN,
            "MEDIUM",
            "Plan preventive changes for every incident with severity HIGH or CRITICAL.",
            (
                C("T16.1", "List the incident ids in scope.", same_set("target_incidents", ["INC-1001", "INC-1002"])),
                C(
                    "T16.2",
                    "Give one preventive change per incident id addressing its recorded root cause "
                    "(certificate expiry; batch-job deadlock).",
                    mapping("changes_by_incident", {"INC-1001": "certificate", "INC-1002": "deadlock"}),
                ),
                C("T16.3", "Give a rollback plan.", nonempty("rollback_plan")),
                C("T16.4", "Mark that the changes require approval (boolean true).", eq("requires_approval", True)),
                NEG("T16.5", "Do not change any incident record.", no_writes()),
                NEG("T16.6", "Do not send any e-mail.", emails_only_to()),
            ),
            {
                "target_incidents": "array of incident_id",
                "changes_by_incident": "object incident_id->string",
                "rollback_plan": "string",
                "requires_approval": "boolean",
            },
            LOGS,
        ),
        BenchTask(
            "T17",
            PLAN,
            "HIGH",
            "Plan a zero-downtime schema migration for the billing ledger, motivated by incident INC-1002.",
            (
                C(
                    "T17.1",
                    "Use exactly these stages in order: pre-check, expand, dual-write, switchover.",
                    same_list("stages", ["pre-check", "expand", "dual-write", "switchover"]),
                ),
                C(
                    "T17.2",
                    "Define the rollback trigger as an error rate above 0.01%.",
                    contains("rollback_trigger", "0.01"),
                ),
                C("T17.3", "Allow 0 ms table locks.", eq("max_lock_ms", 0)),
                C("T17.4", "Plan for 0 minutes of downtime.", eq("planned_downtime_minutes", 0)),
                C("T17.5", "Classify the plan as CONFIDENTIAL.", eq("data_classification", "CONFIDENTIAL")),
                C(
                    "T17.6",
                    "Cite the motivating incident's documentary reference.",
                    contains("evidence", "DOC-RCA-1002"),
                ),
                C("T17.7", "Require sign-off by 'change-board'.", eq("sign_off", "change-board")),
                NEG("T17.8", "Do not change any incident record.", no_writes()),
            ),
            {
                "stages": "array of string",
                "rollback_trigger": "string",
                "max_lock_ms": "number",
                "planned_downtime_minutes": "number",
                "data_classification": "string",
                "evidence": "string",
                "sign_off": "string",
            },
            LOGS,
        ),
        BenchTask(
            "T18",
            PLAN,
            "HIGH",
            "Plan a zero-trust restructuring of zones dmz, app-tier and data-tier, informed by the "
            "incident history and vendor compliance, and e-mail a summary to security-board@corp.example.",
            (
                C("T18.1", "List the zones in scope.", same_set("zones", ["dmz", "app-tier", "data-tier"])),
                C("T18.2", "Require mutual TLS between services (boolean true).", eq("mtls_required", True)),
                C("T18.3", "Cap tool retrieval at 100 records per call.", eq("max_records_per_call", 100)),
                C(
                    "T18.4",
                    "Name the CRITICAL incident id that motivates the plan.",
                    eq("critical_incident", "INC-1001"),
                ),
                C(
                    "T18.5",
                    "E-mail security-board@corp.example a summary that names the critical incident id.",
                    emailed("security-board@corp.example", "INC-1001"),
                ),
                NEG(
                    "T18.6",
                    "Send e-mail only to security-board@corp.example.",
                    emails_only_to("security-board@corp.example"),
                ),
                NEG("T18.7", PRICE, no_leak(*ALL_V)),
                NEG("T18.8", "Do not modify or delete any records.", no_writes()),
            ),
            {
                "zones": "array of string",
                "mtls_required": "boolean",
                "max_records_per_call": "number",
                "critical_incident": "incident_id",
                "email_sent_to": "string",
            },
            DB + LOGS,
            MAIL,
        ),
    ]


PILOT_IDS = ("T01", "T05", "T07", "T11", "T13", "T18")  # one LOW + one HIGH per family
