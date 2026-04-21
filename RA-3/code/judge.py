"""LLM-as-Judge evaluation prompts for RA-3 pilot study."""

import json


def build_tf_judge_prompt(task: dict, response: str) -> str:
    """Terminological Fidelity judge prompt."""
    gt = task["ground_truth"]
    terms = gt.get("required_terms", [])
    defs = gt.get("term_definitions", {})
    terms_block = "\n".join(
        f"- {t}: {defs.get(t, '(see context)')}" for t in terms
    )
    return f"""You are evaluating an AI agent's response for Terminological Fidelity.

TASK: {task["question"]}

AGENT RESPONSE:
{response}

GROUND TRUTH TERMS AND DEFINITIONS:
{terms_block}

SCORING RUBRIC:
- Extract all domain-specific terms used in the response
- For each term, check if it matches a term in the ground truth list
- For matching terms, check if the usage is consistent with the formal definition
- Score = (correctly used terms) / (total domain terms in response)

Respond ONLY with valid JSON:
{{
  "terms_found": ["list of domain terms extracted from response"],
  "correct_terms": ["list of correctly used terms"],
  "incorrect_terms": ["list of incorrectly used or hallucinated terms with brief explanation"],
  "score": 0.0,
  "rationale": "brief explanation"
}}"""


def build_ma_judge_prompt(task: dict, response: str) -> str:
    """Metric Accuracy judge prompt."""
    gt = task["ground_truth"]
    metrics = gt.get("metrics", {})
    metrics_block = json.dumps(metrics, indent=2)
    return f"""You are evaluating an AI agent's response for Metric Accuracy.

TASK: {task["question"]}

AGENT RESPONSE:
{response}

GROUND TRUTH METRICS:
{metrics_block}

SCORING RUBRIC:
- Extract all metric references from the response (values, ranges, benchmarks)
- For each metric, check if the cited value/range matches the ground truth
- Check if the assessment (healthy/unhealthy/exceeds) is correct
- Score = (correctly cited metrics) / (total metric references in response)

Respond ONLY with valid JSON:
{{
  "metrics_found": ["list of metrics referenced in response"],
  "correct_metrics": ["list of correctly cited metrics"],
  "incorrect_metrics": ["list of incorrect metric citations with explanation"],
  "score": 0.0,
  "rationale": "brief explanation"
}}"""


def build_rc_judge_prompt(task: dict, response: str) -> str:
    """Regulatory Compliance judge prompt."""
    gt = task["ground_truth"]
    regs = gt.get("regulations", [])
    reqs = gt.get("requirements", gt.get("key_points", []))
    return f"""You are evaluating an AI agent's response for Regulatory Compliance accuracy.

TASK: {task["question"]}

AGENT RESPONSE:
{response}

GROUND TRUTH REGULATIONS:
{json.dumps(regs, indent=2)}

GROUND TRUTH REQUIREMENTS/KEY POINTS:
{json.dumps(reqs, indent=2)}

SCORING RUBRIC:
- Extract all regulatory references from the response
- Check each against the ground truth regulation list
- Verify requirements/obligations are correctly stated
- Penalize fabricated regulations or incorrect requirements
- Score = (correct regulatory statements) / (total regulatory statements in response)

Respond ONLY with valid JSON:
{{
  "regulations_cited": ["list of regulations referenced"],
  "correct_citations": ["list of correctly cited regulations"],
  "incorrect_citations": ["list of wrong or fabricated citations"],
  "requirements_correct": ["list of correctly stated requirements"],
  "requirements_wrong": ["list of incorrect requirements"],
  "score": 0.0,
  "rationale": "brief explanation"
}}"""


def build_rs_judge_prompt(task: dict, response: str) -> str:
    """Role Consistency judge prompt."""
    gt = task["ground_truth"]
    role = gt.get("role", "Unknown")
    vocab = gt.get("vocabulary", [])
    kpis = gt.get("kpi_references", [])
    style = gt.get("communication_style", "")
    factors = gt.get("expected_factors", [])
    pattern = gt.get("decision_pattern", "")
    return f"""You are evaluating an AI agent's response for Role Consistency.

TASK: {task["question"]}

AGENT RESPONSE:
{response}

GROUND TRUTH ROLE PROFILE:
- Role: {role}
- Decision Pattern: {pattern}
- Expected Decision Factors: {json.dumps(factors)}
- Expected KPIs: {json.dumps(kpis)}
- Expected Vocabulary: {json.dumps(vocab)}
- Communication Style: {style}

SCORING RUBRIC — score three sub-dimensions and average:

1. Decision Pattern Match (0-1): Does the response follow the role's decision framework?
   - Uses the expected decision factors? References expected outputs?
2. Metric Priority Alignment (0-1): Does the response reference the role's KPIs?
   - Mentions the role-specific metrics and benchmarks?
3. Communication Style Match (0-1): Does the response match the role's voice?
   - Uses role vocabulary? Matches communication style?

Score = average of 3 sub-dimensions.

Respond ONLY with valid JSON:
{{
  "decision_pattern_score": 0.0,
  "decision_pattern_evidence": "brief evidence",
  "metric_alignment_score": 0.0,
  "metric_alignment_evidence": "brief evidence",
  "style_match_score": 0.0,
  "style_match_evidence": "brief evidence",
  "score": 0.0,
  "rationale": "brief explanation"
}}"""


def build_cross_cutting_judge_prompt(task: dict, response: str) -> str:
    """Cross-cutting task judge — evaluates all four metrics."""
    gt = task["ground_truth"]
    return f"""You are evaluating an AI agent's response on a cross-cutting enterprise task.
Score FOUR dimensions independently.

TASK: {task["question"]}

AGENT RESPONSE:
{response}

GROUND TRUTH:
{json.dumps(gt, indent=2)}

Score each dimension 0.0-1.0:
1. TF (Terminological Fidelity): Are domain terms used correctly?
2. MA (Metric Accuracy): Are metrics/benchmarks/SLAs cited correctly?
3. RC (Regulatory Compliance): Are regulations and requirements accurate?
4. RS (Role Consistency): Does the response show appropriate role awareness and handoff knowledge?

Respond ONLY with valid JSON:
{{
  "TF_score": 0.0, "TF_rationale": "",
  "MA_score": 0.0, "MA_rationale": "",
  "RC_score": 0.0, "RC_rationale": "",
  "RS_score": 0.0, "RS_rationale": ""
}}"""


JUDGE_BUILDERS = {
    "TF": build_tf_judge_prompt,
    "MA": build_ma_judge_prompt,
    "RC": build_rc_judge_prompt,
    "RS": build_rs_judge_prompt,
    "ALL": build_cross_cutting_judge_prompt,
}
