"""add organization api key

Revision ID: 9cb7d0f1f4b2
Revises: d590cd36ccb8
Create Date: 2026-02-05 09:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9cb7d0f1f4b2"
down_revision: Union[str, None] = "d590cd36ccb8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("organizations", sa.Column("api_key", sa.String(length=128), nullable=True))
    op.execute("UPDATE organizations SET api_key = slug WHERE api_key IS NULL")
    op.alter_column("organizations", "api_key", nullable=False)
    op.create_index(op.f("ix_organizations_api_key"), "organizations", ["api_key"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_organizations_api_key"), table_name="organizations")
    op.drop_column("organizations", "api_key")
