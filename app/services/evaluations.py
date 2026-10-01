from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.schemas.evaluations import EvaluationCreate


def create_evaluation(
    db: Session,
    leader_id: int,
    payload: EvaluationCreate,
) -> dict:
    # Verifica se o funcionário pertence à hierarquia do líder.
    subordinate_id = db.execute(
        text(
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
            SELECT employee_id
            FROM subordinates
            WHERE employee_id = :employee_id
              AND employee_id <> :leader_id
            """
        ),
        {
            "leader_id": leader_id,
            "employee_id": payload.employee_id,
        },
    ).scalar_one_or_none()

    if subordinate_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode avaliar seus subordinados.",
        )

    # Confere se foram enviadas exatamente as questões cadastradas.
    expected_question_ids = set(
        db.execute(
            text("SELECT id FROM employee_reviews.question")
        ).scalars().all()
    )

    received_question_ids = {
        answer.question_id
        for answer in payload.answers
    }

    if received_question_ids != expected_question_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Responda exatamente às questões cadastradas.",
        )

    try:
        # O banco calcula a semana pelo horário de São Paulo.
        evaluation = db.execute(
            text(
                """
                INSERT INTO employee_reviews.evaluation (
                    leader_id,
                    employee_id,
                    week_start
                )
                VALUES (
                    :leader_id,
                    :employee_id,
                    CAST(
                        date_trunc(
                            'week',
                            CURRENT_TIMESTAMP
                                AT TIME ZONE 'America/Sao_Paulo'
                        )
                        AS date
                    )
                )
                RETURNING
                    id,
                    leader_id,
                    employee_id,
                    week_start,
                    submitted_at
                """
            ),
            {
                "leader_id": leader_id,
                "employee_id": payload.employee_id,
            },
        ).mappings().one()

        # Salva as seis respostas na mesma transação.
        db.execute(
            text(
                """
                INSERT INTO employee_reviews.answer (
                    evaluation_id,
                    question_id,
                    score
                )
                VALUES (
                    :evaluation_id,
                    :question_id,
                    :score
                )
                """
            ),
            [
                {
                    "evaluation_id": evaluation["id"],
                    "question_id": answer.question_id,
                    "score": answer.score,
                }
                for answer in payload.answers
            ],
        )

        result = dict(evaluation)
        db.commit()

        return result

    except IntegrityError as exc:
        db.rollback()

        diagnostic = getattr(exc.orig, "diag", None)
        constraint_name = getattr(
            diagnostic,
            "constraint_name",
            None,
        )

        if constraint_name == "uq_evaluation_leader_employee_week":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Você já avaliou esse funcionário nesta semana."
                ),
            ) from exc

        raise

    except Exception:
        db.rollback()
        raise
    

def get_latest_evaluation(
    db: Session,
    leader_id: int,
    employee_id: int,
) -> dict:
    subordinate_id = db.execute(
        text(
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
            SELECT employee_id
            FROM subordinates
            WHERE employee_id = :employee_id
              AND employee_id <> :leader_id
            """
        ),
        {
            "leader_id": leader_id,
            "employee_id": employee_id,
        },
    ).scalar_one_or_none()

    if subordinate_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode consultar avaliações de seus subordinados.",
        )

    evaluation = db.execute(
        text(
            """
            SELECT
                id,
                leader_id,
                employee_id,
                week_start,
                submitted_at
            FROM employee_reviews.evaluation
            WHERE employee_id = :employee_id
            ORDER BY submitted_at DESC, id DESC
            LIMIT 1
            """
        ),
        {"employee_id": employee_id},
    ).mappings().one_or_none()

    if evaluation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Esse funcionário ainda não possui avaliação.",
        )

    answers = db.execute(
        text(
            """
            SELECT
                question.id AS question_id,
                question.title,
                question.weight,
                answer.score
            FROM employee_reviews.answer AS answer
            JOIN employee_reviews.question AS question
                ON question.id = answer.question_id
            WHERE answer.evaluation_id = :evaluation_id
            ORDER BY question.id
            """
        ),
        {"evaluation_id": evaluation["id"]},
    ).mappings().all()

    weighted_score = db.execute(
        text(
            """
            SELECT
                SUM(answer.score * question.weight)::numeric
                / NULLIF(SUM(question.weight), 0)
            FROM employee_reviews.answer AS answer
            JOIN employee_reviews.question AS question
                ON question.id = answer.question_id
            WHERE answer.evaluation_id = :evaluation_id
            """
        ),
        {"evaluation_id": evaluation["id"]},
    ).scalar_one()

    return {
        **dict(evaluation),
        "weighted_score": weighted_score,
        "answers": [dict(answer) for answer in answers],
    }