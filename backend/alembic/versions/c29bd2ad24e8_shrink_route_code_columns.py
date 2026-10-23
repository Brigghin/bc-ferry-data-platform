"""Restore six-character route codes."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c29bd2ad24e8"
down_revision: Union[str, Sequence[str], None] = "cbeaa9065142"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "sailings_route_code_fkey",
        "sailings",
        type_="foreignkey",
    )
    op.alter_column(
        "routes",
        "route_code",
        existing_type=sa.String(length=7),
        type_=sa.String(length=6),
        existing_nullable=False,
    )
    op.alter_column(
        "sailings",
        "route_code",
        existing_type=sa.String(length=7),
        type_=sa.String(length=6),
        existing_nullable=False,
    )
    op.create_foreign_key(
        "sailings_route_code_fkey",
        "sailings",
        "routes",
        ["route_code"],
        ["route_code"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "sailings_route_code_fkey",
        "sailings",
        type_="foreignkey",
    )
    op.alter_column(
        "routes",
        "route_code",
        existing_type=sa.String(length=6),
        type_=sa.String(length=7),
        existing_nullable=False,
    )
    op.alter_column(
        "sailings",
        "route_code",
        existing_type=sa.String(length=6),
        type_=sa.String(length=7),
        existing_nullable=False,
    )
    op.create_foreign_key(
        "sailings_route_code_fkey",
        "sailings",
        "routes",
        ["route_code"],
        ["route_code"],
    )