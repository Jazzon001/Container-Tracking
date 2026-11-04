"""Reglas de negocio de los carros, independientes de HTTP."""
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Carro, EstadoCarro


class ErrorDeNegocio(Exception):
    """Base de los errores que la API traduce a una respuesta HTTP."""


class CarroNoEncontrado(ErrorDeNegocio):
    def __init__(self) -> None:
        super().__init__("Carro no encontrado")


class EstadoInvalido(ErrorDeNegocio):
    def __init__(self, detalle: str) -> None:
        super().__init__(detalle)


class ContenedorEnUso(ErrorDeNegocio):
    def __init__(self) -> None:
        super().__init__("Ese contenedor elemento ya está asignado a otro carro")


def obtener_carro(db: Session, carro_id: int) -> Carro:
    carro = db.get(Carro, carro_id)
    if carro is None:
        raise CarroNoEncontrado()
    return carro


def cargar_carro(db: Session, carro_id: int, contenedor_elemento: str) -> Carro:
    """Asocia un carro disponible con un contenedor elemento y lo pone en tránsito.

    La condición `estado == DISPONIBLE` va dentro del UPDATE para que, si dos
    usuarios intentan cargar el mismo carro a la vez, solo uno lo consiga.
    """
    try:
        resultado = db.execute(
            update(Carro)
            .where(Carro.id == carro_id, Carro.estado == EstadoCarro.DISPONIBLE)
            .values(estado=EstadoCarro.EN_TRANSITO, contenedor_elemento=contenedor_elemento)
        )
        if resultado.rowcount == 0:
            db.rollback()
            obtener_carro(db, carro_id)  # lanza CarroNoEncontrado si no existe
            raise EstadoInvalido("El carro no está disponible para cargarse")
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ContenedorEnUso()
    carro = obtener_carro(db, carro_id)
    db.refresh(carro)
    return carro
