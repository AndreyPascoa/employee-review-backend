from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db


router = APIRouter(
    prefix="/leaders",
    tags=["Líderes"],
)


class LeaderResponse(BaseModel):
    id: int
    name: str


@router.get("", response_model=list[LeaderResponse])
def list_leaders(
    db: Annotated[Session, Depends(get_db)],
):
    query = text(
        """
        SELECT
            employee.id,
            employee.name
        FROM employee_reviews.employee AS employee
        WHERE EXISTS (
            SELECT 1
            FROM employee_reviews.leader_lead AS relationship
            WHERE relationship.leader_id = employee.id
        )
        ORDER BY employee.name, employee.id
        """
    )

    result = db.execute(query)
    return result.mappings().all()