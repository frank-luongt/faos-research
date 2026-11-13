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
| `forecast.py` | Registered forecasts (protocol H7). Writes one predicted lift per cell × model from the probe before any grounded run and prints the file's SHA-256; after the runs it scores calibration and runs the leave-one-industry-out test. |
| `stale.py` / `run_stale.py` | Stale-knowledge arm (protocol H8). Validates the item set in `stale/items.json` (30 per country, at least four industries each, the current value stated in the cell's ontology context), runs each item closed-book and grounded, and runs the H8 test with `--analyse`. Items must be expert-confirmed before they run. |
| `gating.py` | Stage 2, coverage-gated grounding (protocol H9). Checks the probe-item tags in `probe/tags/<cell>.json`, applies the gating rule (an entry is known if at least two tagged items are all correct; decision patterns and hand-offs never gated), and with `--addendum` registers each gated context's hash before any C3g run. `run_agents.py --stage2` then runs the 792 C3g runs. |
| `run_agents.py` | The agent runs. Output is append-only JSONL, and a rerun resumes where it stopped. |
| `run_judges.py` | Two cross-family judges per response, using v5's rubrics. No judge scores its own family. |
| `freeze_assignments.py` | Writes `assignments/judge_pairs.json` and `assignments/repeats.json` at lock, to be hashed. |
| `smoke_test.py` | Makes one call to every pinned model to confirm IDs, routing and prices before lock. |
| `tests/test_forecast.py` | Offline checks of the forecast line, the stable hash and the H7 test on synthetic lifts. |
| `tests/test_stale.py` | Offline checks of the stale-set validator and the H8 test on synthetic answers. |
| `tests/test_gating.py` | Offline checks of the gating rule, the gate and the C3g prompt. |
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
python forecast.py                                # after the probe, before any grounded run
OPENROUTER_API_KEY=... python run_stale.py       # 720 calls, once the items are confirmed
python gating.py --addendum                       # stage 2: after the probe, before any C3g run
OPENROUTER_API_KEY=... python run_agents.py --stage2   # 792 C3g runs
```

## Study materials (draft, awaiting expert review)

All 12 cells now have their materials:

- `../ontology_context/<cell>.json`: one ontology per cell (v5's five files keep their v5 names: `fintech`, `insurance`, `healthcare`, `banking_vn`, `insurance_vn`).
- `tasks_v6.json`: 120 tasks, 10 per cell in v5's mix. v5's 50 tasks are reused unchanged for their five cells; the 70 new tasks live in `pilot/tasks_<cell>.json`. Rebuild with `python build_tasks.py`.
- `probe/<cell>.json`: 90 multiple-choice items per cell (1,080 in all), each with a seeded, balanced answer key. No probe item repeats a task question, though some test facts the tasks also use.
- **RAG corpora.** C2b fills each task's C3 budget from the cell's retrieval text. The largest shortfall over all 120 tasks is 195 characters. v5's five cells keep their v5 `rag_chunks` byte for byte, so v5's C2 prompts still rebuild. Their extra v6 text is in `rag_chunks_v6`, which restates the cell's own ontology as prose and adds no new facts.

Where current law superseded v5 content, v6 applies `corrections.json` on load, leaving v5's files untouched. `V5-TO-V6-DIFF.md` lists every edit.

`EXPERT-CHECK.md` lists the facts most likely to need correction, as well as v5 ground truth that looks out of date. Those facts should be verified by the domain experts before lock.

## Still to build before lock

- **Stale-knowledge set.** 60 draft items in `stale/items.json` (30 per country) and 28 draft US rule additions in `corrections.json`; experts confirm both (see `EXPERT-CHECK.md`), then mark items `confirmed`.
- **Probe tags for stage 2.** Tag each probe item to the ontology entry it tests in `probe/tags/<cell>.json`; `python gating.py` reports progress. If tagging is incomplete at lock, stage 2 is dropped.
- **v5 corrections.** Experts confirm the draft corrections in `corrections.json` (listed in `V5-TO-V6-DIFF.md`); rerun `python corrections.py` and `python build_tasks.py` after any edit.
- **Jev adapter.** Jev answers typed questions with probabilities rather than writing text. Its request format is confirmed by the smoke test before its adapter is written.
- **Settings to decide at lock** (see `settle_at_lock` in `models.lock.json`): reasoning effort, the provider order for each model, and the provider fallback policy.
