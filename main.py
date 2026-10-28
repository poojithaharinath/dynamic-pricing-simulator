"""
Main CLI Entrypoint for the Dynamic Pricing and Promotion Simulation System.
Usage:
    python main.py --mode starter
    python main.py --mode full
"""

import argparse
import sys
import time
from src.pipeline import run_full_simulation_pipeline


def main():
    parser = argparse.ArgumentParser(
        description="Dynamic Pricing and Promotion Simulation System (YottaFlex AI Project)"
    )
    parser.add_argument(
        "--mode",
        choices=["starter", "full"],
        default="starter",
        help="Dataset scale mode: 'starter' (50 SKUs, 30 days) or 'full' (5,000 SKUs, 180 days, 2,000 promos)"
    )
    parser.add_argument(
        "--db",
        default="data/pricing_simulation.db",
        help="SQLite database output file path (default: data/pricing_simulation.db)"
    )
    parser.add_argument(
        "--export-dir",
        default="data/exports",
        help="Directory to store CSV, JSON, and SQL export files (default: data/exports)"
    )
    parser.add_argument(
        "--gt-path",
        default="ground_truth/ground_truth_anomalies.csv",
        help="Path to output ground truth anomalies file"
    )
    parser.add_argument(
        "--report",
        default="validation_report.md",
        help="Output path for validation markdown report (default: validation_report.md)"
    )

    args = parser.parse_args()

    print("=" * 72)
    print("   DYNAMIC PRICING AND PROMOTION SIMULATION SYSTEM")
    print(f"   Mode: {args.mode.upper()} | Fixed Seed: 20261022")
    print("=" * 72)

    start_time = time.time()
    result = run_full_simulation_pipeline(
        mode=args.mode,
        db_path=args.db,
        export_dir=args.export_dir,
        ground_truth_path=args.gt_path,
        validation_report_path=args.report
    )
    elapsed = time.time() - start_time

    val = result["validation_results"]
    comp = val["pricing_compliance"]
    gt = val["ground_truth_benchmark"]

    print("\n--- EXECUTION COMPLETE ---")
    print(f"Time Taken: {elapsed:.2f} seconds")
    print(f"Database File: {result['database_file']}")
    print(f"Validation Status: {val['overall_status']}")
    print(f"Table Row Counts:")
    for tbl, cnt in result["row_counts"].items():
        print(f"  - {tbl:<26}: {cnt:>10,} rows")

    print("\n--- COMPLIANCE & EVALUATION METRICS ---")
    print(f"  - Price-Floor Violation Rate: {comp['floor_violation_rate_pct']}%")
    print(f"  - Margin Compliance Rate:     {comp['margin_compliance_rate_pct']}%")
    print(f"  - Decision Audit Rate:        {comp['audit_completeness_rate_pct']}%")
    print(f"  - Anomaly Detection F1-Score: {gt.get('f1_score', 0):.4f} (Precision: {gt.get('precision', 0):.4f}, Recall: {gt.get('recall', 0):.4f})")
    print(f"\nExports written to: {args.export_dir}")
    print(f"Validation Report:  {args.report}")
    print("=" * 72)


if __name__ == "__main__":
    main()
