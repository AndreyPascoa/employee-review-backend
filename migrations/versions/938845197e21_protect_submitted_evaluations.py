"""protect submitted evaluations

Revision ID: 938845197e21
Revises: e25ba93b9dda
Create Date: 2026-10-01 22:39:33.793123

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '938845197e21'
down_revision: Union[str, Sequence[str], None] = 'e25ba93b9dda'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION employee_reviews.prevent_evaluation_changes()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION
                'Avaliações enviadas e suas respostas não podem ser alteradas ou excluídas.'
                USING ERRCODE = '55000';
        END;
        $$;
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_evaluation_immutable
        BEFORE UPDATE OR DELETE
        ON employee_reviews.evaluation
        FOR EACH ROW
        EXECUTE FUNCTION employee_reviews.prevent_evaluation_changes();
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_answer_immutable
        BEFORE UPDATE OR DELETE
        ON employee_reviews.answer
        FOR EACH ROW
        EXECUTE FUNCTION employee_reviews.prevent_evaluation_changes();
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_evaluation_no_truncate
        BEFORE TRUNCATE
        ON employee_reviews.evaluation
        FOR EACH STATEMENT
        EXECUTE FUNCTION employee_reviews.prevent_evaluation_changes();
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_answer_no_truncate
        BEFORE TRUNCATE
        ON employee_reviews.answer
        FOR EACH STATEMENT
        EXECUTE FUNCTION employee_reviews.prevent_evaluation_changes();
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER trg_answer_no_truncate
        ON employee_reviews.answer;
        """
    )

    op.execute(
        """
        DROP TRIGGER trg_evaluation_no_truncate
        ON employee_reviews.evaluation;
        """
    )

    op.execute(
        """
        DROP TRIGGER trg_answer_immutable
        ON employee_reviews.answer;
        """
    )

    op.execute(
        """
        DROP TRIGGER trg_evaluation_immutable
        ON employee_reviews.evaluation;
        """
    )

    op.execute(
        """
        DROP FUNCTION employee_reviews.prevent_evaluation_changes();
        """
    )