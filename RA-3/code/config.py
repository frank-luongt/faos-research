"""RA-3 Pilot Study Configuration."""

import os
import re
from pathlib import Path

# --- API ---
# Try env var first, then fall back to .env file
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
if not ANTHROPIC_API_KEY:
    _env_file = Path(__file__).resolve().parents[3] / ".env"
    if _env_file.exists():
        for line in _env_file.read_text().splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                ANTHROPIC_API_KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
AGENT_BACKEND = os.environ.get("RA3_AGENT_BACKEND", "anthropic").strip().lower()
AGENT_MODEL = os.environ.get("RA3_AGENT_MODEL", "claude-sonnet-4-20250514")
JUDGE_MODEL = os.environ.get("RA3_JUDGE_MODEL", "claude-sonnet-4-20250514")
AGENT_TEMPERATURE = 0.3
JUDGE_TEMPERATURE = 0.0
AGENT_MAX_TOKENS = 1500
JUDGE_MAX_TOKENS = 800
CONTEXT_TOKEN_BUDGET = 2000  # max tokens for injected context

# --- Ollama (local) ---
OLLAMA_MODEL = os.environ.get("RA3_OLLAMA_MODEL", "qwen2.5:14b-instruct-q4_K_M")
OLLAMA_BASE_URL = os.environ.get("RA3_OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_TIMEOUT_SECONDS = float(os.environ.get("RA3_OLLAMA_TIMEOUT_SECONDS", "300"))

# --- Google AI Studio (Gemma 4) ---
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
if not GOOGLE_API_KEY:
    if _env_file.exists():
        for line in _env_file.read_text().splitlines():
            if line.startswith("GOOGLE_API_KEY="):
                GOOGLE_API_KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
GOOGLE_MODEL = os.environ.get("RA3_GOOGLE_MODEL", "gemma-4-26b-a4b-it")
GOOGLE_TIMEOUT_SECONDS = float(os.environ.get("RA3_GOOGLE_TIMEOUT_SECONDS", "120"))

# --- Dashscope / Alibaba (Qwen) ---
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
if not DASHSCOPE_API_KEY:
    if _env_file.exists():
        for line in _env_file.read_text().splitlines():
            if line.startswith("DASHSCOPE_API_KEY="):
                DASHSCOPE_API_KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
DASHSCOPE_MODEL = os.environ.get("RA3_DASHSCOPE_MODEL", "qwen-plus")
DASHSCOPE_BASE_URL = os.environ.get(
    "RA3_DASHSCOPE_BASE_URL",
    "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
).rstrip("/")
DASHSCOPE_TIMEOUT_SECONDS = float(os.environ.get("RA3_DASHSCOPE_TIMEOUT_SECONDS", "120"))

# --- OpenRouter (multi-model gateway) ---
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
if not OPENROUTER_API_KEY:
    if _env_file.exists():
        for line in _env_file.read_text().splitlines():
            if line.startswith("OPENROUTER_API_KEY="):
                OPENROUTER_API_KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
OPENROUTER_MODEL = os.environ.get("RA3_OPENROUTER_MODEL", "qwen/qwen-2.5-72b-instruct")
OPENROUTER_TIMEOUT_SECONDS = float(os.environ.get("RA3_OPENROUTER_TIMEOUT_SECONDS", "120"))

# --- Experiment ---
REPETITIONS = 3
CONDITIONS = ["C1_ungrounded", "C2_rag", "C3_ontology", "C4_ontology_process"]
INDUSTRIES = ["fintech", "insurance", "healthcare", "banking_vn", "insurance_vn"]
METRICS = ["TF", "MA", "RC", "RS"]

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_FILE = os.path.join(BASE_DIR, "tasks.json")
ONTOLOGY_DIR = os.path.join(BASE_DIR, "ontology_context")
RESULTS_DIR = os.path.join(BASE_DIR, "results")


def _normalize_suffix(value: str) -> str:
    """Normalize user-provided suffixes into filesystem-safe tokens."""
    normalized = re.sub(r"[^a-z0-9]+", "_", value.strip().lower())
    return normalized.strip("_")


def _infer_model_suffix(model_name: str) -> str:
    lowered = model_name.lower()
    if "qwen" in lowered and "14b" in lowered:
        return "qwen14b"
    if "qwen" in lowered and "32b" in lowered:
        return "qwen32b"
    if "qwen" in lowered and "72b" in lowered:
        return "qwen72b"
    if "qwen" in lowered and "plus" in lowered:
        return "qwen_plus"
    if "qwen" in lowered and "turbo" in lowered:
        return "qwen_turbo"
    if "qwen" in lowered and "max" in lowered:
        return "qwen_max"
    if "gemma" in lowered and "4" in lowered and "26b" in lowered:
        return "gemma4_26b"
    if "gemma" in lowered and "4" in lowered and "31b" in lowered:
        return "gemma4_31b"
    if "gemma" in lowered and "4" in lowered and "e4b" in lowered:
        return "gemma4_e4b"
    if "gemma" in lowered and "4" in lowered:
        return "gemma4"
    return _normalize_suffix(lowered)[:40]


def _default_output_suffix() -> str:
    override = os.environ.get("RA3_OUTPUT_SUFFIX", "")
    if override:
        return _normalize_suffix(override)
    if AGENT_BACKEND == "anthropic":
        return ""
    if AGENT_BACKEND == "ollama":
        return _infer_model_suffix(OLLAMA_MODEL)
    if AGENT_BACKEND == "google":
        return _infer_model_suffix(GOOGLE_MODEL)
    if AGENT_BACKEND == "dashscope":
        return _infer_model_suffix(DASHSCOPE_MODEL)
    if AGENT_BACKEND == "openrouter":
        return _infer_model_suffix(OPENROUTER_MODEL)
    return _infer_model_suffix(AGENT_MODEL)


def _suffix_token(output_suffix: str | None = None) -> str:
    if output_suffix is None:
        return _default_output_suffix()
    return _normalize_suffix(output_suffix)


def get_results_file(output_suffix: str | None = None) -> str:
    suffix = _suffix_token(output_suffix)
    filename = f"results_raw_{suffix}.csv" if suffix else "results_raw.csv"
    return os.path.join(RESULTS_DIR, filename)


def get_analysis_file(output_suffix: str | None = None) -> str:
    suffix = _suffix_token(output_suffix)
    filename = f"analysis_summary_{suffix}.json" if suffix else "analysis_summary.json"
    return os.path.join(RESULTS_DIR, filename)


def get_figures_dir(output_suffix: str | None = None) -> str:
    suffix = _suffix_token(output_suffix)
    dirname = f"figures_{suffix}" if suffix else "figures"
    return os.path.join(RESULTS_DIR, dirname)


OUTPUT_SUFFIX = _default_output_suffix()
RAW_RESULTS_FILE = get_results_file()
ANALYSIS_FILE = get_analysis_file()

# --- Pilot mode ---
PILOT_TASK_IDS = [
    "fintech_T1",   # TF
    "fintech_T4",   # MA
    "fintech_T6",   # RC
    "fintech_T8",   # RS
]
