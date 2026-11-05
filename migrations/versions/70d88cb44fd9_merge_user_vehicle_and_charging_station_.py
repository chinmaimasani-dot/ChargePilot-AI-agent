"""merge user vehicle and charging station migrations

Revision ID: 70d88cb44fd9
Revises: 68b6a90eee34, b7c9d1e3f5a7
Create Date: 2026-11-05 11:50:53.368397

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '70d88cb44fd9'
down_revision: Union[str, Sequence[str], None] = ('68b6a90eee34', 'b7c9d1e3f5a7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
