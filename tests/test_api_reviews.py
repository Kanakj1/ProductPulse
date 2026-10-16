"""
ProductPulse — Automated Tests for Reviews API Endpoint
Verifies GET /api/reviews filtering, pagination, parameter validation, and SQL injection safety.
"""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.db.connection import get_connection, get_db, init_db


class TestApiReviewsEndpoint(unittest.TestCase):
    """
    Test suite for /api/reviews endpoint.
    """

    def setUp(self):
        # 1. Create isolated temporary database
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_db_path = Path(self.temp_dir.name) / "test_reviews.db"
        self.conn = init_db(self.temp_db_path)

        # 2. Populate synthetic fixtures
        self.run_id = "run_test_fixture_02"
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
                1000, 10.0, 206, 'bytes 0-99/1000', 1000, 4,
                4, 0, 0, 0, 0, 2, 2, 4, '/tmp/test.jsonl', 1000,
                'sha256_dummy', '/tmp/manifest.json', '2026-10-14T00:00:00Z',
                '2026-10-14T00:00:01Z', 1.0, 'Synthetic'
            );
            """,
            (self.run_id,),
        )

        self.conn.execute("INSERT INTO products (parent_asin, first_seen_run_id) VALUES ('P1', ?);", (self.run_id,))
        self.conn.execute("INSERT INTO products (parent_asin, first_seen_run_id) VALUES ('P2', ?);", (self.run_id,))

        self.conn.execute("INSERT INTO product_variants (asin, parent_asin, first_seen_run_id) VALUES ('V1', 'P1', ?);", (self.run_id,))
        self.conn.execute("INSERT INTO product_variants (asin, parent_asin, first_seen_run_id) VALUES ('V2', 'P2', ?);", (self.run_id,))

        # 4 Reviews with diverse ratings and verified_purchase flags
        self.conn.execute(
            """
            INSERT INTO reviews (
                review_id, canonical_hash, parent_asin, asin, user_id, rating,
                raw_title, raw_text, timestamp_raw, review_timestamp_utc,
                review_epoch_seconds, helpful_vote, verified_purchase,
                has_images, is_blank_text, source_line_number, source_byte_offset,
                source_byte_length, ingestion_run_id
            ) VALUES
            ('R1', 'h1', 'P1', 'V1', 'U1', 5.0, 'Superb', 'Loved it', 1600000000000, '2020-09-13T12:26:40.000Z', 1600000000.0, 5, 1, 1, 0, 1, 0, 100, ?),
            ('R2', 'h2', 'P1', 'V1', 'U2', 3.0, 'Average', 'Okay', 1600000010000, '2020-09-13T12:26:50.000Z', 1600000010.0, 0, 0, 0, 0, 2, 100, 100, ?),
            ('R3', 'h3', 'P2', 'V2', 'U3', 5.0, 'Awesome', 'Great value', 1600000020000, '2020-09-13T12:27:00.000Z', 1600000020.0, 1, 1, 0, 0, 3, 200, 100, ?),
            ('R4', 'h4', 'P2', 'V2', 'U4', 1.0, 'Terrible', 'Broken on arrival', 1600000030000, '2020-09-13T12:27:10.000Z', 1600000030.0, 3, 1, 0, 0, 4, 300, 100, ?);
            """,
            (self.run_id, self.run_id, self.run_id, self.run_id),
        )
        self.conn.commit()

        # 3. Setup FastAPI dependency override
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

    def test_list_reviews_default(self):
        """Verifies GET /api/reviews returns all reviews ordered by recency descending."""
        response = self.client.get("/api/reviews")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["total_reviews"], 4)
        self.assertEqual(data["limit"], 20)
        self.assertEqual(data["offset"], 0)
        self.assertEqual(len(data["items"]), 4)

        # Ordering should be recency descending: R4 (1600000030), R3, R2, R1
        self.assertEqual([r["review_id"] for r in data["items"]], ["R4", "R3", "R2", "R1"])

    def test_list_reviews_pagination(self):
        """Verifies limit and offset slicing."""
        response = self.client.get("/api/reviews?limit=2&offset=1")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["total_reviews"], 4)
        self.assertEqual(data["limit"], 2)
        self.assertEqual(data["offset"], 1)
        self.assertEqual(len(data["items"]), 2)
        self.assertEqual([r["review_id"] for r in data["items"]], ["R3", "R2"])

    def test_filter_by_parent_asin(self):
        """Verifies filtering by parent_asin."""
        response = self.client.get("/api/reviews?parent_asin=P1")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["total_reviews"], 2)
        for item in data["items"]:
            self.assertEqual(item["parent_asin"], "P1")

    def test_filter_by_variant_asin(self):
        """Verifies filtering by specific variant asin."""
        response = self.client.get("/api/reviews?asin=V2")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["total_reviews"], 2)
        for item in data["items"]:
            self.assertEqual(item["asin"], "V2")

    def test_filter_by_rating(self):
        """Verifies filtering by source star rating."""
        response = self.client.get("/api/reviews?rating=5.0")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["total_reviews"], 2)
        for item in data["items"]:
            self.assertEqual(item["rating"], 5.0)

    def test_filter_by_verified_purchase(self):
        """Verifies filtering by verified_purchase=true and verified_purchase=false."""
        r_verified = self.client.get("/api/reviews?verified_purchase=true")
        self.assertEqual(r_verified.status_code, 200)
        data_v = r_verified.json()
        self.assertEqual(data_v["total_reviews"], 3)  # R1, R3, R4

        r_unverified = self.client.get("/api/reviews?verified_purchase=false")
        self.assertEqual(r_unverified.status_code, 200)
        data_u = r_unverified.json()
        self.assertEqual(data_u["total_reviews"], 1)  # R2

    def test_combined_filters(self):
        """Verifies combined filtering (parent_asin + rating + verified_purchase)."""
        response = self.client.get("/api/reviews?parent_asin=P1&rating=5.0&verified_purchase=true")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["total_reviews"], 1)
        self.assertEqual(data["items"][0]["review_id"], "R1")

    def test_empty_results_clean_handling(self):
        """Verifies that non-matching criteria returns 200 with total=0 and empty items."""
        response = self.client.get("/api/reviews?parent_asin=NONEXISTENT")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["total_reviews"], 0)
        self.assertEqual(data["items"], [])

    def test_invalid_rating_parameter(self):
        """Verifies ratings < 1.0 or > 5.0 return HTTP 422."""
        r_low = self.client.get("/api/reviews?rating=0.5")
        self.assertEqual(r_low.status_code, 422)

        r_high = self.client.get("/api/reviews?rating=5.5")
        self.assertEqual(r_high.status_code, 422)

    def test_sql_injection_defense(self):
        """
        Verifies that SQL injection payloads in query parameters are safely handled
        via parameterized statements and do not leak data or cause SQL syntax errors.
        """
        injections = [
            "/api/reviews?parent_asin=' OR 1=1 --",
            "/api/reviews?asin=' UNION SELECT * FROM reviews --",
            "/api/reviews?parent_asin=P1'; DROP TABLE reviews; --",
        ]
        for inj in injections:
            response = self.client.get(inj)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            # None of the injection strings match literal ASINs, so count must be 0
            self.assertEqual(data["total_reviews"], 0)

        # Verify reviews table remains intact
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM reviews;")
        self.assertEqual(cur.fetchone()[0], 4)


if __name__ == "__main__":
    unittest.main()
