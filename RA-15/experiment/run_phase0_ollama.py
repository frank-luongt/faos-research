#!/usr/bin/env python3
"""Run RA-15 Phase 0 prompts against a local Ollama chat model."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from render_phase0_prompts import build_records


DEFAULT_MODEL = "qwen3.6:27b-coding-nvfp4"
OLLAMA_CHAT_URL = "http://127.0.0.1:11434/api/chat"


def call_ollama(
    *,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    timeout: int,
    json_format: bool,
    num_predict: int | None = None,
) -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {
            "temperature": temperature,
        },
    }
    if num_predict is not None:
        payload["options"]["num_predict"] = num_predict
    if json_format:
        payload["format"] = "json"
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        OLLAMA_CHAT_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
    message = body.get("message", {})
    content = message.get("content")
    if not isinstance(content, str):
        raise RuntimeError(f"Ollama response missing message.content: {body}")
    return content


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--limit", type=int, help="Optional record limit for debugging")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--sleep", type=float, default=0.0)
    parser.add_argument(
        "--no-json-format",
        action="store_true",
        help="Do not request Ollama format=json; rely on prompt-only JSON instruction.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    records = build_records(root)
    if args.limit is not None:
        records = records[: args.limit]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with args.output.open("w", encoding="utf-8") as handle:
        for record in records:
            started = time.time()
            output_record: dict[str, Any] = {
                "task_id": record["task_id"],
                "block": record["block"],
                "context_id": record["context_id"],
                "rep": record["rep"],
                "model": args.model,
            }
            try:
                content = call_ollama(
                    model=args.model,
                    system_prompt=record["system_prompt"],
                    user_prompt=record["user_prompt"],
                    temperature=args.temperature,
                    timeout=args.timeout,
                    json_format=not args.no_json_format,
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
            print(
                json.dumps(
                    {
                        "written": written,
                        "total": len(records),
                        "task_id": output_record["task_id"],
                        "context_id": output_record["context_id"],
                        "rep": output_record["rep"],
                        "error": output_record.get("error"),
                    }
                )
            )
            if args.sleep:
                time.sleep(args.sleep)

    print(json.dumps({"output": str(args.output), "records": written}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
