from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.classification import Classification
from app.models.email import Email
from app.models.extraction import Extraction
from app.models.priority import Priority

router = APIRouter(prefix="/metrics", tags=["metrics"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("")
def get_metrics(db: Session = Depends(get_db)) -> dict:
    total_emails = db.query(func.count(Email.id)).scalar() or 0

    # Приоритеты
    priorities = (
        db.query(Priority.priority, func.count(Priority.id))
        .group_by(Priority.priority)
        .all()
    )
    priority_stats = {p: c for p, c in priorities}

    # Категории
    categories = (
        db.query(Classification.category, func.count(Classification.id))
        .group_by(Classification.category)
        .all()
    )
    category_stats = {c: n for c, n in categories}

    # Средняя задержка LLM (по всем трем сервисам)
    avg_class_lat = db.query(func.avg(Classification.latency_ms)).scalar() or 0
    avg_ext_lat = db.query(func.avg(Extraction.latency_ms)).scalar() or 0
    avg_pri_lat = db.query(func.avg(Priority.latency_ms)).scalar() or 0

    # Провайдеры (по классификатору как индикатор)
    providers = (
        db.query(Classification.provider, func.count(Classification.id))
        .group_by(Classification.provider)
        .all()
    )
    provider_stats = {p: c for p, c in providers}

    # Fallback rate (сколько раз сработал fallback на Ollama)
    fallback_count = (
        db.query(func.count(Classification.id))
        .filter(Classification.fallback_used == True)
        .scalar() or 0
    )
    fallback_rate = round(fallback_count / total_emails * 100, 1) if total_emails else 0

    return {
        "total_emails": total_emails,
        "priority_stats": priority_stats,
        "category_stats": category_stats,
        "avg_latency_ms": {
            "classification": round(avg_class_lat),
            "extraction": round(avg_ext_lat),
            "priority": round(avg_pri_lat),
        },
        "provider_stats": provider_stats,
        "fallback_rate": fallback_rate,
    }