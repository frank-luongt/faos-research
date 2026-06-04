"""Build the canonical RA-1 task corpus from RA-3 tasks plus RA-1 supplements."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parents[2]
RA3_TASKS = PROJECT_ROOT / "research-academic/experiments/RA-3-pilot/tasks.json"
PROBLEM_CLASS_MAP = ROOT / "problem_class_map.csv"
TASK_SELECTION = ROOT / "task_selection_v1.csv"
OUTPUT = ROOT / "tasks_ra1.json"
POOL_OUTPUT = ROOT / "tasks_ra1_pool.json"


def load_json(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON list")
    return data


def load_problem_map(path: Path) -> dict[str, dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    by_id = {row["task_id"]: row for row in rows}
    if len(by_id) != len(rows):
        raise ValueError("problem_class_map.csv contains duplicate task_id values")
    return by_id


def load_selection(path: Path) -> list[str]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    selected_ids = [row["task_id"] for row in rows]
    if len(set(selected_ids)) != len(selected_ids):
        raise ValueError("task_selection_v1.csv contains duplicate task_id values")
    return selected_ids


def main() -> None:
    ra3_tasks = load_json(RA3_TASKS)
    supplement_tasks = []
    for supplement_path in sorted(ROOT.glob("*_tasks.json")):
        supplement_tasks.extend(load_json(supplement_path))

    problem_map = load_problem_map(PROBLEM_CLASS_MAP)
    selected_ids = load_selection(TASK_SELECTION)

    pool = []
    for source_task in [*ra3_tasks, *supplement_tasks]:
        task = dict(source_task)
        task_id = task["id"]
        mapping = problem_map.get(task_id)
        if mapping is None:
            raise ValueError(f"Missing problem-class mapping for {task_id}")

        task["problem_class"] = mapping["problem_class"]
        task["predicted_strategy"] = mapping["predicted_strategy"]
        task["ra1_mapping_rationale"] = mapping["rationale"]
        pool.append(task)

    mapped_ids = set(problem_map)
    task_ids = {task["id"] for task in pool}
    extra_mappings = mapped_ids - task_ids
    if extra_mappings:
        raise ValueError(f"Mappings without tasks: {sorted(extra_mappings)}")
    if len(task_ids) != len(pool):
        raise ValueError("Combined task pool contains duplicate task ids")

    pool_by_id = {task["id"]: task for task in pool}
    missing_selection = [task_id for task_id in selected_ids if task_id not in pool_by_id]
    if missing_selection:
        raise ValueError(f"Selected tasks missing from pool: {missing_selection}")

    tasks = [pool_by_id[task_id] for task_id in selected_ids]
    cells = {(task["industry"], task["problem_class"]) for task in tasks}
    if len(cells) != len(tasks):
        raise ValueError("Selected corpus has duplicate industry/problem-class cells")

    POOL_OUTPUT.write_text(json.dumps(pool, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    OUTPUT.write_text(json.dumps(tasks, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {POOL_OUTPUT} ({len(pool)} tasks)")
    print(f"Wrote {OUTPUT} ({len(tasks)} tasks)")


if __name__ == "__main__":
    main()
