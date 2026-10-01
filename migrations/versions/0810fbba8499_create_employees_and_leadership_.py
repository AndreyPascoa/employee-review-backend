"""create employees and leadership relationships

Revision ID: 0810fbba8499
Revises: 
Create Date: 2026-10-01 00:53:57.998320

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0810fbba8499'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "employee",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(150), nullable=False),
        sa.Column("position_name", sa.String(100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        schema="employee_reviews",
    )

    op.create_table(
        "leader_lead",
        sa.Column("leader_id", sa.Integer(), nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("leader_id", "lead_id"),
        sa.ForeignKeyConstraint(
            ["leader_id"],
            ["employee_reviews.employee.id"],
            name="fk_leader",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["lead_id"],
            ["employee_reviews.employee.id"],
            name="fk_lead",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        sa.CheckConstraint(
            "leader_id <> lead_id",
            name="chk_no_self_lead",
        ),
        schema="employee_reviews",
    )
    
    seed_initial_data()


def downgrade() -> None:
    op.drop_table("leader_lead", schema="employee_reviews")
    op.drop_table("employee", schema="employee_reviews")
    
    
def seed_initial_data() -> None:
    employee = sa.table(
        "employee",
        sa.column("id", sa.Integer()),
        sa.column("name", sa.String()),
        sa.column("email", sa.String()),
        sa.column("position_name", sa.String()),
        schema="employee_reviews",
    )

    employees = [
        (1, "Alice Hartman", "alice.hartman@company.com", "CEO"),
        (2, "Bob Sinclair", "bob.sinclair@company.com", "CTO"),
        (3, "Carol Nguyen", "carol.nguyen@company.com", "CFO"),
        (4, "David Okafor", "david.okafor@company.com", "Engineering Manager"),
        (5, "Eva Müller", "eva.muller@company.com", "Engineering Manager"),
        (6, "Frank Rossi", "frank.rossi@company.com", "Product Manager"),
        (7, "Grace Kim", "grace.kim@company.com", "UX Designer"),
        (8, "Henry Patel", "henry.patel@company.com", "Senior Software Engineer"),
        (9, "Isabelle Dubois", "isabelle.dubois@company.com", "Senior Software Engineer"),
        (10, "James Watanabe", "james.watanabe@company.com", "Software Engineer"),
        (11, "Karen Oliveira", "karen.oliveira@company.com", "Software Engineer"),
        (12, "Liam Johansson", "liam.johansson@company.com", "Software Engineer"),
        (13, "Mia Fernandez", "mia.fernandez@company.com", "Data Engineer"),
        (14, "Noah Chukwu", "noah.chukwu@company.com", "Data Analyst"),
        (15, "Olivia Brooks", "olivia.brooks@company.com", "QA Engineer"),
        (16, "Paul Nakamura", "paul.nakamura@company.com", "QA Engineer"),
        (17, "Quinn Santos", "quinn.santos@company.com", "DevOps Engineer"),
        (18, "Rachel Ivanova", "rachel.ivanova@company.com", "Finance Analyst"),
        (19, "Samuel Osei", "samuel.osei@company.com", "Finance Analyst"),
        (20, "Tina Bergmann", "tina.bergmann@company.com", "HR Specialist"),
    ]

    op.bulk_insert(
        employee,
        [
            {
                "id": employee_id,
                "name": name,
                "email": email,
                "position_name": position_name,
            }
            for employee_id, name, email, position_name in employees
        ],
    )

    leader_lead = sa.table(
        "leader_lead",
        sa.column("leader_id", sa.Integer()),
        sa.column("lead_id", sa.Integer()),
        schema="employee_reviews",
    )

    relationships = [
        (1, 2),
        (1, 3),
        (1, 6),
        (1, 20),
        (2, 4),
        (2, 5),
        (2, 7),
        (2, 17),
        (2, 16),
        (4, 8),
        (4, 12),
        (8, 10),
        (8, 11),
        (5, 9),
        (5, 13),
        (5, 14),
        (3, 18),
        (3, 19),
        (6, 15),
    ]

    op.bulk_insert(
        leader_lead,
        [
            {"leader_id": leader_id, "lead_id": lead_id}
            for leader_id, lead_id in relationships
        ],
    )

    op.execute(
        """
        SELECT setval(
            pg_get_serial_sequence('employee_reviews.employee', 'id'),
            (SELECT MAX(id) FROM employee_reviews.employee),
            true
        )
        """
    )