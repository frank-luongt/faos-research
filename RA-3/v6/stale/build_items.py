#!/usr/bin/env python3
"""Builds stale/items.json from the drafts below. Edit here, never the JSON.

Each draft names the current rule, the rule it superseded, two distractors, and
``evidence``: text the cell's ontology context must contain (see stale.validate).
Option letters are placed by a seeded shuffle balanced over the set.

Status: DRAFT. Written by Claude from the cell ontologies and the v5-to-v6
corrections on 2026-11-13. Every item needs a domain expert's confirmation
(status "confirmed") before it runs; ``check`` lists what to verify first.
The US items come from ``us_rules.py``. Their current rules are not in v5's US
ontologies, so this script also writes them into ``corrections.json`` as ``add``
edits (one regulation entry each) and one appended retrieval chunk per US
ontology, so C2b stays budget-matched (PI decision, 2026-11-13).

    python stale/build_items.py   (from RA-3/v6)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import corrections  # noqa: E402
import design  # noqa: E402
import stale  # noqa: E402
from us_rules import US_RULES  # noqa: E402

US_CELL = {"fintech": "fintech_us", "insurance": "insurance_us", "healthcare": "healthcare_us"}


def d(cell, question, current, superseded, distractors, effective, source, evidence, check=""):
    return dict(cell=cell, question=question, current=current, superseded=superseded,
                distractors=distractors, effective=effective, source=source, evidence=evidence, check=check)


DRAFTS = [
    # banking_vn
    d("banking_vn", "Under Vietnam's current AML rules, how soon must a bank file a suspicious transaction report?",
      "Within 3 working days of the transaction or of detecting it", "Within 48 hours of confirming the suspicion",
      ["Within 24 hours of the transaction", "Within 10 working days of the month end"],
      "2023-03-01", "Law 14/2022/QH15 on Anti-Money Laundering", "3_working_days"),
    d("banking_vn", "Which decree currently implements Vietnam's anti-money-laundering law for banks?",
      "Decree 19/2023/ND-CP", "Decree 116/2013/ND-CP", ["Decree 13/2023/ND-CP", "Decree 52/2024/ND-CP"],
      "2023-05-15", "Decree 19/2023/ND-CP", "19/2023", "effective date of Decree 19/2023"),
    d("banking_vn", "What is the large-value cash transaction reporting threshold for Vietnamese banks?",
      "VND 400 million", "VND 300 million", ["VND 200 million", "VND 1 billion"],
      "2023-07-15", "Decision 11/2023/QD-TTg", "VND 400,000,000", "effective date of Decision 11/2023"),
    d("banking_vn", "Which SBV circular governs loan classification and provisioning at Vietnamese banks?",
      "Circular 31/2024/TT-NHNN", "Circular 11/2021/TT-NHNN", ["Circular 39/2016/TT-NHNN", "Circular 22/2019/TT-NHNN"],
      "2024-07-01", "Circular 31/2024/TT-NHNN", "31/2024"),
    d("banking_vn", "Which law on credit institutions currently governs Vietnamese banks?",
      "Law 32/2024/QH15", "Law 47/2010/QH12", ["Law 14/2022/QH15", "Law 54/2019/QH14"],
      "2024-07-01", "Law 32/2024/QH15 on Credit Institutions", "Law 32/2024"),
    d("banking_vn", "In 2026, what is a Vietnamese bank's maximum credit exposure to a single customer?",
      "13% of the bank's equity", "15% of the bank's equity", ["10% of the bank's equity", "25% of the bank's equity"],
      "2024-07-01", "Law 32/2024/QH15, art. 136 and transition schedule", "13% of the bank's equity in 2026",
      "the 2026 step of the transition schedule"),
    d("banking_vn", "In 2026, what is a Vietnamese bank's maximum credit exposure to one customer and its related persons?",
      "21% of the bank's equity", "25% of the bank's equity", ["15% of the bank's equity", "30% of the bank's equity"],
      "2024-07-01", "Law 32/2024/QH15, art. 136 and transition schedule", "21% for a customer and related persons",
      "the 2026 step of the transition schedule"),
    d("banking_vn", "Which SBV circular now sets the rules for payment accounts and eKYC account opening?",
      "Circular 17/2024/TT-NHNN", "Circular 16/2020/TT-NHNN", ["Circular 40/2024/TT-NHNN", "Circular 64/2024/TT-NHNN"],
      "2024-07-01", "Circular 17/2024/TT-NHNN", "17/2024"),
    # insurance_vn
    d("insurance_vn", "Which law is Vietnam's primary insurance business law?",
      "Law 08/2022/QH15, effective 1 January 2023", "The 2000 Law on Insurance Business (amended 2010 and 2019)",
      ["Law 14/2022/QH15", "Law 51/2024/QH15"],
      "2023-01-01", "Law 08/2022/QH15 on Insurance Business", "Law 08/2022/QH15"),
    d("insurance_vn", "Which decree implements Vietnam's insurance business law on licensing, capital and solvency?",
      "Decree 46/2023/ND-CP", "Decree 73/2016/ND-CP", ["Decree 67/2023/ND-CP", "Decree 19/2023/ND-CP"],
      "2023-07-01", "Decree 46/2023/ND-CP", "46/2023", "effective date of Decree 46/2023"),
    d("insurance_vn", "Which decree now governs compulsory motor third-party liability and fire insurance in Vietnam?",
      "Decree 67/2023/ND-CP", "Decree 03/2021/ND-CP", ["Decree 46/2023/ND-CP", "Decree 13/2023/ND-CP"],
      "2023-09-06", "Decree 67/2023/ND-CP", "67/2023", "effective date; Decree 03/2021 as the motor predecessor"),
    d("insurance_vn", "How soon must a Vietnamese insurer file a suspicious transaction report?",
      "Within 3 working days", "Within 48 hours", ["Within 24 hours", "Within 15 working days"],
      "2023-03-01", "Law 14/2022/QH15 on Anti-Money Laundering", "STR_filing_3_working_days"),
    d("insurance_vn", "What legal status does microinsurance have in Vietnam?",
      "A formal framework in its own chapter of the insurance business law", "Pilot schemes only, with no framework in the insurance law",
      ["Banned for commercial insurers", "Allowed only for state-owned insurers"],
      "2023-01-01", "Law 08/2022/QH15, Chapter VII", "first formal legal framework"),
    d("insurance_vn", "How does Vietnam's insurance regulator supervise insurers under the current law?",
      "Risk-based supervision", "Rule-based compliance supervision", ["Self-regulation by the insurance association", "Supervision by the State Bank of Vietnam"],
      "2023-01-01", "Law 08/2022/QH15", "risk-based oversight"),
    # fintech_vn
    d("fintech_vn", "Which decree now governs non-cash payments and payment intermediaries in Vietnam?",
      "Decree 52/2024/ND-CP", "Decree 101/2012/ND-CP", ["Decree 94/2025/ND-CP", "Decree 13/2023/ND-CP"],
      "2024-07-01", "Decree 52/2024/ND-CP", "Decree 52/2024"),
    d("fintech_vn", "What cap applies to foreign ownership of a Vietnamese payment intermediary?",
      "49%", "No specific cap", ["30%", "100% after a licence"],
      "2024-07-01", "Decree 52/2024/ND-CP", "49%"),
    d("fintech_vn", "When must a Vietnamese bank customer pass biometric authentication for an online transfer?",
      "For a single transfer over VND 10 million, or once a day's total exceeds VND 20 million",
      "Never; an SMS OTP or soft token is enough at any amount",
      ["Only for transfers over VND 500 million", "For every online transfer"],
      "2024-07-01", "Decision 2345/QD-NHNN", "over VND 10 million"),
    d("fintech_vn", "Can a Vietnamese bank account or e-wallet that has not been verified against biometric data transact online?",
      "No, not since 1 January 2025", "Yes, with an OTP", ["Yes, up to VND 5 million a day", "Only for domestic payments"],
      "2025-01-01", "Circular 17/2024/TT-NHNN", "From 1 January 2025 accounts"),
    d("fintech_vn", "Is there a legal regulatory sandbox for banking fintech in Vietnam?",
      "Yes, under Decree 94/2025/ND-CP from 1 July 2025", "No; only a draft decree exists",
      ["Yes, under Decree 52/2024/ND-CP", "Only for securities firms"],
      "2025-07-01", "Decree 94/2025/ND-CP", "Decree 94/2025"),
    d("fintech_vn", "What is the main legal basis for personal data protection in Vietnam from 1 January 2026?",
      "The Law on Personal Data Protection, No. 91/2025/QH15", "Decree 13/2023/ND-CP alone, with no statute",
      ["The 2018 Law on Cybersecurity alone", "Circular 64/2024/TT-NHNN"],
      "2026-01-01", "Law 91/2025/QH15", "91/2025"),
    d("fintech_vn", "Is there a binding open-API standard for Vietnamese banks sharing data with third parties?",
      "Yes, Circular 64/2024/TT-NHNN", "No; open APIs are voluntary bank practice",
      ["Yes, Decree 13/2023/ND-CP", "Only for state-owned banks"],
      "2025-03-01", "Circular 64/2024/TT-NHNN", "Circular 64/2024", "effective date of Circular 64/2024"),
    d("fintech_vn", "From what cash amount must a Vietnamese payment provider report a large-value transaction?",
      "VND 400 million", "VND 300 million", ["VND 100 million", "VND 1 billion"],
      "2023-07-15", "Decision 11/2023/QD-TTg", "VND 400 million or more", "effective date of Decision 11/2023"),
    # healthcare_vn
    d("healthcare_vn", "Which law governs medical examination and treatment in Vietnam?",
      "Law 15/2023/QH15", "Law 40/2009/QH12", ["Law 51/2024/QH15", "Law 08/2022/QH15"],
      "2024-01-01", "Law 15/2023/QH15", "15/2023/QH15"),
    d("healthcare_vn", "How does Vietnamese law now classify medical facilities?",
      "Three technical levels: initial, basic and specialised", "Four administrative tiers: central, provincial, district and commune",
      ["Two levels: public and private", "Five grades by bed count"],
      "2024-01-01", "Law 15/2023/QH15", "initial, basic and specialised"),
    d("healthcare_vn", "Which decree guides Vietnam's current law on medical examination and treatment?",
      "Decree 96/2023/ND-CP", "Decree 109/2016/ND-CP", ["Decree 13/2023/ND-CP", "Decree 52/2024/ND-CP"],
      "2023-12-30", "Decree 96/2023/ND-CP", "Decree 96/2023", "effective date of Decree 96/2023"),
    d("healthcare_vn", "How must a Vietnamese hospital treat patients' health information as personal data?",
      "As sensitive personal data needing explicit consent under Decree 13/2023/ND-CP",
      "Under general privacy provisions only, with no personal data decree",
      ["As public data once anonymised by the hospital", "As state secrets under the Ministry of Health"],
      "2023-07-01", "Decree 13/2023/ND-CP", "Decree 13/2023/ND-CP"),
    # securities_vn
    d("securities_vn", "Must a foreign institutional investor pre-fund a share purchase on Vietnam's exchanges?",
      "No, not since November 2024", "Yes, the full amount before the order", ["Yes, 50% before the order", "Only for orders over VND 10 billion"],
      "2024-11-02", "Circular 68/2024/TT-BTC", "without pre-funding", "effective date of Circular 68/2024"),
    d("securities_vn", "How soon must a Vietnamese securities firm report a suspicious transaction?",
      "Within 3 working days of detection", "Within 48 hours of confirmation", ["Within 24 hours", "At the next quarterly report"],
      "2023-03-01", "Law 14/2022/QH15 on Anti-Money Laundering", "within 3 working days of detection"),
    d("banking_vn", "What must a Vietnamese bank check when a customer opens an account online by eKYC?",
      "The chip-based citizen ID, with a biometric match to the chip data", "Any photo ID, with a video call",
      ["A paper ID copy sent by post", "Only the customer's mobile number"],
      "2024-07-01", "Circular 17/2024/TT-NHNN and Decision 2345/QD-NHNN", "biometric_verification_against_chip_ID"),
    # accounting_vn
    d("accounting_vn", "Can a Vietnamese business still issue paper invoices for its sales?",
      "No; electronic invoices are mandatory nationwide since 1 July 2022", "Yes; paper invoices remain allowed alongside e-invoices",
      ["Only businesses with revenue under VND 3 billion", "Only for exports"],
      "2022-07-01", "Decree 123/2020/ND-CP", "from 1 July 2022"),
]


def sync_us_corrections() -> int:
    """Rewrite the US-... add/append edits in corrections.json from US_RULES; returns how many."""
    data = corrections.load()
    onto = data["ontologies"]
    for stem in list(onto):
        onto[stem] = [e for e in onto[stem] if not e["id"].startswith("US-")]
        if not onto[stem]:
            del onto[stem]
    n, chunks = 0, {}
    for rule in US_RULES:
        if not rule["rule"]:  # already stated in the ontology
            continue
        n += 1
        onto.setdefault(rule["stem"], []).append({
            "id": f"US-{n:02d}", "op": "add", "path": ["domain_layer", "regulations", rule["key"]], "v5": None,
            "v6": {"name": rule["name"], "rule": rule["rule"]},
            "why": f"Current US rule (effective {rule['effective']}) for the stale-knowledge set; draft, to be confirmed by the US expert.",
        })
        chunks.setdefault(rule["stem"], []).append(f"{rule['name']}: {rule['rule']}.")
    for stem, sentences in chunks.items():
        n += 1
        with open(design.ONTOLOGY_DIR / f"{stem}.json") as f:
            has_v6 = "rag_chunks_v6" in json.load(f)
        text = "Recent US rule changes. " + " ".join(sentences)
        onto[stem].append({
            "id": f"US-{n:02d}", "op": "append" if has_v6 else "add",
            "path": ["rag_chunks_v6"], "v5": None, "v6": text if has_v6 else [text],
            "why": "Retrieval text restating the added US rules, so C2b carries the same facts as C3.",
        })
    data["status"] = ("draft corrections and US rule additions, to be confirmed by the Vietnam banking and "
                      "insurance experts and the US experts before lock")
    with open(corrections.CORRECTIONS_FILE, "w") as f:
        f.write(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    return n


def drafts() -> list[dict]:
    us = [d(US_CELL.get(r_["stem"], r_["stem"]), r_["question"], r_["current"], r_["superseded"], r_["distractors"],
            r_["effective"], r_["name"] or "already in the ontology", r_["evidence"], r_["check"]) for r_ in US_RULES]
    return DRAFTS + us


def build() -> list[dict]:
    rng = design._rng("stale-items")
    all_drafts = drafts()
    n = len(all_drafts)
    answers = [("ABCD" * n)[i] for i in range(n)]
    offsets = [(1, 2, 3)[i % 3] for i in range(n)]
    rng.shuffle(answers)
    rng.shuffle(offsets)
    counter, items = {}, []
    for dr, a, off in zip(all_drafts, answers, offsets):
        letters = "ABCD"
        s = letters[(letters.index(a) + off) % 4]
        rest = [x for x in letters if x not in (a, s)]
        options = {a: dr["current"], s: dr["superseded"], rest[0]: dr["distractors"][0], rest[1]: dr["distractors"][1]}
        counter[dr["cell"]] = counter.get(dr["cell"], 0) + 1
        items.append({
            "id": f"{dr['cell']}_S{counter[dr['cell']]:02d}", "cell": dr["cell"], "question": dr["question"],
            "options": dict(sorted(options.items())), "answer": a, "superseded": s,
            "effective": dr["effective"], "source": dr["source"], "evidence": dr["evidence"],
            "check": dr["check"], "status": "draft",
        })
    return items


def main() -> int:
    print(f"{sync_us_corrections()} US edits -> {corrections.CORRECTIONS_FILE.name}")
    corrections.write_diff()
    items = build()
    probe_q = set()
    for cell in design.CELLS:
        with open(design.PROBE_DIR / f"{cell}.json") as f:
            probe_q |= {i["question"].strip().lower() for i in json.load(f)}
    clash = [i["id"] for i in items if i["question"].strip().lower() in probe_q]
    problems = stale.validate(items, complete=False) + [f"{c}: repeats a probe question" for c in clash]
    for p in problems:
        print(f"[problem] {p}")
    stale.ITEMS_FILE.write_text(json.dumps(items, indent=1, ensure_ascii=False) + "\n")
    print(f"{len(items)} items -> {stale.ITEMS_FILE}")
    print("full-set check:", "; ".join(stale.validate(items)) or "ok")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
