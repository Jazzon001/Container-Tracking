"""Aplicación de las migraciones de la base de datos (Alembic) desde el código.

Las migraciones son la única fuente de verdad del esquema. La API las aplica al
arrancar y los scripts de administración también, así que nadie tiene que acordarse
de correr un comando aparte ni borrar la base cuando cambia el modelo.
"""
from pathlib import Path

from alembic import command
from alembic.config import Config

RAIZ_BACKEND = Path(__file__).resolve().parents[1]


def configuracion_alembic(url: str | None = None) -> Config:
    """Configuración de Alembic que funciona desde cualquier carpeta de trabajo.

    Sin `url`, usa la de DATABASE_URL (la misma de la aplicación)."""
    configuracion = Config(str(RAIZ_BACKEND / "alembic.ini"))
    configuracion.set_main_option("script_location", str(RAIZ_BACKEND / "migrations"))
    configuracion.attributes["configurar_logs"] = False
    if url:
        configuracion.attributes["url"] = url
    return configuracion


def aplicar_migraciones(url: str | None = None) -> None:
    """Deja la base en la versión más reciente. Si ya lo está, no hace nada."""
    command.upgrade(configuracion_alembic(url), "head")
