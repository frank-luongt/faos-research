#!/usr/bin/env python3
"""RA-3 Pilot Study Experiment Runner.

Usage:
    python run_experiment.py                  # Full experiment (360 runs)
    python run_experiment.py --pilot          # Calibration pilot (4 tasks × 4 conditions × 3 reps)
    python run_experiment.py --resume         # Resume from last checkpoint
    python run_experiment.py --dry-run        # Validate prompts and output paths only
    python run_experiment.py --task fintech_T1 --condition C3_ontology  # Single run
"""

import argparse
import csv
import json
import os
import ssl
import sys
import time
from datetime import datetime, timezone
from urllib import error, request

import anthropic
import certifi

# SSL context for Google AI Studio / Dashscope API calls (macOS Python 3.14+)
_SSL_CTX = ssl.create_default_context(cafile=certifi.where())

import config
from conditions import CONDITION_CONFIGS
from judge import JUDGE_BUILDERS


def load_tasks() -> list[dict]:
    with open(config.TASKS_FILE) as f:
        return json.load(f)


def load_completed_runs(results_file: str) -> set[str]:
    """Load already-completed run keys to support resumption."""
    completed = set()
    if os.path.exists(results_file):
        with open(results_file, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = f"{row['task_id']}|{row['condition']}|{row['rep']}"
                completed.add(key)
    return completed


def call_agent_anthropic(client: anthropic.Anthropic, task: dict, condition: str) -> str:
    """Call the agent LLM through Anthropic."""
    cfg = CONDITION_CONFIGS[condition]
    system_prompt = cfg["system_prompt_fn"](task)
    messages = cfg["messages_fn"](task)

    response = client.messages.create(
        model=config.AGENT_MODEL,
        max_tokens=config.AGENT_MAX_TOKENS,
        temperature=config.AGENT_TEMPERATURE,
        system=system_prompt,
        messages=messages,
    )
    return response.content[0].text


def call_agent_ollama(task: dict, condition: str) -> str:
    """Call the agent LLM through Ollama's local chat API."""
    cfg = CONDITION_CONFIGS[condition]
    system_prompt = cfg["system_prompt_fn"](task)
    messages = cfg["messages_fn"](task)
    payload = {
        "model": config.OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            *messages,
        ],
        "options": {
            "temperature": config.AGENT_TEMPERATURE,
            "num_predict": config.AGENT_MAX_TOKENS,
        },
        "stream": False,
    }
    req = request.Request(
        f"{config.OLLAMA_BASE_URL}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=config.OLLAMA_TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama HTTP {exc.code}: {body[:300]}") from exc
    except error.URLError as exc:
        raise RuntimeError(
            "Could not reach Ollama. Start the local server or update RA3_OLLAMA_BASE_URL."
        ) from exc

    message = data.get("message", {})
    content = message.get("content", "")
    if not content:
        raise RuntimeError(f"Ollama returned no message content: {json.dumps(data)[:300]}")
    return content


def call_agent_google(task: dict, condition: str) -> str:
    """Call the agent LLM through Google AI Studio (Gemini API).

    Uses the OpenAI-compatible endpoint so we avoid a heavy SDK dependency.
    Requires GOOGLE_API_KEY.
    """
    cfg = CONDITION_CONFIGS[condition]
    system_prompt = cfg["system_prompt_fn"](task)
    messages = cfg["messages_fn"](task)
    payload = {
        "model": config.GOOGLE_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            *messages,
        ],
        "temperature": config.AGENT_TEMPERATURE,
        "max_tokens": config.AGENT_MAX_TOKENS,
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.GOOGLE_API_KEY}",
    }
    req = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=config.GOOGLE_TIMEOUT_SECONDS, context=_SSL_CTX) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Google AI Studio HTTP {exc.code}: {body[:300]}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Could not reach Google AI Studio: {exc}") from exc

    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not content:
        raise RuntimeError(f"Google AI Studio returned no content: {json.dumps(data)[:300]}")
    return content


def call_agent_dashscope(task: dict, condition: str) -> str:
    """Call the agent LLM through Alibaba Dashscope (OpenAI-compatible endpoint).

    Requires DASHSCOPE_API_KEY.
    """
    cfg = CONDITION_CONFIGS[condition]
    system_prompt = cfg["system_prompt_fn"](task)
    messages = cfg["messages_fn"](task)
    payload = {
        "model": config.DASHSCOPE_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            *messages,
        ],
        "temperature": config.AGENT_TEMPERATURE,
        "max_tokens": config.AGENT_MAX_TOKENS,
    }
    url = f"{config.DASHSCOPE_BASE_URL}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.DASHSCOPE_API_KEY}",
    }
    req = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=config.DASHSCOPE_TIMEOUT_SECONDS, context=_SSL_CTX) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Dashscope HTTP {exc.code}: {body[:300]}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Could not reach Dashscope: {exc}") from exc

    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not content:
        raise RuntimeError(f"Dashscope returned no content: {json.dumps(data)[:300]}")
    return content


def call_agent_openrouter(task: dict, condition: str) -> str:
    """Call the agent LLM through OpenRouter (OpenAI-compatible gateway).

    Requires OPENROUTER_API_KEY.
    """
    cfg = CONDITION_CONFIGS[condition]
    system_prompt = cfg["system_prompt_fn"](task)
    messages = cfg["messages_fn"](task)
    payload = {
        "model": config.OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            *messages,
        ],
        "temperature": config.AGENT_TEMPERATURE,
        "max_tokens": config.AGENT_MAX_TOKENS,
    }
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
    }
    req = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=config.OPENROUTER_TIMEOUT_SECONDS, context=_SSL_CTX) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenRouter HTTP {exc.code}: {body[:300]}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Could not reach OpenRouter: {exc}") from exc

    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not content:
        raise RuntimeError(f"OpenRouter returned no content: {json.dumps(data)[:300]}")
    return content


def call_agent(agent_client: anthropic.Anthropic | None, task: dict, condition: str) -> str:
    """Dispatch agent calls to the configured backend."""
    if config.AGENT_BACKEND == "anthropic":
        if agent_client is None:
            raise RuntimeError("Anthropic agent client is not initialized.")
        return call_agent_anthropic(agent_client, task, condition)
    if config.AGENT_BACKEND == "ollama":
        return call_agent_ollama(task, condition)
    if config.AGENT_BACKEND == "google":
        return call_agent_google(task, condition)
    if config.AGENT_BACKEND == "dashscope":
        return call_agent_dashscope(task, condition)
    if config.AGENT_BACKEND == "openrouter":
        return call_agent_openrouter(task, condition)
    raise ValueError(f"Unsupported agent backend: {config.AGENT_BACKEND}")


def call_judge(client: anthropic.Anthropic, judge_prompt: str) -> dict:
    """Call the judge LLM and parse JSON response."""
    response = client.messages.create(
        model=config.JUDGE_MODEL,
        max_tokens=config.JUDGE_MAX_TOKENS,
        temperature=config.JUDGE_TEMPERATURE,
        system="You are a precise evaluation judge. Always respond with valid JSON only.",
        messages=[{"role": "user", "content": judge_prompt}],
    )
    text = response.content[0].text.strip()
    # Handle markdown code fences
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print(f"  [WARN] Judge returned invalid JSON, raw: {text[:200]}")
        return {"score": 0.0, "error": "invalid_json", "raw": text[:500]}


def call_c4_process_judge(client: anthropic.Anthropic, task: dict, response: str) -> dict:
    """Run the C4 post-generation quality judge."""
    cfg = CONDITION_CONFIGS["C4_ontology_process"]
    if "post_judge_fn" not in cfg:
        return {}
    prompt = cfg["post_judge_fn"](task, response)
    return call_judge(client, prompt)


def evaluate_response(client: anthropic.Anthropic, task: dict, response: str) -> dict:
    """Evaluate a response using the appropriate judge(s)."""
    metric = task["metric_tested"]

    if metric == "ALL":
        # Cross-cutting: one prompt scores all four metrics
        builder = JUDGE_BUILDERS["ALL"]
        prompt = builder(task, response)
        result = call_judge(client, prompt)
        return {
            "TF": result.get("TF_score", 0.0),
            "MA": result.get("MA_score", 0.0),
            "RC": result.get("RC_score", 0.0),
            "RS": result.get("RS_score", 0.0),
            "judge_detail": json.dumps(result),
        }
    else:
        builder = JUDGE_BUILDERS[metric]
        prompt = builder(task, response)
        result = call_judge(client, prompt)
        score = result.get("score", 0.0)
        scores = {"TF": 0.0, "MA": 0.0, "RC": 0.0, "RS": 0.0}
        scores[metric] = score
        return {
            **scores,
            "judge_detail": json.dumps(result),
        }


def ensure_results_file(results_file: str):
    """Create results CSV with header if it doesn't exist."""
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    if not os.path.exists(results_file):
        with open(results_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "task_id", "industry", "category", "metric_tested",
                "condition", "rep",
                "TF", "MA", "RC", "RS",
                "c4_quality_score", "c4_pass",
                "agent_response_len", "judge_detail",
                "timestamp",
            ])


def append_result(row: dict, results_file: str):
    """Append a single result row to the CSV."""
    with open(results_file, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            row["task_id"], row["industry"], row["category"], row["metric_tested"],
            row["condition"], row["rep"],
            row["TF"], row["MA"], row["RC"], row["RS"],
            row.get("c4_quality_score", ""), row.get("c4_pass", ""),
            row["agent_response_len"], row["judge_detail"],
            row["timestamp"],
        ])


def run_experiment(
    tasks: list[dict],
    conditions: list[str],
    reps: int,
    completed: set[str],
    results_file: str,
    dry_run: bool = False,
):
    """Run the full experiment matrix."""
    agent_client: anthropic.Anthropic | None = None
    judge_client: anthropic.Anthropic | None = None
    if not dry_run:
        judge_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        if config.AGENT_BACKEND == "anthropic":
            agent_client = judge_client
    ensure_results_file(results_file)

    total = len(tasks) * len(conditions) * reps
    skipped = 0
    done = 0
    errors = 0

    print(f"\n{'='*60}")
    print(f"RA-3 Pilot Study — {len(tasks)} tasks × {len(conditions)} conditions × {reps} reps = {total} runs")
    print(f"Already completed: {len(completed)} runs")
    print(f"Agent backend: {config.AGENT_BACKEND}")
    if config.AGENT_BACKEND == "anthropic":
        print(f"Agent model: {config.AGENT_MODEL}")
    elif config.AGENT_BACKEND == "ollama":
        print(f"Ollama model: {config.OLLAMA_MODEL}")
    elif config.AGENT_BACKEND == "google":
        print(f"Google model: {config.GOOGLE_MODEL}")
    elif config.AGENT_BACKEND == "dashscope":
        print(f"Dashscope model: {config.DASHSCOPE_MODEL}")
    elif config.AGENT_BACKEND == "openrouter":
        print(f"OpenRouter model: {config.OPENROUTER_MODEL}")
    print(f"Judge model: {config.JUDGE_MODEL}")
    print(f"Results file: {results_file}")
    if dry_run:
        print("*** DRY RUN — no model calls ***")
    print(f"{'='*60}\n")

    for task in tasks:
        for condition in conditions:
            for rep in range(1, reps + 1):
                run_key = f"{task['id']}|{condition}|{rep}"
                if run_key in completed:
                    skipped += 1
                    continue

                done += 1
                progress = f"[{done + skipped}/{total}]"
                print(f"{progress} {task['id']} | {condition} | rep {rep}", end=" ... ", flush=True)

                if dry_run:
                    cfg = CONDITION_CONFIGS[condition]
                    system_prompt = cfg["system_prompt_fn"](task)
                    messages = cfg["messages_fn"](task)
                    prompt_chars = len(system_prompt) + sum(len(m["content"]) for m in messages)
                    print(f"prompt={prompt_chars} chars, messages={len(messages)}", flush=True)
                    continue

                try:
                    # 1. Agent call
                    agent_response = call_agent(agent_client, task, condition)

                    # 2. C4 post-judge (only for C4 condition)
                    c4_result = {}
                    if condition == "C4_ontology_process":
                        c4_result = call_c4_process_judge(judge_client, task, agent_response)

                    # 3. Evaluate with metric judge
                    scores = evaluate_response(judge_client, task, agent_response)

                    # 4. Record
                    row = {
                        "task_id": task["id"],
                        "industry": task["industry"],
                        "category": task["category"],
                        "metric_tested": task["metric_tested"],
                        "condition": condition,
                        "rep": rep,
                        "TF": scores["TF"],
                        "MA": scores["MA"],
                        "RC": scores["RC"],
                        "RS": scores["RS"],
                        "c4_quality_score": c4_result.get("quality_score", ""),
                        "c4_pass": c4_result.get("pass", ""),
                        "agent_response_len": len(agent_response),
                        "judge_detail": scores["judge_detail"],
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    append_result(row, results_file)
                    print(f"TF={scores['TF']:.2f} MA={scores['MA']:.2f} RC={scores['RC']:.2f} RS={scores['RS']:.2f}", flush=True)

                except anthropic.RateLimitError:
                    print("RATE_LIMITED — waiting 60s")
                    time.sleep(60)
                    done -= 1  # retry on next loop
                    continue
                except Exception as e:
                    print(f"ERROR: {e}")
                    errors += 1
                    continue

                # Small delay to avoid rate limits
                time.sleep(0.5)

    print(f"\n{'='*60}")
    print(f"Complete. Runs: {done} new, {skipped} skipped, {errors} errors.")
    print(f"Results: {results_file}")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description="RA-3 Pilot Study Runner")
    parser.add_argument("--pilot", action="store_true", help="Run calibration pilot only (4 tasks)")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument("--dry-run", action="store_true", help="Validate prompts/output paths without model calls")
    parser.add_argument("--task", type=str, help="Run single task ID")
    parser.add_argument("--condition", type=str, help="Run single condition")
    parser.add_argument("--reps", type=int, default=config.REPETITIONS, help="Number of repetitions")
    parser.add_argument("--output-suffix", type=str, help="Write results to results_raw_<suffix>.csv")
    args = parser.parse_args()

    if not args.dry_run:
        if not config.ANTHROPIC_API_KEY:
            print("ERROR: Set ANTHROPIC_API_KEY environment variable (required for judge).")
            sys.exit(1)
        if config.AGENT_BACKEND == "google" and not config.GOOGLE_API_KEY:
            print("ERROR: Set GOOGLE_API_KEY environment variable for Google AI Studio agent.")
            sys.exit(1)
        if config.AGENT_BACKEND == "dashscope" and not config.DASHSCOPE_API_KEY:
            print("ERROR: Set DASHSCOPE_API_KEY environment variable for Dashscope agent.")
            sys.exit(1)
        if config.AGENT_BACKEND == "openrouter" and not config.OPENROUTER_API_KEY:
            print("ERROR: Set OPENROUTER_API_KEY environment variable for OpenRouter agent.")
            sys.exit(1)

    all_tasks = load_tasks()
    results_file = config.get_results_file(args.output_suffix)
    completed = load_completed_runs(results_file) if args.resume else set()

    # Filter tasks
    if args.pilot:
        tasks = [t for t in all_tasks if t["id"] in config.PILOT_TASK_IDS]
        print(f"PILOT MODE: {len(tasks)} tasks")
    elif args.task:
        tasks = [t for t in all_tasks if t["id"] == args.task]
        if not tasks:
            print(f"ERROR: Task '{args.task}' not found.")
            sys.exit(1)
    else:
        tasks = all_tasks

    # Filter conditions
    if args.condition:
        if args.condition not in CONDITION_CONFIGS:
            print(f"ERROR: Condition '{args.condition}' not found. Options: {list(CONDITION_CONFIGS.keys())}")
            sys.exit(1)
        conditions = [args.condition]
    else:
        conditions = config.CONDITIONS

    run_experiment(tasks, conditions, args.reps, completed, results_file, args.dry_run)


if __name__ == "__main__":
    main()
