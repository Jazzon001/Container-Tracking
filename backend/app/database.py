"""Conexión a la base de datos.

La URL se toma de la variable de entorno DATABASE_URL:
- Si no existe, se usa SQLite local (archivo container_tracking.db).
- En producción se define con la cadena de conexión de Supabase (PostgreSQL).
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


def normalizar_url(url: str) -> str:
    """Supabase entrega la cadena como `postgresql://...`. SQLAlchemy necesita saber qué
    driver usar, así que se le indica psycopg. Las demás URL (SQLite) no se tocan."""
    for prefijo in ("postgresql://", "postgres://"):
        if url.startswith(prefijo):
            return "postgresql+psycopg://" + url[len(prefijo):]
    return url


DATABASE_URL = normalizar_url(os.environ.get("DATABASE_URL", "sqlite:///./container_tracking.db"))

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
# pool_pre_ping: antes de usar una conexión comprueba que siga viva. Las bases en la nube
# cierran las conexiones inactivas, y sin esto la primera petición después fallaría.
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """Entrega una sesión de base de datos por petición y la cierra al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
