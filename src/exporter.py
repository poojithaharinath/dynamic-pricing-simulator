"""
Data Export Pipeline.
Exports SQLite database entities into:
- CSV files (per table)
- JSON files (records format per table)
- SQL seed scripts (DDL + batch INSERT statements)
- Cryptographic SHA-256 manifest
"""

import os
import json
import sqlite3
import pandas as pd
from typing import Dict, List, Any
from src.schema import get_table_names
from src.validation import compute_file_sha256


class DataExporter:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def export_all(self, base_output_dir: str) -> Dict[str, Any]:
        """
        Exports all tables into CSV, JSON, and SQL directories with SHA-256 manifest.
        """
        csv_dir = os.path.join(base_output_dir, "csv")
        json_dir = os.path.join(base_output_dir, "json")
        sql_dir = os.path.join(base_output_dir, "sql")

        os.makedirs(csv_dir, exist_ok=True)
        os.makedirs(json_dir, exist_ok=True)
        os.makedirs(sql_dir, exist_ok=True)

        tables = get_table_names(self.conn)
        manifest = {}
        row_counts = {}

        # 1. Export CSV & JSON per table
        for table in tables:
            df = pd.read_sql_query(f"SELECT * FROM {table}", self.conn)
            row_counts[table] = len(df)

            # CSV
            csv_path = os.path.join(csv_dir, f"{table}.csv")
            df.to_csv(csv_path, index=False)
            manifest[f"csv/{table}.csv"] = {
                "rows": len(df),
                "sha256": compute_file_sha256(csv_path),
                "bytes": os.path.getsize(csv_path)
            }

            # JSON (records format; compact for large tables > 5,000 rows)
            json_path = os.path.join(json_dir, f"{table}.json")
            if len(df) > 5000:
                df.to_json(json_path, orient="records", date_format="iso")
            else:
                df.to_json(json_path, orient="records", date_format="iso", indent=2)

            manifest[f"json/{table}.json"] = {
                "rows": len(df),
                "sha256": compute_file_sha256(json_path),
                "bytes": os.path.getsize(json_path)
            }

        # 2. Export SQL Seed Script
        sql_file_path = os.path.join(sql_dir, "seed_data.sql")
        self._export_sql_dump(sql_file_path, tables)
        manifest["sql/seed_data.sql"] = {
            "sha256": compute_file_sha256(sql_file_path),
            "bytes": os.path.getsize(sql_file_path)
        }

        # 3. Write Manifest JSON
        manifest_path = os.path.join(base_output_dir, "export_manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump({
                "database_tables": tables,
                "row_counts": row_counts,
                "files": manifest
            }, f, indent=2)

        return {
            "status": "SUCCESS",
            "base_output_dir": base_output_dir,
            "row_counts": row_counts,
            "manifest_file": manifest_path
        }

    def _export_sql_dump(self, sql_file_path: str, tables: List[str], batch_size: int = 200):
        """
        Generates an executable SQL script with DDL and batched multi-row INSERT statements.
        """
        cursor = self.conn.cursor()
        with open(sql_file_path, "w", encoding="utf-8") as f:
            f.write("-- Dynamic Pricing & Promotion Simulation System - Seed Dump\n")
            f.write("BEGIN TRANSACTION;\n\n")

            for table in tables:
                cursor.execute(f"SELECT * FROM {table};")
                rows = cursor.fetchall()
                if not rows:
                    continue

                col_names = [description[0] for description in cursor.description]
                col_list_str = ", ".join(col_names)

                f.write(f"-- Table: {table} ({len(rows)} rows)\n")
                for i in range(0, len(rows), batch_size):
                    chunk = rows[i:i + batch_size]
                    value_tuples = []
                    for row in chunk:
                        vals = []
                        for val in row:
                            if val is None:
                                vals.append("NULL")
                            elif isinstance(val, (int, float)):
                                vals.append(str(val))
                            else:
                                clean_str = str(val).replace("'", "''")
                                vals.append(f"'{clean_str}'")
                        value_tuples.append(f"({', '.join(vals)})")
                    f.write(f"INSERT INTO {table} ({col_list_str}) VALUES\n  " + ",\n  ".join(value_tuples) + ";\n")
                f.write("\n")

            f.write("COMMIT;\n")
