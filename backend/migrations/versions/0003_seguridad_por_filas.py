"""seguridad por filas (RLS): ninguna vía directa a los datos

En Supabase (PostgreSQL), las tablas del esquema `public` también quedan expuestas por su
API de datos. Este sistema accede a la base solo a través de su propia API (que valida el
token y el rol de cada usuario), así que a las tablas no debe llegar nadie más.

Se activa la seguridad por filas en todas las tablas y se declara en cada una una política
que niega cualquier lectura o escritura. El rol con el que se conecta la aplicación es el
dueño de las tablas y no está sujeto a estas políticas, así que la aplicación sigue
funcionando igual. Es una segunda barrera (defensa en profundidad), no un reemplazo de los
roles de la API.

En SQLite (desarrollo y pruebas) no existe esta función: la migración no hace nada.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-13
"""
from typing import Sequence, Union

from alembic import op


revision: str = "0003"
down_revision: Union[str, Sequence[str], None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLAS = ("carros", "cargas", "mantenimientos", "usuarios", "alembic_version")


def _es_postgresql() -> bool:
    return op.get_context().dialect.name == "postgresql"


def upgrade() -> None:
    if not _es_postgresql():
        return
    for tabla in TABLAS:
        op.execute(f"ALTER TABLE {tabla} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY {tabla}_sin_acceso_directo ON {tabla} "
            "FOR ALL USING (false) WITH CHECK (false)"
        )


def downgrade() -> None:
    if not _es_postgresql():
        return
    for tabla in TABLAS:
        op.execute(f"DROP POLICY IF EXISTS {tabla}_sin_acceso_directo ON {tabla}")
        op.execute(f"ALTER TABLE {tabla} DISABLE ROW LEVEL SECURITY")
