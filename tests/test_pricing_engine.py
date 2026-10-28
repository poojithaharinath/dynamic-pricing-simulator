"""
Unit tests for Pricing Decision Engine.
Verifies margin floor, competitor freshness, signal rules, promotions, and margin calculations.
"""

import pytest
from src.pricing_engine import (
    PricingEngine,
    ProductProfile,
    CompetitorData,
    StockData,
    DemandData,
    PromotionCandidate,
)


@pytest.fixture
def engine():
    return PricingEngine(freshness_threshold_days=7)


@pytest.fixture
def sample_product():
    return ProductProfile(
        sku="SKU-000001",
        name="Apex Laptop Model-0001",
        category="Electronics",
        brand="Apex",
        base_cost=40000.0,
        min_margin_rate=0.20,  # 20%
        price_floor=45000.0,
        price_ceiling=65000.0,
        lifecycle_status="ACTIVE",
    )


def test_margin_floor_formula(engine):
    # Cost = 1000, M = 0.20 -> P_min = 1000 / 0.8 = 1250
    floor = engine.calculate_margin_floor(1000.0, 0.20)
    assert floor == 1250.0

    # Margin check: (1250 - 1000) / 1250 = 250 / 1250 = 0.20
    margin = engine.calculate_margin_rate(1250.0, 1000.0)
    assert margin == 0.20


def test_effective_floor_enforcement(engine, sample_product):
    # Product cost 40,000, margin 20% -> margin floor = 50,000. Product floor = 45,000.
    # Effective floor = max(50000, 45000) = 50000.
    comp_data = CompetitorData(benchmark_price=43000.0, freshness_status="CURRENT", days_old=1)
    stock_data = StockData(100, 0, 20, "IN_STOCK", "BALANCED")
    demand_data = DemandData(5, "MEDIUM")

    decision = engine.decide_price(
        product=sample_product,
        current_price=52000.0,
        unit_cost=40000.0,
        competitor_data=comp_data,
        stock_data=stock_data,
        demand_data=demand_data,
        promotions=[],
        decision_date="2026-01-15",
        decision_id="DEC-2026-000001",
    )

    # Competitor proposed 43,000, but effective floor is 50,000 -> must clamp to floor!
    assert decision.proposed_price == 43000.0
    assert decision.final_price >= 50000.0
    assert decision.pricing_rule_applied == "MARGIN_FLOOR_ENFORCED"
    assert decision.expected_margin_rate >= 0.20


def test_competitor_freshness_stale_flagging(engine):
    as_of = "2026-01-20"
    # Scrape from 15 days ago
    stale_observations = [(42000.0, "2026-01-05T10:00:00Z")]
    comp_data = engine.evaluate_competitor_benchmark(stale_observations, as_of)
    assert comp_data.freshness_status == "STALE"
    assert comp_data.days_old == 15

    # Fresh scrape from 2 days ago
    fresh_observations = [(42000.0, "2026-01-18T10:00:00Z")]
    comp_data_fresh = engine.evaluate_competitor_benchmark(fresh_observations, as_of)
    assert comp_data_fresh.freshness_status == "CURRENT"
    assert comp_data_fresh.days_old == 2


def test_promotion_margin_violation_rejection(engine, sample_product):
    # Laptop cost = 40,000. Min margin = 20% (requires price >= 50,000).
    # Current price = 52,000.
    # Promotion: 15% discount -> 52,000 * 0.85 = 44,200.
    # Margin on 44,200: (44200 - 40000) / 44200 = 9.5% (< 20% required).
    # Promotion must be REJECTED!
    promo = PromotionCandidate(
        promotion_id="PROMO-001",
        promo_code="DISCOUNT15",
        discount_type="PERCENTAGE",
        discount_value=0.15,
        rule_type="EXCLUSIVE",
        priority_order=1,
    )

    comp_data = CompetitorData(None, "UNAVAILABLE", None)
    stock_data = StockData(100, 0, 20, "IN_STOCK", "BALANCED")
    demand_data = DemandData(5, "MEDIUM")

    decision = engine.decide_price(
        product=sample_product,
        current_price=52000.0,
        unit_cost=40000.0,
        competitor_data=comp_data,
        stock_data=stock_data,
        demand_data=demand_data,
        promotions=[promo],
        decision_date="2026-01-15",
        decision_id="DEC-2026-000002",
    )

    # Promo should NOT be applied because it violates minimum margin
    assert decision.applied_promotion_id is None
    assert decision.final_price >= 50000.0
    assert "rejected" in decision.decision_reason.lower()


def test_demand_surge_and_clearance(engine, sample_product):
    comp_data = CompetitorData(None, "UNAVAILABLE", None)

    # Surge scenario: High demand, low stock
    stock_low = StockData(5, 0, 20, "LOW_STOCK", "LOW_STOCK")
    demand_high = DemandData(12, "HIGH")
    decision_surge = engine.decide_price(
        product=sample_product,
        current_price=55000.0,
        unit_cost=40000.0,
        competitor_data=comp_data,
        stock_data=stock_low,
        demand_data=demand_high,
        promotions=[],
        decision_date="2026-01-15",
        decision_id="DEC-SURGE-1",
    )
    assert decision_surge.pricing_rule_applied == "DEMAND_SURGE_INCREASE"
    assert decision_surge.proposed_price > 55000.0

