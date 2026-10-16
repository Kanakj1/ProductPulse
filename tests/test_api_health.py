"""
ProductPulse — Automated Tests for FastAPI Health API Endpoint
Verifies GET /api/health response status, payload fields, database verification,
and CORS headers without starting a live network server.
"""
import unittest

try:
    from fastapi.testclient import TestClient
    from backend.app.main import app
    FASTAPI_AVAILABLE = app is not None
except ImportError:
    FASTAPI_AVAILABLE = False


class TestApiHealthEndpoint(unittest.TestCase):
    """
    Test suite for FastAPI health endpoint using in-process TestClient.
    """

    def setUp(self):
        if not FASTAPI_AVAILABLE:
            self.skipTest("FastAPI not available in environment.")
        self.client = TestClient(app)

    def test_get_health_endpoint_status_200(self):
        """Verifies GET /api/health returns HTTP 200 OK and expected structure."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data.get("status"), "healthy")
        self.assertEqual(data.get("service"), "ProductPulse API")
        self.assertEqual(data.get("version"), "1.0.0")
        self.assertEqual(data.get("category_lock"), "Cell_Phones_and_Accessories")

        db_info = data.get("database", {})
        self.assertEqual(db_info.get("status"), "connected")
        self.assertEqual(db_info.get("foreign_keys"), "enabled")
        self.assertIn(db_info.get("dataset"), ["loaded", "initialized"])

    def test_health_endpoint_cors_headers(self):
        """Verifies CORS header matches authorized frontend origin."""
        response = self.client.get(
            "/api/health",
            headers={"Origin": "http://localhost:5173"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("access-control-allow-origin"),
            "http://localhost:5173",
        )


if __name__ == "__main__":
    unittest.main()
