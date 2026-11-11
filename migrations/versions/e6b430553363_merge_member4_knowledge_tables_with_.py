"""merge member4 knowledge tables with remaining heads

Revision ID: e6b430553363
Revises: dac2e54e4307, e1f85982ea49
Create Date: 2026-11-10 23:37:08.994069

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6b430553363'
down_revision: Union[str, Sequence[str], None] = ('dac2e54e4307', 'e1f85982ea49')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
