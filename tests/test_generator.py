"""
Unit tests for Synthetic Data Generator.
Verifies determinism with seed 20261022, starter generation, and foreign key compliance.
"""

import sqlite3
import pytest
from src.schema import init_database
from src.generator import DatasetConfig, SyntheticDataGenerator


def test_starter_generation_and_population():
    conn = init_database(":memory:")
    config = DatasetConfig.starter()
    generator = SyntheticDataGenerator(config)

    counts = generator.populate_database(conn)

    assert counts["products"] == 50
    assert counts["promotions"] == 20
    assert counts["price_history"] == 50 * 30  # 1500
    assert counts["inventory_snapshots"] == 50 * 30  # 1500
    assert counts["cost_records"] >= 50
    assert counts["competitor_observations"] > 0
    assert counts["orders"] > 0

    # Ensure foreign key integrity in SQLite
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_key_check;")
    fk_violations = cursor.fetchall()
    assert len(fk_violations) == 0, f"FK Violations detected: {fk_violations}"
    conn.close()


def test_generator_determinism_seed_20261022():
    config1 = DatasetConfig.starter()
    gen1 = SyntheticDataGenerator(config1)
    prods1 = gen1.generate_products()

    config2 = DatasetConfig.starter()
    gen2 = SyntheticDataGenerator(config2)
    prods2 = gen2.generate_products()

    assert prods1 == prods2, "Products generation is not deterministic with seed 20261022"

    promos1, rules1, bridge1 = gen1.generate_promotions_and_rules()
    promos2, rules2, bridge2 = gen2.generate_promotions_and_rules()

    assert promos1 == promos2, "Promotions generation is not deterministic"
    assert rules1 == rules2, "Rules generation is not deterministic"
    assert bridge1 == bridge2, "Bridge generation is not deterministic"

