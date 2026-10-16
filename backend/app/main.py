"""
ProductPulse — FastAPI Backend Application Entrypoint
Binds CORS strictly to http://localhost:5173 and mounts /api endpoints.
"""
from typing import Any, Dict

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from backend.app.api.health import router as health_router
    from backend.app.api.products import router as products_router
    from backend.app.api.reviews import router as reviews_router
    from backend.app.api.analytics import router as analytics_router

    app = FastAPI(
        title="ProductPulse API",
        description="Mobile Phones & Accessories Review Analytics Backend",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # Restrict CORS to authorized frontend hosts
    ALLOWED_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # Mount API routers under /api prefix
    app.include_router(health_router, prefix="/api")
    app.include_router(products_router, prefix="/api")
    app.include_router(reviews_router, prefix="/api")
    app.include_router(analytics_router, prefix="/api")

except ImportError:
    # Fallback placeholder when FastAPI is not yet installed in the Python environment
    app = None  # type: ignore[assignment]


def get_application() -> Any:
    """
    Factory function for the FastAPI application instance.
    Raises RuntimeError if FastAPI is not installed in the environment.
    """
    if app is None:
        raise RuntimeError(
            "FastAPI is not installed in the current Python environment. "
            "Please ensure fastapi is installed before running the server."
        )
    return app


if __name__ == "__main__":
    # Note: Environment safety rule prohibits starting servers without user authorization.
    print("ProductPulse Backend module prepared. Use an ASGI server to launch when authorized.")
