"""
ProductPulse — Automated Tests for Big Data Analytics API Endpoints
Verifies that /api/analytics endpoints faithfully serve authentic Hadoop MapReduce
and Apache Hive analytical outputs with exact schema conformity, correct calculations,
and adherence to the 6 locked aspects.
"""
import unittest

try:
    from fastapi.testclient import TestClient
    from backend.app.main import app
    FASTAPI_AVAILABLE = app is not None
except ImportError:
    FASTAPI_AVAILABLE = False


class TestAnalyticsApiEndpoints(unittest.TestCase):
    """
    Test suite for Big Data Analytics API endpoints using in-process TestClient.
    """

    def setUp(self):
        if not FASTAPI_AVAILABLE:
            self.skipTest("FastAPI not available in environment.")
        self.client = TestClient(app)
        self.locked_aspects = [
            "build_durability",
            "battery_charging",
            "screen_display",
            "performance_software",
            "camera_optics",
            "connectivity_audio",
        ]

    def test_get_analytics_overview(self):
        """Verifies GET /api/analytics/overview returns expected summary metrics and disclosures."""
        response = self.client.get("/api/analytics/overview")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["total_reviews_evaluated"], 25000)
        self.assertEqual(data["total_products_evaluated"], 19065)
        self.assertEqual(data["corpus_avg_star_rating"], 4.1655)
        self.assertEqual(data["aspect_reviews_avg_star_rating"], 4.1299)
        self.assertEqual(data["reviews_with_aspect_mentions"], 16409)
        self.assertEqual(data["reviews_with_no_aspect"], 8591)
        self.assertEqual(
            data["reviews_with_aspect_mentions"] + data["reviews_with_no_aspect"],
            data["total_reviews_evaluated"],
            "Unique reviews with aspects + reviews without aspects must partition all 25,000 reviews exactly",
        )
        self.assertEqual(data["total_aspect_review_pairs"], 26029)
        self.assertEqual(data["total_aspect_mentions"], 26029)
        self.assertEqual(data["locked_aspect_count"], 6)
        self.assertEqual(data["locked_aspects"], self.locked_aspects)
        self.assertIn("Hadoop", data["execution_engine"])
        self.assertIn("Hive", data["execution_engine"])
        self.assertGreater(len(data["methodology_notes"]), 3)

    def test_get_aspect_volumes(self):
        """Verifies GET /api/analytics/aspect-volumes returns exactly the 6 locked aspects with exact counts."""
        response = self.client.get("/api/analytics/aspect-volumes")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["total_aspects"], 6)
        items = data["items"]
        self.assertEqual(len(items), 6)

        aspect_map = {item["aspect"]: item for item in items}
        # Check all 6 locked aspects exist exactly once
        for asp in self.locked_aspects:
            self.assertIn(asp, aspect_map)
            item = aspect_map[asp]
            self.assertIsInstance(item["aspect_label"], str)
            self.assertGreater(item["total_aspect_reviews"], 0)
            self.assertGreaterEqual(item["weighted_avg_rating"], 1.0)
            self.assertLessEqual(item["weighted_avg_rating"], 5.0)
            self.assertGreaterEqual(item["total_helpful_votes"], 0)

        # Reconcile exact counts
        self.assertEqual(aspect_map["build_durability"]["total_aspect_reviews"], 10846)
        self.assertEqual(aspect_map["battery_charging"]["total_aspect_reviews"], 4514)
        self.assertEqual(aspect_map["screen_display"]["total_aspect_reviews"], 4350)
        self.assertEqual(aspect_map["performance_software"]["total_aspect_reviews"], 2506)
        self.assertEqual(aspect_map["camera_optics"]["total_aspect_reviews"], 2256)
        self.assertEqual(aspect_map["connectivity_audio"]["total_aspect_reviews"], 1557)

        # Weighted average rating exact checks
        self.assertAlmostEqual(aspect_map["build_durability"]["weighted_avg_rating"], 4.1485, places=4)
        self.assertAlmostEqual(aspect_map["performance_software"]["weighted_avg_rating"], 4.1923, places=4)

    def test_get_top_products(self):
        """Verifies GET /api/analytics/top-products returns 25 top products and respects filters."""
        response = self.client.get("/api/analytics/top-products")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["total_items"], 25)
        self.assertEqual(len(data["items"]), 25)

        # Top product should be B07P9S6R9Y battery_charging 30 reviews
        first = data["items"][0]
        self.assertEqual(first["parent_asin"], "B07P9S6R9Y")
        self.assertEqual(first["aspect"], "battery_charging")
        self.assertEqual(first["aspect_review_count"], 30)

        # Test aspect filter
        filtered_res = self.client.get("/api/analytics/top-products?aspect=build_durability")
        self.assertEqual(filtered_res.status_code, 200)
        f_data = filtered_res.json()
        for item in f_data["items"]:
            self.assertEqual(item["aspect"], "build_durability")

        # Test ASIN filter
        asin_res = self.client.get("/api/analytics/top-products?parent_asin=B07P9S6R9Y")
        self.assertEqual(asin_res.status_code, 200)
        a_data = asin_res.json()
        self.assertGreaterEqual(len(a_data["items"]), 1)
        self.assertEqual(a_data["items"][0]["parent_asin"], "B07P9S6R9Y")

    def test_get_pain_points(self):
        """Verifies GET /api/analytics/pain-points returns lowest-rated aspects with N>=5."""
        response = self.client.get("/api/analytics/pain-points")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["total_items"], 25)
        self.assertIn("not verified hardware defects", data["scientific_disclaimer"])

        items = data["items"]
        for item in items:
            self.assertGreaterEqual(item["aspect_review_count"], 5)
            self.assertGreaterEqual(item["avg_rating"], 1.0)
            self.assertLessEqual(item["avg_rating"], 5.0)

        # Verify sorted ascending by avg_rating
        ratings = [it["avg_rating"] for it in items]
        self.assertEqual(ratings, sorted(ratings))

    def test_get_rating_bands(self):
        """Verifies GET /api/analytics/rating-bands reconciles with aspect volume totals."""
        response = self.client.get("/api/analytics/rating-bands")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["total_aspects"], 6)

        # Fetch volume response to cross-verify total_aspect_reviews
        vol_data = self.client.get("/api/analytics/aspect-volumes").json()["items"]
        vol_map = {it["aspect"]: it["total_aspect_reviews"] for it in vol_data}

        for item in data["items"]:
            asp = item["aspect"]
            low = item["low_rating_reviews_1_to_2_stars"]
            med = item["med_rating_reviews_3_stars"]
            high = item["high_rating_reviews_4_to_5_stars"]
            total = item["total_aspect_reviews"]

            self.assertEqual(low + med + high, total, f"Rating band sum mismatch for {asp}")
            self.assertEqual(total, vol_map[asp], f"Volume mismatch between Query 1 and Query 4 for {asp}")
            self.assertAlmostEqual(item["high_rating_pct"] + item["low_rating_pct"], (high + low) * 100.0 / total, places=1)

    def test_get_aspect_penetration(self):
        """Verifies GET /api/analytics/aspect-penetration adheres to [0.0%, 100.0%] bounds."""
        response = self.client.get("/api/analytics/aspect-penetration")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["total_items"], 25)

        for item in data["items"]:
            pct = item["aspect_review_penetration_pct"]
            mentions = item["reviews_mentioning_aspect"]
            total_rev = item["total_product_reviews"]

            self.assertGreaterEqual(pct, 0.0)
            self.assertLessEqual(pct, 100.0)
            self.assertLessEqual(mentions, total_rev)
            expected_pct = round(mentions * 100.0 / total_rev, 1)
            self.assertEqual(pct, expected_pct)


if __name__ == "__main__":
    unittest.main()
