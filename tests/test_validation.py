"""
Unit tests for SystemValidator.
Verifies all data integrity checks and ground truth anomaly detection metrics.
"""

import os
import sqlite3
import pytest
from src.schema import init_database
from src.generator import DatasetConfig, SyntheticDataGenerator
from src.edge_cases import inject_edge_cases
from src.validation import SystemValidator


@pytest.fixture
def populated_system(tmp_path):
    conn = init_database(":memory:")
    config = DatasetConfig.starter()
    gen = SyntheticDataGenerator(config)
    gen.populate_database(conn)

    gt_file = str(tmp_path / "ground_truth_test.csv")
    inject_edge_cases(conn, gt_file, cases_per_type=2)

    return conn, gt_file


def test_validation_integrity_checks(populated_system):
    conn, _ = populated_system
    validator = SystemValidator(conn)

    pk_res = validator.check_primary_key_uniqueness()
    assert pk_res["passed"] is True, f"PK uniqueness failed: {pk_res}"

    fk_res = validator.check_foreign_key_integrity()
    assert fk_res["passed"] is True, f"FK integrity failed: {fk_res}"

    date_res = validator.check_date_chronology()
    assert date_res["passed"] is True, f"Date chronology failed: {date_res}"

    arith_res = validator.check_business_arithmetic()
    assert arith_res["passed"] is True, f"Arithmetic failed: {arith_res}"


def test_ground_truth_evaluation_metrics(populated_system):
    conn, gt_file = populated_system
    validator = SystemValidator(conn)

    gt_metrics = validator.evaluate_ground_truth_anomalies(gt_file)
    assert gt_metrics["ground_truth_count"] == 10
    assert gt_metrics["true_positives"] == 10
    assert gt_metrics["false_positives"] == 0
    assert gt_metrics["false_negatives"] == 0
    assert gt_metrics["precision"] == 1.0
    assert gt_metrics["recall"] == 1.0
    assert gt_metrics["f1_score"] == 1.0

