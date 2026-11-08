# RA-3 v6 corpus construction: batch 2

This is the current **draft authoring snapshot**, additive to the preserved `corpus-pilot` checkpoint. It contains six active tasks: three revised banking tasks and three new healthcare tasks across US, Vietnam and Singapore. The banking originals are superseded within this snapshot; do not concatenate both batches and count nine tasks.

`corpus.json` contains 18 proposed cell scopes, eight source records, six facts, six tasks, one fictional banking role policy/profile and zero probes. Four source notes are preserved byte-for-byte from batch 1; four new retrieval notes document HHS, PDPC, the Vietnamese government law reproduction and O*NET. Hashes bind notes, not original source archives. No current-law certification or independent content review is claimed.

Healthcare tasks distinguish the US action/conditional-extension rule, Singapore's notification requirement and Vietnam's archived-record access rights. The Vietnamese clauses reviewed supply no numeric deadline, so its task has no MA key. That is an evidence boundary, not a claim that no deadline exists in Vietnamese law. Singapore is restricted to a private clinic subject to PDPA; US state overlays and Vietnamese implementing provisions remain outside the selected examples. All are administrative cases, not diagnosis or treatment tasks.

Three banking revisions have candidate MA and RS references. US/Singapore healthcare have candidate MA and RC references; Vietnam healthcare has candidate RC only. No healthcare task yet has an RS profile. Thus three tasks have joint MA/RS authoring eligibility, while **zero tasks have independent review and zero cells are launch-ready**. Role policy provenance and the limits of precision scoring are detailed in `SCORING-POLICY.md`.

The two factual families (deposit-insurance aggregation and patient-record access) remain task-only. No probe bank has been authored. O*NET duties and the shared role policy must also be excluded from future knowledge probes; they are common scenario information, not independent coverage evidence. Family tags cannot establish statistical independence or equal task difficulty across countries.

Run offline from this directory:

```sh
python validate.py
python -m unittest discover -s . -p 'test_*.py' -v
```

The validator imports the preserved first-batch contract and checks the parent corpus hash, provenance, role anchors, common context and revision identity. Twelve local tests cover scoring/missingness behavior and important corpus regressions. `validation.json` is the structural summary, not model performance or CI coverage. No model, judge, provider or expert was contacted.

Next: prepare a small review packet for these six tasks before multiplying templates, with separate source/applicability, translation, scoring and role-validity questions. Draft genuinely different probe families and resolve the lack of MA/RS comparability in healthcare before making a balanced six-domain study claim. The remaining four domains have scope proposals only.
