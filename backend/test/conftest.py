"""Preparación compartida de las pruebas.

Cada prueba usa una base SQLite en memoria, nueva y vacía, para que ninguna
prueba dependa de otra y nunca se toque la base real.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture
def client():
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
    yield TestClient(app)
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def crear_carro(client):
    """Crea un carro y devuelve su JSON."""

    def _crear(numero="C-001"):
        return client.post("/carros", json={"numero": numero}).json()

    return _crear


@pytest.fixture
def cargar(client):
    """Carga un carro con un contenedor elemento y devuelve la respuesta HTTP."""

    def _cargar(carro_id, contenedor="100123"):
        return client.post(
            f"/carros/{carro_id}/carga", json={"contenedor_elemento": contenedor}
        )

    return _cargar
