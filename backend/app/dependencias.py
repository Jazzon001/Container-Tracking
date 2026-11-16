"""Dependencias de FastAPI para exigir sesión iniciada y un rol permitido."""
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.errores import CarroNoEncontrado, NoAutenticado, SinPermiso
from app.models import Carro, Rol, Usuario
from app.permisos import PERMISOS, Permisos
from app.seguridad import leer_token
from app.services.carros import obtener_carro
from app.services.usuarios import obtener_por_username

# auto_error=False: así el error de "sin token" lo generamos nosotros y es un 401.
esquema_bearer = HTTPBearer(auto_error=False)


def usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(esquema_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    if credenciales is None:
        raise NoAutenticado()
    usuario = obtener_por_username(db, leer_token(credenciales.credentials))
    if usuario is None:
        raise NoAutenticado("El usuario del token ya no existe")
    return usuario


def requiere_roles(*roles: Rol):
    """Permite la operación solo a los roles indicados. El administrador siempre puede."""
    permitidos = {*roles, Rol.ADMIN}

    def verificar(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
        if usuario.rol not in permitidos:
            raise SinPermiso()
        return usuario

    return verificar


def permisos_de(usuario: Usuario) -> Permisos:
    return PERMISOS[usuario.rol]


def requiere_permiso(accion: str):
    """Permite la operación solo a los perfiles que tienen ese permiso (`cargar`, `liberar`, `mantener`)."""

    def verificar(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
        if not getattr(permisos_de(usuario), accion):
            raise SinPermiso()
        return usuario

    return verificar


def carro_accesible(
    carro_id: int,
    usuario: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
) -> Carro:
    """El carro pedido, si es de un proceso que el usuario puede ver.

    Si es de otro proceso responde como si no existiera: así no se revela qué carros hay."""
    carro = obtener_carro(db, carro_id)
    if not permisos_de(usuario).ve(carro.tipo):
        raise CarroNoEncontrado()
    return carro
