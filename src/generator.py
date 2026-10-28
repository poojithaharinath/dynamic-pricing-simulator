"""
Deterministic Synthetic Data Generator for Dynamic Pricing & Promotion Simulation.
Adheres strictly to Random Seed: 20261022.
Supports Starter (50 SKUs, 30 days, 20 promos) and Full (5,000 SKUs, 180 days, 2,000 promos) modes.
"""

import sqlite3
import random
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple
import numpy as np


CATEGORIES = ["Electronics", "Apparel", "Home_Kitchen", "Sports", "Books", "Beauty"]
BRANDS = ["Apex", "Zenith", "Omni", "Vanguard", "Nova", "Titan", "Aura", "Pulse"]
COMPETITORS = ["RivalRetail", "MarketGiant", "FastKart", "ValuePlus", "PrimeStore"]
COST_CHANGE_REASONS = ["SUPPLIER_INCREASE", "FREIGHT_ADJUSTMENT", "BULK_DISCOUNT", "ANNUAL_REVIEW"]
SOURCE_CHANNELS = ["WEB_SCRAPE", "PARTNER_FEED", "MANUAL_AUDIT"]


@dataclass
class DatasetConfig:
    mode: str = "starter"  # "starter" or "full"
    seed: int = 20261022
    num_skus: int = 50
    days: int = 30
    num_promotions: int = 20
    start_date: str = "2026-01-01"

    @classmethod
    def starter(cls) -> "DatasetConfig":
        return cls(mode="starter", seed=20261022, num_skus=50, days=30, num_promotions=20)

    @classmethod
    def full(cls) -> "DatasetConfig":
        return cls(mode="full", seed=20261022, num_skus=5000, days=180, num_promotions=2000)


class SyntheticDataGenerator:
    def __init__(self, config: DatasetConfig):
        self.config = config
        self.rng = np.random.default_rng(config.seed)
        random.seed(config.seed)
        self.start_dt = datetime.strptime(config.start_date, "%Y-%m-%d")

    def generate_products(self) -> List[Tuple]:
        """
        Generates master products with realistic cost, margin requirements,
        price floors, and ceilings per category.
        """
        products = []
        cost_ranges = {
            "Electronics": (2000.0, 45000.0),
            "Apparel": (350.0, 4000.0),
            "Home_Kitchen": (500.0, 8000.0),
            "Sports": (400.0, 12000.0),
            "Books": (150.0, 1200.0),
            "Beauty": (200.0, 3500.0),
        }

        for i in range(1, self.config.num_skus + 1):
            sku = f"SKU-{i:06d}"
            category = CATEGORIES[i % len(CATEGORIES)]
            brand = BRANDS[(i * 3) % len(BRANDS)]
            name = f"{brand} {category} Model-{i:04d}"

            low_c, high_c = cost_ranges[category]
            base_cost = round(float(self.rng.uniform(low_c, high_c)), 2)

            # Minimum margin rate between 12% and 30%
            min_margin_rate = round(float(self.rng.uniform(0.12, 0.30)), 3)

            # Standard margin floor formula: P_min = Cost / (1 - M)
            margin_floor = base_cost / (1.0 - min_margin_rate)
            price_floor = round(margin_floor * float(self.rng.uniform(0.98, 1.02)), 2)
            if price_floor < base_cost:
                price_floor = round(base_cost * 1.05, 2)

            price_ceiling = round(base_cost * float(self.rng.uniform(1.8, 2.6)), 2)
            if price_ceiling <= price_floor:
                price_ceiling = round(price_floor * 1.5, 2)

            # Lifecycle status
            r_status = self.rng.random()
            if r_status < 0.90:
                lifecycle_status = "ACTIVE"
            elif r_status < 0.95:
                lifecycle_status = "CLEARANCE"
            elif r_status < 0.98:
                lifecycle_status = "DRAFT"
            else:
                lifecycle_status = "DISCONTINUED"

            created_at = f"{self.config.start_date}T00:00:00Z"
            products.append((
                sku, name, category, brand, base_cost, min_margin_rate,
                price_floor, price_ceiling, lifecycle_status, created_at
            ))

        return products

    def generate_cost_records(self, products: List[Tuple]) -> List[Tuple]:
        """
        Generates historical cost ledger. Simulates occasional mid-period supplier price changes.
        """
        cost_records = []
        for prod in products:
            sku = prod[0]
            base_cost = prod[4]

            # Initial cost record starting on day 0
            initial_cost_id = f"COST-{sku}-20260101"
            
            # 25% chance product experiences a cost change during simulation
            if self.rng.random() < 0.25 and self.config.days >= 60:
                mid_day = int(self.rng.integers(30, self.config.days - 15))
                mid_dt = self.start_dt + timedelta(days=mid_day)
                mid_date_str = mid_dt.strftime("%Y-%m-%d")

                # End date for first cost record
                cost_records.append((
                    initial_cost_id, sku, base_cost, self.config.start_date,
                    mid_date_str, "INITIAL_COST", f"{self.config.start_date}T00:00:00Z"
                ))

                # Second cost record
                delta_mult = float(self.rng.uniform(0.92, 1.15))
                new_cost = round(base_cost * delta_mult, 2)
                second_cost_id = f"COST-{sku}-{mid_dt.strftime('%Y%m%d')}"
                reason = str(self.rng.choice(COST_CHANGE_REASONS))

                cost_records.append((
                    second_cost_id, sku, new_cost, mid_date_str,
                    None, reason, f"{mid_date_str}T00:00:00Z"
                ))
            else:
                cost_records.append((
                    initial_cost_id, sku, base_cost, self.config.start_date,
                    None, "INITIAL_COST", f"{self.config.start_date}T00:00:00Z"
                ))

        return cost_records

    def generate_promotions_and_rules(self) -> Tuple[List[Tuple], List[Tuple], List[Tuple]]:
        """
        Generates promotions, associated stacking/exclusion rules, and product eligibility mappings.
        """
        promotions = []
        rules = []
        bridge_mappings = []

        promo_types = ["PERCENTAGE", "FIXED_AMOUNT"]

        for p_idx in range(1, self.config.num_promotions + 1):
            promo_id = f"PROMO-2026-{p_idx:06d}"
            promo_code = f"PROMO{2026}{p_idx:04d}"

            p_type = "PERCENTAGE" if (p_idx % 3 != 0) else "FIXED_AMOUNT"
            if p_type == "PERCENTAGE":
                discount_val = round(float(self.rng.choice([0.05, 0.10, 0.15, 0.20, 0.25])), 2)
            else:
                discount_val = float(self.rng.choice([100.0, 200.0, 500.0, 1000.0]))

            # Staggered duration
            start_offset = int((p_idx * 7) % max(1, self.config.days - 10))
            duration = int(self.rng.integers(7, 30))
            p_start = self.start_dt + timedelta(days=start_offset)
            p_end = p_start + timedelta(days=duration)

            start_str = p_start.strftime("%Y-%m-%d")
            end_str = p_end.strftime("%Y-%m-%d")
            status = "ACTIVE" if p_idx % 10 != 0 else "EXPIRED"

            promotions.append((
                promo_id, promo_code, p_type, discount_val,
                start_str, end_str, status, f"{start_str}T00:00:00Z"
            ))

            # Rules: 60% stackable, 40% exclusive
            rule_id = f"RULE-{p_idx:06d}"
            rule_type = "STACKABLE" if (p_idx % 5 != 0) else "EXCLUSIVE"
            priority = int((p_idx % 5) + 1)
            cap = 5000.0 if p_type == "PERCENTAGE" else None

            rules.append((
                rule_id, promo_id, rule_type, None, priority, cap, f"{start_str}T00:00:00Z"
            ))

            # Eligible SKUs: associate with 5 to 25 SKUs
            sample_size = min(self.config.num_skus, max(3, int(self.config.num_skus * 0.15)))
            eligible_indices = self.rng.choice(
                range(1, self.config.num_skus + 1),
                size=sample_size,
                replace=False
            )
            for sku_idx in eligible_indices:
                sku = f"SKU-{sku_idx:06d}"
                bridge_mappings.append((promo_id, sku, 1))

        return promotions, rules, bridge_mappings

    def generate_competitor_observations(self, products: List[Tuple]) -> List[Tuple]:
        """
        Generates competitor price scrapes across time.
        """
        observations = []
        obs_counter = 1

        # Sample competitor scrape frequency: every 5-10 days per SKU
        for prod in products:
            sku = prod[0]
            base_cost = prod[4]
            target_price = round(base_cost * 1.35, 2)

            # Number of observation events
            obs_days = list(range(0, self.config.days, max(1, int(self.rng.integers(5, 12)))))
            for day in obs_days:
                comp_dt = self.start_dt + timedelta(days=day, hours=int(self.rng.integers(8, 20)))
                comp_name = str(self.rng.choice(COMPETITORS))
                channel = str(self.rng.choice(SOURCE_CHANNELS))
                
                # Competitor price fluctuates around target price +- 12%
                ratio = float(self.rng.uniform(0.90, 1.15))
                observed_price = round(target_price * ratio, 2)
                if observed_price <= 0:
                    observed_price = round(base_cost * 1.1, 2)

                obs_id = f"COMP-{obs_counter:06d}"
                obs_time = comp_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

                observations.append((
                    obs_id, sku, comp_name, observed_price, obs_time, channel, 1, obs_time
                ))
                obs_counter += 1

        return observations

    def generate_inventory_and_price_history(self, products: List[Tuple]) -> Tuple[List[Tuple], List[Tuple]]:
        """
        Generates daily inventory snapshots and daily price history for all SKUs over the full duration.
        """
        inventory_records = []
        price_history_records = []

        for prod in products:
            sku = prod[0]
            base_cost = prod[4]
            margin_rate = prod[5]
            
            # Initial selling price
            base_price = round(base_cost / (1.0 - margin_rate) * 1.05, 2)
            
            current_stock = int(self.rng.integers(40, 250))
            reorder_threshold = 25

            for day in range(self.config.days):
                curr_date = self.start_dt + timedelta(days=day)
                date_str = curr_date.strftime("%Y-%m-%d")
                created_iso = f"{date_str}T00:00:00Z"

                # Price record for day
                price_id = f"PRC-{sku}-{curr_date.strftime('%Y%m%d')}"
                price_history_records.append((
                    price_id, sku, base_price, date_str, None, "ACTIVE", created_iso
                ))

                # Inventory walk
                # Daily sales decrease stock
                daily_sales = int(self.rng.poisson(lam=4))
                reserved = min(current_stock, int(self.rng.integers(0, 5)))
                current_stock = max(0, current_stock - daily_sales)

                # Restock condition
                if current_stock <= reorder_threshold and self.rng.random() < 0.35:
                    current_stock += int(self.rng.integers(50, 150))

                if current_stock == 0:
                    stock_status = "OUT_OF_STOCK"
                elif current_stock < reorder_threshold:
                    stock_status = "LOW_STOCK"
                elif current_stock > 200:
                    stock_status = "OVERSTOCK"
                else:
                    stock_status = "IN_STOCK"

                snapshot_id = f"INV-{sku}-{curr_date.strftime('%Y%m%d')}"
                inventory_records.append((
                    snapshot_id, sku, date_str, current_stock, reserved,
                    reorder_threshold, stock_status, created_iso
                ))

        return inventory_records, price_history_records

    def generate_orders(self, products: List[Tuple]) -> List[Tuple]:
        """
        Generates realistic sales transactions and order records.
        """
        orders = []
        order_idx = 1

        for prod in products:
            sku = prod[0]
            base_cost = prod[4]
            margin_rate = prod[5]
            unit_price = round(base_cost / (1.0 - margin_rate), 2)

            num_orders = int(self.rng.integers(5, max(8, self.config.days * 2)))
            for _ in range(num_orders):
                day_offset = int(self.rng.integers(0, self.config.days))
                order_dt = self.start_dt + timedelta(
                    days=day_offset,
                    hours=int(self.rng.integers(0, 24)),
                    minutes=int(self.rng.integers(0, 60))
                )
                qty = int(self.rng.choice([1, 1, 1, 2, 2, 3, 5]))
                discount = 0.0
                if self.rng.random() < 0.20:
                    discount = round(unit_price * 0.10, 2)
                
                total = round(qty * (unit_price - discount), 2)
                status = "COMPLETED" if self.rng.random() < 0.94 else "RETURNED"

                order_id = f"ORD-{order_idx:06d}"
                orders.append((
                    order_id, sku, order_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    qty, unit_price, discount, total, status,
                    order_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                ))
                order_idx += 1

        return orders

    def populate_database(self, conn: sqlite3.Connection, batch_size: int = 25000) -> Dict[str, int]:
        """
        Populates SQLite database in transactional chunks for maximum throughput.
        Returns a dictionary of generated table row counts.
        """
        cursor = conn.cursor()

        # 1. Products
        products = self.generate_products()
        cursor.executemany(
            """INSERT INTO products (
                sku, name, category, brand, base_cost, min_margin_rate,
                price_floor, price_ceiling, lifecycle_status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            products
        )
        conn.commit()

        # 2. Cost Records
        cost_records = self.generate_cost_records(products)
        cursor.executemany(
            """INSERT INTO cost_records (
                cost_id, sku, unit_cost, effective_start_date,
                effective_end_date, change_reason, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            cost_records
        )
        conn.commit()

        # 3. Promotions & Rules
        promotions, rules, bridge = self.generate_promotions_and_rules()
        cursor.executemany(
            """INSERT INTO promotions (
                promotion_id, promo_code, discount_type, discount_value,
                start_date, end_date, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            promotions
        )
        cursor.executemany(
            """INSERT INTO promotion_rules (
                rule_id, promotion_id, rule_type, stackable_with_promo_id,
                priority_order, max_discount_cap, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            rules
        )
        cursor.executemany(
            """INSERT INTO promotion_products (
                promotion_id, sku, is_eligible
            ) VALUES (?, ?, ?)""",
            bridge
        )
        conn.commit()

        # 4. Competitor Observations
        competitors = self.generate_competitor_observations(products)
        cursor.executemany(
            """INSERT INTO competitor_observations (
                observation_id, sku, competitor_name, observed_price,
                observation_time, source_channel, is_verified, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            competitors
        )
        conn.commit()

        # 5. Inventory & Price History in batches
        inventory_records, price_history = self.generate_inventory_and_price_history(products)

        for i in range(0, len(price_history), batch_size):
            cursor.executemany(
                """INSERT INTO price_history (
                    price_id, sku, base_price, effective_start_date,
                    effective_end_date, lifecycle_state, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                price_history[i:i + batch_size]
            )
        conn.commit()

        for i in range(0, len(inventory_records), batch_size):
            cursor.executemany(
                """INSERT INTO inventory_snapshots (
                    snapshot_id, sku, snapshot_date, available_stock,
                    reserved_stock, reorder_threshold, stock_status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                inventory_records[i:i + batch_size]
            )
        conn.commit()

        # 6. Orders
        orders = self.generate_orders(products)
        cursor.executemany(
            """INSERT INTO orders (
                order_id, sku, order_date, quantity, unit_price,
                discount_applied, total_amount, order_status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            orders
        )
        conn.commit()

        # Collect row counts
        counts = {
            "products": len(products),
            "cost_records": len(cost_records),
            "promotions": len(promotions),
            "promotion_rules": len(rules),
            "promotion_products": len(bridge),
            "competitor_observations": len(competitors),
            "price_history": len(price_history),
            "inventory_snapshots": len(inventory_records),
            "orders": len(orders),
        }
        return counts

