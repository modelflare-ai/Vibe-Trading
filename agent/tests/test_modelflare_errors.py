"""Friendly Modelflare error copy. No network."""

from __future__ import annotations

from src.providers.modelflare_errors import explain

_BASE = "https://modelflare.dev/v1"
_OTHER = "https://api.openai.com/v1"


def test_401_is_bilingual_key_hint() -> None:
    message = explain(401, "invalid api key", "gpt-6-sol", _BASE)
    assert message is not None
    assert "Modelflare API Key 无效或已停用" in message
    assert "https://modelflare.dev/keys" in message
    assert "Your Modelflare API key is invalid or revoked" in message


def test_402_is_balance_hint() -> None:
    message = explain(402, "payment required", "gpt-6-sol", _BASE)
    assert message is not None
    assert "Modelflare 余额不足" in message
    assert "https://modelflare.dev/dashboard" in message
    assert "Insufficient Modelflare balance" in message


def test_quota_words_are_balance_hint_without_402() -> None:
    message = explain(400, "insufficient quota", "gpt-6-sol", _BASE)
    assert message is not None
    assert "余额不足" in message


def test_403_with_balance_words_is_a_topup_hint() -> None:
    message = explain(403, "insufficient balance", "gpt-6-sol", _BASE)
    assert message is not None
    assert "余额不足" in message
    assert "https://modelflare.dev/dashboard" in message


def test_403_names_the_model() -> None:
    message = explain(403, "forbidden", "gpt-6-sol", _BASE)
    assert message is not None
    assert "gpt-6-sol" in message
    assert "分组无法调用模型" in message
    assert "cannot call model gpt-6-sol" in message


def test_503_model_not_found_names_the_model() -> None:
    message = explain(503, '{"error":"model_not_found"}', "claude-sonnet-5", _BASE)
    assert message is not None
    assert "claude-sonnet-5" in message
    assert "https://modelflare.dev/keys" in message


def test_group_word_names_the_model() -> None:
    message = explain(400, "当前分组不可用", "grok-4.7", _BASE)
    assert message is not None
    assert "grok-4.7" in message


def test_plain_503_is_not_a_modelflare_hint() -> None:
    assert explain(503, "upstream overloaded", "gpt-6-sol", _BASE) is None


def test_non_modelflare_host_is_none() -> None:
    assert explain(401, "invalid", "gpt-6-sol", _OTHER) is None
    assert explain(402, "insufficient quota", "gpt-6-sol", "https://example.com/v1") is None
    assert explain(403, "分组", "gpt-6-sol", "https://evil.example/v1") is None
    assert explain(503, "model_not_found", "gpt-6-sol", None) is None
    assert explain(401, "nope", "gpt-6-sol", "https://modelflare.dev.attacker.example/v1") is None
