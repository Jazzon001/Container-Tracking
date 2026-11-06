"""Reglas de negocio de los usuarios, independientes de HTTP."""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errores import CredencialesInvalidas, UsuarioExistente
from app.models import Rol, Usuario
from app.seguridad import hashear_password, verificar_password


def obtener_por_username(db: Session, username: str) -> Usuario | None:
    return db.scalars(select(Usuario).where(Usuario.username == username)).first()


def crear_usuario(db: Session, username: str, password: str, rol: Rol) -> Usuario:
    usuario = Usuario(username=username, password_hash=hashear_password(password), rol=rol)
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise UsuarioExistente()
    return usuario


def autenticar(db: Session, username: str, password: str) -> Usuario:
    usuario = obtener_por_username(db, username)
    if usuario is None or not verificar_password(password, usuario.password_hash):
        raise CredencialesInvalidas()
    return usuario
