from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_leader_id
from app.schemas.evaluations import (
    EvaluationCreate,
    EvaluationDetail,
    EvaluationResponse,
)
from app.services.evaluations import (
    create_evaluation,
    get_latest_evaluation,
)

router = APIRouter(
    prefix="/evaluations",
    tags=["Avaliações"],
)


@router.post(
    "",
    response_model=EvaluationResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_evaluation(
    payload: EvaluationCreate,
    leader_id: Annotated[int, Depends(get_current_leader_id)],
    db: Annotated[Session, Depends(get_db)],
):
    return create_evaluation(
        db=db,
        leader_id=leader_id,
        payload=payload,
    )
    
@router.get(
    "/employee/{employee_id}/latest",
    response_model=EvaluationDetail,
)
def latest_evaluation(
    employee_id: Annotated[int, Path(gt=0)],
    leader_id: Annotated[int, Depends(get_current_leader_id)],
    db: Annotated[Session, Depends(get_db)],
):
    return get_latest_evaluation(
        db=db,
        leader_id=leader_id,
        employee_id=employee_id,
    )