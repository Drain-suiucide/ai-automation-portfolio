from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.schemas.email import EmailDetail, EmailListResponse
from app.services.email_reader import get_email, list_emails

router = APIRouter(prefix="/emails", tags=["emails"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=EmailListResponse)
def list_endpoint(
    category: str | None = Query(None),
    priority: str | None = Query(None, pattern="^P[0-3]$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> EmailListResponse:
    return list_emails(
        db, category=category, priority=priority, limit=limit, offset=offset
    )


@router.get("/{email_id}", response_model=EmailDetail)
def detail_endpoint(email_id: str, db: Session = Depends(get_db)) -> EmailDetail:
    email = get_email(db, email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return email