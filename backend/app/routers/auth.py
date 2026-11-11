from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import LoginIn, TokenOut
from app.seguridad import crear_token
from app.services.usuarios import autenticar

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(datos: LoginIn, db: Session = Depends(get_db)):
    usuario = autenticar(db, datos.username, datos.password)
    return TokenOut(access_token=crear_token(usuario.username), rol=usuario.rol)
