"""Assemble tasks_v6.json: v5's 50 tasks on their v6 cells plus the 70 new-cell tasks in pilot/.

Run after any change to pilot/tasks_*.json. The output is ordered by design.CELLS
and then by each source file's order, so a rebuild is byte-stable.
"""

import json
import sys

import design


def main() -> None:
    by_cell = {}
    for t in design.load_v5_tasks_as_v6():
        by_cell.setdefault(t["cell"], []).append(t)
    for path in sorted((design.V6_DIR / "pilot").glob("tasks_*.json")):
        cell = path.stem.removeprefix("tasks_")
        if cell in by_cell:
            sys.exit(f"{cell}: both a v5 cell and a pilot file")
        with open(path) as f:
            by_cell[cell] = json.load(f)
    tasks = [t for cell in design.CELLS for t in by_cell.get(cell, [])]
    problems = design.validate_tasks(tasks)
    if problems:
        sys.exit("tasks_v6.json not written:\n  " + "\n  ".join(problems))
    design.TASKS_FILE.write_text(json.dumps(tasks, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {design.TASKS_FILE.name}: {len(tasks)} tasks across {len(design.CELLS)} cells")


if __name__ == "__main__":
    main()
