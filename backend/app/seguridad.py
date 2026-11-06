"""Contraseñas y tokens JWT. Funciones puras: no conocen HTTP ni la base de datos.

La clave para firmar los tokens se lee de la variable de entorno JWT_SECRET y
nunca se escribe en el código ni en el repositorio.
"""
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from app.errores import NoAutenticado

ALGORITMO = "HS256"
ITERACIONES = 600_000
DURACION_TOKEN = timedelta(hours=8)  # un turno de trabajo


def _derivar(password: str, sal: bytes, iteraciones: int) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), sal, iteraciones).hex()


def hashear_password(password: str) -> str:
    sal = secrets.token_bytes(16)
    return f"pbkdf2_sha256${ITERACIONES}${sal.hex()}${_derivar(password, sal, ITERACIONES)}"


def verificar_password(password: str, almacenado: str) -> bool:
    try:
        _, iteraciones, sal, esperado = almacenado.split("$")
        obtenido = _derivar(password, bytes.fromhex(sal), int(iteraciones))
    except ValueError:
        return False
    return hmac.compare_digest(obtenido, esperado)


def _secreto() -> str:
    secreto = os.environ.get("JWT_SECRET")
    if not secreto:
        raise RuntimeError("Falta definir la variable de entorno JWT_SECRET")
    return secreto


def crear_token(username: str, duracion: timedelta = DURACION_TOKEN) -> str:
    datos = {"sub": username, "exp": datetime.now(timezone.utc) + duracion}
    return jwt.encode(datos, _secreto(), algorithm=ALGORITMO)


def leer_token(token: str) -> str:
    """Devuelve el nombre de usuario del token, o lanza NoAutenticado si no es válido."""
    try:
        datos = jwt.decode(
            token, _secreto(), algorithms=[ALGORITMO], options={"require": ["exp", "sub"]}
        )
    except jwt.PyJWTError:
        raise NoAutenticado("Token inválido o vencido")
    return datos["sub"]
