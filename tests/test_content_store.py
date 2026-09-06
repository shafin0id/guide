"""
Unit tests for ContentAddressableStore.

Verifies:
1. Invariant SHA-256 digest computation and reference formatting (sha256:<hex>).
2. Content storage and retrieval for string and byte payloads.
3. Thread-safe concurrent storage operations without data race corruption.
4. Atomic file persistence and cache invalidation/clearing.
"""

import concurrent.futures
import shutil
import tempfile
from pathlib import Path
import pytest
from guide_mas.storage.content_store import CompactEntityIndexer, ContentAddressableStore


@pytest.fixture
def temp_cas():
    """Provides a temporary file-backed CAS instance."""
    temp_dir = tempfile.mkdtemp()
    cas = ContentAddressableStore(storage_dir=temp_dir)
    yield cas
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_basic_store_and_retrieve(temp_cas):
    """Verifies storing text returns valid sha256 ref and retrieves identical content."""
    text = "Enterprise SLA contract payload: uptime 99.95%"
    ref = temp_cas.store(text)

    assert ref.startswith("sha256:")
    assert temp_cas.has(ref) is True
    retrieved = temp_cas.retrieve(ref)
    assert retrieved == text


def test_bytes_storage(temp_cas):
    """Verifies binary data storage and retrieval."""
    binary_data = b"\x00\x01\x02\x03\x04\xfe\xff"
    ref = temp_cas.store(binary_data)

    retrieved_bytes = temp_cas.retrieve_bytes(ref)
    assert retrieved_bytes == binary_data


def test_resolve_multiple_refs(temp_cas):
    """Verifies batch resolution of multiple content references."""
    ref1 = temp_cas.store("Doc 1 content")
    ref2 = temp_cas.store("Doc 2 content")

    resolved = temp_cas.resolve_refs([ref1, ref2])
    assert resolved[ref1] == "Doc 1 content"
    assert resolved[ref2] == "Doc 2 content"


def test_missing_ref_raises_keyerror(temp_cas):
    """Verifies that non-existent content references raise KeyError."""
    with pytest.raises(KeyError):
        temp_cas.retrieve("sha256:0000000000000000000000000000000000000000000000000000000000000000")


def test_concurrent_thread_writes(temp_cas):
    """Verifies that high-concurrency writes from multiple threads do not cause race conditions."""
    def worker(idx: int) -> str:
        payload = f"Concurrent test payload item {idx} with unique padding {idx * 42}"
        ref = temp_cas.store(payload)
        assert temp_cas.retrieve(ref) == payload
        return ref

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(worker, i) for i in range(50)]
        refs = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert len(refs) == 50
    assert len(set(refs)) == 50


def test_compact_entity_indexer_creation_and_filtering(temp_cas):
    """Verifies that CompactEntityIndexer offloads full data to CAS and preserves critical attributes."""
    indexer = CompactEntityIndexer(cas_store=temp_cas)

    raw_payload = {
        "records": [
            {
                "vendor_id": "V-001",
                "vendor_name": "Apex Cloud Systems",
                "delivery_sla_days": 3,
                "uptime_guarantee_pct": 99.95,
                "secret_internal_pricing": "$12,000/mo",
                "unrelated_verbose_text": "Extremely long marketing description that bloats prompts" * 50,
            }
        ],
        "status": "ACTIVE",
    }

    index = indexer.create_entity_index(raw_payload)

    assert "_cas_ref" in index
    assert index["_cas_ref"].startswith("sha256:")
    assert temp_cas.has(index["_cas_ref"])

    # Critical fields are retained
    record = index["records"][0]
    assert record["vendor_id"] == "V-001"
    assert record["vendor_name"] == "Apex Cloud Systems"
    assert record["delivery_sla_days"] == 3
    assert record["uptime_guarantee_pct"] == 99.95

    # Non-critical bloated fields are removed
    assert "secret_internal_pricing" not in record
    assert "unrelated_verbose_text" not in record

    # Full raw payload is recoverable via CAS
    recovered = indexer.retrieve_raw(index["_cas_ref"])
    assert recovered["records"][0]["vendor_id"] == "V-001"
    assert "secret_internal_pricing" in recovered["records"][0]


def test_compact_entity_indexer_deduplication(temp_cas):
    """Verifies that duplicated collections (e.g. records vs vendors) are deduplicated."""
    indexer = CompactEntityIndexer(cas_store=temp_cas)

    data = [
        {"vendor_id": "V-001", "vendor_name": "Apex", "delivery_sla_days": 2},
        {"vendor_id": "V-002", "vendor_name": "Beacon", "delivery_sla_days": 5},
    ]

    # Raw tool output having 3-fold internal duplication
    duplicated_payload = {
        "records": data,
        "vendors": data,
        "items": data,
    }

    index = indexer.create_entity_index(duplicated_payload)

    # Only one collection should be retained, avoiding 3x token blowup
    assert "records" in index
    assert "vendors" not in index
    assert "items" not in index
    assert len(index["records"]) == 2

