from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.schemas.pipeline import ProcessRequest, ProcessResponse
from app.services.llm_client import LLMError
from app.services.pipeline import DuplicateEmailError, process_email

router = APIRouter(prefix="/process", tags=["process"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=ProcessResponse)
def process(payload: ProcessRequest, db: Session = Depends(get_db)) -> ProcessResponse:
    try:
        return process_email(db, payload)
    except DuplicateEmailError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except LLMError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e}") from e