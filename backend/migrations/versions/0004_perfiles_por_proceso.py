"""perfiles por proceso

Agrega siete valores al tipo `rol`: los perfiles de cada proceso (digitador, intermedio y
empacador de POY; digitador y empacador de DTY y de Twisting). No cambia ni borra ningún dato:
los usuarios que ya existen conservan su perfil y siguen funcionando igual.

En PostgreSQL el tipo `rol` es un tipo enumerado aparte, y agregar un valor no reescribe ninguna
tabla. Se hace fuera de la transacción porque un valor nuevo no puede usarse dentro de la
transacción que lo crea. En SQLite (desarrollo y pruebas) el rol es un texto con un largo
máximo, y solo hay que ensancharlo.

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004"
down_revision: Union[str, Sequence[str], None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ANTERIORES = ("POY", "ALMACEN", "DTY", "TWISTING", "ADMIN")
NUEVOS = (
    "DIGITADOR_POY",
    "INTERMEDIO_POY",
    "EMPACADOR_POY",
    "DIGITADOR_DTY",
    "EMPACADOR_DTY",
    "DIGITADOR_TWT",
    "EMPACADOR_TWT",
)


def _es_postgresql() -> bool:
    return op.get_context().dialect.name == "postgresql"


def upgrade() -> None:
    if _es_postgresql():
        with op.get_context().autocommit_block():
            for valor in NUEVOS:
                op.execute(f"ALTER TYPE rol ADD VALUE IF NOT EXISTS '{valor}'")
        return
    with op.batch_alter_table("usuarios", schema=None) as batch_op:
        batch_op.alter_column(
            "rol",
            existing_type=sa.Enum(*ANTERIORES, name="rol"),
            type_=sa.Enum(*ANTERIORES, *NUEVOS, name="rol"),
            existing_nullable=False,
        )


def downgrade() -> None:
    # En PostgreSQL no se puede quitar un valor de un tipo enumerado: los valores quedan sin
    # uso, lo cual es inofensivo. Si hay usuarios con los perfiles nuevos, la base anterior no
    # los entendería: hay que cambiarles el perfil antes de volver atrás.
    if _es_postgresql():
        return
    with op.batch_alter_table("usuarios", schema=None) as batch_op:
        batch_op.alter_column(
            "rol",
            existing_type=sa.Enum(*ANTERIORES, *NUEVOS, name="rol"),
            type_=sa.Enum(*ANTERIORES, name="rol"),
            existing_nullable=False,
        )
