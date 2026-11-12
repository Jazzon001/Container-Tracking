"""Consulta del historial de cargas, independiente de HTTP."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Carga, Carro


def listar_cargas(
    db: Session,
    contenedor_elemento: str | None = None,
    numero: str | None = None,
    limite: int = 100,
) -> list[Carga]:
    """Las cargas más recientes primero. Los filtros son exactos y se pueden combinar.

    `numero` es el número del carro. `limite` evita traer todo el historial, que crece
    con cada viaje."""
    consulta = select(Carga).order_by(Carga.cargada_en.desc(), Carga.id.desc()).limit(limite)
    if contenedor_elemento is not None:
        consulta = consulta.where(Carga.contenedor_elemento == contenedor_elemento)
    if numero is not None:
        consulta = consulta.where(Carga.carro.has(Carro.numero == numero))
    return list(db.scalars(consulta).all())
