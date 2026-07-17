import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Make the "app" package importable regardless of the current working
# directory the alembic CLI happens to be invoked from (repo root, backend/,
# or inside the Docker container's WORKDIR) — matters when contributors run
# this from Ubuntu or Windows shells with different cwd conventions.
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings  # noqa: E402
from app.db.base import Base  # noqa: E402
# Import every domain module's models here so they register on Base.metadata
# before autogenerate compares against it. Add a line per new domain module.
from app.modules.stocks.models import Stock, DailyPrice, Fundamental  # noqa: E402,F401
from app.modules.auth.models import User  # noqa: E402,F401
from app.modules.backtest.models import BacktestJob  # noqa: E402,F401
from app.modules.market_data.models import IngestionRun  # noqa: E402,F401
from app.modules.strategies.models import SavedStrategy  # noqa: E402,F401
from app.modules.orgs.models import Organization  # noqa: E402,F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Database URL comes from environment variables (via pydantic_settings),
# never hardcoded in alembic.ini. '%' is escaped because ConfigParser
# treats it as an interpolation character.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("%", "%%"))

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
