"""
ProductPulse — Automated Tests for SQLite Data Loader
Verifies pre-import checksum/bytes assertions, deterministic run identity,
atomic rollback on failures, idempotent repeat-import no-op, and live sample integrity.
"""
import hashlib
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.load_sample_to_sqlite import (
    CATEGORY_LOCK,
    DEFAULT_MANIFEST_PATH,
    DEFAULT_RAW_PATH,
    DEFAULT_SCHEMA_PATH,
    compute_canonical_review_hash,
    compute_deterministic_run_id,
    compute_file_sha256_and_bytes,
    load_dataset,
)


class TestSQLiteLoader(unittest.TestCase):
    """
    Test suite for scripts/load_sample_to_sqlite.py
    """

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.db_path = self.temp_path / "test_loader.db"
        self.schema_path = DEFAULT_SCHEMA_PATH

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_synthetic_sample(
        self,
        records,
        category=CATEGORY_LOCK,
        tamper_hash=False,
        tamper_bytes=False,
    ):
        """Helper to create a temporary synthetic JSONL and matching manifest."""
        raw_file = self.temp_path / "synthetic_sample.jsonl"
        manifest_file = self.temp_path / "synthetic_manifest.json"

        # Write raw lines
        with open(raw_file, "wb") as f:
            for rec in records:
                line = json.dumps(rec, ensure_ascii=False) + "\n"
                f.write(line.encode("utf-8"))

        computed_sha, computed_len = compute_file_sha256_and_bytes(raw_file)

        manifest = {
            "manifest_version": "1.0",
            "dataset_name": "McAuley-Lab/Amazon-Reviews-2023",
            "category": category,
            "source_url": "http://synthetic.test",
            "limits_enforced": {
                "target_records": len(records),
                "max_body_bytes_cap": 1048576,
                "cumulative_timeout_seconds": 30.0,
            },
            "transport_evidence": {
                "final_status": 206,
                "content_range": f"bytes 0-{computed_len-1}/1000000",
                "total_bytes_streamed": computed_len,
            },
            "ingestion_outcomes": {
                "admitted_records_count": len(records),
                "total_lines_processed": len(records),
                "trailing_incomplete_bytes": 0,
                "parse_errors_count": 0,
                "validation_errors_count": 0,
                "duplicates_count": 0,
                "unique_parent_asins_count": len({r["parent_asin"] for r in records}),
                "unique_asins_count": len({r["asin"] for r in records}),
                "unique_users_count": len({r["user_id"] for r in records}),
            },
            "output_files": {
                "raw_jsonl_path": str(raw_file),
                "raw_jsonl_bytes": (computed_len + 100) if tamper_bytes else computed_len,
                "raw_jsonl_sha256": "tampered_sha256_hash" if tamper_hash else computed_sha,
                "manifest_path": str(manifest_file),
            },
            "ingestion_timestamps": {
                "start_utc": "2026-10-14T10:00:00Z",
                "end_utc": "2026-10-14T10:00:01Z",
                "elapsed_seconds": 1.0,
            },
            "academic_disclosures": {
                "sampling_nature": "Synthetic Test Sample",
                "population_claims_allowed": False,
            },
        }

        with open(manifest_file, "w", encoding="utf-8") as mf:
            json.dump(manifest, mf, indent=2)

        return raw_file, manifest_file

    def test_loader_aborts_on_checksum_mismatch(self):
        """Verifies that an incorrect or tampered SHA-256 aborts without touching DB."""
        records = [
            {"parent_asin": "P1", "asin": "V1", "user_id": "U1", "rating": 5.0, "timestamp": 1600000000000, "text": "Great"}
        ]
        raw_file, manifest_file = self._create_synthetic_sample(records, tamper_hash=True)

        with self.assertRaises(ValueError) as ctx:
            load_dataset(
                raw_path=raw_file,
                manifest_path=manifest_file,
                db_path=self.db_path,
                schema_path=self.schema_path,
            )
        self.assertIn("SHA-256 mismatch", str(ctx.exception))
        # Ensure database was not created or modified
        self.assertFalse(self.db_path.exists())

    def test_loader_aborts_on_byte_size_mismatch(self):
        """Verifies that an incorrect byte size aborts before touching DB."""
        records = [
            {"parent_asin": "P1", "asin": "V1", "user_id": "U1", "rating": 5.0, "timestamp": 1600000000000, "text": "Great"}
        ]
        raw_file, manifest_file = self._create_synthetic_sample(records, tamper_bytes=True)

        with self.assertRaises(ValueError) as ctx:
            load_dataset(
                raw_path=raw_file,
                manifest_path=manifest_file,
                db_path=self.db_path,
                schema_path=self.schema_path,
            )
        self.assertIn("byte size mismatch", str(ctx.exception))
        self.assertFalse(self.db_path.exists())

    def test_loader_aborts_on_category_mismatch(self):
        """Verifies that category other than Cell_Phones_and_Accessories is rejected."""
        records = [
            {"parent_asin": "P1", "asin": "V1", "user_id": "U1", "rating": 5.0, "timestamp": 1600000000000, "text": "Great"}
        ]
        raw_file, manifest_file = self._create_synthetic_sample(records, category="Electronics")

        with self.assertRaises(ValueError) as ctx:
            load_dataset(
                raw_path=raw_file,
                manifest_path=manifest_file,
                db_path=self.db_path,
                schema_path=self.schema_path,
            )
        self.assertIn("category mismatch", str(ctx.exception))

    def test_deterministic_run_id_consistency(self):
        """Verifies that identical inputs produce identical deterministic run IDs."""
        id1 = compute_deterministic_run_id("Cell_Phones_and_Accessories", "sha_abc", "dataset_xyz", "1.0")
        id2 = compute_deterministic_run_id("Cell_Phones_and_Accessories", "sha_abc", "dataset_xyz", "1.0")
        id_diff = compute_deterministic_run_id("Cell_Phones_and_Accessories", "sha_diff", "dataset_xyz", "1.0")

        self.assertEqual(id1, id2)
        self.assertEqual(len(id1), 16)
        self.assertNotEqual(id1, id_diff)

    def test_failed_import_rollback(self):
        """
        Verifies that an invalid record (e.g. rating 6.0) causes complete transaction rollback.
        The database must be left with 0 rows in reviews and 0 rows in ingestion_runs.
        """
        records = [
            {"parent_asin": "P1", "asin": "V1", "user_id": "U1", "rating": 5.0, "timestamp": 1600000000000, "text": "Valid"},
            {"parent_asin": "P1", "asin": "V1", "user_id": "U2", "rating": 6.0, "timestamp": 1600000001000, "text": "Invalid rating"},
        ]
        raw_file, manifest_file = self._create_synthetic_sample(records)

        with self.assertRaises(ValueError) as ctx:
            load_dataset(
                raw_path=raw_file,
                manifest_path=manifest_file,
                db_path=self.db_path,
                schema_path=self.schema_path,
            )
        self.assertIn("Rating out of bounds", str(ctx.exception))

        # Check that DB was rolled back completely
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM reviews;")
        self.assertEqual(cur.fetchone()[0], 0)
        cur.execute("SELECT COUNT(*) FROM ingestion_runs;")
        self.assertEqual(cur.fetchone()[0], 0)
        conn.close()

    def test_idempotent_noop_on_repeat_import(self):
        """
        Verifies the strict 5-condition no-op idempotency protocol:
        1st execution: loads records.
        2nd execution: reports idempotent no-op and makes 0 changes.
        """
        records = [
            {"parent_asin": "P1", "asin": "V1", "user_id": "U1", "rating": 4.0, "timestamp": 1600000000000, "text": "Review 1"},
            {"parent_asin": "P1", "asin": "V1", "user_id": "U2", "rating": 5.0, "timestamp": 1600000001000, "text": "Review 2"},
        ]
        raw_file, manifest_file = self._create_synthetic_sample(records)

        # 1st Run -> Success
        res1 = load_dataset(
            raw_path=raw_file,
            manifest_path=manifest_file,
            db_path=self.db_path,
            schema_path=self.schema_path,
        )
        self.assertEqual(res1["status"], "success")
        self.assertEqual(res1["admitted_records"], 2)

        # Verify DB counts
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM reviews;")
        self.assertEqual(cur.fetchone()[0], 2)
        cur.execute("SELECT COUNT(*) FROM ingestion_runs;")
        self.assertEqual(cur.fetchone()[0], 1)
        conn.close()

        # 2nd Run -> Must be IDEMPOTENT NO-OP
        res2 = load_dataset(
            raw_path=raw_file,
            manifest_path=manifest_file,
            db_path=self.db_path,
            schema_path=self.schema_path,
        )
        self.assertEqual(res2["status"], "idempotent_noop")

        # Verify DB counts did not change
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM reviews;")
        self.assertEqual(cur.fetchone()[0], 2)
        cur.execute("SELECT COUNT(*) FROM ingestion_runs;")
        self.assertEqual(cur.fetchone()[0], 1)
        conn.close()

    def test_replace_run_atomic(self):
        """
        Verifies that --replace-run cleanly replaces an existing run
        without leaving duplicate records or orphan errors.
        """
        records = [
            {"parent_asin": "P1", "asin": "V1", "user_id": "U1", "rating": 4.0, "timestamp": 1600000000000, "text": "Initial"}
        ]
        raw_file, manifest_file = self._create_synthetic_sample(records)

        # Initial Load
        load_dataset(
            raw_path=raw_file,
            manifest_path=manifest_file,
            db_path=self.db_path,
            schema_path=self.schema_path,
        )

        # Controlled Replacement
        res_replace = load_dataset(
            raw_path=raw_file,
            manifest_path=manifest_file,
            db_path=self.db_path,
            schema_path=self.schema_path,
            replace_run=True,
        )
        self.assertEqual(res_replace["status"], "success")

        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM reviews;")
        self.assertEqual(cur.fetchone()[0], 1)
        conn.close()

    def test_live_sample_25k_verification(self):
        """
        Loads the actual Phase 2C 25,000-review sample and verifies exact counts
        matching the Phase 3 data contract proposal:
        - Total reviews: 25,000
        - Distinct products: 19,065
        - Distinct variants: 20,484
        - Duplicates: 5 (with occurrence_index = 1 and _#1 suffix)
        Then asserts that re-running is an idempotent no-op.
        """
        if not DEFAULT_RAW_PATH.exists() or not DEFAULT_MANIFEST_PATH.exists():
            self.skipTest("Live Phase 2C dataset files not present in workspace.")

        live_db_path = self.temp_path / "live_25k_test.db"

        # 1. First Load
        res = load_dataset(
            raw_path=DEFAULT_RAW_PATH,
            manifest_path=DEFAULT_MANIFEST_PATH,
            db_path=live_db_path,
            schema_path=self.schema_path,
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["admitted_records"], 25000)
        self.assertEqual(res["distinct_products"], 19065)
        self.assertEqual(res["distinct_variants"], 20484)

        # 2. Database Assertions
        conn = sqlite3.connect(str(live_db_path))
        cur = conn.cursor()

        # Check total reviews
        cur.execute("SELECT COUNT(*) FROM reviews;")
        self.assertEqual(cur.fetchone()[0], 25000)

        # Check products
        cur.execute("SELECT COUNT(*) FROM products;")
        self.assertEqual(cur.fetchone()[0], 19065)

        # Check variants
        cur.execute("SELECT COUNT(*) FROM product_variants;")
        self.assertEqual(cur.fetchone()[0], 20484)

        # Check duplicates count
        cur.execute("SELECT COUNT(*) FROM reviews WHERE occurrence_index > 0;")
        self.assertEqual(cur.fetchone()[0], 5)

        # Check duplicate suffixes
        cur.execute("SELECT review_id FROM reviews WHERE occurrence_index = 1;")
        dup_ids = [row[0] for row in cur.fetchall()]
        self.assertEqual(len(dup_ids), 5)
        for d_id in dup_ids:
            self.assertTrue(d_id.endswith("_#1"), f"Duplicate ID {d_id} must end with _#1")

        # Check blank text count
        cur.execute("SELECT COUNT(*) FROM reviews WHERE is_blank_text = 1;")
        self.assertEqual(cur.fetchone()[0], 7)

        conn.close()

        # 3. Idempotent Repeat Run
        res_repeat = load_dataset(
            raw_path=DEFAULT_RAW_PATH,
            manifest_path=DEFAULT_MANIFEST_PATH,
            db_path=live_db_path,
            schema_path=self.schema_path,
        )
        self.assertEqual(res_repeat["status"], "idempotent_noop")


if __name__ == "__main__":
    unittest.main()
