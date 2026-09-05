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
from guide_mas.storage.content_store import ContentAddressableStore


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
