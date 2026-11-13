"""Minimal OpenRouter chat client (stdlib only), logging what actually served each call."""

import json
import os
import ssl
import time
from urllib import error, request

API_URL = "https://openrouter.ai/api/v1/chat/completions"

try:
    import certifi

    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:  # pragma: no cover
    _SSL_CTX = ssl.create_default_context()


class OpenRouterError(RuntimeError):
    pass


def api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        raise OpenRouterError("OPENROUTER_API_KEY is not set")
    return key


def chat(
    model: str,
    messages: list[dict],
    *,
    max_tokens: int,
    temperature: float = 0.0,
    seed: int | None = None,
    provider_order: list[str] | None = None,
    reasoning: dict | None = None,
    response_format: dict | None = None,
    timeout: float = 300.0,
    retries: int = 4,
) -> dict:
    """One chat completion. Returns text plus served model, routed provider and usage."""
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "usage": {"include": True},
    }
    if seed is not None:
        payload["seed"] = seed
    if provider_order:
        payload["provider"] = {"order": provider_order, "allow_fallbacks": True}
    if reasoning:
        payload["reasoning"] = reasoning
    if response_format:
        payload["response_format"] = response_format

    headers = {
        "Authorization": f"Bearer {api_key()}",
        "Content-Type": "application/json",
        "X-Title": "FAOS RA-3 v6",
    }
    body = json.dumps(payload).encode()
    delay = 2.0
    for attempt in range(retries + 1):
        started = time.monotonic()
        try:
            req = request.Request(API_URL, data=body, headers=headers, method="POST")
            with request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
                data = json.loads(resp.read().decode())
            break
        except error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:400]
            if exc.code in (429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(delay)
                delay *= 2
                continue
            raise OpenRouterError(f"HTTP {exc.code} for {model}: {detail}") from exc
        except error.URLError as exc:
            if attempt < retries:
                time.sleep(delay)
                delay *= 2
                continue
            raise OpenRouterError(f"Could not reach OpenRouter: {exc}") from exc

    if "error" in data:
        raise OpenRouterError(f"{model}: {json.dumps(data['error'])[:400]}")
    choice = (data.get("choices") or [{}])[0]
    text = (choice.get("message") or {}).get("content") or ""
    return {
        "text": text,
        "finish_reason": choice.get("finish_reason"),
        "served_model": data.get("model"),
        "provider": data.get("provider"),
        "generation_id": data.get("id"),
        "usage": data.get("usage", {}),
        "latency_s": round(time.monotonic() - started, 2),
    }
