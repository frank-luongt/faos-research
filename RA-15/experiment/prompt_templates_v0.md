# RA-15 Prompt Templates v0.2

**Date:** 2026-05-09
**Status:** Phase 0 rerun templates after q1 measurement-semantics revision
**Protocol:** [`PILOT-PROTOCOL-v0.1.md`](PILOT-PROTOCOL-v0.1.md)

**Revision note:** Phase 0 on 2026-05-05 passed the parser/schema gate
but exposed ambiguity in q1 (`proceed` / `defer`) on `fintech_T6`.
This v0.2 template replaces q1 with a business-continuity posture:
`clear_to_continue` / `hold_for_review`.

---

## 1. System Prompt

```text
You are an enterprise decision reviewer participating in a measurement study.

Follow the requested role frame, task, and ontology/policy context. Return JSON only.
Do not include markdown, chain-of-thought, hidden reasoning, or any keys not requested.
Use only the allowed labels for each measured content.
The rationale must be one short paragraph of 60 words or fewer.
```

---

## 2. User Prompt Template

```text
Role frame:
{ROLE_FRAME}

Task:
{TASK_TEXT}

Ontology/policy context:
{ONTOLOGY_SNIPPET}

Measurement context:
{CONTEXT_ID} measures exactly these contents in this order:
{MEASURED_CONTENTS}

Allowed labels:
{ALLOWED_LABELS}

Output schema:
{JSON_SCHEMA}

Return JSON only. Include exactly the measured q fields plus rationale.
Do not include unmeasured q fields.
```

---

## 3. Content Label Definitions

Use the same binary labels for all pilot tasks:

| Content | Positive label | Negative label | Decision meaning |
|---|---|---|---|
| q1 | `clear_to_continue` | `hold_for_review` | Whether normal business action is permissible without additional review |
| q2 | `high_risk` | `not_high_risk` | Whether the case should be treated as high risk |
| q3 | `escalate` | `no_escalate` | Whether formal escalation is required |
| q4 | `sufficient` | `insufficient` | Whether available evidence is enough for final decision |

---

## 4. Context-Specific Schemas

### C1 / C1X

Measured contents: `q1`, `q2`

```json
{
  "q1": "clear_to_continue|hold_for_review",
  "q2": "high_risk|not_high_risk",
  "rationale": "one short paragraph"
}
```

### C2 / C2X

Measured contents: `q2`, `q3`

```json
{
  "q2": "high_risk|not_high_risk",
  "q3": "escalate|no_escalate",
  "rationale": "one short paragraph"
}
```

### C3 / C3X

Measured contents: `q3`, `q4`

```json
{
  "q3": "escalate|no_escalate",
  "q4": "sufficient|insufficient",
  "rationale": "one short paragraph"
}
```

### C4 / C4X

Measured contents: `q4`, `q1`

```json
{
  "q4": "sufficient|insufficient",
  "q1": "clear_to_continue|hold_for_review",
  "rationale": "one short paragraph"
}
```

---

## 5. Phase 0 Smoke-Test Prompts

Use only:

- `software_T3`, canonical block
- `fintech_T6`, canonical block
- contexts `C1`, `C2`, `C3`, `C4`
- 3 repetitions per context

Phase 0 pass criteria:

- at least 95% parseable JSON;
- exactly measured q fields plus `rationale`;
- no unmeasured q fields;
- no labels outside the allowed set.
- low-conflict `fintech_T6` no longer shows q1-driven false
  contextuality under the CbD smoke summary.
