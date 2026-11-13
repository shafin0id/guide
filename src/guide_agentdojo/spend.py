"""Provider configuration, pricing and hard spend caps for Protocol v9 live runs."""

from __future__ import annotations

import datetime
import json
import os
import threading
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

REPO_ROOT = Path(__file__).resolve().parents[2]
LEDGER = REPO_ROOT / "experiments" / "results" / "step3" / "ledger.jsonl"

# Hard caps (USD for Gemini estimate; CNY for DeepSeek, measured from the account balance).
GEMINI_CAP_USD = 9.00
DEEPSEEK_MIN_BALANCE_CNY = 10.09  # stop when the account balance falls to this (90.09 start, 80 CNY spendable)


class SpendCapReached(RuntimeError):
    """Raised before a request when the pre-registered spend cap is reached."""


@dataclass(frozen=True)
class Provider:
    name: str
    model: str
    base_url: str
    key_env: str
    extra_body: dict[str, Any] = field(default_factory=dict)
    # USD per 1M tokens: (input cache miss, input cache hit, output)
    price: tuple[float, float, float] = (0.0, 0.0, 0.0)


PROVIDERS: dict[str, Provider] = {
    "deepseek": Provider(
        "deepseek",
        os.environ.get("DEEPSEEK_MODEL", "deepseek-flash"),
        "https://api.deepseek.com",
        "DEEPSEEK_API_KEY",
        {"thinking": {"type": "disabled"}},
        (0.15, 0.003, 0.60),
    ),
    "gemini": Provider(
        "gemini",
        "gemini-3.1-flash-lite",
        "https://generativelanguage.googleapis.com/v1beta/openai/",
        "GEMINI_API_KEY",
        {"reasoning_effort": "minimal"},
        (0.25, 0.025, 1.50),
    ),
}


def resolve_key(key_env: str, env_file: str | None = ".env") -> str:
    key = os.environ.get(key_env)
    if not key and env_file and os.path.exists(env_file):
        key = dotenv_values(env_file).get(key_env)
    if not key:
        raise ValueError(f"{key_env} must be set in environment or .env")
    return key


def is_deepseek_peak(now: datetime.datetime | None = None) -> bool:
    """Peak: 01:00-04:00 and 06:00-10:00 UTC, Monday-Friday (holiday exemptions ignored: conservative)."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    return now.weekday() < 5 and (1 <= now.hour < 4 or 6 <= now.hour < 10)


def call_cost_usd(p: Provider, miss: int, hit: int, out: int, now: datetime.datetime | None = None) -> float:
    mult = 2.0 if p.name == "deepseek" and is_deepseek_peak(now) else 1.0
    return mult * (miss * p.price[0] + hit * p.price[1] + out * p.price[2]) / 1_000_000


_lock = threading.Lock()


def record(provider: str, label: str, miss: int, hit: int, out: int, usd: float) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "t": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "provider": provider,
        "label": label,
        "miss": miss,
        "hit": hit,
        "out": out,
        "usd": round(usd, 6),
    }
    with _lock, LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def cumulative_usd(provider: str) -> float:
    if not LEDGER.exists():
        return 0.0
    total = 0.0
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            if r["provider"] == provider:
                total += r["usd"]
    return total


def deepseek_balance_cny(key: str) -> float:
    req = urllib.request.Request("https://api.deepseek.com/user/balance", headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=20) as r:  # noqa: S310 - fixed https URL
        d = json.load(r)
    for b in d["balance_infos"]:
        if b["currency"] == "CNY":
            return float(b["total_balance"])
    raise RuntimeError("no CNY balance")


def check_cap(provider: str, key: str | None = None) -> None:
    """Raise SpendCapReached if the provider's cap is hit. DeepSeek is checked against the real balance."""
    if provider == "gemini":
        if cumulative_usd("gemini") >= GEMINI_CAP_USD:
            raise SpendCapReached(f"Gemini estimated spend reached ${GEMINI_CAP_USD}")
    elif provider == "deepseek":
        bal = deepseek_balance_cny(key or resolve_key("DEEPSEEK_API_KEY"))
        if bal <= DEEPSEEK_MIN_BALANCE_CNY:
            raise SpendCapReached(f"DeepSeek balance {bal} CNY at/below floor {DEEPSEEK_MIN_BALANCE_CNY}")
