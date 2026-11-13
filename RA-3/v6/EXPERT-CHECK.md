# RA-3 v6: facts for expert review before lock

The 12 cells' ontologies, tasks and probes were drafted in November 2026 from the standards, laws and regulator guidance as I understood them. Each cell's domain expert reviews the cell in full before lock. This file lists the facts most likely to be wrong or out of date, so the review can start there.

## 1. New-cell facts with the lowest confidence

| Cell | Fact as written | Where |
| --- | --- | --- |
| accounting_vn | Circular 99/2025/TT-BTC replaces Circular 200/2014 for fiscal years from 2026 | ontology (marked "verify"), probe |
| fintech_vn | Decree 52/2024/ND-CP caps foreign ownership of payment intermediaries at 49% | ontology, probe |
| fintech_vn | Decree 94/2025/ND-CP sets the banking fintech sandbox | ontology, probe |
| fintech_vn | Mobile Money pilot under Decision 316/QD-TTg, with a VND 10 million monthly cap | ontology, probe |
| fintech_vn | Law 91/2025/QH15 on personal data protection takes effect 1 January 2026 | ontology, probe |
| fintech_vn | Law 71/2025/QH15 on the digital technology industry and Resolution 05/2025/NQ-CP on the crypto-asset pilot | ontology, probe |
| securities_vn | FTSE Russell's 2025 decision to reclassify Vietnam as secondary emerging | probe |
| banking_vn, fintech_vn | Deposit insurance pays at most VND 125 million per depositor per institution | probe |

## 2. Facts in the v5-cell probes to confirm

- **banking_vn**:
  - Law 32/2024/QH15 took effect on 1 July 2024. Its shareholding caps are 5% for an individual, 10% for an institution and 15% with related persons. Its single-customer credit limit starts at 14% of equity and falls to 10%.
  - Circular 31/2024 replaced Circular 11/2021.
  - The suspicious transaction report (STR) is due within 3 working days.
  - Decision 2345/QD-NHNN requires biometric checks above VND 10 million per transfer or VND 20 million a day.
  - From 1 January 2025, Circular 17/2024 restricts online transactions on accounts without biometric verification.
  - The reserve requirement is 3% on VND deposits under 12 months, and USD deposits are capped at 0% interest.
  - The VND/USD band is ±5%.
  - The compulsory bank transfers were CB to Vietcombank, OceanBank to MB, GPBank to VPBank and DongA to HDBank.
- **insurance_vn**:
  - Decree 67/2023 sets the compulsory motor third-party liability (TNDS) limits at VND 150 million per person for injury, VND 50 million per accident for motorbike damage and VND 100 million per accident for car damage.
  - Circular 67/2023 bars bank staff from offering unit-linked products within 60 days before or after a loan disbursement, and requires those sales to be recorded.
  - Insurers pay within 15 days of a complete claim file.
  - Claims must be filed within 1 year, and lawsuits within 3 years.
  - Insurance fraud is Article 213 of the Penal Code.
  - The social health insurance contribution is 4.5% of salary.
- **healthcare_us**:
  - Under the CMS 2024 prior-authorisation rule, standard decisions are due in 7 days and expedited decisions in 72 hours.
  - Press Ganey runs NDNQI.
  - The Joint Commission expects a root cause analysis within 45 business days.
- **fintech_us**:
  - FinCEN's March 2025 interim rule exempts domestic companies from Corporate Transparency Act beneficial ownership (BOI) reporting.
  - The GENIUS Act became law in 2025.
  - Visa's VAMP replaced its earlier monitoring programs in 2025.
  - Mastercard's Excessive Chargeback Program (ECP) threshold is 1.5%.
  - Fedwire moved to ISO 20022 in July 2025.
- **insurance_us**: the RBC action levels are 200%, 150%, 100% and 70% of the Authorized Control Level, and ORSA applies above $500 million in premium.

## 3. v5 ground truth that looks out of date

Five cells reuse v5's tasks, along with their ground truth and their ontologies. In both Vietnam cells, some of that ground truth now conflicts with current law. Judges score against the ground truth, and C3 passes the ontology to the model. A model that cites current law could therefore lose points, and C3 would feed it superseded rules.

| Cell | v5 says | Current law (to confirm) | Tasks affected |
| --- | --- | --- | --- |
| banking_vn | Decree 116/2013 governs AML; STR within 48 hours | 2022 AML Law and Decree 19/2023; STR within 3 working days; VND 400 million threshold now set by Decision 11/2023/QD-TTg | T6, T8 |
| banking_vn | Circular 22/2019 sets CAR ≥ 8%, LCR ≥ 100% and NSFR ≥ 100% | CAR is set by Circular 41/2016 (Basel II). Circular 22/2019 sets a liquidity reserve of at least 10%, 30-day solvency ratios and a loan-to-deposit ratio (LDR) of at most 85%. The SBV has not formally required LCR or NSFR | T2, T7 |
| banking_vn | Single-customer limit 15% of equity (Circular 22/2019) | Law 32/2024: 14% from July 2024, falling to 10%; 15% with related persons once fully phased in | T7, T10 (L7 board threshold) |
| banking_vn | Loan classification under Circular 11/2021 | Circular 31/2024 from 1 July 2024 (groups and specific rates appear unchanged) | T1, T9 (reference only) |
| banking_vn | eKYC under Circular 16/2020 | Circular 17/2024 and Decision 2345/QD-NHNN | none directly (ontology only) |
| banking_vn | CIC score 300–900 with FICO-style weights | Not confirmed; the weights look borrowed from FICO | T3 |
| insurance_vn | STR within 48 hours | 3 working days under the 2022 AML Law | ontology only (no task scores it) |
| insurance_vn | Life insurer charter capital VND 750 billion, broker VND 8 billion | Not confirmed against Decree 46/2023 | T3, T7 |
| insurance_vn | Retirement insurance premium tax-deductible up to VND 3 million a month | I believe the cap is VND 1 million a month | ontology only |
| healthcare_us | Readmission < 15% and HAI < 1.5% as "healthy" thresholds | These are rules of thumb. CMS penalties use risk-adjusted ratios, not fixed thresholds | T4 |

**Decision (Frank, 2026-11-13): correct it and publish a diff.** v6 applies the corrections in `corrections.json` on load, and v5's files stay byte-identical. Every edit is listed with its v5 value, v6 value and reason in [`V5-TO-V6-DIFF.md`](V5-TO-V6-DIFF.md). The CIC score, the insurance charter capital and the healthcare rules of thumb were left unchanged pending the experts, as the diff's last section explains. The corrections are drafts: the Vietnam banking and insurance experts confirm each one, and their edits go into `corrections.json` before lock.
