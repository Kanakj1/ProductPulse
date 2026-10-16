"""
ProductPulse — Health API Endpoint
Reports backend and database health status without exposing sensitive information.
"""
import sqlite3
from typing import Any, Dict, Optional

CATEGORY_LOCK = "Cell_Phones_and_Accessories"
API_VERSION = "1.0.0"


def get_health_status(conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
    """
    Evaluates backend and database health safely.
    Strictly avoids leaking filesystem paths, credentials, or internal environment details.
    """
    db_status = "not_connected"
    foreign_keys_status = "unknown"
    dataset_status = "uninitialized"

    if conn is not None:
        try:
            cur = conn.cursor()
            # 1. Connectivity check
            cur.execute("SELECT 1;")
            one_res = cur.fetchone()
            if one_res and one_res[0] == 1:
                db_status = "connected"

            # 2. Foreign key pragma verification
            cur.execute("PRAGMA foreign_keys;")
            fk_res = cur.fetchone()
            if fk_res and fk_res[0] == 1:
                foreign_keys_status = "enabled"
            else:
                foreign_keys_status = "disabled"

            # 3. Non-sensitive dataset presence check
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='ingestion_runs';"
            )
            table_res = cur.fetchone()
            if table_res:
                cur.execute("SELECT COUNT(*) FROM ingestion_runs;")
                runs_count = cur.fetchone()[0]
                dataset_status = "loaded" if runs_count > 0 else "initialized"
            else:
                dataset_status = "schema_pending"

        except Exception:
            db_status = "error"
            dataset_status = "error"

    overall_healthy = (db_status == "connected") and (foreign_keys_status == "enabled")

    return {
        "status": "healthy" if overall_healthy else "degraded",
        "service": "ProductPulse API",
        "version": API_VERSION,
        "category_lock": CATEGORY_LOCK,
        "database": {
            "status": db_status,
            "foreign_keys": foreign_keys_status,
            "dataset": dataset_status,
        },
    }


# FastAPI router definition (conditional import for environments without FastAPI)
try:
    from fastapi import APIRouter, Depends, Response, status
    from backend.db.connection import get_db

    router = APIRouter(tags=["Health"])

    @router.get("/health", summary="Backend Health Check")
    def health_check(
        response: Response,
        db: sqlite3.Connection = Depends(get_db),
    ) -> Dict[str, Any]:
        """
        Public health endpoint returning system operational status.
        Does not expose internal paths, secrets, or server configurations.
        """
        health_data = get_health_status(db)
        if health_data["status"] != "healthy":
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return health_data

except ImportError:
    router = None
