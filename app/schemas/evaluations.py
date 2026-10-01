from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator
from datetime import date, datetime
from decimal import Decimal


PositiveId = Annotated[int, Field(strict=True, gt=0)]
Score = Annotated[int, Field(strict=True, ge=1, le=4)]


class AnswerCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: PositiveId
    score: Score


class EvaluationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    employee_id: PositiveId
    answers: list[AnswerCreate] = Field(
        min_length=6,
        max_length=6,
    )

    @model_validator(mode="after")
    def validate_unique_questions(self) -> "EvaluationCreate":
        question_ids = [
            answer.question_id
            for answer in self.answers
        ]

        if len(question_ids) != len(set(question_ids)):
            raise ValueError(
                "Cada questão deve ser respondida uma única vez."
            )

        return self
    
class EvaluationResponse(BaseModel):
    id: int
    leader_id: int
    employee_id: int
    week_start: date
    submitted_at: datetime
   
    
class AnswerDetail(BaseModel):
    question_id: int
    title: str
    weight: int
    score: int


class EvaluationDetail(EvaluationResponse):
    weighted_score: Decimal
    answers: list[AnswerDetail]