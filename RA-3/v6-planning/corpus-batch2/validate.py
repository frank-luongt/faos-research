"""Validate the second snapshot using the preserved first-batch contract."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / "corpus-pilot"
spec = importlib.util.spec_from_file_location("ra3_corpus_pilot_contract", BASE / "contract.py")
base_contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_contract)
require = base_contract.require


def validate(corpus, root=ROOT):
    require(corpus["schema_version"] == 2, "Expected batch-two schema")
    require(hashlib.sha256((BASE / "corpus.json").read_bytes()).hexdigest() == corpus["parent_corpus_sha256"], "Parent corpus changed")
    summary = base_contract.validate_corpus(corpus, root)
    profiles = base_contract.keyed(corpus["role_profiles"], "profile_id")
    policies = base_contract.keyed(corpus["scenario_policies"], "policy_id")
    source_ids = {s["source_id"] for s in corpus["sources"]}
    parent = json.loads((BASE / "corpus.json").read_text())
    parent_tasks = {t["item_id"]: t for t in parent["tasks"]}
    active_ids = {t["item_id"] for t in corpus["tasks"]}
    replaced = []
    for policy in policies.values():
        require(policy["status"] == "RESEARCHER_AUTHORED_FICTIONAL_POLICY", "Scenario policy provenance lost")
        require(policy["condition_visibility"] == "IDENTICAL_COMMON_CONTEXT_ALL_ARMS", "Role policy must be common to arms")
        require(policy["common_context"] and policy["kpis"], "Missing scenario instructions")
    for profile in profiles.values():
        require(profile["policy_id"] in policies and profile["source_ids"] and set(profile["source_ids"]) <= source_ids, "Missing role provenance")
        require(set(profile["dimensions"]) == {"decision_pattern", "metric_alignment", "communication_style"}, "Incomplete RS profile")
        for anchors in profile["dimensions"].values():
            require(set(anchors) == {"zero", "half", "one"} and all(anchors.values()), "Incomplete RS anchors")
    for task in corpus["tasks"]:
        rs = task["metric_eligibility"]["RS"]["eligible"]
        ma = task["metric_eligibility"]["MA"]["eligible"]
        require(task["primary_ma_rs_eligible"] == (rs and ma), "Primary eligibility disagrees with metric references")
        numeric_ids = task["required_numeric_ids"]
        require(len(numeric_ids) == len(set(numeric_ids)), "Duplicate numeric reference")
        require(bool(numeric_ids) == ma, "MA needs explicit required numeric references")
        if ma:
            require(set(numeric_ids) <= task["reference_keys"]["MA"].keys(), "Numeric reference lacks answer")
        if rs:
            profile = profiles[task["role_profile_id"]]
            policy = policies[task["scenario_policy_id"]]
            require(profile["policy_id"] == policy["policy_id"], "Role/policy mismatch")
            require(task["reference_keys"]["RS"] == {"profile_id": profile["profile_id"], "policy_id": policy["policy_id"]}, "RS reference binding mismatch")
            require(task["common_context"] == policy["common_context"], "Common role context differs")
        if "supersedes_item_id" in task:
            old_id = task["supersedes_item_id"]
            require(old_id in parent_tasks and old_id not in active_ids, "Revision counted alongside original")
            require(task["cell_id"] == parent_tasks[old_id]["cell_id"], "Revision changed jurisdiction")
            replaced.append(old_id)
    require(len(replaced) == len(set(replaced)), "Multiple active revisions of one task")
    summary.update({"revision_count": len(replaced), "role_profiles": len(profiles),
                    "cells_with_tasks": len({t["cell_id"] for t in corpus["tasks"]}),
                    "independently_reviewed_tasks": 0})
    return summary


def common_prompt(task):
    """Common task input before any condition-specific context is added."""
    return task["prompt"] + ("\n\n" + task["common_context"] if task.get("common_context") else "")


if __name__ == "__main__":
    print(json.dumps(validate(json.loads((ROOT / "corpus.json").read_text())), indent=2))
