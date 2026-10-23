"""Add capture timestamp to sailing history."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "cbeaa9065142"
down_revision: Union[str, Sequence[str], None] = "6d4c52fefe0d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sailings",
        sa.Column(
            "captured_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("sailings", "captured_at")