from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.config import settings

app = FastAPI(
    title="Inbox Copilot",
    version="0.1.0",
    description="Human-in-the-loop AI assistant for email triage.",
)

app.include_router(health_router, tags=["health"])


@app.get("/")
def root() -> dict:
    return {"service": "inbox-copilot", "env": settings.app_env, "version": "0.1.0"}