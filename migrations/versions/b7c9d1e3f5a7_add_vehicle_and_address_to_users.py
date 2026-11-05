"""add vehicle_id and address_id to users

Revision ID: b7c9d1e3f5a7
Revises: a1b2c3d4e5f6
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7c9d1e3f5a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "vehicle_id",
            sa.Integer(),
            sa.ForeignKey("vehicles.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "address_id",
            sa.Integer(),
            sa.ForeignKey("addresses.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(op.f("ix_users_vehicle_id"), "users", ["vehicle_id"], unique=False)
    op.create_index(op.f("ix_users_address_id"), "users", ["address_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_address_id"), table_name="users")
    op.drop_index(op.f("ix_users_vehicle_id"), table_name="users")
    op.drop_column("users", "address_id")
    op.drop_column("users", "vehicle_id")
