"""Reglas de negocio del mantenimiento de carros, independientes de HTTP."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import EstadoCarro, Mantenimiento
from app.services.carros import obtener_carro, transicionar_estado


def iniciar_mantenimiento(db: Session, carro_id: int) -> Mantenimiento:
    """Un carro disponible entra a mantenimiento y se registra su fecha de entrada."""
    transicionar_estado(
        db,
        carro_id,
        EstadoCarro.DISPONIBLE,
        {"estado": EstadoCarro.EN_MANTENIMIENTO},
        "Solo un carro disponible puede entrar a mantenimiento",
    )
    registro = Mantenimiento(carro_id=carro_id, fecha_entrada=datetime.now(timezone.utc))
    db.add(registro)
    db.commit()
    return registro


def finalizar_mantenimiento(db: Session, carro_id: int) -> Mantenimiento:
    """El carro sale de mantenimiento, queda disponible y se registra su fecha de salida."""
    transicionar_estado(
        db,
        carro_id,
        EstadoCarro.EN_MANTENIMIENTO,
        {"estado": EstadoCarro.DISPONIBLE},
        "El carro no está en mantenimiento",
    )
    registro = db.scalars(
        select(Mantenimiento).where(
            Mantenimiento.carro_id == carro_id, Mantenimiento.fecha_salida.is_(None)
        )
    ).one()
    registro.fecha_salida = datetime.now(timezone.utc)
    db.commit()
    return registro


def historial_de_mantenimiento(db: Session, carro_id: int) -> list[Mantenimiento]:
    obtener_carro(db, carro_id)  # lanza CarroNoEncontrado si no existe
    consulta = select(Mantenimiento).where(Mantenimiento.carro_id == carro_id)
    return list(db.scalars(consulta.order_by(Mantenimiento.id)).all())
