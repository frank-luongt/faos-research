#!/usr/bin/env python3
"""Run RA-15 Phase 1.3 construct-decoupling prompts through OpenRouter."""

from __future__ import annotations

import argparse
import json
import os
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from render_phase1_prompts import DEFAULT_REPS
from render_phase13_prompts import build_records


OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_OPENROUTER_MODEL = "qwen/qwen-2.5-72b-instruct"
DEFAULT_TIMEOUT_SECONDS = 240
DEFAULT_MAX_TOKENS = 800


def load_dotenv(root: Path) -> dict[str, str]:
    env_file = root / ".env"
    if not env_file.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def env_value(root: Path, key: str, default: str = "") -> str:
    value = os.environ.get(key, "")
    if value:
        return value
    return load_dotenv(root).get(key, default)


def first_env_value(root: Path, keys: tuple[str, ...], default: str = "") -> str:
    for key in keys:
        value = env_value(root, key)
        if value:
            return value
    return default


def ssl_context() -> ssl.SSLContext:
    try:
        import certifi  # type: ignore[import-not-found]
    except ImportError:
        return ssl.create_default_context()
    return ssl.create_default_context(cafile=certifi.where())


def call_openrouter(
    *,
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    timeout: int,
    max_tokens: int,
    json_object: bool,
) -> str:
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_object:
        payload["response_format"] = {"type": "json_object"}

    request = urllib.request.Request(
        OPENROUTER_CHAT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "X-Title": "FAOS RA-15 Contextuality Auditor",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
            context=ssl_context(),
        ) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenRouter HTTP {exc.code}: {detail[:500]}") from exc

    content = body.get("choices", [{}])[0].get("message", {}).get("content")
    if not isinstance(content, str) or not content:
        raise RuntimeError(f"OpenRouter response missing choices[0].message.content: {body}")
    return content


def record_key(record: dict[str, Any]) -> tuple[str, str, str, str, int]:
    return (
        str(record["condition"]),
        str(record["task_id"]),
        str(record["block"]),
        str(record["context_id"]),
        int(record["rep"]),
    )


def load_completed(path: Path) -> set[tuple[str, str, str, str, int]]:
    if not path.exists():
        return set()
    completed: set[tuple[str, str, str, str, int]] = set()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("response") and not record.get("error"):
                completed.add(record_key(record))
    return completed


def main() -> int:
    root = Path(__file__).resolve().parents[3]
    default_model = first_env_value(
        root,
        ("RA15_OPENROUTER_MODEL", "RA6_OPENROUTER_MODEL", "RA3_OPENROUTER_MODEL"),
        DEFAULT_OPENROUTER_MODEL,
    )
    default_timeout = int(
        first_env_value(
            root,
            ("RA15_OPENROUTER_TIMEOUT_SECONDS", "RA6_OPENROUTER_TIMEOUT_SECONDS", "RA3_OPENROUTER_TIMEOUT_SECONDS"),
            str(DEFAULT_TIMEOUT_SECONDS),
        )
    )
    default_max_tokens = int(env_value(root, "RA15_OPENROUTER_MAX_TOKENS", str(DEFAULT_MAX_TOKENS)))

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=default_model)
    parser.add_argument("--api-key", default=env_value(root, "OPENROUTER_API_KEY"))
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--reps", type=int, default=DEFAULT_REPS)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--timeout", type=int, default=default_timeout)
    parser.add_argument("--max-tokens", type=int, default=default_max_tokens)
    parser.add_argument("--sleep", type=float, default=0.0)
    parser.add_argument(
        "--json-object",
        action="store_true",
        help="Request OpenAI-compatible JSON object mode; default relies on prompt-only JSON instruction.",
    )
    parser.add_argument("--restart", action="store_true")
    args = parser.parse_args()

    if not args.api_key:
        raise SystemExit(
            "OPENROUTER_API_KEY is required. Set it in the environment, repo .env, or pass --api-key."
        )

    experiment_root = Path(__file__).resolve().parent
    records = build_records(experiment_root, reps=args.reps)
    if args.limit is not None:
        records = records[: args.limit]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    completed = set() if args.restart else load_completed(args.output)
    pending = [record for record in records if record_key(record) not in completed]

    mode = "w" if args.restart else "a"
    written = 0
    with args.output.open(mode, encoding="utf-8") as handle:
        for record in pending:
            started = time.time()
            output_record: dict[str, Any] = {
                "phase": "phase1.3",
                "provider": "openrouter",
                "condition": record["condition"],
                "source_block": record["source_block"],
                "task_id": record["task_id"],
                "industry": record["industry"],
                "problem_class": record["problem_class"],
                "predicted_strategy": record["predicted_strategy"],
                "conflict_band": record["conflict_band"],
                "block": record["block"],
                "context_id": record["context_id"],
                "rep": record["rep"],
                "model": args.model,
            }
            try:
                content = call_openrouter(
                    api_key=args.api_key,
                    model=args.model,
                    system_prompt=record["system_prompt"],
                    user_prompt=record["user_prompt"],
                    temperature=args.temperature,
                    timeout=args.timeout,
                    max_tokens=args.max_tokens,
                    json_object=args.json_object,
                )
                output_record["response"] = content
                output_record["latency_sec"] = round(time.time() - started, 3)
            except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
                output_record["response"] = ""
                output_record["error"] = str(exc)
                output_record["latency_sec"] = round(time.time() - started, 3)
            handle.write(json.dumps(output_record, ensure_ascii=False) + "\n")
            handle.flush()
            written += 1
            done = len(completed) + written
            print(
                json.dumps(
                    {
                        "written_this_run": written,
                        "done": done,
                        "total": len(records),
                        "provider": output_record["provider"],
                        "model": output_record["model"],
                        "task_id": output_record["task_id"],
                        "block": output_record["block"],
                        "context_id": output_record["context_id"],
                        "rep": output_record["rep"],
                        "error": output_record.get("error"),
                    }
                )
            )
            if args.sleep:
                time.sleep(args.sleep)

    print(
        json.dumps(
            {
                "output": str(args.output),
                "provider": "openrouter",
                "model": args.model,
                "records_total": len(records),
                "records_previously_completed": len(completed),
                "records_written_this_run": written,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
