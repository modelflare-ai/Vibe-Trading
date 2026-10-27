"""Prompt for a Modelflare API key and probe ``GET {base}/models``.

Run directly with ``python -m cli.mf_onboard`` from the ``agent`` directory,
or via the interactive CLI and ``vibe-trading provider doctor``.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

SIGNUP_URL = "http://modelflare.dev/sign-up?utm_source=github&utm_campaign=mf_Vibe-Trading"
DEFAULT_BASE_URL = "https://modelflare.dev/v1"


def _env_candidates() -> tuple[Path, ...]:
    agent_dir = Path(__file__).resolve().parents[1]
    return (
        Path.home() / ".vibe-trading" / ".env",
        agent_dir / ".env",
        Path.cwd() / ".env",
    )


def _load_dotenv_gaps() -> None:
    """Fill missing environment variables from the first existing dotenv files."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        load_dotenv = None  # type: ignore[assignment]
    for path in _env_candidates():
        if not path.is_file():
            continue
        if load_dotenv is not None:
            load_dotenv(path, override=False)
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if key and key not in os.environ:
                os.environ[key] = value.strip().strip('"').strip("'")


def _provider() -> str:
    return os.environ.get("LANGCHAIN_PROVIDER", "modelflare").strip().lower() or "modelflare"


def _base_url() -> str:
    return os.environ.get("MODELFLARE_BASE_URL", DEFAULT_BASE_URL).strip() or DEFAULT_BASE_URL


def _target_env_path() -> Path:
    for path in _env_candidates():
        if path.is_file():
            return path
    return _env_candidates()[0]


def _upsert_env(path: Path, updates: dict[str, str]) -> None:
    """Upsert dotenv keys. Values must be single-line; the key is not logged."""
    for value in updates.values():
        if "\n" in value or "\r" in value:
            raise ValueError("Environment values cannot contain newlines")
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    last_active: dict[str, int] = {}
    for index, raw in enumerate(lines):
        stripped = raw.lstrip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key = stripped.split("=", 1)[0].strip()
        if key.lower().startswith("export "):
            key = key[7:].strip()
        if key in updates:
            last_active[key] = index
    seen: set[str] = set()
    for key, index in last_active.items():
        stripped = lines[index].lstrip()
        prefix = "export " if stripped.lower().startswith("export ") else ""
        lines[index] = f"{prefix}{key}={updates[key]}"
        seen.add(key)
    missing = [key for key in updates if key not in seen]
    if missing:
        if lines and lines[-1].strip():
            lines.append("")
        for key in missing:
            lines.append(f"{key}={updates[key]}")
    tmp = path.parent / (path.name + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def _persist_key(key: str) -> None:
    os.environ["MODELFLARE_API_KEY"] = key
    os.environ.setdefault("LANGCHAIN_PROVIDER", "modelflare")
    os.environ.setdefault("LANGCHAIN_MODEL_NAME", "gpt-6-sol")
    os.environ.setdefault("MODELFLARE_BASE_URL", _base_url())
    updates = {
        "MODELFLARE_API_KEY": key,
        "LANGCHAIN_PROVIDER": os.environ.get("LANGCHAIN_PROVIDER", "modelflare"),
        "LANGCHAIN_MODEL_NAME": os.environ.get("LANGCHAIN_MODEL_NAME", "gpt-6-sol"),
        "MODELFLARE_BASE_URL": _base_url(),
    }
    _upsert_env(_target_env_path(), updates)


def _model_count(body: str) -> int | None:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    records = payload.get("data")
    if not isinstance(records, list):
        records = payload.get("models")
    if not isinstance(records, list):
        return None
    return len(records)


def _probe(base_url: str, api_key: str) -> tuple[int, str]:
    url = base_url.rstrip("/") + "/models"
    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            raw = response.read().decode("utf-8", "replace")
            status = getattr(response, "status", None) or response.getcode()
            return int(status), raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        return int(exc.code), raw
    except urllib.error.URLError as exc:
        return 0, str(exc.reason if getattr(exc, "reason", None) else exc)


def maybe_prompt_modelflare_key() -> int | None:
    """Prompt and probe when Modelflare is selected and the key is missing.

    Returns:
        ``None`` when this hook does not apply.
        ``0`` when ``GET /models`` succeeds.
        A non-zero code when the probe fails. A non-TTY skips the prompt.
    """
    _load_dotenv_gaps()
    if _provider() != "modelflare":
        return None
    key = os.environ.get("MODELFLARE_API_KEY", "").strip()
    if key:
        return None

    print(f"Modelflare API key missing. Sign up: {SIGNUP_URL}")
    print(f"缺少 Modelflare API Key。注册：{SIGNUP_URL}")
    if sys.stdin.isatty() and sys.stdout.isatty():
        try:
            pasted = input("Paste MODELFLARE_API_KEY (input hidden is off; paste and press Enter): ").strip()
        except EOFError:
            pasted = ""
        if pasted:
            _persist_key(pasted)
            key = pasted

    base_url = _base_url()
    status, body = _probe(base_url, key)
    if status == 200:
        count = _model_count(body)
        if count is not None:
            print(f"Modelflare connected: {count} models. 已连通")
            return 0
    from src.providers.modelflare_errors import explain

    model = os.environ.get("LANGCHAIN_MODEL_NAME", "gpt-6-sol").strip() or "gpt-6-sol"
    friendly = explain(status or None, body, model, base_url)
    if friendly:
        print(friendly)
    else:
        redacted = body.replace(key, "[redacted]") if key else body
        print(f"Modelflare model list failed (HTTP {status}): {redacted[:500]}")
    return 1


def main() -> int:
    """CLI entry for ``python -m cli.mf_onboard``."""
    code = maybe_prompt_modelflare_key()
    if code is None:
        print("Modelflare onboarding skipped (provider is not modelflare, or MODELFLARE_API_KEY is already set).")
        return 0
    return code


if __name__ == "__main__":
    sys.exit(main())
