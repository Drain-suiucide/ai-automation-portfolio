import time

import redis
from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine

router = APIRouter()


@router.get("/health")
def health() -> dict:
    result: dict = {"status": "ok", "checks": {}}

    # Postgres
    t0 = time.perf_counter()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        result["checks"]["postgres"] = {
            "ok": True,
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
        }
    except Exception as e:
        result["status"] = "degraded"
        result["checks"]["postgres"] = {"ok": False, "error": str(e)}

    # Redis
    t0 = time.perf_counter()
    try:
        r = redis.from_url(settings.redis_url, socket_connect_timeout=2)
        r.ping()
        result["checks"]["redis"] = {
            "ok": True,
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
        }
    except Exception as e:
        result["status"] = "degraded"
        result["checks"]["redis"] = {"ok": False, "error": str(e)}

    return result