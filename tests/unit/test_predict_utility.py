"""Unit tests for the v7a predictor (src/guide_agentdojo/predict.py).

Tests the predictor's logic in isolation; does NOT test agreement with v6 data
(per plan §1.4 step 2 — that comparison happens only after `protocol-v7a` is tagged).
"""

from __future__ import annotations

from agentdojo.benchmark import get_suite

from guide_agentdojo.predict import _build_model, _caps_by_key, _verdict
from guide_research.provenance import corpus_of


def test_recipient_in_prompt_is_admitted() -> None:
    """banking/user_task_3: send_money to an IBAN that appears in the task PROMPT itself
    must be admitted (recipient is supported by the trusted corpus)."""
    suite = get_suite("v1.2.2", "banking")
    user_task = suite.user_tasks["user_task_3"]
    env = suite.load_and_inject_default_environment({})
    gt = user_task.ground_truth(env)
    model = _build_model("banking", suite, user_task.PROMPT)
    caps = _caps_by_key(model)

    send_money_calls = [fc for fc in gt if fc.function == "send_money"]
    assert send_money_calls, "fixture task must contain a send_money ground-truth call"
    for fc in send_money_calls:
        v = _verdict(fc, caps)
        assert not v.blocked, f"expected admitted, got blocked: {v.reason}"


def test_recipient_only_in_environment_data_is_blocked() -> None:
    """banking/user_task_0: send_money to an IBAN read from a file (environment data,
    never in the task PROMPT) must be blocked — the recipient is not provenance-supported."""
    suite = get_suite("v1.2.2", "banking")
    user_task = suite.user_tasks["user_task_0"]
    env = suite.load_and_inject_default_environment({})
    gt = user_task.ground_truth(env)
    model = _build_model("banking", suite, user_task.PROMPT)
    caps = _caps_by_key(model)

    send_money_calls = [fc for fc in gt if fc.function == "send_money"]
    assert send_money_calls, "fixture task must contain a send_money ground-truth call"
    for fc in send_money_calls:
        v = _verdict(fc, caps)
        assert v.blocked, f"expected blocked, got admitted"
        assert v.reason.startswith("recipient=")


def test_trusted_corpus_matches_pipeline_construction() -> None:
    """The predictor's trusted corpus must be built exactly as the live pipeline builds it:
    corpus_of({"objective": PROMPT}) — nothing more, nothing less."""
    suite = get_suite("v1.2.2", "banking")
    user_task = suite.user_tasks["user_task_3"]
    model = _build_model("banking", suite, user_task.PROMPT)
    expected = corpus_of({"objective": user_task.PROMPT})
    assert model.trusted_corpus == expected
