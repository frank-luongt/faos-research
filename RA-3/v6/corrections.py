"""v6 corrections to v5 content: ground truth and ontology facts that current law superseded.

Edits are ``set`` (replace a v5 value), ``rename`` (a key), ``add`` (a new key,
v5 null) or ``append`` (to a list, v5 null). ``add`` and ``append`` carry the
current US rules the stale-knowledge set grounds against (ids US-..., written
by ``stale/build_items.py`` from ``stale/us_rules.py``).

v5's files stay byte-identical so v5 still reproduces. v6 applies the edits in
``corrections.json`` when it loads a v5 task or ontology. Each edit records the
v5 value it replaces, and applying an edit fails loudly if the v5 file no longer
holds that value, so a correction can never land on text it was not written for.
``V5-TO-V6-DIFF.md`` is generated from the same file by ``python corrections.py``.
"""

import copy
import json
from pathlib import Path

HERE = Path(__file__).parent
CORRECTIONS_FILE = HERE / "corrections.json"
DIFF_FILE = HERE / "V5-TO-V6-DIFF.md"


def load() -> dict:
    with open(CORRECTIONS_FILE) as f:
        return json.load(f)


def _parent(obj, path):
    for key in path[:-1]:
        obj = obj[key]
    return obj


def apply(obj: dict, edits: list[dict]) -> dict:
    """Return a corrected deep copy of ``obj``; raise if any edit's v5 value is missing."""
    out = copy.deepcopy(obj)
    for e in edits:
        parent, key = _parent(out, e["path"]), e["path"][-1]
        if e.get("op") == "add":
            if not isinstance(parent, dict) or key in parent or e["v5"] is not None:
                raise ValueError(f"correction {e['id']}: cannot add {e['path']}, it already exists")
            parent[key] = copy.deepcopy(e["v6"])
        elif e.get("op") == "append":
            if not isinstance(parent.get(key) if isinstance(parent, dict) else None, list) or e["v5"] is not None:
                raise ValueError(f"correction {e['id']}: {e['path']} is not a list to append to")
            parent[key].append(copy.deepcopy(e["v6"]))
        elif e.get("op", "set") == "rename":
            if not isinstance(parent, dict) or key not in parent or e["v5"] != key or e["v6"] in parent:
                raise ValueError(f"correction {e['id']}: cannot rename to {e['v6']}")
            items = [(e["v6"] if k == key else k, v) for k, v in parent.items()]
            parent.clear()
            parent.update(items)
        else:
            if parent[key] != e["v5"]:
                raise ValueError(f"correction {e['id']}: v5 value at {e['path']} has changed")
            parent[key] = copy.deepcopy(e["v6"])
    return out


def for_task(task_id: str) -> list[dict]:
    return load().get("tasks", {}).get(task_id, [])


def for_ontology(stem: str) -> list[dict]:
    return load().get("ontologies", {}).get(stem, [])


def _fmt(value) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return text.replace("|", "\\|").replace("\n", " ")


def write_diff() -> None:
    data = load()
    n = sum(len(v) for group in ("ontologies", "tasks") for v in data.get(group, {}).values())
    lines = [
        "# RA-3 v5 to v6 diff",
        "",
        "Generated from `corrections.json` by `python corrections.py`; do not edit by hand.",
        "",
        data["preamble"],
        "",
        f"{n} edits. Status: {data['status']}.",
        "",
    ]
    for group, title in (("ontologies", "Ontology files"), ("tasks", "Task ground truth and questions")):
        lines += [f"## {title}", ""]
        for target, edits in data.get(group, {}).items():
            lines += [f"### {target}", "", "| ID | Field | v5 | v6 | Why |", "| --- | --- | --- | --- | --- |"]
            for e in edits:
                field = ".".join(str(p) for p in e["path"])
                if e.get("op") == "rename":
                    field += " (key renamed)"
                elif e.get("op") in ("add", "append"):
                    field += f" ({e['op']}ed)" if e["op"] == "append" else " (added)"
                lines.append(f"| {e['id']} | `{field}` | {_fmt(e['v5'])} | {_fmt(e['v6'])} | {_fmt(e['why'])} |")
            lines.append("")
    lines += ["## Checked and left unchanged", ""] + [f"- {x}" for x in data.get("unchanged", [])] + [""]
    DIFF_FILE.write_text("\n".join(lines))
    print(f"wrote {DIFF_FILE.name}: {n} edits")


if __name__ == "__main__":
    write_diff()
