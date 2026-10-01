"""create evaluations and answers

Revision ID: e25ba93b9dda
Revises: dc9b292442a6
Create Date: 2026-10-01 22:22:33.776977

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e25ba93b9dda'
down_revision: Union[str, Sequence[str], None] = 'dc9b292442a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evaluation",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("leader_id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["leader_id"],
            ["employee_reviews.employee.id"],
            name="fk_evaluation_leader",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employee_reviews.employee.id"],
            name="fk_evaluation_employee",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "leader_id",
            "employee_id",
            "week_start",
            name="uq_evaluation_leader_employee_week",
        ),
        sa.CheckConstraint(
            "leader_id <> employee_id",
            name="chk_evaluation_no_self",
        ),
        sa.CheckConstraint(
            "EXTRACT(ISODOW FROM week_start) = 1",
            name="chk_evaluation_week_starts_monday",
        ),
        schema="employee_reviews",
    )

    op.create_index(
        "ix_evaluation_employee_submitted_at",
        "evaluation",
        ["employee_id", "submitted_at"],
        schema="employee_reviews",
    )

    op.create_table(
        "answer",
        sa.Column("evaluation_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.SmallInteger(), nullable=False),
        sa.PrimaryKeyConstraint(
            "evaluation_id",
            "question_id",
            name="pk_answer",
        ),
        sa.ForeignKeyConstraint(
            ["evaluation_id"],
            ["employee_reviews.evaluation.id"],
            name="fk_answer_evaluation",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["employee_reviews.question.id"],
            name="fk_answer_question",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "score BETWEEN 1 AND 4",
            name="chk_answer_score",
        ),
        schema="employee_reviews",
    )


def downgrade() -> None:
    op.drop_table("answer", schema="employee_reviews")

    op.drop_index(
        "ix_evaluation_employee_submitted_at",
        table_name="evaluation",
        schema="employee_reviews",
    )

    op.drop_table("evaluation", schema="employee_reviews")
