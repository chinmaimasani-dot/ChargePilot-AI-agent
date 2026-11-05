"""create address_details table

Revision ID: 20261104_0001
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "20261104_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "address_details",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("hno", sa.String(length=50), nullable=True),
        sa.Column("street_village", sa.String(length=150), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("state", sa.String(length=100), nullable=False),
        sa.Column("pincode", sa.String(length=10), nullable=False),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("long", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_address_details_id", "address_details", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_address_details_id", table_name="address_details")
    op.drop_table("address_details")
