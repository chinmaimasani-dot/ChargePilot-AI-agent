from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from chargepilot_slot_availability_api.database import Base, DATABASE_URL
import chargepilot_slot_availability_api.models  # Register the models


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Read the database URL from .env. Escape percent signs for Alembic's config parser.
config.set_main_option("sqlalchemy.url", DATABASE_URL.replace("%", "%%"))

target_metadata = Base.metadata


def include_object(obj, name, type_, reflected, compare_to):
    # This repository owns only the slots_availability table.
    return type_ != "table" or name == "slots_availability"


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_object=include_object,
        version_table="slot_availability_alembic_version",
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_object=include_object,
            version_table="slot_availability_alembic_version",
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()