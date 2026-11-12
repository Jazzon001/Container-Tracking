"""esquema inicial

Crea las tablas del sistema: carros, mantenimientos y usuarios.

Revision ID: 0001
Revises:
Create Date: 2026-11-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tipos enumerados que PostgreSQL crea aparte de las tablas (SQLite no los usa).
TIPOS_ENUMERADOS = ("tipocarro", "estadocarro", "rol")


def upgrade() -> None:
    op.create_table(
        "carros",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("numero", sa.String(length=50), nullable=False),
        sa.Column("tipo", sa.Enum("POY", "DTY", "TWISTING", name="tipocarro"), nullable=False),
        sa.Column(
            "estado",
            sa.Enum("DISPONIBLE", "EN_TRANSITO", "EN_MANTENIMIENTO", name="estadocarro"),
            nullable=False,
        ),
        sa.Column("contenedor_elemento", sa.String(length=50), nullable=True),
        sa.Column("estado_desde", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("contenedor_elemento"),
    )
    with op.batch_alter_table("carros", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_carros_numero"), ["numero"], unique=True)
        batch_op.create_index(batch_op.f("ix_carros_tipo"), ["tipo"], unique=False)

    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("password_hash", sa.String(length=200), nullable=False),
        sa.Column(
            "rol",
            sa.Enum("POY", "ALMACEN", "DTY", "TWISTING", "ADMIN", name="rol"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("usuarios", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_usuarios_username"), ["username"], unique=True)

    op.create_table(
        "mantenimientos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("carro_id", sa.Integer(), nullable=False),
        sa.Column("fecha_entrada", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_salida", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["carro_id"], ["carros.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("mantenimientos", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_mantenimientos_carro_id"), ["carro_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("mantenimientos", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_mantenimientos_carro_id"))
    op.drop_table("mantenimientos")

    with op.batch_alter_table("usuarios", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_usuarios_username"))
    op.drop_table("usuarios")

    with op.batch_alter_table("carros", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_carros_tipo"))
        batch_op.drop_index(batch_op.f("ix_carros_numero"))
    op.drop_table("carros")

    # En PostgreSQL, borrar las tablas no borra sus tipos enumerados.
    if op.get_bind().dialect.name == "postgresql":
        for tipo in TIPOS_ENUMERADOS:
            op.execute(f"DROP TYPE IF EXISTS {tipo}")
