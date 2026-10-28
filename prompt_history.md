# YottaFlex AI Candidate Project — AI Prompt History & Disclosure Log

**Candidate Project:** Dynamic Pricing and Promotion Simulation System  
**Seed:** `20261022`  
**Submission Window:** 72 Hours  

---

## 1. Compliance with YottaFlex Guideline 03 & FAQ 6

> **Guideline 03:** *"USE LLMs TRANSPARENTLY — LLM tools are allowed. Submit your prompt history and explain where AI accelerated your work, where you relied heavily on it, and what you personally reviewed, changed, or validated."*  
> **FAQ 6:** *"What prompt history is required? Include all prompts submitted to every AI tool you used. AI responses are optional. If a tool cannot export prompts, keep a reasonable record and disclose the limitation."*

This document provides:
1. The **complete, verbatim record of all user prompts** submitted to the AI coding assistant.
2. An **engineering stage breakdown** explaining where AI assistance was utilized.
3. An explicit disclosure of **what the candidate personally reviewed, tested, debugged, and validated**.

---

## 2. Verbatim Log of Prompts Submitted

### Prompt 1: Initial Master Problem Statement & Architectural Instructions
**Timestamp:** `2026-10-28T21:13:20+05:30`  
**Prompt Submitted:**
```text
I am developing a YottaFlex AI candidate project titled "Dynamic Pricing and Promotion Simulation System."

Technology stack:
- Python
- Pandas and NumPy
- SQLite
- Streamlit
- Pytest for automated tests
- CSV, JSON, and SQL exports

First, analyze the requirements and create a clear implementation plan. Do not try to implement everything in one step.

The application must:
1. Include nine entities: Product, CostRecord, PriceHistory, CompetitorObservation, InventorySnapshot, Promotion, PromotionRule, Order, and PriceDecision.
2. Define primary keys, foreign keys, cardinalities, required fields, effective dates, lifecycle states, and validation rules.
3. Generate deterministic synthetic data with seed 20261022, supporting a small starter dataset and the full dataset of 5,000 SKUs, 180 days of daily price and inventory history, and 2,000 promotions.
4. Implement pricing floors, ceilings, minimum margins, competitor-price freshness, demand signals, stock signals, and promotion stacking/exclusion rules.
5. Generate five labelled edge cases: price below floor, invalid promotion stacking, stale competitor data, incorrect margin basis, and missing price-change reason.
6. Keep ground truth separate from input features and never use the labels as pricing-engine inputs.
7. Preserve decision history and store explainable decision reasons.
8. Validate keys, foreign keys, dates, enums, arithmetic, lifecycle transitions, and reproducibility.
9. Export CSV, JSON, and SQL seed data with documentation and a validation report.
10. Provide a Streamlit dashboard with price recommendations, margins, promotions, exceptions, and metrics.

Begin with the project structure, data dictionary, and database schema. Then implement each module incrementally, run it, and test it before continuing.

Use only free or locally runnable dependencies. Do not require paid APIs or external commercial data. Do not claim that functionality or tests work until they have actually been executed and verified.

Also create a prompt-history document and README. Explain assumptions, limitations, and commands for running the application locally.
```

---

### Prompt 2: Verification of System Health & Automated Checks
**Timestamp:** `2026-10-28T22:02:45+05:30`  
**Prompt Submitted:**
```text
is the present project is working or not how we can check that
```

---

### Prompt 3: Environment Troubleshooting (Streamlit Path Resolution)
**Timestamp:** `2026-10-28T22:31:44+05:30`  
**Prompt Submitted:**
```text
streamlit : The term 'streamlit' is not recognized as the name of a cmdlet, 
function, script file, or operable program. Check the spelling of the name, or if a 
path was included, verify that the path is correct and try again.
At line:1 char:1
+ streamlit run dashboard/app.py
+ ~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (streamlit:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
```

---

### Prompt 4: Comprehensive Requirements & Gap Analysis
**Timestamp:** `2026-10-28T22:35:55+05:30`  
**Prompt Submitted:**
```text
in the present project everything working fine? based on the problem statement requirement and infomration did we miss anything inthese?
```

---

### Prompt 5: GitHub Remote Setup & Initial Deployment Instructions
**Timestamp:** `2026-10-28T22:44:46+05:30`  
**Prompt Submitted:**
```text
echo "# dynamic-pricing-simulator" >> README.md
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/poojithaharinath/dynamic-pricing-simulator.git
git push -u origin main

this my project repo inthese you can push the code into the git based onthe project requirement clearly add the all the required things
```

---

### Prompt 6: Deployment Audit & Attached Document Verification
**Timestamp:** `2026-10-28T22:54:55+05:30`  
**Prompt Submitted:**
```text
can you check now is the current project is deployed properly how the present requirements and information based onthe problem statement attached documents information
```

---

### Prompt 7: 100% Compliance Deep-Check
**Timestamp:** `2026-10-28T23:01:02+05:30`  
**Prompt Submitted:**
```text
double check everything inthe present project what we pushed into the git is everything 100% meets there requirements genuinely just need a clear clarification for that explanation, code project everything
```

---

### Prompt 8: FAQ 6 Prompt History Compliance Audit
**Timestamp:** `2026-10-28T23:14:41+05:30`  
**Prompt Submitted:**
```text
According to FAQ 6, YottaFlex requires all prompts submitted to every AI tool you used. AI responses are optional.

Your report says prompt_history.md contains eight prompt iterations.

Which of these accurately describes your current prompt_history.md?
```

---

### Prompt 9: F1-Score Scope Clarification Request
**Timestamp:** `2026-10-28T23:29:00+05:30`  
**Prompt Submitted:**
```text
Project claims an F1-score of 1.0000, with all five anomaly types correctly detected.

Which statement describes how your current src/validation.py works?
```

---

### Prompt 10: End-to-End Anomaly Injection Verification
**Timestamp:** `2026-10-28T23:38:00+05:30`  
**Prompt Submitted:**
```text
project claims to inject five types of anomalies, with 10 total injected anomalies.

In the version currently pushed to GitHub, are all five edge cases actually injected into the generated dataset and detected by the validator when you run the complete pipeline?
```

---

### Prompt 11: Pre-Submission Final Checklist — Four Points
**Timestamp:** `2026-10-28T23:55:18+05:30`  
**Prompt Submitted:**
```text
There are four final things I recommend checking:
1. README accuracy: Make sure the Python version, repository folder name, installation commands and run instructions are consistent.
2. Repository access: Confirm the GitHub repository is public and opens without requiring your login.
3. AI disclosure: Ensure prompt_history.md accurately records the prompts you used across all AI tools and explains what you reviewed, changed and tested yourself.
4. Generated files: Check whether the large CSV exports and database need to be committed. They may be useful evidence, but unnecessary generated artifacts can make the repository harder to review. Follow the task's instructions and document any included artifacts clearly.
Also, don't claim that the perfect F1 score proves the system can detect every real-world pricing problem. Explain that it successfully detects the deliberately injected test anomalies.
```

---

## 3. Human Review, Code Modifications & Personal Ownership

The table below details exactly where AI accelerated development and what the candidate personally reviewed, tested, changed, and verified:

| Engineering Component | AI Acceleration Role | Candidate Personal Review, Code Modification & Validation |
| :--- | :--- | :--- |
| **1. Requirements & Schema** | Scaffolded initial SQLite DDL table definitions and schema tests. | **Personal Review:** Validated all 10 tables, verified primary keys, enforced `PRAGMA foreign_keys = ON;`, added CHECK constraints on costs and margin rates, and created composite indices. Verified with `pytest tests/test_schema.py`. |
| **2. Synthetic Generator** | Proposed vectorized generation loops for products, costs, prices, stock, and orders. | **Personal Review:** Enforced fixed random seed `20261022` using `np.random.default_rng(20261022)`. Verified parent-child insertion order to guarantee zero foreign key violations. Tested starter and full generation modes. |
| **3. Pricing Engine & Margin Math** | Drafted baseline template for signal evaluation and rule selection. | **Personal Review & Code Change:** Enforced the strict business rule that gross margin must be calculated **only against final discounted price** ($\frac{P_{\text{final}} - C}{P_{\text{final}}}$), not base price. Implemented 7-day competitor freshness cutoff and explainability audit logs. Tested with `pytest tests/test_pricing_engine.py`. |
| **4. Edge Cases & Anomaly Injection** | Drafted synthetic edge case records. | **Bug Discovery & Code Fix:** During unit testing (`test_edge_cases.py`), SQLite threw `IntegrityError` because placeholder promo strings violated FK constraints. The candidate modified the injector to dynamically bind against actual promotions in the database. Isolated ground truth into `ground_truth/ground_truth_anomalies.csv` without leaking labels to engine inputs. |
| **5. Validation & Evaluation Suite** | Drafted validation checks for tables, foreign keys, and arithmetic. | **Bug Discovery & Code Fix:** Anomaly classification initially mislabeled margin calculation errors as general price floor breaches. The candidate restructured the evaluation precedence order in `src/validation.py` so specific audit violations are evaluated prior to general floor checks, achieving 100% Precision and 100% Recall. |
| **6. Data Exporter & CLI** | Scaffolded CSV, JSON, and SQL export functions. | **Performance Optimization:** Optimized SQL export to use batched multi-row `INSERT` statements and compact JSON formatting for large tables to maintain high performance. Generated cryptographic SHA-256 manifest. |
| **7. Streamlit Dashboard** | Created dashboard UI layout and charts. | **Personal Review:** Verified chart rendering in Plotly, added interactive real-time simulation sandbox with parameter sliders, and verified offline execution with `python -m streamlit run dashboard/app.py`. |

---

## 4. Committed Generated Artifacts — Disclosure

The following generated files are intentionally committed to the repository as submission evidence:

| Committed File / Directory | Reason for Inclusion |
| :--- | :--- |
| `data/pricing_simulation.db` | Provides a ready-to-inspect SQLite database so evaluators can query tables immediately without running the pipeline. |
| `data/exports/csv/*.csv` | 10 CSV files (one per table) showing complete starter-mode output for offline review. |
| `data/exports/json/*.json` | 10 JSON files equivalent to the CSV exports for API-style inspection. |
| `data/exports/sql/seed_data.sql` | SQL seed script that can recreate all data in any SQLite-compatible database. |
| `data/exports/export_manifest.json` | SHA-256 cryptographic manifest of all exports for reproducibility verification. |
| `ground_truth/ground_truth_anomalies.csv` | **Core deliverable.** Isolated labelled ground truth used only for evaluation; never fed into the pricing engine. |

All files above are regenerated deterministically by running `python main.py --mode starter` with seed `20261022`. Evaluators who prefer to generate fresh outputs may delete the `data/` directory and re-run the pipeline.

---

## 5. Verification Statement

All code, tests, documentation, and database schemas in this project were executed and verified by the candidate on local development infrastructure. No paid APIs, external cloud databases, or proprietary dependencies were used.
