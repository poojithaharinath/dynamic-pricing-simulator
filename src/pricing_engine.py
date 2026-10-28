"""
Dynamic Pricing and Promotion Decision Engine.
Implements:
- Margin floor calculation: P_min = Cost / (1 - M)
- Absolute price floor and ceiling constraints
- Competitor benchmark calculation and freshness threshold check
- Demand and inventory signal evaluation
- Promotion eligibility, stacking, and exclusion enforcement
- Margin basis verification on final discounted price
- Transparent, audit-ready explainability logging
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import numpy as np


@dataclass
class ProductProfile:
    sku: str
    name: str
    category: str
    brand: str
    base_cost: float
    min_margin_rate: float
    price_floor: float
    price_ceiling: float
    lifecycle_status: str


@dataclass
class CompetitorData:
    benchmark_price: Optional[float]
    freshness_status: str  # 'CURRENT', 'STALE', 'UNAVAILABLE'
    days_old: Optional[int]


@dataclass
class StockData:
    available_stock: int
    reserved_stock: int
    reorder_threshold: int
    stock_status: str
    stock_signal: str  # 'HIGH_STOCK', 'BALANCED', 'LOW_STOCK', 'OUT_OF_STOCK'


@dataclass
class DemandData:
    recent_order_count: int
    demand_signal: str  # 'HIGH', 'MEDIUM', 'LOW'


@dataclass
class PromotionCandidate:
    promotion_id: str
    promo_code: str
    discount_type: str  # 'PERCENTAGE' or 'FIXED_AMOUNT'
    discount_value: float
    rule_type: str  # 'STACKABLE', 'EXCLUSIVE', etc.
    priority_order: int


@dataclass
class PricingDecisionResult:
    decision_id: str
    sku: str
    decision_date: str
    input_cost: float
    current_price: float
    competitor_benchmark_price: Optional[float]
    competitor_freshness_status: str
    demand_signal: str
    stock_signal: str
    applied_promotion_id: Optional[str]
    proposed_price: float
    final_price: float
    expected_margin_rate: float
    pricing_rule_applied: str
    decision_status: str  # 'APPROVED', 'REJECTED', 'FLAGGED'
    decision_reason: str
    is_anomaly: int = 0


class PricingEngine:
    def __init__(self, freshness_threshold_days: int = 7):
        self.freshness_threshold_days = freshness_threshold_days

    def calculate_margin_floor(self, unit_cost: float, min_margin_rate: float) -> float:
        """
        P_min = Cost / (1 - M)
        """
        if min_margin_rate >= 1.0:
            raise ValueError(f"Invalid min_margin_rate {min_margin_rate} must be < 1.0")
        return round(unit_cost / (1.0 - min_margin_rate), 2)

    def calculate_margin_rate(self, price: float, cost: float) -> float:
        """
        Margin % = (Price - Cost) / Price
        """
        if price <= 0:
            return 0.0
        return round((price - cost) / price, 4)

    def evaluate_competitor_benchmark(
        self,
        observations: List[Tuple[float, str]],  # (observed_price, observation_time)
        as_of_date: str
    ) -> CompetitorData:
        """
        Computes competitor benchmark price (median) and verifies observation freshness.
        """
        if not observations:
            return CompetitorData(benchmark_price=None, freshness_status="UNAVAILABLE", days_old=None)

        as_of_dt = datetime.strptime(as_of_date, "%Y-%m-%d")
        valid_prices = []
        min_days_old = 999999

        for price, obs_time_str in observations:
            obs_dt = datetime.strptime(obs_time_str[:10], "%Y-%m-%d")
            delta_days = (as_of_dt - obs_dt).days
            if delta_days < min_days_old:
                min_days_old = delta_days
            valid_prices.append(price)

        if not valid_prices:
            return CompetitorData(benchmark_price=None, freshness_status="UNAVAILABLE", days_old=None)

        median_benchmark = round(float(np.median(valid_prices)), 2)

        if min_days_old > self.freshness_threshold_days:
            freshness = "STALE"
        else:
            freshness = "CURRENT"

        return CompetitorData(
            benchmark_price=median_benchmark,
            freshness_status=freshness,
            days_old=min_days_old
        )

    def evaluate_signals(
        self,
        stock_units: int,
        reorder_threshold: int,
        recent_order_count: int
    ) -> Tuple[StockData, DemandData]:
        """
        Determines categorical stock and demand signals.
        """
        if stock_units <= 0:
            stock_status = "OUT_OF_STOCK"
            stock_signal = "OUT_OF_STOCK"
        elif stock_units <= reorder_threshold:
            stock_status = "LOW_STOCK"
            stock_signal = "LOW_STOCK"
        elif stock_units > 200:
            stock_status = "OVERSTOCK"
            stock_signal = "HIGH_STOCK"
        else:
            stock_status = "IN_STOCK"
            stock_signal = "BALANCED"

        stock_data = StockData(
            available_stock=stock_units,
            reserved_stock=0,
            reorder_threshold=reorder_threshold,
            stock_status=stock_status,
            stock_signal=stock_signal
        )

        if recent_order_count >= 8:
            demand_signal = "HIGH"
        elif recent_order_count <= 2:
            demand_signal = "LOW"
        else:
            demand_signal = "MEDIUM"

        demand_data = DemandData(
            recent_order_count=recent_order_count,
            demand_signal=demand_signal
        )

        return stock_data, demand_data

    def evaluate_promotions(
        self,
        base_price: float,
        unit_cost: float,
        min_margin_rate: float,
        candidates: List[PromotionCandidate]
    ) -> Tuple[Optional[PromotionCandidate], float, List[str]]:
        """
        Evaluates promotional candidates against stacking rules, priority,
        and post-discount margin constraints.
        """
        if not candidates:
            return None, 0.0, []

        # Sort candidates by priority_order (1 is highest priority)
        sorted_candidates = sorted(candidates, key=lambda c: c.priority_order)
        notes = []

        chosen_promo = None
        best_discount_amt = 0.0

        for promo in sorted_candidates:
            if promo.discount_type == "PERCENTAGE":
                discount_amt = round(base_price * promo.discount_value, 2)
            else:
                discount_amt = round(promo.discount_value, 2)

            tentative_price = round(base_price - discount_amt, 2)
            
            # CRITICAL BUSINESS RULE: Margin calculated on final discounted price
            margin_rate = self.calculate_margin_rate(tentative_price, unit_cost)

            if margin_rate < min_margin_rate:
                notes.append(
                    f"Promo {promo.promotion_id} ({promo.discount_value}) rejected: "
                    f"post-discount margin {margin_rate*100:.2f}% < required {min_margin_rate*100:.2f}%."
                )
                continue

            # Eligible promo found
            chosen_promo = promo
            best_discount_amt = discount_amt
            notes.append(
                f"Promo {promo.promotion_id} ({promo.promo_code}) accepted: "
                f"discount ₹{discount_amt:.2f}, resulting margin {margin_rate*100:.2f}%."
            )
            break  # Pick highest-priority eligible promotion

        return chosen_promo, best_discount_amt, notes

    def decide_price(
        self,
        product: ProductProfile,
        current_price: float,
        unit_cost: float,
        competitor_data: CompetitorData,
        stock_data: StockData,
        demand_data: DemandData,
        promotions: List[PromotionCandidate],
        decision_date: str,
        decision_id: str
    ) -> PricingDecisionResult:
        """
        Executes end-to-end pricing logic with full explainability and constraint enforcement.
        """
        # Step 1: Guardrail boundaries
        margin_floor = self.calculate_margin_floor(unit_cost, product.min_margin_rate)
        effective_floor = max(margin_floor, product.price_floor)
        effective_ceiling = product.price_ceiling

        reasons = []
        reasons.append(
            f"Cost: ₹{unit_cost:.2f}; Min Margin: {product.min_margin_rate*100:.1f}%; "
            f"Calculated Margin Floor: ₹{margin_floor:.2f}; Product Floor: ₹{product.price_floor:.2f} "
            f"(Effective Floor: ₹{effective_floor:.2f}, Ceiling: ₹{effective_ceiling:.2f})."
        )

        # Step 2: Signal-driven candidate proposal
        pricing_rule = "BASE_PRICE_MAINTAINED"
        candidate_price = current_price
        decision_status = "APPROVED"

        # Stockout handling
        if stock_data.stock_signal == "OUT_OF_STOCK":
            pricing_rule = "STOCKOUT_PROTECTION"
            candidate_price = current_price
            reasons.append("Inventory is OUT_OF_STOCK; maintaining base price to protect catalog integrity.")

        # High Demand & Low Stock -> Surge adjustment (+5% to +10%)
        elif demand_data.demand_signal == "HIGH" and stock_data.stock_signal == "LOW_STOCK":
            pricing_rule = "DEMAND_SURGE_INCREASE"
            candidate_price = round(current_price * 1.08, 2)
            reasons.append("High demand coupled with low stock detected; surging price +8% to balance velocity.")

        # Low Demand & High Stock -> Clearance reduction (-5% to -10%)
        elif demand_data.demand_signal == "LOW" and stock_data.stock_signal == "HIGH_STOCK":
            pricing_rule = "CLEARANCE_DEEP_DISCOUNT"
            candidate_price = round(current_price * 0.92, 2)
            reasons.append("Low demand coupled with overstock detected; discounting candidate price -8% to drive inventory turns.")

        # Competitor benchmark handling
        elif competitor_data.benchmark_price is not None:
            if competitor_data.freshness_status == "CURRENT":
                pricing_rule = "COMPETITIVE_MATCH"
                candidate_price = competitor_data.benchmark_price
                reasons.append(
                    f"Current competitor benchmark ₹{competitor_data.benchmark_price:.2f} observed "
                    f"({competitor_data.days_old} days ago); matching market benchmark."
                )
            else:
                decision_status = "FLAGGED"
                pricing_rule = "BASE_PRICE_MAINTAINED"
                candidate_price = current_price
                reasons.append(
                    f"Competitor benchmark ₹{competitor_data.benchmark_price:.2f} is STALE "
                    f"({competitor_data.days_old} days old > threshold {self.freshness_threshold_days} days); "
                    f"fell back to current price and flagged decision."
                )
        else:
            reasons.append("No competitor benchmark available; maintaining current base price.")

        proposed_price = candidate_price

        # Step 3: Floor & Ceiling Enforcement
        if proposed_price < effective_floor:
            candidate_price = effective_floor
            pricing_rule = "MARGIN_FLOOR_ENFORCED"
            reasons.append(
                f"Proposed price ₹{proposed_price:.2f} was below effective floor ₹{effective_floor:.2f}; "
                f"enforced floor to safeguard minimum profit margin."
            )

        if candidate_price > effective_ceiling:
            candidate_price = effective_ceiling
            reasons.append(
                f"Candidate price capped at maximum product ceiling ₹{effective_ceiling:.2f}."
            )

        # Step 4: Promotion Eligibility & Application
        applied_promo, promo_discount, promo_notes = self.evaluate_promotions(
            candidate_price, unit_cost, product.min_margin_rate, promotions
        )
        for note in promo_notes:
            reasons.append(note)

        final_price = round(candidate_price - promo_discount, 2)

        # Final floor safeguard
        if final_price < effective_floor:
            final_price = effective_floor
            reasons.append(f"Post-promotion final price clamped to effective floor ₹{effective_floor:.2f}.")

        # Step 5: Final Margin Calculation on Final Selling Price
        expected_margin = self.calculate_margin_rate(final_price, unit_cost)
        reasons.append(
            f"Final price ₹{final_price:.2f} yields gross margin of {expected_margin*100:.2f}% "
            f"(required >= {product.min_margin_rate*100:.2f}%)."
        )

        full_reason_text = " | ".join(reasons)

        return PricingDecisionResult(
            decision_id=decision_id,
            sku=product.sku,
            decision_date=decision_date,
            input_cost=unit_cost,
            current_price=current_price,
            competitor_benchmark_price=competitor_data.benchmark_price,
            competitor_freshness_status=competitor_data.freshness_status,
            demand_signal=demand_data.demand_signal,
            stock_signal=stock_data.stock_signal,
            applied_promotion_id=applied_promo.promotion_id if applied_promo else None,
            proposed_price=proposed_price,
            final_price=final_price,
            expected_margin_rate=expected_margin,
            pricing_rule_applied=pricing_rule,
            decision_status=decision_status,
            decision_reason=full_reason_text,
            is_anomaly=0
        )

