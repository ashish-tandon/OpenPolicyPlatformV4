"""Alembic environment configuration for OpenPolicy Platform"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import your models here
from app.models import Base
from app.models.auth import User, Session, PasswordResetToken
from app.models.policy import Policy, Category, Bill, Vote
from app.models.analytics import PageView, APICall, SearchQuery

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Model metadata
target_metadata = Base.metadata

# Environment variables for database connection
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/openpolicy_prod"
)

def get_url():
    """Get database URL from environment or config"""
    return DATABASE_URL

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
    
    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.
    
    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Custom naming conventions
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s"
        }
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.
    
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = get_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Enable transaction per migration
            transaction_per_migration=True,
            # Compare types for column changes
            compare_type=True,
            # Compare server defaults
            compare_server_default=True,
            # Include schemas
            include_schemas=True,
            # Version table configuration
            version_table='alembic_version',
            version_table_schema='public',
            # Custom naming conventions
            naming_convention={
                "ix": "ix_%(column_0_label)s",
                "uq": "uq_%(table_name)s_%(column_0_name)s",
                "ck": "ck_%(table_name)s_%(constraint_name)s",
                "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
                "pk": "pk_%(table_name)s"
            }
        )

        with context.begin_transaction():
            # Set search path for PostgreSQL schemas
            context.execute("SET search_path TO public, auth, policy, analytics, audit")
            context.run_migrations()


# Determine which mode to run in
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()