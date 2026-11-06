from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencias import requiere_roles
from app.models import Rol
from app.schemas import UsuarioCreate, UsuarioOut
from app.services import usuarios as servicio

router = APIRouter(
    prefix="/usuarios",
    tags=["usuarios"],
    dependencies=[Depends(requiere_roles(Rol.ADMIN))],
)


@router.post("", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def crear_usuario(datos: UsuarioCreate, db: Session = Depends(get_db)):
    return servicio.crear_usuario(db, datos.username, datos.password, datos.rol)
