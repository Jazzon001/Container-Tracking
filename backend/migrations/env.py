"""Entorno de Alembic: define a qué base se conecta y qué modelos se comparan."""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app import models  # noqa: F401  (importarlo registra las tablas en Base)
from app.database import DATABASE_URL, Base

config = context.config
# Cuando se aplican desde la aplicación no se reconfigura el registro de mensajes.
if config.config_file_name is not None and config.attributes.get("configurar_logs", True):
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def _url() -> str:
    # La aplicación y las pruebas pasan la URL directamente; desde la terminal se usa DATABASE_URL.
    return config.attributes.get("url") or DATABASE_URL


def run_migrations_offline() -> None:
    """Genera el SQL sin conectarse a la base (alembic upgrade head --sql)."""
    context.configure(
        url=_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuracion = config.get_section(config.config_ini_section, {})
    configuracion["sqlalchemy.url"] = _url()
    motor = engine_from_config(configuracion, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with motor.connect() as conexion:
        context.configure(
            connection=conexion,
            target_metadata=target_metadata,
            compare_type=True,
            # SQLite no puede alterar columnas directamente: Alembic reconstruye la tabla.
            render_as_batch=conexion.dialect.name == "sqlite",
        )
        with context.begin_transaction():
            context.run_migrations()
    motor.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
