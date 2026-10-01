from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db


def get_current_leader_id(
    leader_id: Annotated[int, Header(alias="X-Leader-ID", gt=0)],
    db: Annotated[Session, Depends(get_db)],
) -> int:
    employee_id = db.execute(
        text(
            """
            SELECT id
            FROM employee_reviews.employee
            WHERE id = :employee_id
            """
        ),
        {"employee_id": leader_id},
    ).scalar_one_or_none()

    if employee_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Funcionário selecionado não encontrado.",
        )

    return employee_id