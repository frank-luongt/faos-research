# RA-3 v6 run harness

This harness runs the pre-registered RA-3 v6 study: 6 industries × 2 jurisdictions (US, Vietnam) = 12 cells, 3 conditions, and 6 models. The protocol lives in Foundation-AgenticOS at `research-academic/papers/RA-3-Neurosymbolic-Enterprise-AI/RA-3-V6-STUDY-PROTOCOL-DRAFT-2026-10-31.md`.

**Status: pre-lock skeleton.** Nothing has been run. The protocol is locked with a SHA-256 hash only after the PI approves it, and the lock also pins this harness's commit.

## Layout

| File | What it does |
| --- | --- |
| `models.lock.json` | The six agent models, three panel judges and Jev, all pinned to exact OpenRouter IDs with their prices (retrieved 2026-11-12). Its status is `draft-pin` until lock. |
| `design.py` | Cells, conditions, the run matrix (2,160 primary runs plus 216 seeded repeats), the seeded judge-pair rotation and task-set validation. |
| `conditions_v6.py` | C1 and C3 use v5's prompt builders unchanged. C2b is RAG trimmed to the same character budget as the task's C3 context, and any shortfall is logged. |
| `openrouter_client.py` | Stdlib OpenRouter client. Every call records the served model, the routed provider and the usage. |
| `run_probe.py` / `coverage.py` | The 90-item closed-book probe for each cell and model, and coverage computed as probe accuracy. Coverage is never computed from C1 scores. |
| `run_agents.py` | The agent runs. Output is append-only JSONL, and a rerun resumes where it stopped. |
| `run_judges.py` | Two cross-family judges per response, using v5's rubrics. No judge scores its own family. |
| `freeze_assignments.py` | Writes `assignments/judge_pairs.json` and `assignments/repeats.json` at lock, to be hashed. |
| `smoke_test.py` | Makes one call to every pinned model to confirm IDs, routing and prices before lock. |
| `tests/test_design.py` | Offline checks: protocol call counts, no self-judging, balanced rotation, and the C2b budget. |
| `power/` | The four power simulations (1–10 Nov 2026) and their outputs. `power_sim_v4.py` is the adopted US+VN design. |

Run logs go to `results/`, which is gitignored. They are released with the paper under the Data Availability policy.

## Commands (from `RA-3/v6`)

```bash
python tests/test_design.py                       # offline, no key
python run_agents.py --dry-run --v5-tasks         # prompt sizes on v5's tasks
OPENROUTER_API_KEY=... python smoke_test.py       # ~7 tiny calls
OPENROUTER_API_KEY=... python run_probe.py        # 6,480 calls
OPENROUTER_API_KEY=... python run_agents.py       # ~2,376 calls
OPENROUTER_API_KEY=... python run_judges.py       # ~4,752 calls
python coverage.py
```

## Pilot cell: accounting_us (draft, awaiting review)

US Accounting is the first cell written in full, as a pattern for the other new cells. It has three parts:

- `../ontology_context/accounting_us.json`: Controller, Chief Audit Executive and Tax Director roles; concepts from ASC 606, 842, 326, 350, 330, 450, 820 and 740; and SOX, PCAOB and SEC rules. Its RAG corpus is about 8,800 characters, so C2b matches C3 to within 41 characters.
- `pilot/tasks_accounting_us.json`: 10 tasks in v5's mix and schema. They merge into `tasks_v6.json` once reviewed.
- `probe/accounting_us.json`: 90 multiple-choice items with a seeded, balanced answer key.

The facts were written from the standards and SEC rules as of November 2026. A US accounting expert should check them before lock.

## Still to build before lock

- **Materials.** These are still to write:
  - `tasks_v6.json`: 120 tasks with 10 per cell in v5's mix. v5's 50 tasks are reused for their five cells.
  - `probe/<cell>.json`: 90 items per cell, 1,080 in all.
  - The missing ontology files: `banking_us`, `healthcare_vn`, `securities_us`, `securities_vn`, `fintech_vn`, `accounting_us` and `accounting_vn`.
- **RAG corpora.** v5's `rag_chunks` hold only about 2,200–2,700 characters, so the dry run shows every C2b prompt falling short of its C3 budget (by up to about 4,400 characters). Each cell needs a retrieval corpus of at least the C3 context size (about 7,500 characters) for C2b to be budget-matched.
- **Jev adapter.** Jev answers typed questions with probabilities rather than writing text. Its request format is confirmed by the smoke test before its adapter is written.
- **Settings to decide at lock** (see `settle_at_lock` in `models.lock.json`): reasoning effort, the provider order for each model, and the provider fallback policy.
