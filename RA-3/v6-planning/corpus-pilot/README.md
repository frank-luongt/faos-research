# RA-3 v6 corpus construction pilot

Prepared 7 November 2026. This package scopes the original six domains across US, Vietnam and Singapore and supplies three draft banking tasks. It contains no experiment outputs and is not a qualified or locked corpus.

`corpus.json` is the authored source of truth: 18 proposed cell boundaries, four official-source retrieval records, three source-bound fact records, three tasks and zero probes. `scope-register.csv` and `fact-register.csv` are review copies. The remaining 15 cells have proposed scopes only. New York is the proposed US insurance subjurisdiction; it is not a nationwide insurance-law claim. Product and actor matching across countries still needs domain review.

## Evidence and temporal scope

The four linked sources are an OCC explanation, a Vietnamese government explanation of Decision 32/2021/QD-TTg, an SDIC consumer guide and SDIC Circular-01/2024. Relevant webpage/PDF text was retrieved. `evidence/*.md` contains short, agent-authored paraphrases and retrieval limitations. SHA-256 values bind those notes, **not the original webpages or PDF bytes**. `archive_sha256` is null throughout. Retrieval date does not establish legal currency, and null effective-end dates mean unknown, not indefinite validity.

The Vietnamese signed decision was located but not directly inspected: text extraction was empty and screenshot results contained placeholders only. The government explanation remains the cited support. Some FDIC and Singapore statutory pages returned access errors. These facts are draft content requiring source-version and applicability review; no independent expert has approved them.

Each example is explicitly tied to its cited source version. None claims to describe all law in force on 7 November 2026. Source/version pinning will also need to be made comparable across cells before the study measures jurisdiction-associated knowledge differences.

## Eligibility and leakage

The banking prompts ask for a cap, combined balance, covered amount and amount above the cap. Reference calculations are explicit. MA eligibility is a **candidate authoring judgment**, not validated measurement. TF, RC and RS remain ineligible because their required reference/rubric evidence is absent. Consequently **zero tasks meet the planned joint MA/RS primary-task requirement**. Adding a role name to a prompt would not establish RS eligibility.

The legacy MA rubric divides correct metric references by references made. It does not measure completion of all requested answers. No-reference responses, abstention and omissions still require a frozen policy. `normalize_scores` accepts already-assigned scores; it does not implement a judge or silently replace that rubric. It keeps legitimate zero separate from null for ineligibility, judge failure, generation failure or undefined denominators. Analysis must preserve assigned task denominators and use the protocol's eventual missing-outcome treatment; this function does not authorize complete-case averages.

All three banking facts share `deposit-insurance-aggregation-and-cap`. They are related country variants, not independent topic families. They are reserved for outcome tasks; the family must not also appear in closed-book probes. The validator checks declared families globally. It cannot detect an author assigning misleading family labels, and zero existing probes is **not evidence of probe independence**.

## Offline checks

From this directory:

```sh
python contract.py
python -m unittest discover -s . -p 'test_*.py' -v
```

The standard-library checks cover source-note integrity, cell/fact bindings, eligibility references and task/probe family overlap. Eleven local regression tests additionally exercise actual zero vs unscored values, missing/invalid judge scores and account-aggregation reference calculations. They are local verification, not CI coverage or human content validation. `validation.json` records the structural result.

No legacy task, scorer, ontology or analysis is changed. No API key, model call, provider spend or recruitment is involved.

## Next construction step

Author source-backed provider-administration tasks for healthcare in all three jurisdictions, with explicit actor and instrument dates. In parallel within corpus authoring, define a defensible RS reference for the banking tasks and resolve MA omission/denominator policy. Build probes from different factual families only after those allocations are recorded. Expand beyond six domains only after source and dependence feasibility are demonstrated.
