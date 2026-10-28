# YottaFlex AI Dynamic Pricing Simulation — Validation & Audit Report

**Dataset Mode:** `STARTER`  
**Random Seed:** `20261022`  
**Audit Evaluation Timestamp:** `2026-10-28T17:50:49Z`  
**Overall Validation Status:** **PASSED**  

---

## 1. Executive Summary & Verification Dashboard

| Verification Category | Status | Target Metric | Measured Value | Outcome |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Key Uniqueness** | PASSED | 100% Unique across all 10 tables | 100% Unique | Compliant |
| **Foreign Key Referential Integrity** | PASSED | 0 Orphan records | 0 Violations | Compliant |
| **Date Chronology** | PASSED | End Date >= Start Date | 0 Violations | Compliant |
| **Financial & Margin Arithmetic** | PASSED | Margin = (Price - Cost) / Price | 0 Mismatches | Compliant |
| **Operational Price-Floor Violation Rate** | PASSED | 0.0% unapproved violations | **0.0%** | Zero Floor Breaches |
| **Margin Compliance Rate** | PASSED | >= 99.0% compliance | **100.0%** | Compliant |
| **Decision Audit Completeness** | PASSED | 100.0% explained decisions | **100.0%** | Fully Auditable |
| **Edge-Case Anomaly Precision** | PASSED | >= 95.0% | **100.0%** | Perfect Precision |
| **Edge-Case Anomaly Recall** | PASSED | >= 95.0% | **100.0%** | 100% Detection Rate |
| **Edge-Case Anomaly F1-Score** | PASSED | >= 0.95 | **1.0000** | Optimal F1 |

---

## 2. Table Row Count Verification

| Table Name | Description | Generated Row Count |
| :--- | :--- | :--- |
| `products` | Master SKU catalog | 50 |
| `cost_records` | Chronological cost changes | 50 |
| `price_history` | Historical base prices | 1,500 |
| `competitor_observations` | Scraping benchmark observations | 212 |
| `inventory_snapshots` | Daily inventory snapshots | 1,500 |
| `promotions` | Discount promotions | 20 |
| `promotion_products` | Bridge table (SKU eligibility) | 140 |
| `promotion_rules` | Stacking, priority, and exclusivity | 20 |
| `orders` | Sales transactions | 1,577 |
| `price_decisions` | Pricing engine decision ledger | 55 |

---

## 3. Ground Truth Edge-Case Detection Evaluation

Independent audit detection was executed against the isolated ground truth dataset (`ground_truth/ground_truth_anomalies.csv`).  
Ground truth labels were strictly separated and **never** provided as input features to the pricing engine.

- **Total Labelled Edge Cases:** 10
- **True Positives (TP):** 10
- **False Positives (FP):** 0
- **False Negatives (FN):** 0
- **Precision:** 1.0000
- **Recall:** 1.0000
- **F1 Score:** 1.0000

### Breakdown of Injected Edge Cases Handled:
1. `PRICE_BELOW_FLOOR`: Price fell below effective floor; flagged and clamped by floor guardrail.
2. `PROMOTION_STACKING`: Incompatible promotion stacking combination rejected by exclusivity rules.
3. `STALE_COMPETITOR`: Scrapes older than 7 days flagged as STALE; fallback strategy enacted.
4. `INCORRECT_MARGIN_BASIS`: Margin calculated on undiscounted base price caught and audited.
5. `MISSING_PRICE_REASON`: Missing explainability rationale flagged as audit exception.

---

## 4. Export Artifacts & Checksums

All database entities were exported into CSV, JSON, and SQL seed scripts. Full cryptographic SHA-256 signatures are documented in `data/exports\export_manifest.json`.
