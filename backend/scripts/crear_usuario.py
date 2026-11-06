"""Crea un usuario desde la terminal. Sirve para crear el primer administrador.

Uso (desde la carpeta backend, con el entorno virtual activo):
    python -m scripts.crear_usuario admin admin

La contraseña se pide por teclado: así nunca queda escrita en un archivo ni en
el historial de la terminal.
"""
import argparse
import getpass
import sys

from app import models  # noqa: F401  (importarlo registra las tablas en Base)
from app.database import Base, SessionLocal, engine
from app.errores import ErrorDeNegocio
from app.models import Rol
from app.services.usuarios import crear_usuario


def main() -> int:
    parser = argparse.ArgumentParser(description="Crea un usuario del sistema.")
    parser.add_argument("username")
    parser.add_argument("rol", choices=[rol.value for rol in Rol])
    argumentos = parser.parse_args()

    password = getpass.getpass("Contraseña (mínimo 8 caracteres): ")
    if len(password) < 8:
        print("La contraseña debe tener al menos 8 caracteres.")
        return 1
    if password != getpass.getpass("Repite la contraseña: "):
        print("Las contraseñas no coinciden.")
        return 1

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        try:
            usuario = crear_usuario(db, argumentos.username.strip(), password, Rol(argumentos.rol))
        except ErrorDeNegocio as error:
            print(error)
            return 1
    print(f"Usuario '{usuario.username}' creado con rol {usuario.rol.value}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
