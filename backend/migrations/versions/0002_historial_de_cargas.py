"""historial de cargas

Agrega la tabla `cargas`, que conserva qué contenedor elemento iba en cada carro y
cuándo se cargó y se recibió. Los carros que ya iban en tránsito conservan su carga
abierta, para que al recibirlos el historial quede completo.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cargas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("carro_id", sa.Integer(), nullable=False),
        sa.Column("contenedor_elemento", sa.String(length=50), nullable=False),
        sa.Column("cargada_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recibida_en", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["carro_id"], ["carros.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("cargas", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_cargas_carro_id"), ["carro_id"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_cargas_contenedor_elemento"), ["contenedor_elemento"], unique=False
        )

    # Los carros que ya iban en tránsito antes de existir el historial.
    op.execute(
        "INSERT INTO cargas (carro_id, contenedor_elemento, cargada_en) "
        "SELECT id, contenedor_elemento, estado_desde FROM carros "
        "WHERE estado = 'EN_TRANSITO' AND contenedor_elemento IS NOT NULL"
    )


def downgrade() -> None:
    with op.batch_alter_table("cargas", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_cargas_contenedor_elemento"))
        batch_op.drop_index(batch_op.f("ix_cargas_carro_id"))
    op.drop_table("cargas")
