from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_leader_id


router = APIRouter(
    prefix="/employees",
    tags=["Funcionários"],
)


class EmployeeResponse(BaseModel):
    id: int
    name: str
    email: str
    position_name: str


@router.get("", response_model=list[EmployeeResponse])
def list_subordinates(
    leader_id: Annotated[int, Depends(get_current_leader_id)],
    db: Annotated[Session, Depends(get_db)],
):
    query = text(
        """
        WITH RECURSIVE subordinates AS (
            SELECT lead_id AS employee_id
            FROM employee_reviews.leader_lead
            WHERE leader_id = :leader_id

            UNION

            SELECT relationship.lead_id
            FROM employee_reviews.leader_lead AS relationship
            JOIN subordinates
                ON relationship.leader_id = subordinates.employee_id
        )
        SELECT
            employee.id,
            employee.name,
            employee.email,
            employee.position_name
        FROM employee_reviews.employee AS employee
        JOIN subordinates
            ON subordinates.employee_id = employee.id
        WHERE employee.id <> :leader_id
        ORDER BY employee.name, employee.id
        """
    )

    result = db.execute(query, {"leader_id": leader_id})
    return result.mappings().all()