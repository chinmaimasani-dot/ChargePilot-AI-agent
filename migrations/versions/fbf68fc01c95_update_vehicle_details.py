"""update vehicle details

Revision ID: fbf68fc01c95
Revises: 98213fbb8dbd
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "fbf68fc01c95"
down_revision: Union[str, Sequence[str], None] = "98213fbb8dbd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename existing columns so their stored values are preserved.
    op.alter_column(
        "vehicles",
        "make",
        new_column_name="company_name",
        existing_type=sa.String(length=80),
        type_=sa.String(length=100),
        existing_nullable=False,
    )
    op.alter_column(
        "vehicles",
        "battery_capacity_kwh",
        new_column_name="charging_capacity",
        existing_type=sa.Float(),
        type_=sa.Float(),
        existing_nullable=False,
    )
    op.alter_column(
        "vehicles",
        "model_year",
        new_column_name="year_of_manufacturing",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )

    # Add new fields as nullable first so existing rows can be populated.
    op.add_column(
        "vehicles", sa.Column("vehicle_number", sa.String(length=30), nullable=True)
    )
    op.add_column(
        "vehicles", sa.Column("vehicle_type", sa.String(length=20), nullable=True)
    )
    op.add_column(
        "vehicles", sa.Column("vehicle_model", sa.String(length=50), nullable=True)
    )
    op.add_column(
        "vehicles", sa.Column("charging_type", sa.String(length=2), nullable=True)
    )

    # The old columns are retained privately to preserve their existing values.
    op.alter_column(
        "vehicles", "model", existing_type=sa.String(length=100), nullable=True
    )
    op.alter_column(
        "vehicles", "connector_type", existing_type=sa.String(length=50), nullable=True
    )
    op.alter_column(
        "vehicles",
        "max_charging_power_kw",
        existing_type=sa.Float(),
        nullable=True,
    )

    vehicles = sa.table(
        "vehicles",
        sa.column("id", sa.Integer()),
        sa.column("model", sa.String()),
        sa.column("connector_type", sa.String()),
        sa.column("vehicle_number", sa.String()),
        sa.column("vehicle_type", sa.String()),
        sa.column("vehicle_model", sa.String()),
        sa.column("charging_type", sa.String()),
    )

    op.execute(
        sa.update(vehicles).values(
            vehicle_number=sa.func.concat("LEGACY-", vehicles.c.id),
            vehicle_type="4 wheeler",
            vehicle_model=sa.case(
                (vehicles.c.model.ilike("%suv%"), "SUV"),
                else_="Sedan",
            ),
            charging_type=sa.case(
                (
                    sa.or_(
                        vehicles.c.connector_type.ilike("%ccs%"),
                        vehicles.c.connector_type.ilike("%chademo%"),
                        vehicles.c.connector_type.ilike("%dc%"),
                    ),
                    "DC",
                ),
                else_="AC",
            ),
        )
    )

    # Require the new values after existing rows have been populated.
    for column_name, column_type in (
        ("vehicle_number", sa.String(length=30)),
        ("vehicle_type", sa.String(length=20)),
        ("vehicle_model", sa.String(length=50)),
        ("charging_type", sa.String(length=2)),
    ):
        op.alter_column(
            "vehicles",
            column_name,
            existing_type=column_type,
            nullable=False,
        )

    op.create_index(
        op.f("ix_vehicles_vehicle_number"),
        "vehicles",
        ["vehicle_number"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_vehicles_vehicle_number"), table_name="vehicles")

    op.drop_column("vehicles", "charging_type")
    op.drop_column("vehicles", "vehicle_model")
    op.drop_column("vehicles", "vehicle_type")
    op.drop_column("vehicles", "vehicle_number")

    op.alter_column(
        "vehicles",
        "year_of_manufacturing",
        new_column_name="model_year",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )
    op.alter_column(
        "vehicles",
        "charging_capacity",
        new_column_name="battery_capacity_kwh",
        existing_type=sa.Float(),
        existing_nullable=False,
    )
    op.alter_column(
        "vehicles",
        "company_name",
        new_column_name="make",
        existing_type=sa.String(length=100),
        type_=sa.String(length=80),
        existing_nullable=False,
    )