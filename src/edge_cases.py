"""
Edge Case Generator and Anomaly Injection Module.
Generates the 5 mandatory labelled edge cases:
1. PRICE_BELOW_FLOOR: Selling price falls below minimum allowable floor.
2. PROMOTION_STACKING: Prohibited promotion combination applied.
3. STALE_COMPETITOR: Stale competitor observation treated as current without fallback.
4. INCORRECT_MARGIN_BASIS: Margin calculated on base price instead of final discounted price.
5. MISSING_PRICE_REASON: Price change lacks an audit-compliant explanation.

Ground truth labels are stored in a dedicated file, completely separate from feature inputs.
"""

import sqlite3
import csv
import os
from typing import List, Dict, Any


EDGE_CASE_TYPES = {
    "PRICE_BELOW_FLOOR": "INVALID_PRICE_FLOOR",
    "PROMOTION_STACKING": "INVALID_STACKING",
    "STALE_COMPETITOR": "STALE_INPUT",
    "INCORRECT_MARGIN_BASIS": "INVALID_MARGIN_CALCULATION",
    "MISSING_PRICE_REASON": "AUDIT_EXCEPTION"
}


def inject_edge_cases(
    conn: sqlite3.Connection,
    ground_truth_csv_path: str,
    cases_per_type: int = 2
) -> List[Dict[str, Any]]:
    """
    Injects labelled anomalies into the database and writes the ground truth
    label file. Does NOT expose ground truth labels to decision engine features.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT sku, base_cost, min_margin_rate, price_floor, price_ceiling FROM products LIMIT 20;")
    products = cursor.fetchall()
    if not products:
        raise ValueError("Cannot inject edge cases into empty products table")

    cursor.execute("SELECT promotion_id FROM promotions LIMIT 5;")
    existing_promos = [r[0] for r in cursor.fetchall()]
    sample_promo_id = existing_promos[0] if existing_promos else None

    ground_truth_records = []
    injected_decisions = []
    case_idx = 1

    for c_type, label in EDGE_CASE_TYPES.items():
        for i in range(cases_per_type):
            prod = products[(case_idx - 1) % len(products)]
            sku, cost, min_margin, p_floor, p_ceil = prod
            dec_id = f"DEC-EDGE-{case_idx:04d}"
            date_str = "2026-01-25"
            created_at = f"{date_str}T12:00:00Z"

            margin_floor = round(cost / (1.0 - min_margin), 2)
            current_price = round(margin_floor * 1.30, 2)

            if c_type == "PRICE_BELOW_FLOOR":
                # Price strictly below effective floor
                bad_price = round(cost * 0.90, 2)
                bad_margin = round((bad_price - cost) / bad_price, 4)
                reason = "Injected Anomaly: Test price set below minimum margin floor."
                decision_tuple = (
                    dec_id, sku, date_str, cost, current_price,
                    bad_price, "CURRENT", "MEDIUM", "BALANCED", None,
                    bad_price, bad_price, bad_margin, "COMPETITIVE_MATCH",
                    "APPROVED", reason, 1, created_at
                )
                details = f"Final price ₹{bad_price} is below effective floor ₹{margin_floor}"

            elif c_type == "PROMOTION_STACKING":
                # Stacking error: applying discount while ignoring exclusivity
                discounted_price = round(current_price * 0.88, 2)
                margin = round((discounted_price - cost) / discounted_price, 4)
                reason = "Injected Anomaly: Stacking multiple non-stackable promotions in violation of exclusivity rule."
                decision_tuple = (
                    dec_id, sku, date_str, cost, current_price,
                    None, "UNAVAILABLE", "MEDIUM", "BALANCED", sample_promo_id,
                    current_price, discounted_price, margin, "CLEARANCE_DEEP_DISCOUNT",
                    "APPROVED", reason, 1, created_at
                )
                details = f"Applied stacked promo {sample_promo_id} prohibited by EXCLUSIVE stacking rule"

            elif c_type == "STALE_COMPETITOR":
                # Stale competitor data treated as CURRENT
                stale_comp_price = round(margin_floor * 1.20, 2)
                margin = round((stale_comp_price - cost) / stale_comp_price, 4)
                reason = "Injected Anomaly: Treated 30-day old competitor price as CURRENT benchmark without fallback."
                decision_tuple = (
                    dec_id, sku, date_str, cost, current_price,
                    stale_comp_price, "CURRENT", "MEDIUM", "BALANCED", None,
                    stale_comp_price, stale_comp_price, margin, "COMPETITIVE_MATCH",
                    "APPROVED", reason, 1, created_at
                )
                details = "Competitor observation date was 30 days old but marked CURRENT and used directly"

            elif c_type == "INCORRECT_MARGIN_BASIS":
                # Margin incorrectly calculated on base price instead of final discounted price
                base_p = round(margin_floor * 1.40, 2)
                disc_p = round(margin_floor * 1.10, 2)
                flawed_margin = round((base_p - cost) / base_p, 4)
                reason = "Injected Anomaly: Flawed calculation using undiscounted base price as margin basis."
                decision_tuple = (
                    dec_id, sku, date_str, cost, current_price,
                    None, "UNAVAILABLE", "MEDIUM", "BALANCED", sample_promo_id,
                    base_p, disc_p, flawed_margin, "CLEARANCE_DEEP_DISCOUNT",
                    "APPROVED", reason, 1, created_at
                )
                details = f"Expected margin rate was computed on base price ₹{base_p} rather than final discounted price ₹{disc_p}"

            elif c_type == "MISSING_PRICE_REASON":
                # Price changed but reason is missing/empty
                new_price = round(current_price * 1.15, 2)
                margin = round((new_price - cost) / new_price, 4)
                decision_tuple = (
                    dec_id, sku, date_str, cost, current_price,
                    None, "UNAVAILABLE", "HIGH", "LOW_STOCK", None,
                    new_price, new_price, margin, "DEMAND_SURGE_INCREASE",
                    "APPROVED", None, 1, created_at
                )
                details = "Price increased by 15% with null/empty decision_reason"

            injected_decisions.append(decision_tuple)
            ground_truth_records.append({
                "decision_id": dec_id,
                "sku": sku,
                "issue_type": c_type,
                "expected_label": label,
                "injected_details": details,
                "is_intentional_edge_case": 1
            })
            case_idx += 1

    # Insert into price_decisions
    cursor.executemany(
        """
        INSERT INTO price_decisions (
            decision_id, sku, decision_date, input_cost, current_price,
            competitor_benchmark_price, competitor_freshness_status,
            demand_signal, stock_signal, applied_promotion_id,
            proposed_price, final_price, expected_margin_rate,
            pricing_rule_applied, decision_status, decision_reason,
            is_anomaly, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        injected_decisions
    )
    conn.commit()

    # Save ground truth to external CSV
    os.makedirs(os.path.dirname(os.path.abspath(ground_truth_csv_path)), exist_ok=True)
    with open(ground_truth_csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["decision_id", "sku", "issue_type", "expected_label", "injected_details", "is_intentional_edge_case"]
        )
        writer.writeheader()
        writer.writerows(ground_truth_records)

    return ground_truth_records
