"""merge vehicle details and charging station migrations

Revision ID: 68b6a90eee34
Revises: d51e08236d2a, fbf68fc01c95
Create Date: 2026-11-05 09:31:27.960353

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '68b6a90eee34'
down_revision: Union[str, Sequence[str], None] = ('d51e08236d2a', 'fbf68fc01c95')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
