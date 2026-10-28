"""
Database Schema Definitions and DDL for Dynamic Pricing and Promotion Simulation System.
Defines 9 primary entities + 1 relational bridge table with primary keys,
foreign keys, constraints, and indices in SQLite.
"""

import sqlite3
from typing import Optional

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

-- 1. Master Product Catalog
CREATE TABLE IF NOT EXISTS products (
    sku TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL CHECK(category IN ('Electronics', 'Apparel', 'Home_Kitchen', 'Sports', 'Books', 'Beauty')),
    brand TEXT NOT NULL,
    base_cost REAL NOT NULL CHECK(base_cost > 0),
    min_margin_rate REAL NOT NULL CHECK(min_margin_rate >= 0.05 AND min_margin_rate <= 0.60),
    price_floor REAL NOT NULL CHECK(price_floor > 0),
    price_ceiling REAL NOT NULL CHECK(price_ceiling >= price_floor),
    lifecycle_status TEXT NOT NULL CHECK(lifecycle_status IN ('ACTIVE', 'DISCONTINUED', 'DRAFT', 'CLEARANCE')),
    created_at TEXT NOT NULL
);

-- 2. Cost Records (Chronological ledger)
CREATE TABLE IF NOT EXISTS cost_records (
    cost_id TEXT PRIMARY KEY,
    sku TEXT NOT NULL,
    unit_cost REAL NOT NULL CHECK(unit_cost > 0),
    effective_start_date TEXT NOT NULL,
    effective_end_date TEXT,
    change_reason TEXT NOT NULL CHECK(change_reason IN ('INITIAL_COST', 'SUPPLIER_INCREASE', 'FREIGHT_ADJUSTMENT', 'BULK_DISCOUNT', 'ANNUAL_REVIEW')),
    created_at TEXT NOT NULL,
    FOREIGN KEY (sku) REFERENCES products(sku) ON DELETE CASCADE
);

-- 3. Price History
CREATE TABLE IF NOT EXISTS price_history (
    price_id TEXT PRIMARY KEY,
    sku TEXT NOT NULL,
    base_price REAL NOT NULL CHECK(base_price > 0),
    effective_start_date TEXT NOT NULL,
    effective_end_date TEXT,
    lifecycle_state TEXT NOT NULL CHECK(lifecycle_state IN ('ACTIVE', 'SUPERSEDED', 'CANCELLED')),
    created_at TEXT NOT NULL,
    FOREIGN KEY (sku) REFERENCES products(sku) ON DELETE CASCADE
);

-- 4. Competitor Observations
CREATE TABLE IF NOT EXISTS competitor_observations (
    observation_id TEXT PRIMARY KEY,
    sku TEXT NOT NULL,
    competitor_name TEXT NOT NULL,
    observed_price REAL NOT NULL CHECK(observed_price > 0),
    observation_time TEXT NOT NULL,
    source_channel TEXT NOT NULL CHECK(source_channel IN ('WEB_SCRAPE', 'PARTNER_FEED', 'MANUAL_AUDIT')),
    is_verified INTEGER NOT NULL CHECK(is_verified IN (0, 1)),
    created_at TEXT NOT NULL,
    FOREIGN KEY (sku) REFERENCES products(sku) ON DELETE CASCADE
);

-- 5. Inventory Snapshots
CREATE TABLE IF NOT EXISTS inventory_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    sku TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    available_stock INTEGER NOT NULL CHECK(available_stock >= 0),
    reserved_stock INTEGER NOT NULL CHECK(reserved_stock >= 0),
    reorder_threshold INTEGER NOT NULL CHECK(reorder_threshold >= 0),
    stock_status TEXT NOT NULL CHECK(stock_status IN ('IN_STOCK', 'LOW_STOCK', 'OUT_OF_STOCK', 'OVERSTOCK')),
    created_at TEXT NOT NULL,
    FOREIGN KEY (sku) REFERENCES products(sku) ON DELETE CASCADE
);

-- 6. Promotions
CREATE TABLE IF NOT EXISTS promotions (
    promotion_id TEXT PRIMARY KEY,
    promo_code TEXT NOT NULL UNIQUE,
    discount_type TEXT NOT NULL CHECK(discount_type IN ('PERCENTAGE', 'FIXED_AMOUNT')),
    discount_value REAL NOT NULL CHECK(discount_value > 0),
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('DRAFT', 'ACTIVE', 'EXPIRED', 'PAUSED')),
    created_at TEXT NOT NULL
);

-- 7. Promotion Products Bridge Table (Many-to-Many)
CREATE TABLE IF NOT EXISTS promotion_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    promotion_id TEXT NOT NULL,
    sku TEXT NOT NULL,
    is_eligible INTEGER NOT NULL DEFAULT 1 CHECK(is_eligible IN (0, 1)),
    FOREIGN KEY (promotion_id) REFERENCES promotions(promotion_id) ON DELETE CASCADE,
    FOREIGN KEY (sku) REFERENCES products(sku) ON DELETE CASCADE,
    UNIQUE(promotion_id, sku)
);

-- 8. Promotion Rules
CREATE TABLE IF NOT EXISTS promotion_rules (
    rule_id TEXT PRIMARY KEY,
    promotion_id TEXT NOT NULL,
    rule_type TEXT NOT NULL CHECK(rule_type IN ('STACKABLE', 'EXCLUSIVE', 'CATEGORY_RESTRICTION', 'MIN_PURCHASE')),
    stackable_with_promo_id TEXT,
    priority_order INTEGER NOT NULL DEFAULT 1 CHECK(priority_order >= 1),
    max_discount_cap REAL CHECK(max_discount_cap IS NULL OR max_discount_cap > 0),
    created_at TEXT NOT NULL,
    FOREIGN KEY (promotion_id) REFERENCES promotions(promotion_id) ON DELETE CASCADE,
    FOREIGN KEY (stackable_with_promo_id) REFERENCES promotions(promotion_id) ON DELETE SET NULL
);

-- 9. Orders
CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    sku TEXT NOT NULL,
    order_date TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity >= 1),
    unit_price REAL NOT NULL CHECK(unit_price > 0),
    discount_applied REAL NOT NULL DEFAULT 0.0 CHECK(discount_applied >= 0),
    total_amount REAL NOT NULL CHECK(total_amount >= 0),
    order_status TEXT NOT NULL CHECK(order_status IN ('COMPLETED', 'RETURNED', 'CANCELLED')),
    created_at TEXT NOT NULL,
    FOREIGN KEY (sku) REFERENCES products(sku) ON DELETE CASCADE
);

-- 10. Price Decisions (Audit and Explainability Log)
CREATE TABLE IF NOT EXISTS price_decisions (
    decision_id TEXT PRIMARY KEY,
    sku TEXT NOT NULL,
    decision_date TEXT NOT NULL,
    input_cost REAL NOT NULL CHECK(input_cost > 0),
    current_price REAL NOT NULL CHECK(current_price > 0),
    competitor_benchmark_price REAL,
    competitor_freshness_status TEXT NOT NULL CHECK(competitor_freshness_status IN ('CURRENT', 'STALE', 'UNAVAILABLE')),
    demand_signal TEXT NOT NULL CHECK(demand_signal IN ('HIGH', 'MEDIUM', 'LOW')),
    stock_signal TEXT NOT NULL CHECK(stock_signal IN ('HIGH_STOCK', 'BALANCED', 'LOW_STOCK', 'OUT_OF_STOCK')),
    applied_promotion_id TEXT,
    proposed_price REAL NOT NULL CHECK(proposed_price > 0),
    final_price REAL NOT NULL CHECK(final_price > 0),
    expected_margin_rate REAL NOT NULL,
    pricing_rule_applied TEXT NOT NULL CHECK(pricing_rule_applied IN (
        'COMPETITIVE_MATCH', 'MARGIN_FLOOR_ENFORCED', 'DEMAND_SURGE_INCREASE',
        'CLEARANCE_DEEP_DISCOUNT', 'STOCKOUT_PROTECTION', 'BASE_PRICE_MAINTAINED'
    )),
    decision_status TEXT NOT NULL CHECK(decision_status IN ('APPROVED', 'REJECTED', 'FLAGGED')),
    decision_reason TEXT,
    is_anomaly INTEGER NOT NULL DEFAULT 0 CHECK(is_anomaly IN (0, 1)),
    created_at TEXT NOT NULL,
    FOREIGN KEY (sku) REFERENCES products(sku) ON DELETE CASCADE,
    FOREIGN KEY (applied_promotion_id) REFERENCES promotions(promotion_id) ON DELETE SET NULL
);

-- Performance and Lookup Indices
CREATE INDEX IF NOT EXISTS idx_cost_sku ON cost_records(sku, effective_start_date);
CREATE INDEX IF NOT EXISTS idx_price_sku ON price_history(sku, effective_start_date);
CREATE INDEX IF NOT EXISTS idx_comp_sku_time ON competitor_observations(sku, observation_time);
CREATE INDEX IF NOT EXISTS idx_inv_sku_date ON inventory_snapshots(sku, snapshot_date);
CREATE INDEX IF NOT EXISTS idx_promo_dates ON promotions(start_date, end_date, status);
CREATE INDEX IF NOT EXISTS idx_promo_prod_sku ON promotion_products(sku);
CREATE INDEX IF NOT EXISTS idx_orders_sku_date ON orders(sku, order_date);
CREATE INDEX IF NOT EXISTS idx_decisions_sku_date ON price_decisions(sku, decision_date);
CREATE INDEX IF NOT EXISTS idx_decisions_status ON price_decisions(decision_status);
"""


def init_database(db_path: str = ":memory:") -> sqlite3.Connection:
    """
    Initializes the SQLite database with full schema, foreign keys enabled,
    and fast WAL journaling mode when on disk.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    if db_path != ":memory:":
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn


def get_table_names(conn: sqlite3.Connection) -> list[str]:
    """Returns all user table names defined in the SQLite database."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
    return [row[0] for row in cursor.fetchall()]
