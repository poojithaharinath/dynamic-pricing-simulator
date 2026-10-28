"""
Unit tests for schema creation, table definitions, foreign key enforcement, and constraints.
"""

import sqlite3
import pytest
from src.schema import init_database, get_table_names


def test_schema_creates_all_ten_tables():
    conn = init_database(":memory:")
    tables = get_table_names(conn)
    expected_tables = {
        "products",
        "cost_records",
        "price_history",
        "competitor_observations",
        "inventory_snapshots",
        "promotions",
        "promotion_products",
        "promotion_rules",
        "orders",
        "price_decisions",
    }
    assert expected_tables.issubset(set(tables)), f"Missing tables: {expected_tables - set(tables)}"
    conn.close()


def test_foreign_key_enforcement():
    conn = init_database(":memory:")
    cursor = conn.cursor()

    # Attempt inserting cost record for non-existent SKU should fail FK constraint
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            """
            INSERT INTO cost_records (cost_id, sku, unit_cost, effective_start_date, change_reason, created_at)
            VALUES ('COST-001', 'SKU-NONEXISTENT', 100.0, '2026-01-01', 'INITIAL_COST', '2026-01-01T00:00:00Z')
            """
        )
    conn.close()


def test_check_constraints():
    conn = init_database(":memory:")
    cursor = conn.cursor()

    # Inserting product with negative base_cost must fail CHECK constraint
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            """
            INSERT INTO products (sku, name, category, brand, base_cost, min_margin_rate, price_floor, price_ceiling, lifecycle_status, created_at)
            VALUES ('SKU-000001', 'Test Item', 'Electronics', 'TestBrand', -50.0, 0.20, 100.0, 200.0, 'ACTIVE', '2026-01-01T00:00:00Z')
            """
        )

    # Inserting invalid category must fail
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            """
            INSERT INTO products (sku, name, category, brand, base_cost, min_margin_rate, price_floor, price_ceiling, lifecycle_status, created_at)
            VALUES ('SKU-000001', 'Test Item', 'InvalidCat', 'TestBrand', 50.0, 0.20, 100.0, 200.0, 'ACTIVE', '2026-01-01T00:00:00Z')
            """
        )

    # Valid product insertion must succeed
    cursor.execute(
        """
        INSERT INTO products (sku, name, category, brand, base_cost, min_margin_rate, price_floor, price_ceiling, lifecycle_status, created_at)
        VALUES ('SKU-000001', 'Test Item', 'Electronics', 'Apex', 100.0, 0.20, 125.0, 250.0, 'ACTIVE', '2026-01-01T00:00:00Z')
        """
    )
    conn.commit()

    cursor.execute("SELECT count(*) FROM products WHERE sku = 'SKU-000001'")
    assert cursor.fetchone()[0] == 1
    conn.close()
