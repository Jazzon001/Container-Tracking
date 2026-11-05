from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import MantenimientoOut
from app.services import mantenimiento as servicio

router = APIRouter(prefix="/carros/{carro_id}/mantenimiento", tags=["mantenimiento"])


@router.post("", response_model=MantenimientoOut, status_code=status.HTTP_201_CREATED)
def iniciar_mantenimiento(carro_id: int, db: Session = Depends(get_db)):
    return servicio.iniciar_mantenimiento(db, carro_id)


@router.post("/salida", response_model=MantenimientoOut)
def finalizar_mantenimiento(carro_id: int, db: Session = Depends(get_db)):
    return servicio.finalizar_mantenimiento(db, carro_id)


@router.get("", response_model=list[MantenimientoOut])
def historial_de_mantenimiento(carro_id: int, db: Session = Depends(get_db)):
    return servicio.historial_de_mantenimiento(db, carro_id)
