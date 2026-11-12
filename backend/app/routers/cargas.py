from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencias import usuario_actual
from app.schemas import CargaOut
from app.services import cargas as servicio

# Consultar el historial: cualquier usuario con sesión iniciada.
router = APIRouter(prefix="/cargas", tags=["cargas"], dependencies=[Depends(usuario_actual)])


@router.get("", response_model=list[CargaOut])
def listar_cargas(
    contenedor_elemento: str | None = None,
    numero: str | None = None,
    limite: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    return servicio.listar_cargas(db, contenedor_elemento, numero, limite)
