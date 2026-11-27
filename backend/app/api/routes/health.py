"""Liveness + database readiness probe (public, no auth)."""

import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


class HealthOut(BaseModel):
    status: Literal["ok", "error"]
    database: Literal["ok", "unavailable"]


@router.get(
    "/health",
    response_model=HealthOut,
    responses={503: {"model": HealthOut, "description": "Database unreachable"}},
)
def health(db: Annotated[Session, Depends(get_db)], response: Response) -> HealthOut:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.exception("Health check: database unreachable")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthOut(status="error", database="unavailable")
    return HealthOut(status="ok", database="ok")
