"""Security metadata and ToolSpec mappings for AgentDojo suites.

Maps every function from the 4 AgentDojo suites (banking, slack, travel, workspace)
into GUIDE's ToolSpec and OperationSpec definitions.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from agentdojo.functions_runtime import Function

from guide.tools import OperationSpec, ToolRegistry, ToolSpec
from guide.types import Sensitivity, ToolResult

# Security-critical tool classification for AgentDojo functions:
# Maps func_name -> (is_write_effect, is_external, control_params, resource_class)
DOJO_TOOL_SECURITY: dict[str, tuple[bool, bool, tuple[str, ...], str]] = {
    # === Banking Suite ===
    "get_iban": (False, False, (), "bank"),
    "get_balance": (False, False, (), "bank"),
    "get_most_recent_transactions": (False, False, (), "bank"),
    "get_scheduled_transactions": (False, False, (), "bank"),
    "read_file": (False, False, ("file_path",), "filesystem"),
    "get_user_info": (False, False, (), "bank"),
    "send_money": (True, True, ("recipient",), "bank"),
    "schedule_transaction": (True, True, ("recipient",), "bank"),
    "update_scheduled_transaction": (True, True, ("recipient",), "bank"),
    "update_password": (True, False, (), "bank"),
    "update_user_info": (True, False, (), "bank"),

    # === Slack Suite ===
    "get_channels": (False, False, (), "slack"),
    "read_channel_messages": (False, False, (), "slack"),
    "read_inbox": (False, False, (), "slack"),
    "get_users_in_channel": (False, False, (), "slack"),
    "get_webpage": (False, False, (), "web"),
    "send_direct_message": (True, True, ("recipient",), "slack"),
    "send_channel_message": (True, False, ("channel",), "slack"),
    "add_user_to_channel": (True, False, ("user", "channel"), "slack"),
    "invite_user_to_slack": (True, True, ("user_email",), "slack"),
    "remove_user_from_slack": (True, False, ("user",), "slack"),
    "post_webpage": (True, True, ("url",), "web"),

    # === Travel Suite ===
    "get_user_information": (False, False, (), "user"),
    "get_all_hotels_in_city": (False, False, (), "travel"),
    "get_hotels_prices": (False, False, (), "travel"),
    "get_rating_reviews_for_hotels": (False, False, (), "travel"),
    "get_hotels_address": (False, False, (), "travel"),
    "get_all_restaurants_in_city": (False, False, (), "travel"),
    "get_cuisine_type_for_restaurants": (False, False, (), "travel"),
    "get_restaurants_address": (False, False, (), "travel"),
    "get_rating_reviews_for_restaurants": (False, False, (), "travel"),
    "get_dietary_restrictions_for_all_restaurants": (False, False, (), "travel"),
    "get_contact_information_for_restaurants": (False, False, (), "travel"),
    "get_price_for_restaurants": (False, False, (), "travel"),
    "check_restaurant_opening_hours": (False, False, (), "travel"),
    "get_all_car_rental_companies_in_city": (False, False, (), "travel"),
    "get_car_types_available": (False, False, (), "travel"),
    "get_rating_reviews_for_car_rental": (False, False, (), "travel"),
    "get_car_fuel_options": (False, False, (), "travel"),
    "get_car_rental_address": (False, False, (), "travel"),
    "get_car_price_per_day": (False, False, (), "travel"),
    "create_calendar_event": (True, False, ("participants",), "calendar"),
    "search_calendar_events": (False, False, (), "calendar"),
    "get_day_calendar_events": (False, False, (), "calendar"),
    "cancel_calendar_event": (True, False, ("event_id",), "calendar"),
    "reserve_hotel": (True, True, ("hotel",), "travel"),
    "reserve_car_rental": (True, True, ("company",), "travel"),
    "reserve_restaurant": (True, True, ("restaurant",), "travel"),
    "get_flight_information": (False, False, (), "travel"),
    "send_email": (True, True, ("recipients", "cc", "bcc"), "email"),

    # === Workspace Suite ===
    "delete_email": (True, False, ("email_id",), "email"),
    "get_unread_emails": (False, False, (), "email"),
    "get_sent_emails": (False, False, (), "email"),
    "get_received_emails": (False, False, (), "email"),
    "get_draft_emails": (False, False, (), "email"),
    "search_emails": (False, False, (), "email"),
    "search_contacts_by_name": (False, False, (), "contacts"),
    "search_contacts_by_email": (False, False, (), "contacts"),
    "get_current_day": (False, False, (), "calendar"),
    "reschedule_calendar_event": (True, False, ("event_id",), "calendar"),
    "add_calendar_event_participants": (True, False, ("event_id", "participants"), "calendar"),
    "append_to_file": (True, False, ("file_id",), "filesystem"),
    "search_files_by_filename": (False, False, (), "filesystem"),
    "create_file": (True, False, ("filename",), "filesystem"),
    "delete_file": (True, False, ("file_id",), "filesystem"),
    "get_file_by_id": (False, False, (), "filesystem"),
    "list_files": (False, False, (), "filesystem"),
    "share_file": (True, True, ("email", "file_id"), "filesystem"),
    "search_files": (False, False, (), "filesystem"),
}


class DojoToolWrapper:
    """Wraps an AgentDojo Function into GUIDE's Tool protocol."""

    def __init__(self, fn: Function) -> None:
        self.fn = fn
        write_effect, external, control_params, res_class = DOJO_TOOL_SECURITY.get(
            fn.name, (False, False, (), "generic")
        )
        schema = fn.parameters.model_json_schema()
        param_desc = {
            k: v.get("description", "")
            for k, v in schema.get("properties", {}).items()
            if isinstance(v, dict)
        }
        op = OperationSpec(
            name=fn.name,
            description=fn.description or "",
            write_effect=write_effect,
            external=external,
            params=param_desc,
            control_params=control_params,
        )
        self.spec = ToolSpec(
            name=fn.name,
            description=fn.description or "",
            resource_class=res_class,
            operations={fn.name: op},
            default_sensitivity=Sensitivity.INTERNAL,
        )

    def invoke(self, operation: str, args: Mapping[str, Any]) -> ToolResult:
        return ToolResult(tool=self.fn.name, operation=operation, output=None)


def build_tool_registry(functions: Iterable[Function]) -> ToolRegistry:
    """Creates a ToolRegistry containing wrapped AgentDojo functions."""
    reg = ToolRegistry()
    for f in functions:
        reg.register(DojoToolWrapper(f))
    return reg
