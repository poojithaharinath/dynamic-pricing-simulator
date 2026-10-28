"""
Automated Reproducibility Tests.
Verifies that multiple runs with the fixed seed 20261022 produce byte-identical data and checksums.
"""

import hashlib
import sqlite3
import pytest
from src.schema import init_database, get_table_names
from src.generator import DatasetConfig, SyntheticDataGenerator


def get_database_content_hash(conn: sqlite3.Connection) -> str:
    """Computes a unified MD5/SHA-256 hash of all rows across all tables in order."""
    cursor = conn.cursor()
    tables = get_table_names(conn)
    hasher = hashlib.sha256()

    for table in sorted(tables):
        cursor.execute(f"SELECT * FROM {table} ORDER BY 1;")
        rows = cursor.fetchall()
        for r in rows:
            hasher.update(str(r).encode("utf-8"))

    return hasher.hexdigest()


def test_seed_20261022_reproducibility():
    # Run 1
    conn1 = init_database(":memory:")
    config1 = DatasetConfig.starter()
    gen1 = SyntheticDataGenerator(config1)
    counts1 = gen1.populate_database(conn1)
    hash1 = get_database_content_hash(conn1)
    conn1.close()

    # Run 2
    conn2 = init_database(":memory:")
    config2 = DatasetConfig.starter()
    gen2 = SyntheticDataGenerator(config2)
    counts2 = gen2.populate_database(conn2)
    hash2 = get_database_content_hash(conn2)
    conn2.close()

    assert counts1 == counts2, f"Row counts differ: {counts1} vs {counts2}"
    assert hash1 == hash2, f"Reproducibility hash mismatch: {hash1} vs {hash2}"
