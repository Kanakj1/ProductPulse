"""
ProductPulse — Automated Tests for Database Schema, Constraints & Health Status
Verifies strict foreign keys, composite FK variant validation, CHECK constraints,
duplicate review identification, and non-sensitive health reporting.
"""
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from backend.db.connection import get_connection, init_db
from backend.app.api.health import get_health_status


class TestDatabaseSchemaAndConstraints(unittest.TestCase):
    """
    Unit test suite for SQLite schema and referential constraints.
    """

    def setUp(self):
        # Create a temporary database file for isolation
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_productpulse.db"
        self.conn = init_db(self.db_path)

        # Insert a valid baseline ingestion_run for foreign-key references
        self.run_id = "run_test_sample_01"
        self.conn.execute(
            """
            INSERT INTO ingestion_runs (
                run_id, dataset_name, category, source_url, target_records,
                max_body_bytes_cap, cumulative_timeout_seconds, final_status,
                content_range, total_bytes_streamed, admitted_records_count,
                total_lines_processed, trailing_incomplete_bytes, parse_errors_count,
                validation_errors_count, duplicates_count, unique_parent_asins_count,
                unique_asins_count, unique_users_count, raw_jsonl_path, raw_jsonl_bytes,
                raw_jsonl_sha256, manifest_path, start_utc, end_utc, elapsed_seconds,
                sampling_nature
            ) VALUES (
                ?, 'TestDataset', 'Cell_Phones_and_Accessories', 'http://test', 100,
                1000, 10.0, 206, 'bytes 0-99/1000', 1000, 1,
                1, 0, 0, 0, 0, 1, 1, 1, '/tmp/test.jsonl', 1000,
                'sha256_dummy', '/tmp/manifest.json', '2026-10-14T00:00:00Z',
                '2026-10-14T00:00:01Z', 1.0, 'Test'
            );
            """,
            (self.run_id,),
        )
        self.conn.commit()

    def tearDown(self):
        self.conn.close()
        self.temp_dir.cleanup()

    def test_foreign_keys_pragma_enforced(self):
        """Verifies that PRAGMA foreign_keys is strictly enabled on every connection."""
        cur = self.conn.cursor()
        cur.execute("PRAGMA foreign_keys;")
        status = cur.fetchone()[0]
        self.assertEqual(status, 1, "SQLite foreign_keys must be active (1)")

    def test_schema_tables_and_indexes_exist(self):
        """Verifies that all 4 Tier 1 tables and 5 serving indexes exist."""
        cur = self.conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cur.fetchall()}
        expected_tables = {"ingestion_runs", "products", "product_variants", "reviews"}
        self.assertTrue(expected_tables.issubset(tables), f"Missing tables: {expected_tables - tables}")

        cur.execute("SELECT name FROM sqlite_master WHERE type='index';")
        indexes = {row[0] for row in cur.fetchall()}
        expected_indexes = {
            "idx_reviews_parent_asin_date",
            "idx_reviews_parent_asin_rating",
            "idx_product_variants_parent",
            "idx_reviews_user_id",
            "idx_reviews_has_images",
        }
        self.assertTrue(expected_indexes.issubset(indexes), f"Missing indexes: {expected_indexes - indexes}")

    def test_rating_check_constraint_rejects_out_of_bounds(self):
        """Verifies that ratings below 1.0 or above 5.0 violate CHECK constraint."""
        # Setup product and variant
        self.conn.execute(
            "INSERT INTO products (parent_asin, first_seen_run_id) VALUES ('P1', ?);",
            (self.run_id,),
        )
        self.conn.execute(
            "INSERT INTO product_variants (asin, parent_asin, first_seen_run_id) VALUES ('V1', 'P1', ?);",
            (self.run_id,),
        )
        self.conn.commit()

        # Rating too low: 0.5
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                """
                INSERT INTO reviews (
                    review_id, canonical_hash, parent_asin, asin, user_id, rating,
                    timestamp_raw, review_timestamp_utc, review_epoch_seconds,
                    verified_purchase, source_line_number, source_byte_offset,
                    source_byte_length, ingestion_run_id
                ) VALUES (
                    'r_low', 'hash_low', 'P1', 'V1', 'U1', 0.5,
                    1600000000000, '2020-09-13T12:26:40.000Z', 1600000000.0,
                    1, 1, 0, 100, ?
                );
                """,
                (self.run_id,),
            )

        # Rating too high: 5.5
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                """
                INSERT INTO reviews (
                    review_id, canonical_hash, parent_asin, asin, user_id, rating,
                    timestamp_raw, review_timestamp_utc, review_epoch_seconds,
                    verified_purchase, source_line_number, source_byte_offset,
                    source_byte_length, ingestion_run_id
                ) VALUES (
                    'r_high', 'hash_high', 'P1', 'V1', 'U1', 5.5,
                    1600000000000, '2020-09-13T12:26:40.000Z', 1600000000.0,
                    1, 1, 0, 100, ?
                );
                """,
                (self.run_id,),
            )

    def test_rating_check_constraint_accepts_valid_boundaries(self):
        """Verifies that 1.0, 3.5, and 5.0 ratings insert successfully."""
        self.conn.execute(
            "INSERT INTO products (parent_asin, first_seen_run_id) VALUES ('P1', ?);",
            (self.run_id,),
        )
        self.conn.execute(
            "INSERT INTO product_variants (asin, parent_asin, first_seen_run_id) VALUES ('V1', 'P1', ?);",
            (self.run_id,),
        )

        for i, val in enumerate([1.0, 3.5, 5.0]):
            self.conn.execute(
                """
                INSERT INTO reviews (
                    review_id, canonical_hash, parent_asin, asin, user_id, rating,
                    timestamp_raw, review_timestamp_utc, review_epoch_seconds,
                    verified_purchase, source_line_number, source_byte_offset,
                    source_byte_length, ingestion_run_id
                ) VALUES (
                    ?, ?, 'P1', 'V1', 'U1', ?,
                    1600000000000, '2020-09-13T12:26:40.000Z', 1600000000.0,
                    1, 1, 0, 100, ?
                );
                """,
                (f"r_valid_{i}", f"hash_valid_{i}", val, self.run_id),
            )
        self.conn.commit()

        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM reviews WHERE parent_asin = 'P1';")
        self.assertEqual(cur.fetchone()[0], 3)

    def test_composite_foreign_key_rejects_mismatched_variant_parent(self):
        """
        Critical Test:
        Parent P1 has variant V1.
        Parent P2 has variant V2.
        A review with asin='V1' but parent_asin='P2' MUST be rejected by the composite foreign key,
        even though V1 exists in product_variants and P2 exists in products!
        """
        self.conn.execute("INSERT INTO products (parent_asin, first_seen_run_id) VALUES ('P1', ?);", (self.run_id,))
        self.conn.execute("INSERT INTO products (parent_asin, first_seen_run_id) VALUES ('P2', ?);", (self.run_id,))
        self.conn.execute(
            "INSERT INTO product_variants (asin, parent_asin, first_seen_run_id) VALUES ('V1', 'P1', ?);",
            (self.run_id,),
        )
        self.conn.execute(
            "INSERT INTO product_variants (asin, parent_asin, first_seen_run_id) VALUES ('V2', 'P2', ?);",
            (self.run_id,),
        )
        self.conn.commit()

        # Attempt to insert review pairing V1 with P2 (mismatch!)
        with self.assertRaises(sqlite3.IntegrityError) as ctx:
            self.conn.execute(
                """
                INSERT INTO reviews (
                    review_id, canonical_hash, parent_asin, asin, user_id, rating,
                    timestamp_raw, review_timestamp_utc, review_epoch_seconds,
                    verified_purchase, source_line_number, source_byte_offset,
                    source_byte_length, ingestion_run_id
                ) VALUES (
                    'r_mismatch', 'hash_mismatch', 'P2', 'V1', 'U1', 4.0,
                    1600000000000, '2020-09-13T12:26:40.000Z', 1600000000.0,
                    1, 1, 0, 100, ?
                );
                """,
                (self.run_id,),
            )
        self.assertIn("FOREIGN KEY constraint failed", str(ctx.exception))

    def test_composite_foreign_key_accepts_matched_variant_parent(self):
        """Verifies that reviews matching (asin, parent_asin) in product_variants insert cleanly."""
        self.conn.execute("INSERT INTO products (parent_asin, first_seen_run_id) VALUES ('P1', ?);", (self.run_id,))
        self.conn.execute(
            "INSERT INTO product_variants (asin, parent_asin, first_seen_run_id) VALUES ('V1', 'P1', ?);",
            (self.run_id,),
        )
        self.conn.execute(
            """
            INSERT INTO reviews (
                review_id, canonical_hash, parent_asin, asin, user_id, rating,
                timestamp_raw, review_timestamp_utc, review_epoch_seconds,
                verified_purchase, source_line_number, source_byte_offset,
                source_byte_length, ingestion_run_id
            ) VALUES (
                'r_matched', 'hash_matched', 'P1', 'V1', 'U1', 4.0,
                1600000000000, '2020-09-13T12:26:40.000Z', 1600000000.0,
                1, 1, 0, 100, ?
            );
            """,
            (self.run_id,),
        )
        self.conn.commit()

        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM reviews WHERE review_id = 'r_matched';")
        self.assertEqual(cur.fetchone()[0], 1)

    def test_duplicate_review_id_suffix_avoids_pk_collision(self):
        """
        Verifies duplicate review handling:
        Occurrence 0 -> <canonical_hash>
        Occurrence 1 -> <canonical_hash>_#1
        Both are successfully stored with distinct primary keys.
        """
        self.conn.execute("INSERT INTO products (parent_asin, first_seen_run_id) VALUES ('P1', ?);", (self.run_id,))
        self.conn.execute(
            "INSERT INTO product_variants (asin, parent_asin, first_seen_run_id) VALUES ('V1', 'P1', ?);",
            (self.run_id,),
        )

        canonical_hash = "abcdef0123456789abcdef0123456789"
        id_first = canonical_hash
        id_dup = f"{canonical_hash}_#1"

        # First occurrence (index 0)
        self.conn.execute(
            """
            INSERT INTO reviews (
                review_id, canonical_hash, occurrence_index, parent_asin, asin,
                user_id, rating, timestamp_raw, review_timestamp_utc,
                review_epoch_seconds, verified_purchase, source_line_number,
                source_byte_offset, source_byte_length, ingestion_run_id
            ) VALUES (
                ?, ?, 0, 'P1', 'V1', 'U1', 5.0,
                1600000000000, '2020-09-13T12:26:40.000Z', 1600000000.0,
                1, 10, 500, 100, ?
            );
            """,
            (id_first, canonical_hash, self.run_id),
        )

        # Duplicate occurrence (index 1)
        self.conn.execute(
            """
            INSERT INTO reviews (
                review_id, canonical_hash, occurrence_index, parent_asin, asin,
                user_id, rating, timestamp_raw, review_timestamp_utc,
                review_epoch_seconds, verified_purchase, source_line_number,
                source_byte_offset, source_byte_length, ingestion_run_id
            ) VALUES (
                ?, ?, 1, 'P1', 'V1', 'U1', 5.0,
                1600000000000, '2020-09-13T12:26:40.000Z', 1600000000.0,
                1, 25, 1200, 100, ?
            );
            """,
            (id_dup, canonical_hash, self.run_id),
        )
        self.conn.commit()

        cur = self.conn.cursor()
        cur.execute("SELECT review_id, occurrence_index FROM reviews WHERE canonical_hash = ? ORDER BY occurrence_index;", (canonical_hash,))
        rows = cur.fetchall()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0], id_first)
        self.assertEqual(rows[0][1], 0)
        self.assertEqual(rows[1][0], id_dup)
        self.assertEqual(rows[1][1], 1)

    def test_health_check_status_no_sensitive_data(self):
        """Verifies health check output reports connectivity and avoids leaking sensitive details."""
        health = get_health_status(self.conn)
        self.assertEqual(health["status"], "healthy")
        self.assertEqual(health["service"], "ProductPulse API")
        self.assertEqual(health["category_lock"], "Cell_Phones_and_Accessories")
        self.assertEqual(health["database"]["status"], "connected")
        self.assertEqual(health["database"]["foreign_keys"], "enabled")
        self.assertEqual(health["database"]["dataset"], "loaded")

        # Check for sensitive data leakage
        health_str = str(health)
        self.assertNotIn("password", health_str.lower())
        self.assertNotIn("secret", health_str.lower())
        self.assertNotIn("test_productpulse.db", health_str)
        self.assertNotIn(self.temp_dir.name, health_str)


if __name__ == "__main__":
    unittest.main()
