"""Reglas de negocio de los carros, independientes de HTTP."""
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errores import CarroNoEncontrado, ContenedorEnUso, EstadoInvalido
from app.models import Carga, Carro, EstadoCarro, TipoCarro
from app.tiempo import ahora


def obtener_carro(db: Session, carro_id: int) -> Carro:
    carro = db.get(Carro, carro_id)
    if carro is None:
        raise CarroNoEncontrado()
    return carro


def listar_carros(
    db: Session,
    estado: EstadoCarro | None = None,
    numero: str | None = None,
    tipo: TipoCarro | None = None,
    contenedor_elemento: str | None = None,
) -> list[Carro]:
    consulta = select(Carro).order_by(Carro.id)
    if estado is not None:
        consulta = consulta.where(Carro.estado == estado)
    if numero is not None:
        consulta = consulta.where(Carro.numero == numero)
    if tipo is not None:
        consulta = consulta.where(Carro.tipo == tipo)
    if contenedor_elemento is not None:
        consulta = consulta.where(Carro.contenedor_elemento == contenedor_elemento)
    return list(db.scalars(consulta).all())


def transicionar_estado(
    db: Session,
    carro_id: int,
    desde: EstadoCarro,
    valores: dict,
    error_estado: str,
    momento: datetime | None = None,
) -> None:
    """Cambia el carro de un estado a otro de forma atómica (sin hacer commit).

    La condición `estado == desde` va dentro del UPDATE para que, si dos usuarios
    actúan sobre el mismo carro a la vez, solo uno lo consiga. Cada cambio de estado
    registra también cuándo ocurrió (`estado_desde`), en un solo lugar para todas
    las operaciones. Quien necesite registrar el mismo instante en otro lado (el
    historial de cargas) lo pasa en `momento`.
    """
    resultado = db.execute(
        update(Carro)
        .where(Carro.id == carro_id, Carro.estado == desde)
        .values(**valores, estado_desde=momento or ahora())
    )
    if resultado.rowcount == 0:
        db.rollback()
        obtener_carro(db, carro_id)  # lanza CarroNoEncontrado si no existe
        raise EstadoInvalido(error_estado)


def _carro_actualizado(db: Session, carro_id: int) -> Carro:
    carro = obtener_carro(db, carro_id)
    db.refresh(carro)
    return carro


def cargar_carro(db: Session, carro_id: int, contenedor_elemento: str) -> Carro:
    """Asocia un carro disponible con un contenedor elemento y lo pone en tránsito.

    También abre su registro en el historial de cargas, en la misma transacción: o se
    guardan el cambio de estado y el historial, o ninguno de los dos."""
    momento = ahora()
    try:
        transicionar_estado(
            db,
            carro_id,
            EstadoCarro.DISPONIBLE,
            {"estado": EstadoCarro.EN_TRANSITO, "contenedor_elemento": contenedor_elemento},
            "El carro no está disponible para cargarse",
            momento,
        )
        db.add(Carga(carro_id=carro_id, contenedor_elemento=contenedor_elemento, cargada_en=momento))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ContenedorEnUso()
    return _carro_actualizado(db, carro_id)


def entregar_carro(db: Session, carro_id: int) -> Carro:
    """Almacén recibe el carro vacío: queda disponible y libera su contenedor elemento.

    Cierra su registro en el historial de cargas. Si el carro iba en tránsito desde antes
    de existir el historial y no tiene registro abierto, no se considera un error."""
    momento = ahora()
    transicionar_estado(
        db,
        carro_id,
        EstadoCarro.EN_TRANSITO,
        {"estado": EstadoCarro.DISPONIBLE, "contenedor_elemento": None},
        "El carro no está en tránsito",
        momento,
    )
    db.execute(
        update(Carga)
        .where(Carga.carro_id == carro_id, Carga.recibida_en.is_(None))
        .values(recibida_en=momento)
    )
    db.commit()
    return _carro_actualizado(db, carro_id)
