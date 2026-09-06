"""
Content-Addressable Storage (CAS) Module.

Enforces pointer-based context passing (input_refs[]) to minimize prompt token expansion
and leverage cryptographic content integrity across multi-agent delegation hops.
"""

import hashlib
import json
import os
from pathlib import Path
import threading
import time
from typing import Any, Dict, List, Optional, Set, Union


class ContentAddressableStore:
    """
    Immutable content-addressable memory store indexed by SHA-256 digests.
    Supports thread-safe in-memory caching and atomic persistent disk storage.
    """

    def __init__(self, storage_dir: Optional[Union[str, Path]] = None):
        self.storage_dir: Optional[Path] = Path(storage_dir) if storage_dir else None
        self._memory_cache: Dict[str, bytes] = {}
        self._metadata_cache: Dict[str, Dict[str, Union[str, int, float]]] = {}
        self._lock = threading.Lock()

        if self.storage_dir:
            self.storage_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def compute_sha256(content_bytes: bytes) -> str:
        """Computes the SHA-256 hexadecimal hash string for binary data."""
        return hashlib.sha256(content_bytes).hexdigest()

    def store(
        self,
        content: Union[str, bytes],
        metadata: Optional[Dict[str, Union[str, int, float]]] = None
    ) -> str:
        """
        Stores content into CAS, returning a content reference URI (sha256:<digest>).
        Performs atomic disk writes via temporary file swap to eliminate race conditions.

        Args:
            content: Text string or raw bytes to store.
            metadata: Optional key-value metadata to associate with the content.

        Returns:
            Standardized content reference string: 'sha256:<hex_digest>'
        """
        if isinstance(content, str):
            content_bytes = content.encode("utf-8")
        elif isinstance(content, bytes):
            content_bytes = content
        else:
            raise TypeError(f"Content must be str or bytes, got {type(content).__name__}")

        digest = self.compute_sha256(content_bytes)
        ref = f"sha256:{digest}"

        with self._lock:
            self._memory_cache[digest] = content_bytes
            if metadata:
                self._metadata_cache[digest] = metadata

        if self.storage_dir:
            file_path = self.storage_dir / digest
            if not file_path.exists():
                # Atomic file write: write to unique temp file then atomic replace
                temp_file = self.storage_dir / f".tmp_{digest}_{os.getpid()}_{threading.get_ident()}_{time.time_ns()}"
                try:
                    temp_file.write_bytes(content_bytes)
                    temp_file.replace(file_path)
                except Exception:
                    if temp_file.exists():
                        try:
                            temp_file.unlink()
                        except OSError:
                            pass
                    if not file_path.exists():
                        raise

        return ref

    def retrieve_bytes(self, ref: str) -> bytes:
        """
        Retrieves raw binary payload for a given content reference.

        Args:
            ref: Content reference URI in format 'sha256:<digest>' or raw digest.

        Returns:
            Raw bytes of the stored content.

        Raises:
            KeyError: If the content is not found in memory or disk.
        """
        digest = ref.replace("sha256:", "").strip()

        with self._lock:
            if digest in self._memory_cache:
                return self._memory_cache[digest]

        if self.storage_dir:
            file_path = self.storage_dir / digest
            if file_path.exists():
                content_bytes = file_path.read_bytes()
                with self._lock:
                    self._memory_cache[digest] = content_bytes
                return content_bytes

        raise KeyError(f"Content reference not found in store: {ref}")

    def retrieve(self, ref: str) -> str:
        """
        Retrieves UTF-8 decoded text content for a given content reference.

        Args:
            ref: Content reference URI.

        Returns:
            Decoded string content.
        """
        return self.retrieve_bytes(ref).decode("utf-8")

    def has(self, ref: str) -> bool:
        """Checks whether a content reference exists in the store."""
        digest = ref.replace("sha256:", "").strip()
        with self._lock:
            if digest in self._memory_cache:
                return True
        if self.storage_dir and (self.storage_dir / digest).exists():
            return True
        return False

    def resolve_refs(self, refs: List[str]) -> Dict[str, str]:
        """
        Resolves a list of content references into a dictionary mapping refs to text content.

        Args:
            refs: List of reference URIs.

        Returns:
            Dictionary of {ref: string_content}.
        """
        resolved: Dict[str, str] = {}
        for ref in refs:
            resolved[ref] = self.retrieve(ref)
        return resolved

    def clear(self) -> None:
        """Clears in-memory cache and optionally disk files."""
        with self._lock:
            self._memory_cache.clear()
            self._metadata_cache.clear()
        if self.storage_dir and self.storage_dir.exists():
            for child in self.storage_dir.iterdir():
                if child.is_file():
                    try:
                        child.unlink()
                    except OSError:
                        pass


class CompactEntityIndexer:
    """
    Indexes verbose structured data payloads into Content Addressable Storage (CAS)
    and constructs compact entity indices for token-efficient prompt context.
    Eliminates internal duplication and retains critical fields required by downstream tasks.
    """

    DEFAULT_CRITICAL_FIELDS: Set[str] = {
        "vendor_id",
        "vendor_name",
        "delivery_sla_days",
        "uptime_guarantee_pct",
        "warranty_months",
        "incident_id",
        "service",
        "root_cause",
        "citation_ref",
        "verification_status",
        "step_number",
        "operation",
        "resource_class",
        "data_sensitivity",
        "plan_id",
        "status",
        "severity",
        "timestamp",
        "id",
        "name",
    }

    def __init__(self, cas_store: Optional[ContentAddressableStore] = None):
        self.cas_store = cas_store or ContentAddressableStore()

    def create_entity_index(
        self,
        raw_data: Any,
        entity_types: Optional[List[str]] = None,
        critical_fields: Optional[Set[str]] = None,
    ) -> Dict[str, Any]:
        """
        Offloads full raw payload to CAS and returns a compact index containing
        only critical attributes and the CAS pointer (_cas_ref).

        Args:
            raw_data: Arbitrary structured data (dict, list, or JSON string).
            entity_types: Optional list of entity key names to prioritize.
            critical_fields: Optional override set of critical attribute keys to preserve.

        Returns:
            Compact dictionary with minimal fields and '_cas_ref' pointer.
        """
        if critical_fields is None:
            fields_to_keep = self.DEFAULT_CRITICAL_FIELDS
        else:
            fields_to_keep = set(critical_fields)

        # 1. Store full raw payload in CAS
        if isinstance(raw_data, str):
            raw_str = raw_data
            try:
                parsed_data = json.loads(raw_data)
            except Exception:
                parsed_data = {"raw_text": raw_data}
        else:
            raw_str = json.dumps(raw_data, sort_keys=True, ensure_ascii=False)
            parsed_data = raw_data

        cas_ref = self.cas_store.store(raw_str)

        # 2. Extract compact entities and eliminate duplicate collections
        compact_index: Dict[str, Any] = {"_cas_ref": cas_ref}

        if isinstance(parsed_data, list):
            compact_index["entities"] = [
                self._filter_entity(item, fields_to_keep)
                for item in parsed_data
            ]
        elif isinstance(parsed_data, dict):
            seen_collections: List[Any] = []
            entity_keys = entity_types or [
                "records", "logs", "incidents", "vendors", "events", "entities", "items"
            ]

            # Process entity list collections without duplicating identical collections
            for k in entity_keys:
                if k in parsed_data and isinstance(parsed_data[k], list):
                    if any(parsed_data[k] == prev for prev in seen_collections):
                        continue
                    seen_collections.append(parsed_data[k])
                    compact_index[k] = [
                        self._filter_entity(item, fields_to_keep)
                        for item in parsed_data[k]
                    ]

            # Process any remaining fields
            for k, v in parsed_data.items():
                if k in entity_keys or k.startswith("_"):
                    continue
                if isinstance(v, list):
                    if any(v == prev for prev in seen_collections):
                        continue
                    seen_collections.append(v)
                    compact_index[k] = [
                        self._filter_entity(item, fields_to_keep)
                        for item in v
                    ]
                elif isinstance(v, dict):
                    compact_index[k] = self._filter_entity(v, fields_to_keep)
                elif (
                    k in fields_to_keep
                    or k.endswith("_id")
                    or k.startswith("status")
                    or isinstance(v, (int, float, bool))
                ):
                    compact_index[k] = v
        else:
            compact_index["summary"] = str(parsed_data)

        return compact_index

    @classmethod
    def _filter_entity(cls, entity: Any, fields_to_keep: Set[str]) -> Any:
        if not isinstance(entity, dict):
            return entity
        filtered: Dict[str, Any] = {}
        for k, v in entity.items():
            if k in fields_to_keep:
                filtered[k] = v
            elif isinstance(v, (int, float, bool)) and not k.startswith("_"):
                filtered[k] = v
        return filtered

    def retrieve_raw(self, cas_ref: str) -> Any:
        """Retrieves raw content from CAS and deserializes if JSON."""
        content_str = self.cas_store.retrieve(cas_ref)
        try:
            return json.loads(content_str)
        except Exception:
            return content_str


# Backward-compatible alias
ContentAddressableStorage = ContentAddressableStore

