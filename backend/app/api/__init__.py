"""
ProductPulse — API Routers Package
"""
from backend.app.api.health import router as health_router
from backend.app.api.products import router as products_router
from backend.app.api.reviews import router as reviews_router

__all__ = ["health_router", "products_router", "reviews_router"]
