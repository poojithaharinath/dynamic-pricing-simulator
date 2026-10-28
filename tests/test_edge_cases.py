"""
Unit tests for Edge Cases & Ground Truth Anomaly Injection.
Verifies all 5 edge case types are created, persisted, and recorded in a separate ground truth file.
"""

import os
import sqlite3
import pandas as pd
import pytest
from src.schema import init_database
from src.generator import DatasetConfig, SyntheticDataGenerator
from src.edge_cases import inject_edge_cases, EDGE_CASE_TYPES


def test_edge_cases_injection(tmp_path):
    conn = init_database(":memory:")
    config = DatasetConfig.starter()
    generator = SyntheticDataGenerator(config)
    generator.populate_database(conn)

    gt_file = str(tmp_path / "ground_truth_anomalies.csv")
    records = inject_edge_cases(conn, gt_file, cases_per_type=2)

    assert len(records) == 10  # 5 types * 2 cases
    assert os.path.exists(gt_file)

    # Check that all 5 required edge case types are present
    df_gt = pd.read_csv(gt_file)
    unique_types = set(df_gt["issue_type"].unique())
    assert unique_types == set(EDGE_CASE_TYPES.keys())

    # Check that price_decisions has the records with is_anomaly = 1
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM price_decisions WHERE is_anomaly = 1;")
    anomaly_count = cursor.fetchone()[0]
    assert anomaly_count == 10

    # Ensure decisions table has at least one record with null decision_reason (MISSING_PRICE_REASON)
    cursor.execute("SELECT count(*) FROM price_decisions WHERE decision_reason IS NULL;")
    assert cursor.fetchone()[0] == 2
    conn.close()

