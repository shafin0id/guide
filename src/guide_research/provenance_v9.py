"""Protocol v9 provenance-guard variants (Step 3).

Extends :class:`ProvenanceGuard` with two independent, pre-declared mechanisms:

* ``directory_mode``: a control value is also accepted when it equals an identifier returned by an
  *enumeration* tool (channel list, user list, file list, contact lookup). Only identifier fields are
  recorded, never free text (file contents, message bodies). ``"internal"`` applies this to sinks
  that are not external; ``"all"`` applies it to every sink; ``"off"`` reproduces v8.
* ``extra_control``: additional control parameters (credential and profile writes) that the v8
  registry did not mark as control parameters.

Combined with ``match="token"`` (whole-token instead of substring matching) these give the
``hardened`` variants. The default arguments reproduce the submitted v8 guard exactly.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, Literal

from guide.policy import Decision, PolicyContext, PolicyDecision, PolicyEngine
from guide.tools import ToolRegistry
from guide.types import ToolCall
from guide_research.provenance import Match, ProvenanceGuard, supported

DirectoryMode = Literal["off", "internal", "all"]

HARDENED_EXTRA_CONTROL: dict[str, tuple[str, ...]] = {
    "update_password": ("password",),
    "update_user_info": ("first_name", "last_name", "street", "city"),
}


def _ids(result: Any, fields: tuple[str, ...]) -> list[str]:
    out: list[str] = []
    items = result if isinstance(result, list | tuple) else [result]
    for it in items:
        if isinstance(it, str):
            out.append(it)
            continue
        for f in fields:
            v = it.get(f) if isinstance(it, dict) else getattr(it, f, None)
            if isinstance(v, str) and v:
                out.append(v)
    return out


# Enumeration tools and the identifier fields they expose (declared a priori from tool semantics).
DIRECTORY_EXTRACTORS: dict[str, Callable[[Any], list[str]]] = {
    "get_channels": lambda r: _ids(r, ()),
    "get_users_in_channel": lambda r: _ids(r, ()),
    "list_files": lambda r: _ids(r, ("id_", "filename")),
    "search_files_by_filename": lambda r: _ids(r, ("id_", "filename")),
    "search_files": lambda r: _ids(r, ("id_", "filename")),
    "search_contacts_by_name": lambda r: _ids(r, ("email", "name")),
    "search_contacts_by_email": lambda r: _ids(r, ("email", "name")),
}


class DirectoryGuard(ProvenanceGuard):
    def __init__(
        self,
        inner: PolicyEngine,
        registry: ToolRegistry,
        match: Match = "substring",
        *,
        directory_mode: DirectoryMode = "off",
        extra_control: Mapping[str, tuple[str, ...]] | None = None,
    ) -> None:
        super().__init__(inner, registry, match)
        self.directory_mode: DirectoryMode = directory_mode
        self.extra_control = dict(extra_control or {})
        self._directory: dict[str, set[str]] = {}

    def observe_directory(self, run_id: str, tool: str, result: Any) -> None:
        extractor = DIRECTORY_EXTRACTORS.get(tool)
        if extractor is None or self.directory_mode == "off" or result is None:
            return
        with self._lock:
            self._directory.setdefault(run_id, set()).update(s.strip().lower() for s in extractor(result))

    def forget(self, run_id: str) -> None:
        super().forget(run_id)
        with self._lock:
            self._directory.pop(run_id, None)

    def evaluate(self, call: ToolCall, context: PolicyContext) -> PolicyDecision:
        decision = self.inner.evaluate(call, context)
        if decision.decision is Decision.DENY:
            return decision
        op = self.registry.get(call.tool).spec.operations[call.operation]
        control = tuple(dict.fromkeys((*op.control_params, *self.extra_control.get(call.tool, ()))))
        if not (op.write_effect or op.external) or not control:
            return decision
        with self._lock:
            trusted = "\n".join(self._trusted.get(context.run_id, []))
            untrusted = "\n".join(self._untrusted.get(context.run_id, []))
            directory = set(self._directory.get(context.run_id, ()))
        use_directory = self.directory_mode == "all" or (self.directory_mode == "internal" and not op.external)
        for param in control:
            raw = decision.call.args.get(param)
            values = raw if isinstance(raw, list | tuple) else [raw]
            for value in values:
                v = str(value or "").strip().lower()
                if not v:
                    continue
                if supported(v, trusted, self.match):
                    continue
                if use_directory and v in directory:
                    continue
                origin = "untrusted content" if v in untrusted else "no source"
                return PolicyDecision(
                    Decision.DENY,
                    call,
                    "provenance.control_unsupported",
                    f"'{param}' value is not supported by trusted task content (found in: {origin})",
                )
        return decision


# name -> (match, directory_mode, extra_control). `strict` is the submitted v8 behaviour.
VARIANTS: dict[str, tuple[Match, DirectoryMode, Mapping[str, tuple[str, ...]]]] = {
    "strict": ("substring", "off", {}),
    "hard": ("token", "off", HARDENED_EXTRA_CONTROL),
    "flexI": ("substring", "internal", {}),
    "flexA": ("substring", "all", {}),
    "flexI_hard": ("token", "internal", HARDENED_EXTRA_CONTROL),
    "flexA_hard": ("token", "all", HARDENED_EXTRA_CONTROL),
    # credential/profile writes as control values, substring matching kept (no token-match utility cost)
    "cred": ("substring", "off", HARDENED_EXTRA_CONTROL),
    "flexI_cred": ("substring", "internal", HARDENED_EXTRA_CONTROL),
}


def make_guard(variant: str, inner: PolicyEngine, registry: ToolRegistry) -> DirectoryGuard:
    match, mode, extra = VARIANTS[variant]
    return DirectoryGuard(inner, registry, match, directory_mode=mode, extra_control=extra)
