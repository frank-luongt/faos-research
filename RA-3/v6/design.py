"""RA-3 v6 study design: cells, models, conditions, run matrix and judge rotation.

Everything here is deterministic and offline. The seeded assignments it produces
(judge pairs, 10% repeats) are written out at lock by ``freeze_assignments.py``
so they can be hashed with the protocol.
"""

import hashlib
import json
import random
from pathlib import Path

V6_DIR = Path(__file__).resolve().parent
RA3_DIR = V6_DIR.parent
LOCK_FILE = V6_DIR / "models.lock.json"
TASKS_FILE = V6_DIR / "tasks_v6.json"
PROBE_DIR = V6_DIR / "probe"
ONTOLOGY_DIR = RA3_DIR / "ontology_context"
RESULTS_DIR = V6_DIR / "results"

GLOBAL_SEED = 20261112

INDUSTRIES = ["banking", "insurance", "healthcare", "securities", "fintech", "accounting"]
JURISDICTIONS = ["us", "vn"]
CELLS = [f"{i}_{j}" for i in INDUSTRIES for j in JURISDICTIONS]

# v5 ontology files keep their published names; new cells use the cell id.
_V5_ONTOLOGY_NAMES = {
    "fintech_us": "fintech",
    "insurance_us": "insurance",
    "healthcare_us": "healthcare",
    "banking_vn": "banking_vn",
    "insurance_vn": "insurance_vn",
}

CONDITIONS = ["C1_ungrounded", "C2b_rag_matched", "C3_ontology"]
TASKS_PER_CELL = 10
TASK_MIX = {  # v5's mix per cell
    "terminology": 3,
    "metric_interpretation": 2,
    "regulatory": 2,
    "role_analysis": 2,
    "cross_cutting": 1,
}
REPEAT_SHARE = 0.10
PROBE_ITEMS_PER_CELL = 90


def ontology_stem(cell: str) -> str:
    return _V5_ONTOLOGY_NAMES.get(cell, cell)


def ontology_path(cell: str) -> Path:
    return ONTOLOGY_DIR / f"{ontology_stem(cell)}.json"


def jurisdiction(cell: str) -> str:
    return cell.rsplit("_", 1)[1]


def load_lock() -> dict:
    with open(LOCK_FILE) as f:
        return json.load(f)


def agent_models(lock: dict | None = None) -> list[dict]:
    return (lock or load_lock())["agents"]


def panel_judges(lock: dict | None = None) -> list[dict]:
    return (lock or load_lock())["panel_judges"]


def _rng(*parts: str) -> random.Random:
    """A stable RNG per key, independent of iteration order and Python's hash seed."""
    key = "|".join([str(GLOBAL_SEED), *parts]).encode()
    return random.Random(int.from_bytes(hashlib.sha256(key).digest()[:8], "big"))


def judge_pairs(lock: dict | None = None) -> list[tuple[str, str]]:
    fams = [j["family"] for j in panel_judges(lock)]
    return [(a, b) for i, a in enumerate(fams) for b in fams[i + 1:]]


def assign_judge_pairs(tasks_by_cell: dict[str, list[str]], lock: dict | None = None) -> dict:
    """Map (cell, model_key, condition) -> {task_id: (judge_family_a, judge_family_b)}.

    Frontier responses get the two judges not of their own family. Open-weight
    responses get the three pairs as equally as possible within each
    cell x model x condition (3 or 4 uses each over 10 tasks), seeded.
    """
    lock = lock or load_lock()
    pairs = judge_pairs(lock)
    out = {}
    for cell, task_ids in tasks_by_cell.items():
        for m in agent_models(lock):
            for cond in CONDITIONS:
                if m["type"] == "frontier":
                    pair = tuple(p for p in (j["family"] for j in panel_judges(lock)) if p != m["family"])
                    out[(cell, m["key"], cond)] = {t: pair for t in task_ids}
                    continue
                rng = _rng("judges", cell, m["key"], cond)
                order = pairs[:]
                rng.shuffle(order)  # which pair gets the extra use varies
                seq = [order[i % len(order)] for i in range(len(task_ids))]
                rng.shuffle(seq)
                out[(cell, m["key"], cond)] = dict(zip(task_ids, seq))
    return out


def run_matrix(task_ids: list[str], lock: dict | None = None) -> list[dict]:
    """All primary runs (rep 1) plus the seeded 10% repeats (rep 2)."""
    lock = lock or load_lock()
    primary = [
        {"task_id": t, "model": m["key"], "condition": c, "rep": 1}
        for t in task_ids for m in agent_models(lock) for c in CONDITIONS
    ]
    n_rep = round(len(primary) * REPEAT_SHARE)
    repeats = _rng("repeats").sample(primary, n_rep)
    return primary + [{**r, "rep": 2} for r in sorted(repeats, key=run_key)]


def run_key(run: dict) -> str:
    return f"{run['model']}|{run['task_id']}|{run['condition']}|{run['rep']}"


def load_tasks(path: Path = TASKS_FILE) -> list[dict]:
    with open(path) as f:
        return json.load(f)


def load_v5_tasks_as_v6() -> list[dict]:
    """v5's 50 tasks mapped onto their v6 cells, for dry runs before tasks_v6.json exists."""
    inverse = {v: k for k, v in _V5_ONTOLOGY_NAMES.items()}
    with open(RA3_DIR / "code" / "tasks.json") as f:
        tasks = json.load(f)
    return [{**t, "cell": inverse[t["industry"]]} for t in tasks]


def validate_tasks(tasks: list[dict]) -> list[str]:
    """Return problems with a v6 task set (empty list = valid)."""
    problems = []
    ids = [t["id"] for t in tasks]
    if len(ids) != len(set(ids)):
        problems.append("duplicate task ids")
    for cell in CELLS:
        ts = [t for t in tasks if t.get("cell") == cell]
        if len(ts) != TASKS_PER_CELL:
            problems.append(f"{cell}: {len(ts)} tasks, expected {TASKS_PER_CELL}")
        mix = {}
        for t in ts:
            mix[t["category"]] = mix.get(t["category"], 0) + 1
        if ts and mix != TASK_MIX:
            problems.append(f"{cell}: category mix {mix} differs from {TASK_MIX}")
        if not ontology_path(cell).exists():
            problems.append(f"{cell}: missing ontology {ontology_path(cell).name}")
    for t in tasks:
        if t.get("cell") not in CELLS:
            problems.append(f"{t['id']}: unknown cell {t.get('cell')}")
    return problems

# Generation settings (v5 used T=0.3 for agents; v6 runs agents at T=0).
AGENT_TEMPERATURE = 0.0
JUDGE_TEMPERATURE = 0.0
AGENT_MAX_TOKENS = 1500  # v5's limit; revisit at lock if reasoning tokens count against it
JUDGE_MAX_TOKENS = 800
PROBE_MAX_TOKENS = 512


def call_seed(key: str) -> int:
    return _rng("seed", key).randrange(2**31)


def validate_probe(cell: str, items: list[dict]) -> list[str]:
    """Return problems with one cell's probe set (empty list = valid)."""
    problems = []
    if len(items) != PROBE_ITEMS_PER_CELL:
        problems.append(f"{cell}: {len(items)} items, expected {PROBE_ITEMS_PER_CELL}")
    ids = [i["id"] for i in items]
    if len(ids) != len(set(ids)) or not all(i.startswith(f"{cell}_P") for i in ids):
        problems.append(f"{cell}: item ids must be unique and start with {cell}_P")
    answers = {}
    for it in items:
        if sorted(it["options"]) != ["A", "B", "C", "D"] or it["answer"] not in it["options"]:
            problems.append(f"{it['id']}: needs options A-D and an answer among them")
        if len(set(it["options"].values())) != 4:
            problems.append(f"{it['id']}: duplicate option text")
        answers[it["answer"]] = answers.get(it["answer"], 0) + 1
    if answers and max(answers.values()) - min(answers.values()) > 2:
        problems.append(f"{cell}: answer letters unbalanced {answers}")
    return problems
