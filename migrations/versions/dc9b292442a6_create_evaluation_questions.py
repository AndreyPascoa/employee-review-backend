"""create evaluation questions

Revision ID: dc9b292442a6
Revises: 0810fbba8499
Create Date: 2026-10-01 22:15:33.872030

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dc9b292442a6'
down_revision: Union[str, Sequence[str], None] = '0810fbba8499'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    question = op.create_table(
        "question",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("weight", sa.Integer(), nullable=False),
        sa.UniqueConstraint("title", name="uq_question_title"),
        sa.CheckConstraint(
            "weight > 0 AND weight <= 100",
            name="chk_question_weight",
        ),
        schema="employee_reviews",
    )

    op.bulk_insert(
        question,
        [
            {
                "id": 1,
                "title": "Entrega de Resultados",
                "weight": 25,
            },
            {
                "id": 2,
                "title": "Execução e Qualidade do Trabalho",
                "weight": 20,
            },
            {
                "id": 3,
                "title": "Capacidade de Aprendizado e Desenvolvimento",
                "weight": 20,
            },
            {
                "id": 4,
                "title": "Resolução de Problemas e Pensamento Crítico",
                "weight": 15,
            },
            {
                "id": 5,
                "title": "Colaboração, Influência e Liderança",
                "weight": 10,
            },
            {
                "id": 6,
                "title": "Visão Estratégica e Potencial de Crescimento",
                "weight": 10,
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("question", schema="employee_reviews")
