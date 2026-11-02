"""Add inferred sailing date."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d92f4b65a1c3"
down_revision: Union[str, Sequence[str], None] = "c29bd2ad24e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sailings",
        sa.Column("sailing_date", sa.Date(), nullable=True),
    )
    op.execute(
        "UPDATE sailings "
        "SET sailing_date = (captured_at AT TIME ZONE 'America/Vancouver')::date"
    )
    op.alter_column(
        "sailings",
        "sailing_date",
        existing_type=sa.Date(),
        nullable=False,
    )


def downgrade() -> None:
    op.drop_column("sailings", "sailing_date")