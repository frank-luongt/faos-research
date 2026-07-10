# RA-15 Contextuality Pilot Protocol v0.1

**Date:** 2026-05-05; revised 2026-05-12
**Status:** Historical exploratory protocol; Phase 1.3 and the 2026-05-15 canonical-formalism correction are complete
**Parent concept note:** [`../../RA-15-CONTEXTUALITY-CONCEPT-NOTE.md`](../../RA-15-CONTEXTUALITY-CONCEPT-NOTE.md)
**Source corpus:** [`../RA-1-coordination/tasks_ra1.json`](../RA-1-coordination/tasks_ra1.json)

---

## 1. Purpose

This pilot tests whether Contextuality-by-Default (CbD) can provide a useful signal for enterprise LLM agent orchestration.

The pilot is not a full RA-15 experiment. It answers one gate question:

> Does residual contextuality add predictive value beyond direct prompt influence, output entropy, and simple task instability?

If no, RA-15 should pivot or be archived. If yes, RA-15 can move to a full paper scaffold.

**2026-07-10 supersession note:** This document records sequential exploratory instrument development, not a preregistered confirmatory design. Phase 1.3 and the later formalism audit supersede the original positive-contextuality gate. The publishable result is the canonical CbD null plus the measurement/direct-influence audit method.

---

## 2. Design Summary

| Element | v0.1 choice |
|---|---|
| Source tasks | RA-1 balanced corpus |
| Pilot size | 8 tasks |
| Expected contrast | 4 high-conflict vs 4 low-conflict tasks |
| Outcome type | Binary labels only |
| Contents | q1 business-continuity posture, q2 risk severity, q3 escalation need, q4 evidence sufficiency |
| Contexts | Four cyclic contexts C1-C4 |
| Ontology blocks | Canonical for all 8 tasks; conflict block for 4 high-conflict tasks |
| Repetitions | 12 per task/context/block/model in pilot run |
| Primary local model | Local Qwen 3.6 27B NVFP4 for Phase 0--1.3 |
| Replication model | OpenRouter `google/gemma-4-31b-it`, completed after Phase 1.3 |

Minimum primary-local-model call count:

```
Canonical block: 8 tasks x 4 contexts x 12 reps = 384 calls
Conflict block:  4 tasks x 4 contexts x 12 reps = 192 calls
Total first model = 576 calls
```

No multi-agent strategy arm should run until binary parsing, CbD metrics, and Phase 1.3 construct decoupling work on this solo-agent pilot.

Phase progression so far:

| Phase | Status | Current interpretation |
|---|---|---|
| Phase 0 | Complete | Parser and q1 semantics repaired |
| Phase 1 | Complete | Full primary-local-model pilot valid after timeout repair |
| Phase 1.1 | Complete | q4 action-readiness redesign isolated measurement-induced canonical effects |
| Phase 1.2 | Complete | Role/order controls preserved `insurance_T9` conflict and stable negative controls |
| Phase 1.3 | Complete | 384/384 Qwen and 384/384 Gemma 4 repaired rows; canonical `CNTX=0.000` for all groups |

---

## 3. Pilot Task Selection

The fixed v0 task list is in [`pilot_tasks_v0.csv`](pilot_tasks_v0.csv).

Selection principles:

1. Include high-conflict tasks where role, prompt framing, or ontology condition should plausibly matter.
2. Include low-conflict regulatory tasks where a stable answer should be easier.
3. Use RA-1 task IDs only, so the pilot inherits existing task metadata.
4. Prefer tasks that can be reduced to four binary contents without destroying the enterprise decision.

High-conflict expected tasks:

- `fintech_T9`
- `insurance_T9`
- `insurance_vn_T8`
- `software_T3`

Low-conflict expected tasks:

- `fintech_T6`
- `insurance_T6`
- `healthcare_T6`
- `banking_vn_T6`

---

## 4. Context Matrix

The fixed v0 context matrix is in [`context_matrix_v0.csv`](context_matrix_v0.csv).

For each task and ontology block, run four contexts:

| Context | Contents measured | Role frame | Prompt order |
|---|---|---|---|
| C1 | q1, q2 | domain operator / business owner | business-continuity posture first, risk second |
| C2 | q2, q3 | risk / compliance reviewer | risk first, escalation second |
| C3 | q3, q4 | audit / governance reviewer | escalation first, evidence second |
| C4 | q4, q1 | neutral arbitration reviewer | evidence first, decision second |

This creates the cyclic system:

```
C1: (q1, q2)
C2: (q2, q3)
C3: (q3, q4)
C4: (q4, q1)
```

Each `q_i` is observed in exactly two contexts, allowing direct influence and residual contextuality to be separated.

---

## 5. Binary Contents

Each task must instantiate the same four contents:

| Content | Generic binary form | Example labels |
|---|---|---|
| q1 | Is normal business action permissible without additional review? | `clear_to_continue` vs `hold_for_review` |
| q2 | Is the risk severity high? | `high_risk` vs `not_high_risk` |
| q3 | Is escalation required? | `escalate` vs `no_escalate` |
| q4 | Is available evidence sufficient for final decision? | `sufficient` vs `insufficient` |

The prompt must force one of the allowed labels for each measured content. Rationale text may be collected, but the parser only trusts the label field.

Recommended output schema:

```json
{
  "q1": "clear_to_continue|hold_for_review",
  "q2": "high_risk|not_high_risk",
  "q3": "escalate|no_escalate",
  "q4": "sufficient|insufficient",
  "rationale": "one short paragraph"
}
```

For contexts that measure only two contents, omitted contents must not appear.

---

## 6. Ontology Blocks

### 6.1 Canonical Block

All 8 tasks run under a concise canonical ontology snippet:

- relevant role;
- decision policy;
- key risk concepts;
- escalation rule;
- evidence sufficiency criteria.

The canonical snippet should be short enough to avoid RA-4-style volume confounds.

### 6.2 Conflict Block

Only the 4 high-conflict tasks run a conflict block. The conflict snippet should introduce one controlled contradiction:

- a policy threshold conflict;
- a role-priority conflict;
- an escalation-rule conflict;
- or a misleading domain claim.

The conflict must be documented in a per-task appendix before execution. Do not invent conflict snippets ad hoc during runs.

---

## 7. Metrics

### 7.1 Direct Influence

For each content measured in two contexts, compute marginal drift:

```
DI(q_i) = abs(P(R_i = +1 | c_a) - P(R_i = +1 | c_b))
```

Aggregate probability-scale direct influence:

```
DI_p = sum_i DI(q_i)
```

This captures ordinary prompt / role / order disturbance. High direct influence is not contextuality.

### 7.2 Residual Contextuality

Use the standard CbD cyclic-system criterion for binary rank-4 systems.

For context-pair correlations:

```
E12 = E[q1*q2 in C1]
E23 = E[q2*q3 in C2]
E34 = E[q3*q4 in C3]
E41 = E[q4*q1 in C4]
```

Compute:

```
S_odd = max over sign choices with odd number of minus signs:
        +/-E12 +/-E23 +/-E34 +/-E41

Delta = 2 * DI_p
CNTX_canonical = 0.5 * max(0, S_odd - 2 - Delta)

# Historical auxiliary score retained only for audit comparison:
Residual_p = max(0, S_odd - 2 - DI_p)
```

The canonical formula above supersedes the under-normalized probability-scale formula in the original protocol. Five known-system fixtures now verify the arithmetic layer; they do not validate the task labels.

### 7.3 Output Entropy

For each content/context pair:

```
H(R_i^c) = -p log2 p - (1-p) log2(1-p)
```

where `p` is the empirical probability of the positive label.

### 7.4 Instability

Per task:

```
instability = 1 - max_label_frequency(q1 over all contexts/reps)
```

Use q1 business-continuity posture as the primary instability variable.

---

## 8. Phase 1.3 Addendum

Phase 1.3 revises q1 and q4 labels for construct decoupling:

| Content | Phase 1.2 label family | Phase 1.3 label family |
|---|---|---|
| q1 | `clear_to_continue` / `hold_for_review` | `action_permitted_in_principle` / `action_not_permitted_in_principle` |
| q4 | `evidence_ready_for_action` / `evidence_not_ready_for_action` | `evidence_packet_ready` / `evidence_packet_not_ready` |

Rationale:

- q1 measures whether the action is permitted in principle under policy.
- q4 measures whether the current evidence packet is procedurally ready.
- q4 can be negative while q1 is positive.
- Missing evidence alone should not make q1 negative unless policy makes evidence completeness a condition of substantive permission.

Detailed protocol: `PHASE1-3-PROTOCOL-v0.1.md`.

### 7.5 Pilot Success Regression

With only 8 tasks, regression is descriptive. Use it as a direction check:

```
instability ~ CNTX_canonical + DI_p + H_mean + conflict_block + problem_class
```

This regression was a historical direction check and was not used for confirmatory inference. The final paper does not require a positive `CNTX_canonical` result.

---

## 8. Prompt Template Requirements

Each prompt must specify:

1. task text from RA-1;
2. role frame;
3. ontology snippet;
4. measured contents only;
5. allowed labels;
6. JSON output schema;
7. no chain-of-thought request;
8. short rationale only.

Template sketch:

```text
You are acting as {ROLE_FRAME}.

Task:
{TASK_TEXT}

Ontology/policy context:
{ONTOLOGY_SNIPPET}

Return JSON only. Answer exactly these contents:
{CONTENT_LIST_WITH_LABELS}

Allowed labels:
{LABEL_MAP}

Schema:
{JSON_SCHEMA}
```

---

## 9. Execution Phases

### Phase 0 - Prompt Smoke Test

- 2 tasks: `software_T3`, `fintech_T6`
- 4 contexts
- canonical block only
- 3 reps

Pass criteria:

- >= 95% parseable JSON;
- no omitted measured contents;
- no unrequested contents;
- labels fit allowed set.

### Phase 1 - First-Model Pilot

- 8 tasks
- canonical block for all tasks
- conflict block for 4 high-conflict tasks
- 12 reps

Output:

- direct influence table;
- contextuality table;
- entropy table;
- high-vs-low contrast summary.

### Phase 2 - Replication Gate (completed as a targeted robustness check)

Run local Qwen secondary only if Phase 1 produces one of:

- at least 2 tasks with `CNTX > 0`;
- high-conflict mean `CNTX` greater than low-conflict mean `CNTX`;
- conflict block increases `CNTX` in at least 2 of 4 high-conflict tasks.

### Phase 3 - Orchestration Arm (not executed; routing remains prospective)

Defer until Phase 2. Candidate arm:

- solo vs consensus vs debate vs synthesis;
- only 4 tasks: 2 high-CNTX and 2 low-CNTX;
- test whether high-CNTX tasks gain more from debate/synthesis.

---

## 10. Binding Decision Matrix

| Pilot result | Decision |
|---|---|
| `CNTX` predicts instability beyond direct influence and entropy | Promote to full RA-15 scaffold |
| Direct influence high, `CNTX` null | Pivot to prompt-architecture invariance paper |
| Entropy predicts instability better than `CNTX` | Fold into RA-14 dual-entropy safety |
| Conflict block raises direct influence only | Report as RA-11 P5 boundary note, no RA-15 launch |
| Parse failure / no robust signal | Archive pilot and do not spend full-experiment budget |

---

## 11. Threats to Validity

- **Binary reduction loss:** Enterprise decisions are richer than binary labels. This is acceptable for pilot math, but not for a full paper without categorical extension.
- **Direct influence dominance:** Prompt contexts will change marginals. CbD is chosen precisely to separate this from contextual residue.
- **Small n:** Eight tasks cannot support strong inferential claims. The pilot is only a gate.
- **Ontology snippet quality:** Conflict snippets must be pre-written and audited; otherwise the conflict block becomes uncontrolled prompt injection.
- **Model-specific behavior:** The two-endpoint check does not establish model-family generality.

---

## 12. Deliverables Before Execution

- [x] Pilot task list v0
- [x] Context matrix v0
- [x] Canonical ontology snippets for 8 tasks
- [x] Conflict snippets for 4 high-conflict tasks
- [x] Prompt templates
- [x] Phase 0 prompt renderer
- [x] JSON parser / validator
- [x] CbD smoke-summary implementation
- [x] CbD unit tests against five known contextual / noncontextual systems
- [x] Phase 0 smoke-test log
- [x] q1 measurement revision after Phase 0 ambiguity finding
- [x] Phase 0 rerun on revised q1 instrument
- [x] Phase 1 primary-local-model pilot output log

---

## 13. Stop Rule

This historical gate is resolved. RA-15 proceeds only as an exploratory
method / negative-results paper: all Phase 1.3 canonical contextuality
scores are zero, and the routing translation remains an unvalidated future
study. A positive contextuality result is not required for this paper.
