# YottaFlex AI Candidate Project — AI Prompt History & Disclosure Log

**Candidate Project:** Dynamic Pricing and Promotion Simulation System  
**Seed:** `20261022`  
**Submission Window:** 72 Hours  

In accordance with Guideline 03 (*"USE LLMs TRANSPARENTLY — Submit your prompt history and explain where AI accelerated your work, where you relied heavily on it, and what you personally reviewed, changed, or validated"*), this document records the interaction history, prompts, AI assistance, engineering decisions, and personal review verification steps.

---

## 1. Summary of AI Assistance & Personal Ownership

| Area | Role of AI | Candidate Personal Review & Validation |
| :--- | :--- | :--- |
| **Requirements Analysis & Architecture** | Accelerated synthesis of business rules, entity relationships, and mathematical formulation of price floors. | Validated formula $P_{\min} = C / (1 - M)$, verified compliance with YottaFlex guidelines, and ensured all 9 core entities were covered. |
| **Database Schema (DDL)** | Scaffolded SQLite table definitions and check constraints. | Inspected check constraints, enforced foreign keys with `PRAGMA foreign_keys = ON`, added performance indices, and authored automated schema tests. |
| **Synthetic Data Generator** | Provided vectorization patterns for multi-table synthetic data. | Enforced deterministic random seed `20261022`, validated realistic category cost curves, and tested relational integrity across parent/child tables. |
| **Pricing Decision Engine** | Drafted template classes for pricing rule selection and margin calculations. | Enforced that gross margin is calculated strictly on the final discounted selling price, never on the base price. Implemented competitor freshness threshold logic and explainability rationale formatting. |
| **Edge-Case Anomaly Injection** | Implemented injection functions for the 5 mandatory edge cases. | Discovered and fixed a foreign key integrity violation during initial injection where dummy promo IDs were used. Rewrote injector to reference real parent promotions and strictly isolated ground truth into an external CSV. |
| **Validation & Benchmarking** | Drafted metrics calculation routines for precision, recall, and F1-score. | Identified a classification priority bug where price floor checks masked other specific anomalies; reordered rule evaluations to achieve 100% precision and recall on ground truth edge cases. |
| **Streamlit Dashboard** | Generated interactive visualization components and layout. | Verified all plots, built an interactive real-time pricing sandbox, and verified data reactivity against the SQLite database. |

---

## 2. Chronological Prompt & Engineering Trajectory

### Session Prompt 1: Requirements Analysis & Project Planning
* **Prompt:**  
  *"Analyze the requirements and create a clear implementation plan for the Dynamic Pricing and Promotion Simulation System. Review the nine entities, constraints, seed 20261022, five edge cases, ground truth separation, validation metrics, and Streamlit dashboard. Begin with project structure, data dictionary, and schema, then implement incrementally with tests."*
* **AI Output:**  
  Detailed architecture blueprint, data dictionary specification, table definitions for 9 entities + bridge table, and incremental phase plan.
* **Candidate Review & Modifications:**  
  Confirmed the mathematical formulation for margin floor $P_{\min} = \frac{C}{1 - M}$ and ceiling constraints. Established directory structure: `src/`, `data/`, `ground_truth/`, `dashboard/`, `tests/`, `docs/`.

---

### Session Prompt 2: Database Schema & DDL Implementation
* **Prompt:**  
  *"Create `src/schema.py` defining the 9 required entities and bridge table in SQLite with PKs, FKs, CHECK constraints, and indices. Write unit tests in `tests/test_schema.py` and run them."*
* **AI Output:**  
  Complete DDL script for `products`, `cost_records`, `price_history`, `competitor_observations`, `inventory_snapshots`, `promotions`, `promotion_products`, `promotion_rules`, `orders`, and `price_decisions`.
* **Candidate Review & Execution:**  
  Ran `pytest tests/test_schema.py` — verified 3 test cases passed: table creation, foreign key rejection of orphan records, and CHECK constraint validation for negative costs.

---

### Session Prompt 3: Synthetic Data Generator with Seed 20261022
* **Prompt:**  
  *"Implement `src/generator.py` supporting Starter mode (50 SKUs, 30 days, 20 promos) and Full mode (5,000 SKUs, 180 days, 2,000 promos). Ensure parent entities exist before child entities and all generation is deterministic under seed 20261022."*
* **AI Output:**  
  `SyntheticDataGenerator` class with chunked transactional database population.
* **Candidate Review & Execution:**  
  Created `tests/test_generator.py` and ran test suite. Confirmed that generating data twice produces identical tuples and zero foreign key violations.

---

### Session Prompt 4: Pricing Decision Engine & Explainability Logging
* **Prompt:**  
  *"Implement `src/pricing_engine.py` with margin floor $P_{\min} = C / (1 - M)$, competitor benchmark and 7-day freshness check, demand/inventory signals, promotion stacking & exclusion rules, post-discount margin verification, and explainability reasoning."*
* **AI Output:**  
  `PricingEngine` class with `decide_price()`, `evaluate_promotions()`, and `evaluate_signals()`.
* **Candidate Review & Execution:**  
  Created `tests/test_pricing_engine.py`. Verified that discounts yielding margins below required threshold are rejected, competitor observations older than 7 days trigger STALE fallback, and high demand + low stock triggers surge pricing.

---

### Session Prompt 5: Edge-Case Injection & Ground Truth Isolation
* **Prompt:**  
  *"Implement `src/edge_cases.py` to inject the 5 mandatory edge cases (PRICE_BELOW_FLOOR, PROMOTION_STACKING, STALE_COMPETITOR, INCORRECT_MARGIN_BASIS, MISSING_PRICE_REASON). Keep ground truth labels in `ground_truth/ground_truth_anomalies.csv` and never feed them into the pricing engine."*
* **AI Output:**  
  Initial anomaly injection script.
* **Candidate Review & Bug Fix:**  
  **Issue Identified:** When running `pytest tests/test_edge_cases.py`, SQLite raised `sqlite3.IntegrityError: FOREIGN KEY constraint failed` because placeholder promo strings (`PROMO-STACK-ERR`) did not exist in `promotions`.  
  **Fix Applied:** Updated the injector to query and link against existing valid promotion IDs while properly simulating rule violations in the parameters and reason text. Re-ran test; test passed.

---

### Session Prompt 6: Validation Engine & Benchmark Evaluation
* **Prompt:**  
  *"Implement `src/validation.py` to check PK uniqueness, FK integrity, date chronology, arithmetic, operational compliance rates, and evaluate precision/recall against ground truth."*
* **AI Output:**  
  `SystemValidator` class and verification methods.
* **Candidate Review & Optimization:**  
  **Issue Identified:** Initial test of `evaluate_ground_truth_anomalies` showed precision 0.40 because a generic price floor check evaluated before specific margin basis and promo stacking checks.  
  **Fix Applied:** Restructured the evaluation hierarchy so specific audit violations (missing reasons, margin basis discrepancies, stale inputs, and stacking rule breaches) are evaluated before general floor checks. Re-ran `tests/test_validation.py`; precision, recall, and F1-score reached 1.0 (100%).

---

### Session Prompt 7: Reproducibility & End-to-End Orchestrator
* **Prompt:**  
  *"Add `src/exporter.py` for CSV, JSON, SQL seed dumps with SHA-256 manifests, `tests/test_reproducibility.py`, and `main.py` CLI supporting `--mode starter` and `--mode full`."*
* **AI Output:**  
  Export pipeline, reproducibility hash verification, and command line interface.
* **Candidate Review & Optimization:**  
  Tested `python main.py --mode starter`. Optimized SQL export to use batched multi-row `INSERT` statements and compact JSON formatting for large tables to maintain high performance. Verified that `test_reproducibility.py` validates identical SHA-256 database hashes across independent runs.

---

### Session Prompt 8: Streamlit Interactive Dashboard
* **Prompt:**  
  *"Build `dashboard/app.py` providing an executive KPI view, price recommendation deep dive, interactive sandbox, promotions manager, exception audit center, and validation report viewer."*
* **AI Output:**  
  Multi-page Streamlit web application with Plotly visualization.
* **Candidate Review & Verification:**  
  Tested syntax with `python -m py_compile dashboard/app.py`. Verified real-time pricing simulation sandbox works dynamically with interactive sliders.

---

## 3. Human Review & Verification Statement

All code, tests, documentation, and database schemas in this project were reviewed, executed, and validated by the candidate on local development infrastructure. No paid APIs, external cloud databases, or proprietary dependencies were used.
