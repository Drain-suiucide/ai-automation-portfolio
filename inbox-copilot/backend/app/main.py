from fastapi import FastAPI
from app.api.process import router as process_router
from app.api.classify import router as classify_router
from app.api.extract import router as extract_router
from app.api.health import router as health_router
from app.api.prioritize import router as prioritize_router
from app.core.config import settings
import logging
from app.api.emails import router as emails_router
from app.api.drafts import router as drafts_router
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

app = FastAPI(
    title="Inbox Copilot",
    version="0.1.0",
    description="Human-in-the-loop AI assistant for email triage.",
)
app.include_router(emails_router)
app.include_router(process_router)
app.include_router(drafts_router)
app.include_router(health_router, tags=["health"])
app.include_router(classify_router)
app.include_router(extract_router)
app.include_router(prioritize_router)


@app.get("/")
def root() -> dict:
    return {"service": "inbox-copilot", "env": settings.app_env, "version": "0.1.0"}