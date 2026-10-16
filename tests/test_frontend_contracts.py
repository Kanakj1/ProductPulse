"""
ProductPulse — Frontend Contract & Integrity Tests
Validates frontend file structure, configuration invariants, and schema parity with backend Pydantic models.
"""
import json
import re
from pathlib import Path
import unittest

from backend.app.schemas.products import (
    ProductSummary,
    ProductListResponse,
    RatingDistribution,
    ProductDetailResponse,
)
from backend.app.schemas.reviews import (
    ReviewItem,
    ReviewListResponse,
)


class TestFrontendContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace_root = Path(__file__).resolve().parent.parent
        cls.frontend_dir = cls.workspace_root / "frontend"
        cls.api_types_file = cls.frontend_dir / "src" / "types" / "api.ts"
        cls.api_config_file = cls.frontend_dir / "src" / "api" / "config.ts"
        cls.api_client_file = cls.frontend_dir / "src" / "api" / "client.ts"

    def test_frontend_structure_exists(self):
        """Verifies that all required frontend foundation files exist."""
        required_files = [
            "package.json",
            "tsconfig.json",
            "tsconfig.node.json",
            "vite.config.ts",
            "tailwind.config.js",
            "postcss.config.js",
            "index.html",
            "src/main.tsx",
            "src/App.tsx",
            "src/index.css",
            "src/types/api.ts",
            "src/api/config.ts",
            "src/api/client.ts",
            "src/components/common/StarRating.tsx",
            "src/components/common/StatusBadge.tsx",
            "src/components/common/Pagination.tsx",
            "src/components/common/OfflineBanner.tsx",
            "src/components/common/NoticeBanner.tsx",
            "src/components/layout/Navbar.tsx",
            "src/components/layout/Footer.tsx",
            "src/components/overview/OverviewView.tsx",
            "src/components/catalogue/ProductCatalogueView.tsx",
            "src/components/catalogue/ProductDetailModal.tsx",
            "src/components/reviews/ReviewsView.tsx",
            "src/components/future/FutureFeaturePlaceholder.tsx",
            "tests/api_client.test.ts",
        ]

        for rel_path in required_files:
            file_path = self.frontend_dir / rel_path
            self.assertTrue(
                file_path.exists(),
                f"Missing required frontend file: {rel_path}",
            )

    def test_package_json_dependencies(self):
        """Verifies package.json dependencies and scripts."""
        package_json_path = self.frontend_dir / "package.json"
        with open(package_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get("name"), "productpulse-frontend")
        deps = data.get("dependencies", {})
        dev_deps = data.get("devDependencies", {})

        self.assertIn("react", deps)
        self.assertIn("react-dom", deps)
        self.assertIn("vite", dev_deps)
        self.assertIn("typescript", dev_deps)
        self.assertIn("tailwindcss", dev_deps)

    def test_api_config_invariants(self):
        """Verifies centralized API config defaults to localhost:8000 and Cell_Phones_and_Accessories."""
        content = self.api_config_file.read_text(encoding="utf-8")
        self.assertIn("http://localhost:8000", content)
        self.assertIn("Cell_Phones_and_Accessories", content)

    def test_vite_config_bindings(self):
        """Verifies vite.config.ts binds to port 5173 and 127.0.0.1."""
        vite_cfg = (self.frontend_dir / "vite.config.ts").read_text(encoding="utf-8")
        self.assertIn("port: 5173", vite_cfg)
        self.assertIn("host: '127.0.0.1'", vite_cfg)

    def test_schema_parity_product_summary(self):
        """Verifies frontend ProductSummary has all Pydantic ProductSummary fields."""
        ts_content = self.api_types_file.read_text(encoding="utf-8")
        for field_name in ProductSummary.model_fields.keys():
            self.assertRegex(
                ts_content,
                rf"\b{field_name}\b",
                f"Field '{field_name}' in Pydantic ProductSummary not found in api.ts",
            )

    def test_schema_parity_product_list_response(self):
        """Verifies frontend ProductListResponse has all Pydantic ProductListResponse fields."""
        ts_content = self.api_types_file.read_text(encoding="utf-8")
        for field_name in ProductListResponse.model_fields.keys():
            self.assertRegex(
                ts_content,
                rf"\b{field_name}\b",
                f"Field '{field_name}' in Pydantic ProductListResponse not found in api.ts",
            )

    def test_schema_parity_rating_distribution(self):
        """Verifies frontend RatingDistribution has all Pydantic RatingDistribution fields."""
        ts_content = self.api_types_file.read_text(encoding="utf-8")
        for field_name in RatingDistribution.model_fields.keys():
            self.assertRegex(
                ts_content,
                rf"\b{field_name}\b",
                f"Field '{field_name}' in Pydantic RatingDistribution not found in api.ts",
            )

    def test_schema_parity_product_detail_response(self):
        """Verifies frontend ProductDetailResponse has all Pydantic ProductDetailResponse fields."""
        ts_content = self.api_types_file.read_text(encoding="utf-8")
        for field_name in ProductDetailResponse.model_fields.keys():
            self.assertRegex(
                ts_content,
                rf"\b{field_name}\b",
                f"Field '{field_name}' in Pydantic ProductDetailResponse not found in api.ts",
            )

    def test_schema_parity_review_item(self):
        """Verifies frontend ReviewItem has all Pydantic ReviewItem fields."""
        ts_content = self.api_types_file.read_text(encoding="utf-8")
        for field_name in ReviewItem.model_fields.keys():
            self.assertRegex(
                ts_content,
                rf"\b{field_name}\b",
                f"Field '{field_name}' in Pydantic ReviewItem not found in api.ts",
            )

    def test_schema_parity_review_list_response(self):
        """Verifies frontend ReviewListResponse has all Pydantic ReviewListResponse fields."""
        ts_content = self.api_types_file.read_text(encoding="utf-8")
        for field_name in ReviewListResponse.model_fields.keys():
            self.assertRegex(
                ts_content,
                rf"\b{field_name}\b",
                f"Field '{field_name}' in Pydantic ReviewListResponse not found in api.ts",
            )

    def test_api_client_routes_alignment(self):
        """Verifies that the API client calls exact backend routes."""
        client_code = self.api_client_file.read_text(encoding="utf-8")
        self.assertIn("/api/health", client_code)
        self.assertIn("/api/products?", client_code)
        self.assertIn("/api/products/${safeAsin}", client_code)
        self.assertIn("/api/reviews?", client_code)


if __name__ == "__main__":
    unittest.main()
