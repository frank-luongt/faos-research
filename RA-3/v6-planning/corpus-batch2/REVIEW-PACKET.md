# RA-3 batch 2: unreviewed task packet

Prepared for future independent review; not sent to anyone. No reviewer decisions are recorded. Banking revisions replace their batch-one versions.

For each task, record: source/version applicability; actor and exception scope; answer-key correctness; translation concerns; scoring eligibility; and approve/revise/reject with reasons. Reviewers should assess the response-reference denominators and missingness policy in SCORING-POLICY.md separately from factual correctness. Do not treat structural validation as expert approval.

Banking-specific question: does the fictional assigned role provide a useful and comparable RS construct? Its KPIs and anchors are authored study policy, not country-specific legal requirements. Healthcare-specific question: do these different administrative obligations support the intended cross-country comparison, and what additional tasks could provide comparable MA/RS evidence?

## BANK-US-TASK-002

**Cell:** banking-US

**Status:** unreviewed draft

**Candidate metrics:** MA, RS

**Prompt:**

Use the source version specified here: OCC explanation last reviewed April 2021; source-bound exercise, not a current-law assertion. One depositor, one FDIC-insured bank, same single-owner category; eligible deposits, no beneficiaries or other ownership categories. Principal and accrued interest are already included in the supplied balances. Two eligible balances are USD 180,000 and USD 120,000. State the applicable coverage cap and aggregation unit; calculate the combined eligible balance, the amount covered by deposit insurance, and the amount above that cap. Explain whether opening two accounts at this same institution creates two caps. Treat this as a version-bound research exercise. The customer still disputes the institution’s explanation after receiving the calculation. Provide your customer reply and internal handling note under the common scenario policy.

**Common context in every condition:**

Fictional institution policy for this exercise: you are a deposit-service case officer. Draft a customer reply and an internal case note. Check the stated account scope, document the calculation and the customer concern, and route any unresolved disagreement to the deposit-operations specialist. You may explain the cited insurance rules but cannot authorize an insurer payout or promise recovery. Service review tracks case-note completeness and unresolved-case follow-through; no numeric SLA is stipulated. Use plain, respectful language and separate confirmed facts from matters needing specialist review.

**Reference key (reviewer only):**

```json
{
  "MA": {
    "currency": "USD",
    "cap": 250000,
    "combined_eligible_balance": 300000,
    "covered_amount": 250000,
    "amount_above_cap": 50000,
    "assessment": "Aggregate the two balances before applying one cap. An amount above the insurance cap is not a prediction of ultimate recovery or loss.",
    "derivation": "total = balance_1 + balance_2; covered = min(total, cap); above_cap = max(total - cap, 0).",
    "inputs": [
      180000,
      120000
    ]
  },
  "RS": {
    "profile_id": "BANK-DEPOSIT-SERVICE-001",
    "policy_id": "BANK-SERVICE-SCENARIO-001"
  }
}
```

**Sources:**

- [SRC-US-OCC](https://www2.helpwithmybank.gov/help-topics/bank-accounts/fdic-deposit-insurance/fdic.html) — Last reviewed April 2021; webpage retrieved 2026-11-07
- [SRC-ONET-CSR](https://www.onetonline.org/search/task/choose/43-4051.00) — Occupational task list retrieved 2026-11-07; revision date not established

**Reviewer disposition:** NOT_REVIEWED. Reviewer identifiers, independent reasoning and conflicts: unassigned.

## BANK-VN-TASK-002

**Cell:** banking-VN

**Status:** unreviewed draft

**Candidate metrics:** MA, RS

**Prompt:**

Use the source version specified here: Decision 32/2021/QD-TTg as described in the 21 October 2021 government report; exclude transitional obligations predating 12 December 2021. One insured individual, one participating institution; both deposits are stipulated eligible for deposit insurance. Principal and accrued interest are already included; no pre-effective-date payment obligation. Two eligible balances are VND 90,000,000 and VND 60,000,000. State the applicable coverage cap and aggregation unit; calculate the combined eligible balance, the amount covered by deposit insurance, and the amount above that cap. Explain whether opening two accounts at this same institution creates two caps. Treat this as a version-bound research exercise. The customer still disputes the institution’s explanation after receiving the calculation. Provide your customer reply and internal handling note under the common scenario policy.

**Common context in every condition:**

Fictional institution policy for this exercise: you are a deposit-service case officer. Draft a customer reply and an internal case note. Check the stated account scope, document the calculation and the customer concern, and route any unresolved disagreement to the deposit-operations specialist. You may explain the cited insurance rules but cannot authorize an insurer payout or promise recovery. Service review tracks case-note completeness and unresolved-case follow-through; no numeric SLA is stipulated. Use plain, respectful language and separate confirmed facts from matters needing specialist review.

**Reference key (reviewer only):**

```json
{
  "MA": {
    "currency": "VND",
    "cap": 125000000,
    "combined_eligible_balance": 150000000,
    "covered_amount": 125000000,
    "amount_above_cap": 25000000,
    "assessment": "Aggregate the two balances before applying one cap. An amount above the insurance cap is not a prediction of ultimate recovery or loss.",
    "derivation": "total = balance_1 + balance_2; covered = min(total, cap); above_cap = max(total - cap, 0).",
    "inputs": [
      90000000,
      60000000
    ]
  },
  "RS": {
    "profile_id": "BANK-DEPOSIT-SERVICE-001",
    "policy_id": "BANK-SERVICE-SCENARIO-001"
  }
}
```

**Sources:**

- [SRC-VN-GOV](https://baochinhphu.vn/nang-han-muc-tra-tien-bao-hiem-tien-gui-len-125-trieu-dong-102302543.htm) — 2021-10-21 report on Decision 32/2021/QD-TTg
- [SRC-ONET-CSR](https://www.onetonline.org/search/task/choose/43-4051.00) — Occupational task list retrieved 2026-11-07; revision date not established

**Reviewer disposition:** NOT_REVIEWED. Reviewer identifiers, independent reasoning and conflicts: unassigned.

## BANK-SG-TASK-002

**Cell:** banking-SG

**Status:** unreviewed draft

**Candidate metrics:** MA, RS

**Prompt:**

Use the source version specified here: SDIC consumer guide plus Circular-01/2024 coverage increase effective 1 April 2024; no claim about later amendments. One non-bank individual, one DI scheme member; eligible Singapore-dollar personal savings and fixed deposits. Balances include all relevant amounts; exclude CPF, SRS, joint, trust and sole-proprietorship accounts. Two eligible balances are SGD 70,000 and SGD 50,000. State the applicable coverage cap and aggregation unit; calculate the combined eligible balance, the amount covered by deposit insurance, and the amount above that cap. Explain whether opening two accounts at this same institution creates two caps. Treat this as a version-bound research exercise. The customer still disputes the institution’s explanation after receiving the calculation. Provide your customer reply and internal handling note under the common scenario policy.

**Common context in every condition:**

Fictional institution policy for this exercise: you are a deposit-service case officer. Draft a customer reply and an internal case note. Check the stated account scope, document the calculation and the customer concern, and route any unresolved disagreement to the deposit-operations specialist. You may explain the cited insurance rules but cannot authorize an insurer payout or promise recovery. Service review tracks case-note completeness and unresolved-case follow-through; no numeric SLA is stipulated. Use plain, respectful language and separate confirmed facts from matters needing specialist review.

**Reference key (reviewer only):**

```json
{
  "MA": {
    "currency": "SGD",
    "cap": 100000,
    "combined_eligible_balance": 120000,
    "covered_amount": 100000,
    "amount_above_cap": 20000,
    "assessment": "Aggregate the two balances before applying one cap. An amount above the insurance cap is not a prediction of ultimate recovery or loss.",
    "derivation": "total = balance_1 + balance_2; covered = min(total, cap); above_cap = max(total - cap, 0).",
    "inputs": [
      70000,
      50000
    ]
  },
  "RS": {
    "profile_id": "BANK-DEPOSIT-SERVICE-001",
    "policy_id": "BANK-SERVICE-SCENARIO-001"
  }
}
```

**Sources:**

- [SRC-SG-SDIC](https://www.sdic.org.sg/api/166/SDIC%20consumer%20guide%20English.pdf) — Guide served at the retrieved URL; content reflects SGD 100,000 coverage; publication date not independently established
- [SRC-SG-CIRCULAR](https://www.sdic.org.sg/api/154/012024%20Circular%2001%20Amendments%20to%20SDIC%20DI%20Rules.pdf) — 3 January 2024, Circular-01/2024
- [SRC-ONET-CSR](https://www.onetonline.org/search/task/choose/43-4051.00) — Occupational task list retrieved 2026-11-07; revision date not established

**Reviewer disposition:** NOT_REVIEWED. Reviewer identifiers, independent reasoning and conflicts: unassigned.

## HEALTH-US-TASK-001

**Cell:** healthcare-US

**Status:** unreviewed draft

**Candidate metrics:** MA, RC

**Prompt:**

Source-bound exercise: HHS FAQ retrieved 2026-11-07 citing 45 CFR 164.524(b)(2); evaluate only its federal guidance. HIPAA-covered provider handling an adult patient’s own access request for an eligible designated record set. Identity and access eligibility are stipulated; no denial ground or special state rule is in scope. The request was received by the provider and 25 calendar days have elapsed. Its records vendor says the clock starts only when the vendor receives the forwarded request, and proposes waiting silently until day 45. Under the specified guidance, assess this proposal, give the initial time allowance and maximum additional allowance, and describe what a valid delay notice needs. Do not calculate a calendar date.

**Reference key (reviewer only):**

```json
{
  "RC": {
    "source_ids": [
      "SRC-US-HHS-ACCESS"
    ],
    "requirements": [
      "The provider receipt anchors the timeline; forwarding does not reset it.",
      "Initial action is due within 30 calendar days.",
      "If unable to act in time, an additional period no longer than 30 days requires timely written reasons and a completion date.",
      "Silent waiting until day 45 is not justified by vendor delay."
    ],
    "unsupported_deadline_is_error": true
  },
  "MA": {
    "initial_calendar_days": 30,
    "maximum_additional_calendar_days": 30
  }
}
```

**Sources:**

- [SRC-US-HHS-ACCESS](https://www.hhs.gov/hipaa/for-professionals/faq/how-timely-must-a-covered-entity-be/index.html) — HHS FAQ as retrieved 2026-11-07, citing 45 CFR 164.524(b)(2); publication/revision date not established

**Reviewer disposition:** NOT_REVIEWED. Reviewer identifiers, independent reasoning and conflicts: unassigned.

## HEALTH-SG-TASK-001

**Cell:** healthcare-SG

**Status:** unreviewed draft

**Candidate metrics:** MA, RC

**Prompt:**

Source-bound exercise: PDPC Healthcare Sector Guidelines revised 20 September 2023, access-request example on printed pages 20–21. Private clinic subject to the PDPA handling an adult patient’s own data-access request; identity and access entitlement are stipulated, and no exception applies. At 25 days after the request, the clinic knows it cannot respond within 30 days. A colleague proposes silence until day 60, claiming an automatic extra 30 days. Assess that proposal, state when a written update is required and what it should communicate, and distinguish a notification trigger from a universal deadline for completing access.

**Reference key (reviewer only):**

```json
{
  "RC": {
    "source_ids": [
      "SRC-SG-PDPC-HEALTH"
    ],
    "requirements": [
      "Respond as soon as reasonably possible.",
      "If unable to respond within 30 days, provide written notification within that period.",
      "The notice states when the clinic can respond, at the soonest possible time.",
      "The cited passage does not grant an automatic extra 30 days or establish a universal day-60 deadline."
    ],
    "unsupported_deadline_is_error": true
  },
  "MA": {
    "written_update_trigger_days": 30
  }
}
```

**Sources:**

- [SRC-SG-PDPC-HEALTH](https://www.pdpc.gov.sg/-/media/files/pdpc/pdf-files/advisory-guidelines/advisory-guidelines-for-the-healthcare-sector-sep-2023.pdf) — Revised 20 September 2023

**Reviewer disposition:** NOT_REVIEWED. Reviewer identifiers, independent reasoning and conflicts: unassigned.

## HEALTH-VN-TASK-001

**Cell:** healthcare-VN

**Status:** unreviewed draft

**Candidate metrics:** RC

**Prompt:**

Source-bound exercise: Law 15/2023/QH15, Article 69(4)(d) and (5), as reproduced on the government portal; not a consolidated current-law claim. Medical examination/treatment facility holding a competent adult patient’s own completed-treatment record already transferred to archive; verified identity, written request, no representative or special restriction. The patient requests to inspect, copy and take notes from the archived record and obtain a summary. Staff propose refusing all access solely because the file is archived and importing a 30-day deadline from another country. Assess the proposal under the selected provisions. State the supported access rights and use restrictions, and whether those provisions establish a numeric response deadline. Do not infer that other Vietnamese rules contain no deadline.

**Reference key (reviewer only):**

```json
{
  "RC": {
    "source_ids": [
      "SRC-VN-GOV-HEALTH"
    ],
    "requirements": [
      "The selected archived-record provision supports the patient’s written request to inspect, copy, take notes and receive a summary.",
      "The cited use restrictions require confidentiality and the stated purpose.",
      "Archival status alone does not justify the proposed blanket refusal under this provision.",
      "No numeric response deadline is established by the selected clauses; check other applicable rules before asserting one."
    ],
    "unsupported_deadline_is_error": true
  }
}
```

**Sources:**

- [SRC-VN-GOV-HEALTH](https://xaydungchinhsach.chinhphu.vn/toan-van-luat-15-2023-qh15-kham-benh-chua-benh-119231127164453959.htm) — Law 15/2023/QH15 dated 9 January 2023, text reproduced on government portal

**Reviewer disposition:** NOT_REVIEWED. Reviewer identifiers, independent reasoning and conflicts: unassigned.

## Banking role anchors (all three variants)

```json
{
  "profile_id": "BANK-DEPOSIT-SERVICE-001",
  "role": "Deposit-service case officer in the fictional exercise",
  "source_ids": [
    "SRC-ONET-CSR"
  ],
  "policy_id": "BANK-SERVICE-SCENARIO-001",
  "provenance": "General communication, records and referral duties have occupational support; banking adaptation, KPIs and anchors are researcher-authored.",
  "external_validity": "UNVALIDATED_ACROSS_JURISDICTIONS",
  "dimensions": {
    "decision_pattern": {
      "zero": "No usable case decision process, or claims authority to authorize insurer payment.",
      "half": "Provides a relevant case process but omits documentation or unresolved-disagreement referral.",
      "one": "Uses the stated scope, records the case and calculation, and routes the explicitly unresolved disagreement without claiming payout authority."
    },
    "metric_alignment": {
      "zero": "Neither stipulated service measure is operationalized, or replaces them with sales targets.",
      "half": "Operationalizes only case-note completeness or only unresolved-case follow-through.",
      "one": "Makes both measures actionable in the internal note; no invented numeric SLA is required."
    },
    "communication_style": {
      "zero": "Response is hostile, promises guaranteed recovery, or has no usable customer communication.",
      "half": "Generally respectful but fails to explain key terms or distinguish confirmed facts from pending review.",
      "one": "Uses clear, respectful customer language with explained terms and a clear distinction between facts and pending review."
    }
  },
  "scoring": "Mean of three dimension ratings in {0, 0.5, 1}; task-specific candidate anchors for the legacy RS dimensions.",
  "separation_from_ma": "RS checks workflow and communication; it does not award a second numeric-accuracy point. Avoid double counting the cap calculation as a KPI.",
  "review_disposition": "DRAFT_PENDING_INDEPENDENT_REVIEW"
}
```
