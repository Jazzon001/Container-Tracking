"""Preparación compartida de las pruebas.

Cada prueba usa una base SQLite en memoria, nueva y vacía, para que ninguna
prueba dependa de otra y nunca se toque la base real.

El cliente `client` ya viene autenticado como administrador, para que las pruebas
de negocio no repitan el inicio de sesión. Para probar permisos se usa
`cliente_como(rol)` y, para probar la falta de sesión, `cliente_anonimo`.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Rol, Usuario
from app.seguridad import crear_token


@pytest.fixture(autouse=True)
def secreto_jwt(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "secreto-solo-para-pruebas-de-32-caracteres")


@pytest.fixture(autouse=True)
def hash_rapido(monkeypatch):
    # En producción el hash es lento a propósito; en las pruebas se acelera.
    monkeypatch.setattr("app.seguridad.ITERACIONES", 1_000)


@pytest.fixture
def sesion_de_pruebas():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestingSession
    app.dependency_overrides.clear()
    engine.dispose()


def _cliente_con_rol(sesion, rol):
    """Crea (si no existe) un usuario con ese rol y un cliente con su token."""
    username = f"prueba_{rol.value}"
    with sesion() as db:
        if db.query(Usuario).filter_by(username=username).first() is None:
            # El hash no se usa: el token se genera directo, sin pasar por el login.
            db.add(Usuario(username=username, password_hash="no-se-usa", rol=rol))
            db.commit()
    cliente = TestClient(app)
    cliente.headers["Authorization"] = f"Bearer {crear_token(username)}"
    return cliente


@pytest.fixture
def client(sesion_de_pruebas):
    return _cliente_con_rol(sesion_de_pruebas, Rol.ADMIN)


@pytest.fixture
def cliente_como(sesion_de_pruebas):
    def _como(rol):
        return _cliente_con_rol(sesion_de_pruebas, rol)

    return _como


@pytest.fixture
def cliente_anonimo(sesion_de_pruebas):
    return TestClient(app)


@pytest.fixture
def crear_carro(client):
    """Crea un carro y devuelve su JSON."""

    def _crear(numero="C-001", tipo="poy"):
        return client.post("/carros", json={"numero": numero, "tipo": tipo}).json()

    return _crear


@pytest.fixture
def cargar(client):
    """Carga un carro con un contenedor elemento y devuelve la respuesta HTTP."""

    def _cargar(carro_id, contenedor="100123"):
        return client.post(
            f"/carros/{carro_id}/carga", json={"contenedor_elemento": contenedor}
        )

    return _cargar
