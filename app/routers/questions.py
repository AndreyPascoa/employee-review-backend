from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db


router = APIRouter(
    prefix="/questions",
    tags=["Questões"],
)


class QuestionResponse(BaseModel):
    id: int
    title: str
    weight: int


@router.get("", response_model=list[QuestionResponse])
def list_questions(
    db: Annotated[Session, Depends(get_db)],
):
    query = text(
        """
        SELECT id, title, weight
        FROM employee_reviews.question
        ORDER BY id
        """
    )

    result = db.execute(query)
    return result.mappings().all()