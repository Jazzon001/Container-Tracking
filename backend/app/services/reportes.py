"""Reporte de carros: une el Excel de NOW con lo que registró este sistema."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Carga
from app.services.reporte_excel import leer_movimientos
from app.services.reporte_tiempos import Registro, Reporte, armar_reporte

# Una consulta con miles de valores en IN es lenta y algunas bases limitan cuántos se aceptan.
LOTE = 500


def cargar_registros(db: Session, contenedores: set[str]) -> dict[str, Registro]:
    """Lo que este sistema guardó de cada contenedor elemento. Si un mismo código se cargó más de una
    vez, se toma la carga más reciente."""
    ordenados = sorted(contenedores)
    cargas = []
    for inicio in range(0, len(ordenados), LOTE):
        lote = ordenados[inicio : inicio + LOTE]
        cargas += db.scalars(select(Carga).where(Carga.contenedor_elemento.in_(lote))).all()

    registros: dict[str, Registro] = {}
    for carga in sorted(cargas, key=lambda c: c.cargada_en):
        registros[carga.contenedor_elemento] = Registro(_sin_zona(carga.cargada_en), _sin_zona(carga.recibida_en))
    return registros


def _sin_zona(fecha: datetime | None) -> datetime | None:
    """SQLite devuelve las fechas sin zona horaria y PostgreSQL con ella: se comparan todas como UTC sin zona."""
    if fecha is None or fecha.tzinfo is None:
        return fecha
    return fecha.astimezone(timezone.utc).replace(tzinfo=None)


def generar_reporte(db: Session, contenido: bytes, desplazamiento_horas: int) -> Reporte:
    """El reporte del Excel de NOW (en bytes) cruzado con las cargas de este sistema."""
    movimientos = leer_movimientos(contenido)
    contenedores = {m.contenedor for m in movimientos}
    return armar_reporte(movimientos, cargar_registros(db, contenedores), desplazamiento_horas)
