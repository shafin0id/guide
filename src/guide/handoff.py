"""Signed, hash-linked hand-off packages (proposal §8.1, Appendix B.3).

Guarantees and non-guarantees
-----------------------------
* Tamper evidence: any change to a sealed package is detected (Ed25519 over the link hash).
* Attribution: each principal signs with its *own* key, so a package proves which agent
  issued it. (baseline-v0 shared one key per run; see docs/adr/0003.)
* Lineage: ``link_hash = SHA-256(parent_hash || canonical(package))`` chains packages.
* NOT factual correctness: a signed package can carry a wrong or injected finding.
* Keys are in-process; production deployments must supply a KMS-backed :class:`KeyRing`.

Canonical form: UTF-8 JSON, sorted keys, no insignificant whitespace, no floats (times are
integer milliseconds). For this restricted value domain it coincides with RFC 8785 output
for ASCII keys, but RFC 8785 is not claimed in general.
"""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any

from guide.errors import IntegrityError

if TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

GENESIS = "0" * 64


def canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class ContentStore:
    """Content-addressed store; references are verified on read.

    The reference is the SHA-256 of the canonical form. With ``preserve_order`` (default) the
    blob is kept in its original key order and re-canonicalised on read for verification, so
    agents see data exactly as produced. Presenting canonical (sorted-key) JSON to agents
    raised malformed-output rates in protocol-v1 (docs/experiments.md, finding D1).
    """

    def __init__(self, preserve_order: bool = True) -> None:
        self.preserve_order = preserve_order
        self._blobs: dict[str, bytes] = {}

    def put(self, obj: Any) -> str:
        canonical = canonical_json(obj)
        ref = "sha256:" + sha256_hex(canonical)
        self._blobs[ref] = json.dumps(obj, ensure_ascii=False).encode("utf-8") if self.preserve_order else canonical
        return ref

    def get(self, ref: str) -> Any:
        data = self._blobs.get(ref)
        if data is None:
            raise IntegrityError(f"unknown content reference {ref}")
        try:
            obj = json.loads(data)
        except json.JSONDecodeError:
            raise IntegrityError(f"content for {ref} is not valid JSON") from None
        if "sha256:" + sha256_hex(canonical_json(obj)) != ref:
            raise IntegrityError(f"content hash mismatch for {ref}")
        return obj


@dataclass(frozen=True)
class IntentPackage:
    run_id: str
    handoff_id: str
    parent_hash: str
    sender: str
    receiver: str
    objective: str
    constraints: tuple[str, ...]
    input_refs: tuple[str, ...]
    permitted_tools: tuple[str, ...]
    expected_schema: Mapping[str, Any]
    issued_at_ms: int
    expiry_ms: int

    _TYPES = {
        "run_id": str,
        "handoff_id": str,
        "parent_hash": str,
        "sender": str,
        "receiver": str,
        "objective": str,
        "constraints": list,
        "input_refs": list,
        "permitted_tools": list,
        "expected_schema": dict,
        "issued_at_ms": int,
        "expiry_ms": int,
    }

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        for k in ("constraints", "input_refs", "permitted_tools"):
            d[k] = list(d[k])
        d["expected_schema"] = dict(self.expected_schema)
        return d

    def canonical(self) -> bytes:
        return canonical_json(self.to_dict())

    def link_hash(self) -> str:
        return sha256_hex(self.parent_hash.encode("ascii") + self.canonical())

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> IntentPackage:
        if not isinstance(data, Mapping):
            raise IntegrityError("schema: package is not an object")
        missing = [k for k in cls._TYPES if k not in data]
        if missing:
            raise IntegrityError(f"schema: missing fields {missing}")
        extra = [k for k in data if k not in cls._TYPES]
        if extra:
            raise IntegrityError(f"schema: unexpected fields {extra}")
        for key, typ in cls._TYPES.items():
            value = data[key]
            if not isinstance(value, typ) or (typ is int and isinstance(value, bool)):
                raise IntegrityError(f"schema: field '{key}' has wrong type")
        for key in ("constraints", "input_refs", "permitted_tools"):
            if not all(isinstance(v, str) for v in data[key]):
                raise IntegrityError(f"schema: field '{key}' must contain strings")
        return cls(**{**data, **{k: tuple(data[k]) for k in ("constraints", "input_refs", "permitted_tools")}})


class KeyRing:
    """Per-principal Ed25519 keys. In-process reference implementation."""

    def __init__(self) -> None:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        self._gen = Ed25519PrivateKey.generate
        self._private: dict[str, Ed25519PrivateKey] = {}
        self._public: dict[str, Ed25519PublicKey] = {}

    def enroll(self, principal: str) -> None:
        if principal not in self._private:
            key = self._gen()
            self._private[principal] = key
            self._public[principal] = key.public_key()

    def sign(self, principal: str, data: bytes) -> str:
        try:
            return self._private[principal].sign(data).hex()
        except KeyError:
            raise IntegrityError(f"no signing key for principal {principal}") from None

    def verify(self, principal: str, data: bytes, signature_hex: str) -> None:
        from cryptography.exceptions import InvalidSignature

        public = self._public.get(principal)
        if public is None:
            raise IntegrityError(f"unknown sender {principal}")
        try:
            public.verify(bytes.fromhex(signature_hex), data)
        except (InvalidSignature, ValueError):
            raise IntegrityError("signature: verification failed") from None


def seal(package: IntentPackage, keyring: KeyRing) -> dict[str, Any]:
    """Return the wire form of a sealed package: {package, link_hash, signature}."""
    link = package.link_hash()
    return {
        "package": package.to_dict(),
        "link_hash": link,
        "signature": keyring.sign(package.sender, link.encode("ascii")),
    }


def open_sealed(
    wire: Mapping[str, Any],
    keyring: KeyRing,
    *,
    expected_parent: str,
    expected_receiver: str,
    now_ms: int | None = None,
) -> IntentPackage:
    """Verify a sealed package; raise :class:`IntegrityError` with a reason on any failure."""
    if not isinstance(wire, Mapping) or not {"package", "link_hash", "signature"} <= set(wire):
        raise IntegrityError("schema: envelope missing package/link_hash/signature")
    package = IntentPackage.from_dict(wire["package"])
    if package.parent_hash != expected_parent:
        raise IntegrityError("lineage: parent hash does not match the last accepted hand-off")
    if package.receiver != expected_receiver:
        raise IntegrityError("routing: package addressed to a different receiver")
    link = package.link_hash()
    if not isinstance(wire["link_hash"], str) or link != wire["link_hash"]:
        raise IntegrityError("content: link hash does not match package content")
    if not isinstance(wire["signature"], str):
        raise IntegrityError("signature: malformed")
    keyring.verify(package.sender, link.encode("ascii"), wire["signature"])
    now = int(time.time() * 1000) if now_ms is None else now_ms
    if now > package.expiry_ms:
        raise IntegrityError("expiry: package expired")
    return package
