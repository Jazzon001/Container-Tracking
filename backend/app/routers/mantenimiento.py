from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencias import requiere_roles, usuario_actual
from app.models import Rol
from app.schemas import MantenimientoOut
from app.services import mantenimiento as servicio

router = APIRouter(
    prefix="/carros/{carro_id}/mantenimiento",
    tags=["mantenimiento"],
    dependencies=[Depends(usuario_actual)],
)

# Registrar mantenimiento aplica a carros de POY y a los propios de DTY.
puede_registrar = Depends(requiere_roles(Rol.POY, Rol.DTY))


@router.post(
    "",
    response_model=MantenimientoOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[puede_registrar],
)
def iniciar_mantenimiento(carro_id: int, db: Session = Depends(get_db)):
    return servicio.iniciar_mantenimiento(db, carro_id)


@router.post("/salida", response_model=MantenimientoOut, dependencies=[puede_registrar])
def finalizar_mantenimiento(carro_id: int, db: Session = Depends(get_db)):
    return servicio.finalizar_mantenimiento(db, carro_id)


@router.get("", response_model=list[MantenimientoOut])
def historial_de_mantenimiento(carro_id: int, db: Session = Depends(get_db)):
    return servicio.historial_de_mantenimiento(db, carro_id)
