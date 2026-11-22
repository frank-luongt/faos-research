# Stage-2 probe tags

Each `<cell>.json` maps every probe item id to the ontology entry it tests, as a dotted path into the cell's ontology after `corrections.json` is applied (for example `domain_layer.concepts.cet1_ratio`), or to `null`. `gating.py` reads these files to build C3g contexts (protocol H9).

**Tagging rule (2026-11-22).** An item is tagged to an entry only if the entry's own text states the fact the item's correct answer depends on, so that removing the entry from the context really removes that fact. Entries are taken at the granularity `gating.py` removes: `domain_layer.concepts.*`, `domain_layer.regulations.*`, `role_layer.<role>.kpis.*` and `role_layer.<role>.domain_knowledge.*`. Where a fact sits in both a domain entry and a role KPI, the domain entry is used. An item is `null` when the ontology does not state its answer (for example a fact the probe tests that the ontology only names, or does not mention). Decision patterns and interaction-layer hand-offs are never tagged, as the protocol fixes.

The tags were written by one coder (Claude, from a lexical first pass reviewed item by item) before any probe run. A second coder should spot-check a sample before lock.

**Result.** An entry is gateable only with at least two tagged items:

| Cell | Tagged items | Gateable entries | Largest possible C3 cut |
| --- | --- | --- | --- |
| banking_us | 51 | 15 | 32% |
| banking_vn | 26 | 8 | 21% |
| insurance_us | 5 | 1 | 3% |
| insurance_vn | 27 | 9 | 26% |
| healthcare_us | 5 | 1 | 1% |
| healthcare_vn | 48 | 12 | 32% |
| securities_us | 33 | 10 | 21% |
| securities_vn | 43 | 11 | 28% |
| fintech_us | 4 | 0 | 0% |
| fintech_vn | 43 | 11 | 33% |
| accounting_us | 60 | 17 | 36% |
| accounting_vn | 51 | 17 | 41% |

"Largest possible C3 cut" is the mean context reduction if a model knew every gateable entry. Over all 12 cells it is 23%, against H9's requirement that gated contexts be at least 10% shorter on average. In the three v5 US cells (insurance, healthcare, fintech), the v5 ontologies are thin and the probe mostly tests facts they do not state, so C3g is almost the same as C3 there.
