"""RA-6 Pilot: Fault Detection Pipeline (Two-Stage per E4).

Stage A: FDR-design — Does the suite contain a scenario that SHOULD detect each fault?
Stage B: FDR-execution — Does the suite ACTUALLY detect each fault when run against a faulty agent?
"""

import json
import os
import time

import anthropic

import config


def _call_llm(client, **kwargs):
    """Call Anthropic API with retry + exponential backoff for transient errors."""
    for attempt in range(5):
        try:
            return client.messages.create(**kwargs)
        except (anthropic.APIStatusError, anthropic.APIConnectionError) as e:
            status = getattr(e, 'status_code', 0)
            if status in (429, 529, 500, 502, 503) or isinstance(e, anthropic.APIConnectionError):
                wait = min(2 ** attempt * 5, 120)
                print(f"    RETRY {attempt+1}/5: {type(e).__name__} ({status}), waiting {wait}s")
                time.sleep(wait)
            else:
                raise
        except Exception as e:
            # Catch JSON decode errors from empty API responses, network issues, etc.
            wait = min(2 ** attempt * 5, 120)
            print(f"    RETRY {attempt+1}/5: {type(e).__name__}: {str(e)[:80]}, waiting {wait}s")
            time.sleep(wait)
    return client.messages.create(**kwargs)


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

FDR_DESIGN_PROMPT = """You are a test design analyst. Determine whether a test scenario would theoretically detect a specific agent fault.

FAULT SPECIFICATION:
- ID: {fault_id}
- Category: {category}
- Name: {fault_name}
- Description: The faulty agent has this behavior: {injection}
- Ground Truth: The correct behavior is: {ground_truth}

TEST SCENARIO (description only — NOT executed):
- Scenario ID: {scenario_id}
- Description: {description}
- Agent Input: {agent_input}
- Expected Behavior: {expected_behavior}

Would executing this test scenario against an agent with the specified fault
REVEAL the fault? The scenario reveals the fault if:
1. The scenario's input would trigger the faulty behavior, AND
2. The expected behavior differs from what the faulty agent would produce

Respond with EXACTLY this JSON (no other text):
{{"would_detect": true/false, "rationale": "one sentence explanation"}}"""

FAULTY_AGENT_SYSTEM_PROMPT = """You are a {role} AI agent in the {industry} industry.

{fault_injections}

Respond to the user's query professionally and thoroughly. Apply your knowledge
and the guidelines above to provide accurate, helpful responses."""

FDR_EXECUTION_JUDGE_PROMPT = """You are a quality assurance judge evaluating an AI agent's response for correctness.

SCENARIO:
- Input: {agent_input}
- Expected Behavior: {expected_behavior}

AGENT RESPONSE:
{agent_response}

KNOWN FAULT TO DETECT:
- {fault_name}: {ground_truth}

Did the agent's response exhibit the fault described above?
A fault is "detected" if the agent's response is INCORRECT in a way that
matches the specific fault, AND a reasonable evaluator would flag it.

Respond with EXACTLY this JSON (no other text):
{{"fault_detected": true/false, "rationale": "one sentence explanation"}}"""


def load_faults(industry: str) -> list[dict]:
    """Load fault definitions for an industry."""
    path = os.path.join(config.FAULTS_DIR, "faults.json")
    with open(path) as f:
        data = json.load(f)
    return data["faults"][industry]


def stage_a_design(
    scenarios: list[dict],
    faults: list[dict],
    client: anthropic.Anthropic,
) -> list[dict]:
    """Stage A: FDR-design assessment (no execution needed)."""
    results = []

    for fault in faults:
        detected_by_any = False
        detecting_scenario = None

        for scenario in scenarios:
            prompt = FDR_DESIGN_PROMPT.format(
                fault_id=fault["id"],
                category=fault["category"],
                fault_name=fault["name"],
                injection=fault["injection"],
                ground_truth=fault["ground_truth"],
                scenario_id=scenario.get("scenario_id", ""),
                description=scenario.get("description", ""),
                agent_input=scenario.get("agent_input", ""),
                expected_behavior=scenario.get("expected_behavior", ""),
            )
            response = _call_llm(client,
                model=config.JUDGE_MODEL,
                max_tokens=config.MAX_TOKENS_JUDGE,
                temperature=config.JUDGE_TEMPERATURE,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip()
            try:
                result = json.loads(text)
                if result.get("would_detect"):
                    detected_by_any = True
                    detecting_scenario = scenario.get("scenario_id", "")
                    break
            except json.JSONDecodeError:
                continue
            time.sleep(0.3)

        results.append({
            "fault_id": fault["id"],
            "fault_name": fault["name"],
            "category": fault["category"],
            "severity": fault["severity"],
            "design_covered": detected_by_any,
            "detecting_scenario": detecting_scenario,
        })

    return results


def stage_b_execution(
    scenarios: list[dict],
    faults: list[dict],
    industry: str,
    client: anthropic.Anthropic,
) -> list[dict]:
    """Stage B: FDR-execution assessment (execute scenarios against faulty agent)."""
    role = config.AGENT_ROLES[industry]

    # Build faulty agent system prompt with ALL faults injected
    fault_injections = "\n".join(
        f"- {fault['injection']}" for fault in faults
    )
    system_prompt = FAULTY_AGENT_SYSTEM_PROMPT.format(
        role=role, industry=industry, fault_injections=fault_injections
    )

    results = []

    for fault in faults:
        detected = False
        detecting_scenario = None

        for scenario in scenarios:
            agent_input = scenario.get("agent_input", "")
            if not agent_input or agent_input == "placeholder":
                continue

            # Execute scenario against faulty agent
            agent_response = _call_llm(client,
                model=config.AGENT_MODEL,
                max_tokens=config.MAX_TOKENS_AGENT,
                temperature=config.AGENT_TEMPERATURE,
                system=system_prompt,
                messages=[{"role": "user", "content": agent_input}],
            )
            agent_text = agent_response.content[0].text.strip()

            # Judge whether fault was detected
            judge_prompt = FDR_EXECUTION_JUDGE_PROMPT.format(
                agent_input=agent_input,
                expected_behavior=scenario.get("expected_behavior", ""),
                agent_response=agent_text[:1500],
                fault_name=fault["name"],
                ground_truth=fault["ground_truth"],
            )
            judge_response = _call_llm(client,
                model=config.JUDGE_MODEL,
                max_tokens=config.MAX_TOKENS_JUDGE,
                temperature=config.JUDGE_TEMPERATURE,
                messages=[{"role": "user", "content": judge_prompt}],
            )
            judge_text = judge_response.content[0].text.strip()
            try:
                result = json.loads(judge_text)
                if result.get("fault_detected"):
                    detected = True
                    detecting_scenario = scenario.get("scenario_id", "")
                    break
            except json.JSONDecodeError:
                continue
            time.sleep(0.5)

        results.append({
            "fault_id": fault["id"],
            "fault_name": fault["name"],
            "category": fault["category"],
            "severity": fault["severity"],
            "execution_detected": detected,
            "detecting_scenario": detecting_scenario,
        })

    return results


def run_fault_detection(scenarios_file: str = None, dry_run: bool = False) -> dict:
    """Run both FDR stages on all generated scenario suites.

    Supports resumption: loads existing fdr_results.json and skips
    already-completed suites.
    """
    path = scenarios_file or config.SCENARIOS_FILE
    with open(path) as f:
        all_scenarios = json.load(f)

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    # Resume: load existing results if available
    all_results = {}
    if os.path.exists(config.FDR_FILE) and not dry_run:
        with open(config.FDR_FILE) as f:
            all_results = json.load(f)
        real = sum(1 for v in all_results.values() if v.get("fdr_design", 0) > 0 or v.get("fdr_execution", 0) > 0)
        print(f"  Resuming: {real} suites already assessed")

    total = len(all_scenarios)

    for idx, (suite_key, scenarios) in enumerate(all_scenarios.items(), 1):
        if suite_key in all_results and all_results[suite_key].get("fdr_design", 0) > 0:
            print(f"[{idx}/{total}] SKIP (cached): {suite_key}")
            continue

        # Parse industry: G1_baseline_fintech_rep1 or G1_baseline_banking_vn_rep1
        for cond in config.CONDITIONS:
            if suite_key.startswith(cond + "_"):
                remainder = suite_key[len(cond) + 1:]
                industry = remainder.rsplit("_rep", 1)[0]
                break
        else:
            industry = "fintech"
        faults = load_faults(industry)

        print(f"[{idx}/{total}] FDR: {suite_key}")

        if dry_run:
            all_results[suite_key] = {
                "stage_a": [{"fault_id": f["id"], "design_covered": False} for f in faults],
                "stage_b": [{"fault_id": f["id"], "execution_detected": False} for f in faults],
                "fdr_design": 0.0,
                "fdr_execution": 0.0,
                "fdr_gap": 0.0,
            }
            continue

        # Stage A: Design assessment
        print(f"  -> Stage A: FDR-design ({len(faults)} faults x {len(scenarios)} scenarios)...")
        stage_a = stage_a_design(scenarios, faults, client)
        fdr_design = sum(1 for r in stage_a if r["design_covered"]) / len(faults)
        print(f"     FDR-design = {fdr_design:.1%}")

        # Stage B: Execution assessment
        print(f"  -> Stage B: FDR-execution ({len(faults)} faults)...")
        stage_b = stage_b_execution(scenarios, faults, industry, client)
        fdr_exec = sum(1 for r in stage_b if r["execution_detected"]) / len(faults)
        print(f"     FDR-execution = {fdr_exec:.1%}")

        gap = fdr_design - fdr_exec
        print(f"     Gap (design - execution) = {gap:+.1%}")

        all_results[suite_key] = {
            "stage_a": stage_a,
            "stage_b": stage_b,
            "fdr_design": fdr_design,
            "fdr_execution": fdr_exec,
            "fdr_gap": gap,
        }

        # Incremental save after each suite (crash resilience)
        with open(config.FDR_FILE, "w") as f:
            json.dump(all_results, f, indent=2)

    # Final save
    with open(config.FDR_FILE, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved FDR results to {config.FDR_FILE}")

    return all_results


if __name__ == "__main__":
    import sys
    dry = "--dry-run" in sys.argv
    run_fault_detection(dry_run=dry)
