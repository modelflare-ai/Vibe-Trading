"""Friendly Modelflare API errors.

``explain`` returns a bilingual message only when the base URL host contains
``modelflare.dev``. Every other host returns ``None`` so callers keep the
original provider error.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

_KEYS_URL = "https://modelflare.dev/keys"
_DASHBOARD_URL = "https://modelflare.dev/dashboard"
_QUOTA_RE = re.compile(r"quota|balance|insufficient|额度|余额", re.IGNORECASE)


def _host(base_url: str | None) -> str:
    raw = (base_url or "").strip()
    if not raw:
        return ""
    if "://" not in raw:
        raw = "https://" + raw
    try:
        return (urlparse(raw).hostname or "").lower()
    except ValueError:
        return ""


def _status_code(status: int | str | None) -> int | None:
    if status is None or status == "":
        return None
    try:
        return int(status)
    except (TypeError, ValueError):
        return None


def _text(message: str | None) -> str:
    return message or ""


def explain(
    status: int | str | None,
    message: str | None,
    model: str | None,
    base_url: str | None,
) -> str | None:
    """Return a bilingual Modelflare hint, or ``None`` when this is not one.

    Args:
        status: HTTP status, if the caller has one.
        message: Provider error text or response body.
        model: Model id to name in the group error.
        base_url: Endpoint the request was sent to.

    Returns:
        A short Chinese and English message, or ``None``.
    """
    host = _host(base_url)
    # Host equals modelflare.dev or is a subdomain of it. A lookalike such as
    # modelflare.dev.example does not match.
    if host != "modelflare.dev" and not host.endswith(".modelflare.dev"):
        return None

    code = _status_code(status)
    body = _text(message)
    lowered = body.lower()
    model_name = (model or "").strip() or "(unknown)"

    if code == 401:
        return (
            "Modelflare API Key 无效或已停用。请到 "
            f"{_KEYS_URL} 复制新的 Key。\n"
            "Your Modelflare API key is invalid or revoked. "
            f"Get a key at {_KEYS_URL}"
        )

    quota = bool(_QUOTA_RE.search(body))
    # A 403 is the group error unless the body itself says the balance is gone.
    # "分组" is the gateway's own wording for a model the key cannot call.
    group_error = (
        "分组" in body
        or (code == 503 and "model_not_found" in lowered)
        or (code == 403 and not quota)
    )
    if code == 402 or (quota and not group_error):
        return (
            f"Modelflare 余额不足，请充值：{_DASHBOARD_URL}\n"
            f"Insufficient Modelflare balance. Top up at {_DASHBOARD_URL}"
        )
    if group_error or code == 403:
        return (
            f"当前 Key 的分组无法调用模型 {model_name}，请在 {_KEYS_URL} 调整分组，或换一个模型。\n"
            f"This Modelflare key's group cannot call model {model_name}. "
            f"Change the group at {_KEYS_URL} or pick another model."
        )
    return None
