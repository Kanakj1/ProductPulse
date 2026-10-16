"""
ProductPulse — Automated Tests for Products API Endpoints
Verifies GET /api/products and GET /api/products/{parent_asin} using isolated test databases.
"""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.db.connection import get_connection, get_db, init_db


class TestApiProductsEndpoints(unittest.TestCase):
    """
    Test suite for /api/products catalog and detail endpoints.
    """

    def setUp(self):
        # 1. Create isolated temporary database
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_db_path = Path(self.temp_dir.name) / "test_products.db"
        self.conn = init_db(self.temp_db_path)

        # 2. Populate synthetic fixtures
        self.run_id = "run_test_fixture_01"
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
                ?, 'TestDataset', 'Cell_Phones_and_Accessories', 'http://test', 10,
                1000, 10.0, 206, 'bytes 0-99/1000', 1000, 3,
                3, 0, 0, 0, 0, 2, 3, 3, '/tmp/test.jsonl', 1000,
                'sha256_dummy', '/tmp/manifest.json', '2026-10-14T00:00:00Z',
                '2026-10-14T00:00:01Z', 1.0, 'Synthetic'
            );
            """,
            (self.run_id,),
        )

        # Two products
        self.conn.execute(
            "INSERT INTO products (parent_asin, first_seen_run_id) VALUES ('P1', ?);",
            (self.run_id,),
        )
        self.conn.execute(
            "INSERT INTO products (parent_asin, first_seen_run_id) VALUES ('P2', ?);",
            (self.run_id,),
        )

        # Three variants: P1 has V1 & V2; P2 has V3
        self.conn.execute(
            "INSERT INTO product_variants (asin, parent_asin, first_seen_run_id) VALUES ('V1', 'P1', ?);",
            (self.run_id,),
        )
        self.conn.execute(
            "INSERT INTO product_variants (asin, parent_asin, first_seen_run_id) VALUES ('V2', 'P1', ?);",
            (self.run_id,),
        )
        self.conn.execute(
            "INSERT INTO product_variants (asin, parent_asin, first_seen_run_id) VALUES ('V3', 'P2', ?);",
            (self.run_id,),
        )

        # Three reviews: P1 has 2 reviews (ratings 5.0 and 4.0); P2 has 1 review (rating 2.0)
        self.conn.execute(
            """
            INSERT INTO reviews (
                review_id, canonical_hash, parent_asin, asin, user_id, rating,
                raw_title, raw_text, timestamp_raw, review_timestamp_utc,
                review_epoch_seconds, helpful_vote, verified_purchase,
                has_images, is_blank_text, source_line_number, source_byte_offset,
                source_byte_length, ingestion_run_id
            ) VALUES
            ('R1', 'h1', 'P1', 'V1', 'U1', 5.0, 'Great', 'Works well', 1600000000000, '2020-09-13T12:26:40.000Z', 1600000000.0, 1, 1, 0, 0, 1, 0, 100, ?),
            ('R2', 'h2', 'P1', 'V2', 'U2', 4.0, 'Good', 'Decent', 1600000001000, '2020-09-13T12:26:41.000Z', 1600000001.0, 0, 1, 1, 0, 2, 100, 100, ?),
            ('R3', 'h3', 'P2', 'V3', 'U3', 2.0, 'Bad', 'Poor battery', 1600000002000, '2020-09-13T12:26:42.000Z', 1600000002.0, 2, 0, 0, 0, 3, 200, 100, ?);
            """,
            (self.run_id, self.run_id, self.run_id),
        )
        self.conn.commit()

        # 3. Setup FastAPI dependency override to use temporary database
        def override_get_db():
            conn = get_connection(self.temp_db_path)
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.conn.close()
        self.temp_dir.cleanup()

    def test_list_products_default_pagination(self):
        """Verifies GET /api/products returns HTTP 200 with paginated product list."""
        response = self.client.get("/api/products")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["total_products"], 2)
        self.assertEqual(data["limit"], 20)
        self.assertEqual(data["offset"], 0)
        self.assertIn("rating_basis", data)

        items = data["items"]
        self.assertEqual(len(items), 2)
        # P1 has 2 reviews, P2 has 1 review -> P1 should be first
        self.assertEqual(items[0]["parent_asin"], "P1")
        self.assertEqual(items[0]["review_count"], 2)
        self.assertEqual(items[0]["avg_rating"], 4.5)
        self.assertEqual(items[1]["parent_asin"], "P2")
        self.assertEqual(items[1]["review_count"], 1)
        self.assertEqual(items[1]["avg_rating"], 2.0)

    def test_list_products_custom_pagination(self):
        """Verifies limit and offset parameters work correctly."""
        response = self.client.get("/api/products?limit=1&offset=1")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["total_products"], 2)
        self.assertEqual(data["limit"], 1)
        self.assertEqual(data["offset"], 1)
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["parent_asin"], "P2")

    def test_list_products_invalid_limit(self):
        """Verifies that limit=0 or limit>100 returns HTTP 422 Unprocessable Entity."""
        r_zero = self.client.get("/api/products?limit=0")
        self.assertEqual(r_zero.status_code, 422)

        r_high = self.client.get("/api/products?limit=101")
        self.assertEqual(r_high.status_code, 422)

    def test_list_products_invalid_offset(self):
        """Verifies that offset < 0 returns HTTP 422."""
        response = self.client.get("/api/products?offset=-1")
        self.assertEqual(response.status_code, 422)

    def test_get_product_detail_success(self):
        """Verifies GET /api/products/{parent_asin} returns comprehensive product details."""
        response = self.client.get("/api/products/P1")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["parent_asin"], "P1")
        self.assertEqual(data["main_category"], "Cell_Phones_and_Accessories")
        self.assertFalse(data["has_metadata"])
        self.assertIn("metadata_notice", data)

        # Variants
        self.assertEqual(sorted(data["variants"]), ["V1", "V2"])

        # Statistics
        self.assertEqual(data["review_count"], 2)
        self.assertEqual(data["avg_rating"], 4.5)
        self.assertEqual(data["verified_purchase_count"], 2)
        self.assertEqual(data["has_images_count"], 1)
        self.assertEqual(data["first_review_utc"], "2020-09-13T12:26:40.000Z")
        self.assertEqual(data["latest_review_utc"], "2020-09-13T12:26:41.000Z")

        # Rating distribution
        dist = data["rating_distribution"]
        self.assertEqual(dist["stars_5"], 1)
        self.assertEqual(dist["stars_4"], 1)
        self.assertEqual(dist["stars_3"], 0)
        self.assertEqual(dist["stars_2"], 0)
        self.assertEqual(dist["stars_1"], 0)

    def test_get_product_detail_not_found(self):
        """Verifies that an unknown parent_asin returns HTTP 404."""
        response = self.client.get("/api/products/NONEXISTENT_PARENT")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("not found", data["detail"].lower())

    def test_get_product_detail_sql_injection_attempt(self):
        """
        Verifies that injection strings in the path parameter are safely treated
        as literal string identifiers and return 404 without database corruption.
        """
        injection_paths = [
            "/api/products/' OR '1'='1",
            "/api/products/P1'; DROP TABLE reviews; --",
        ]
        for path in injection_paths:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 404)

        # Confirm reviews table is still completely intact
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM reviews;")
        self.assertEqual(cur.fetchone()[0], 3)


if __name__ == "__main__":
    unittest.main()
