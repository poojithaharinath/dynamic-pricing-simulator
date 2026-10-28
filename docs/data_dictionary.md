# YottaFlex AI Dynamic Pricing and Promotion Simulation System
## Data Dictionary & Schema Specification

**System Version:** 1.0.0  
**Target Seed:** `20261022`  
**Database Engine:** SQLite 3  

---

## 1. Entity-Relationship Overview & Cardinalities

The simulation system is composed of nine primary domain entities and one relational bridge table:

| Entity Name | Primary Key | Parent Entity / FK | Cardinality (Parent : Child) | Lifecycle / Temporal Support |
| :--- | :--- | :--- | :--- | :--- |
| **Product** | `sku` | None (Master) | 1 : N to CostRecord, PriceHistory, CompetitorObservation, InventorySnapshot, Order, PriceDecision | Lifecycle status (`ACTIVE`, `DISCONTINUED`, `DRAFT`, `CLEARANCE`) |
| **CostRecord** | `cost_id` | `Product(sku)` | N : 1 | Temporal: `effective_start_date`, `effective_end_date` |
| **PriceHistory** | `price_id` | `Product(sku)` | N : 1 | Temporal: `effective_start_date`, `effective_end_date`; State: `ACTIVE`, `SUPERSEDED`, `CANCELLED` |
| **CompetitorObservation** | `observation_id` | `Product(sku)` | N : 1 | Temporal scrape: `observation_time`, `is_verified` |
| **InventorySnapshot** | `snapshot_id` | `Product(sku)` | N : 1 | Daily snapshot: `snapshot_date`, status `IN_STOCK`, `LOW_STOCK`, `OUT_OF_STOCK`, `OVERSTOCK` |
| **Promotion** | `promotion_id` | None (Master) | 1 : N to PromotionRule; M : N to Product | Temporal campaign: `start_date`, `end_date`; State: `DRAFT`, `ACTIVE`, `EXPIRED`, `PAUSED` |
| **PromotionProduct** | `id` (Bridge) | `Promotion(promotion_id)`, `Product(sku)` | N : M bridge | Eligibility mapping |
| **PromotionRule** | `rule_id` | `Promotion(promotion_id)` | N : 1 | Stacking & exclusion constraints: `STACKABLE`, `EXCLUSIVE`, `CATEGORY_RESTRICTION`, `MIN_PURCHASE` |
| **Order** | `order_id` | `Product(sku)` | N : 1 | Transaction log: `order_date`, `order_status` (`COMPLETED`, `RETURNED`, `CANCELLED`) |
| **PriceDecision** | `decision_id` | `Product(sku)`, `Promotion(applied_promotion_id)` | N : 1 | Audit & explainability log: `decision_status` (`APPROVED`, `REJECTED`, `FLAGGED`), reasons & signals |

---

## 2. Detailed Table Specifications

### 2.1 Table: `products`
Master catalog containing product attributes, pricing guardrails, and category definitions.

| Field Name | Data Type | Nullable | Primary / Foreign Key | Description & Allowed Values | Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `sku` | TEXT | NO | PK | Unique Stock Keeping Unit (e.g. `SKU-000001` to `SKU-005000`) | Pattern: `^SKU-\d{6}$` |
| `name` | TEXT | NO | - | Descriptive product title | Non-empty |
| `category` | TEXT | NO | - | Department (`Electronics`, `Apparel`, `Home_Kitchen`, `Sports`, `Books`, `Beauty`) | Enum set |
| `brand` | TEXT | NO | - | Brand identifier (e.g. `Apex`, `Zenith`, `Omni`, `Vanguard`, `Nova`) | Non-empty |
| `base_cost` | REAL | NO | - | Baseline cost in INR (₹) | Value > 0 |
| `min_margin_rate`| REAL | NO | - | Minimum gross margin threshold (e.g., 0.15 = 15%) | 0.05 <= rate <= 0.50 |
| `price_floor` | REAL | NO | - | Absolute minimum permitted selling price | `price_floor >= base_cost` |
| `price_ceiling` | REAL | NO | - | Absolute maximum permitted selling price | `price_ceiling > price_floor` |
| `lifecycle_status`| TEXT | NO | - | Lifecycle status: `ACTIVE`, `DISCONTINUED`, `DRAFT`, `CLEARANCE` | Valid Enum |
| `created_at` | TEXT | NO | - | ISO8601 creation timestamp (`YYYY-MM-DDTHH:MM:SSZ`) | Valid ISO timestamp |

### 2.2 Table: `cost_records`
Chronological cost ledger tracking changes in procurement and manufacturing costs.

| Field Name | Data Type | Nullable | Primary / Foreign Key | Description & Allowed Values | Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `cost_id` | TEXT | NO | PK | Format: `COST-SKU-XXXXXX-YYYYMMDD` | Unique PK |
| `sku` | TEXT | NO | FK -> `products(sku)` | Reference to product SKU | Valid FK |
| `unit_cost` | REAL | NO | - | Cost per unit in INR (₹) | `unit_cost > 0` |
| `effective_start_date` | TEXT | NO | - | Start of validity period (`YYYY-MM-DD`) | ISO date |
| `effective_end_date` | TEXT | YES | - | End of validity period (`YYYY-MM-DD`), NULL if active | `end_date >= start_date` if not NULL |
| `change_reason` | TEXT | NO | - | `INITIAL_COST`, `SUPPLIER_INCREASE`, `FREIGHT_ADJUSTMENT`, `BULK_DISCOUNT`, `ANNUAL_REVIEW` | Valid Enum |
| `created_at` | TEXT | NO | - | ISO8601 record creation timestamp | Valid ISO timestamp |

### 2.3 Table: `price_history`
Daily and historical record of base selling prices.

| Field Name | Data Type | Nullable | Primary / Foreign Key | Description & Allowed Values | Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `price_id` | TEXT | NO | PK | Format: `PRC-SKU-XXXXXX-YYYYMMDD` | Unique PK |
| `sku` | TEXT | NO | FK -> `products(sku)` | Reference to product SKU | Valid FK |
| `base_price` | REAL | NO | - | Base selling price before promotions in INR (₹) | `base_price > 0` |
| `effective_start_date` | TEXT | NO | - | Effective start date (`YYYY-MM-DD`) | ISO date |
| `effective_end_date` | TEXT | YES | - | Effective end date (`YYYY-MM-DD`) | `end_date >= start_date` if not NULL |
| `lifecycle_state` | TEXT | NO | - | `ACTIVE`, `SUPERSEDED`, `CANCELLED` | Valid Enum |
| `created_at` | TEXT | NO | - | ISO8601 creation timestamp | Valid ISO timestamp |

### 2.4 Table: `competitor_observations`
External marketplace price scrapes and benchmark intelligence.

| Field Name | Data Type | Nullable | Primary / Foreign Key | Description & Allowed Values | Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `observation_id` | TEXT | NO | PK | Format: `COMP-XXXXXX` | Unique PK |
| `sku` | TEXT | NO | FK -> `products(sku)` | Reference to product SKU | Valid FK |
| `competitor_name` | TEXT | NO | - | Name of rival seller (e.g. `RivalRetail`, `MarketGiant`, `FastKart`) | Non-empty |
| `observed_price` | REAL | NO | - | Competitor's listed price in INR (₹) | `observed_price > 0` |
| `observation_time`| TEXT | NO | - | Timestamp when price was observed (`YYYY-MM-DDTHH:MM:SSZ`) | Valid ISO timestamp |
| `source_channel` | TEXT | NO | - | Data source (`WEB_SCRAPE`, `PARTNER_FEED`, `MANUAL_AUDIT`) | Valid Enum |
| `is_verified` | INTEGER | NO | - | 1 if verified, 0 if noisy | In (0, 1) |
| `created_at` | TEXT | NO | - | ISO8601 creation timestamp | Valid ISO timestamp |

### 2.5 Table: `inventory_snapshots`
Daily inventory positions capturing on-hand stock and availability status.

| Field Name | Data Type | Nullable | Primary / Foreign Key | Description & Allowed Values | Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `snapshot_id` | TEXT | NO | PK | Format: `INV-SKU-XXXXXX-YYYYMMDD` | Unique PK |
| `sku` | TEXT | NO | FK -> `products(sku)` | Reference to product SKU | Valid FK |
| `snapshot_date` | TEXT | NO | - | Date of snapshot (`YYYY-MM-DD`) | ISO date |
| `available_stock` | INTEGER | NO | - | Physical stock ready for sale | `available_stock >= 0` |
| `reserved_stock` | INTEGER | NO | - | Stock allocated to pending orders | `reserved_stock >= 0` |
| `reorder_threshold`| INTEGER | NO | - | Threshold triggering replenishment | `reorder_threshold >= 0` |
| `stock_status` | TEXT | NO | - | `IN_STOCK`, `LOW_STOCK`, `OUT_OF_STOCK`, `OVERSTOCK` | Valid Enum |
| `created_at` | TEXT | NO | - | ISO8601 creation timestamp | Valid ISO timestamp |

### 2.6 Table: `promotions`
Discount campaigns and promotional offers.

| Field Name | Data Type | Nullable | Primary / Foreign Key | Description & Allowed Values | Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `promotion_id` | TEXT | NO | PK | Format: `PROMO-YYYY-XXXXXX` | Unique PK |
| `promo_code` | TEXT | NO | - | Coupon code (e.g. `SUMMER15`, `FLASH500`) | Non-empty text |
| `discount_type` | TEXT | NO | - | `PERCENTAGE` or `FIXED_AMOUNT` | Valid Enum |
| `discount_value` | REAL | NO | - | Rate (e.g., 0.15 for 15%) or flat amount in INR | `discount_value > 0` |
| `start_date` | TEXT | NO | - | Start date of campaign (`YYYY-MM-DD`) | ISO date |
| `end_date` | TEXT | NO | - | End date of campaign (`YYYY-MM-DD`) | `end_date >= start_date` |
| `status` | TEXT | NO | - | `DRAFT`, `ACTIVE`, `EXPIRED`, `PAUSED` | Valid Enum |
| `created_at` | TEXT | NO | - | ISO8601 creation timestamp | Valid ISO timestamp |

### 2.7 Table: `promotion_products` (Bridge)
Many-to-many relationship mapping promotions to eligible SKUs.

| Field Name | Data Type | Nullable | Primary / Foreign Key | Description & Allowed Values | Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | NO | PK | Autoincrement surrogate PK | Unique integer |
| `promotion_id` | TEXT | NO | FK -> `promotions(promotion_id)` | Promotional campaign | Valid FK |
| `sku` | TEXT | NO | FK -> `products(sku)` | Eligible SKU | Valid FK |
| `is_eligible` | INTEGER | NO | - | 1 if active on SKU, 0 if excluded | In (0, 1) |

### 2.8 Table: `promotion_rules`
Stacking, priority, and exclusivity governance.

| Field Name | Data Type | Nullable | Primary / Foreign Key | Description & Allowed Values | Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `rule_id` | TEXT | NO | PK | Format: `RULE-XXXXXX` | Unique PK |
| `promotion_id` | TEXT | NO | FK -> `promotions(promotion_id)` | Promotion to which rule applies | Valid FK |
| `rule_type` | TEXT | NO | - | `STACKABLE`, `EXCLUSIVE`, `CATEGORY_RESTRICTION`, `MIN_PURCHASE` | Valid Enum |
| `stackable_with_promo_id` | TEXT | YES | FK -> `promotions(promotion_id)` | Specific allowed stacked promo, or NULL | Valid FK if not NULL |
| `priority_order` | INTEGER | NO | - | Precedence order (1 = highest) | `priority_order >= 1` |
| `max_discount_cap`| REAL | YES | - | Maximum total discount in INR | Value > 0 if not NULL |
| `created_at` | TEXT | NO | - | ISO8601 creation timestamp | Valid ISO timestamp |

### 2.9 Table: `orders`
Sales transactions used for customer demand signal evaluation and financial reconciliation.

| Field Name | Data Type | Nullable | Primary / Foreign Key | Description & Allowed Values | Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `order_id` | TEXT | NO | PK | Format: `ORD-XXXXXX` | Unique PK |
| `sku` | TEXT | NO | FK -> `products(sku)` | Purchased product | Valid FK |
| `order_date` | TEXT | NO | - | Timestamp of purchase (`YYYY-MM-DDTHH:MM:SSZ`) | Valid ISO timestamp |
| `quantity` | INTEGER | NO | - | Units purchased | `quantity >= 1` |
| `unit_price` | REAL | NO | - | Price charged per unit in INR (₹) | `unit_price > 0` |
| `discount_applied`| REAL | NO | - | Total discount applied per unit | `discount_applied >= 0` |
| `total_amount` | REAL | NO | - | Total order amount = `quantity * (unit_price - discount)` | Arithmetic consistency |
| `order_status` | TEXT | NO | - | `COMPLETED`, `RETURNED`, `CANCELLED` | Valid Enum |
| `created_at` | TEXT | NO | - | ISO8601 creation timestamp | Valid ISO timestamp |

### 2.10 Table: `price_decisions`
Core decision audit ledger. Records inputs, candidate prices, applied rules, explainable rationales, and audit outcomes.

| Field Name | Data Type | Nullable | Primary / Foreign Key | Description & Allowed Values | Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `decision_id` | TEXT | NO | PK | Format: `DEC-YYYY-XXXXXX` | Unique PK |
| `sku` | TEXT | NO | FK -> `products(sku)` | Product SKU | Valid FK |
| `decision_date` | TEXT | NO | - | Effective decision date (`YYYY-MM-DD`) | ISO date |
| `input_cost` | REAL | NO | - | Unit cost considered in decision | `input_cost > 0` |
| `current_price` | REAL | NO | - | Current base selling price | `current_price > 0` |
| `competitor_benchmark_price` | REAL | YES | - | Median or minimum competitor price | `> 0` if present |
| `competitor_freshness_status` | TEXT | NO | - | `CURRENT`, `STALE`, `UNAVAILABLE` | Valid Enum |
| `demand_signal` | TEXT | NO | - | `HIGH`, `MEDIUM`, `LOW` | Valid Enum |
| `stock_signal` | TEXT | NO | - | `HIGH_STOCK`, `BALANCED`, `LOW_STOCK`, `OUT_OF_STOCK` | Valid Enum |
| `applied_promotion_id` | TEXT | YES | FK -> `promotions(promotion_id)` | Applied promotion, if any | Valid FK if present |
| `proposed_price` | REAL | NO | - | Initial candidate price before constraints | `proposed_price > 0` |
| `final_price` | REAL | NO | - | Final recommended price after constraints & discounts | `final_price > 0` |
| `expected_margin_rate` | REAL | NO | - | Final margin rate: `(final_price - input_cost) / final_price` | Formula compliance |
| `pricing_rule_applied` | TEXT | NO | - | `COMPETITIVE_MATCH`, `MARGIN_FLOOR_ENFORCED`, `DEMAND_SURGE_INCREASE`, `CLEARANCE_DEEP_DISCOUNT`, `STOCKOUT_PROTECTION`, `BASE_PRICE_MAINTAINED` | Valid Enum |
| `decision_status` | TEXT | NO | - | `APPROVED`, `REJECTED`, `FLAGGED` | Valid Enum |
| `decision_reason` | TEXT | NO | - | Detailed explainable justification | Must be non-empty for compliant records |
| `created_at` | TEXT | NO | - | ISO8601 creation timestamp | Valid ISO timestamp |

---

## 3. Ground Truth Anomaly Table / File (`ground_truth_anomalies.csv`)
Separated from model features and decision engine inputs. Used solely for evaluation and validation reporting.

| Column Name | Data Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `decision_id` | TEXT | NO | Foreign reference to `price_decisions(decision_id)` |
| `issue_type` | TEXT | NO | `PRICE_BELOW_FLOOR`, `PROMOTION_STACKING`, `STALE_COMPETITOR`, `INCORRECT_MARGIN_BASIS`, `MISSING_PRICE_REASON` |
| `expected_label` | TEXT | NO | Expected classification (e.g., `INVALID_PRICE_FLOOR`, `INVALID_STACKING`, `STALE_INPUT`, `INVALID_MARGIN_CALCULATION`, `AUDIT_EXCEPTION`) |
| `injected_details` | TEXT | NO | Audit narrative describing what anomaly was injected and ground-truth expectation |
| `is_intentional_edge_case` | INTEGER | NO | Always 1 for labelled test cases |

---

## 4. Business Arithmetic & Pricing Rules

1. **Minimum Price Floor from Cost and Margin Requirement:**
   $$P_{\text{margin\_floor}} = \frac{C}{1 - M}$$
   Where $C$ is unit cost, and $M$ is minimum margin rate (e.g. 0.20 for 20%).
   $$P_{\text{floor\_effective}} = \max(P_{\text{margin\_floor}}, P_{\text{product\_floor}})$$

2. **Price Ceiling Enforcement:**
   $$P_{\text{final}} \le P_{\text{ceiling}}$$

3. **Competitor Freshness Threshold:**
   A competitor observation is **STALE** if:
   $$\Delta t = (\text{decision\_date} - \text{observation\_time}) > 7\text{ days}$$
   Stale observations cannot drive automatic price reduction without human review or explicit fallback flagging.

4. **Promotion Discount & Margin Basis Rule:**
   For a promotional discount $d$ applied to base price $P_{\text{base}}$:
   $$P_{\text{final}} = P_{\text{base}} \times (1 - d) \quad \text{or} \quad P_{\text{final}} = P_{\text{base}} - \text{discount\_amount}$$
   The actual margin must be computed against **$P_{\text{final}}$**, NEVER against $P_{\text{base}}$:
   $$\text{Actual Margin Rate} = \frac{P_{\text{final}} - C}{P_{\text{final}}}$$
   If $\text{Actual Margin Rate} < M$, the promotion is **ineligible** and must be rejected.
