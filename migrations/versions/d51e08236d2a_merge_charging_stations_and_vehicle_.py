"""merge charging stations and vehicle migrations

Revision ID: d51e08236d2a
Revises: 58c43f936c1e, 98213fbb8dbd
Create Date: 2026-11-04 17:21:52.527386

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd51e08236d2a'
down_revision: Union[str, Sequence[str], None] = ('58c43f936c1e', '98213fbb8dbd')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
