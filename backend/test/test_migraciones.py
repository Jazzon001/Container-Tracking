import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect

from app.database import Base
from app.migraciones import aplicar_migraciones, configuracion_alembic

TABLAS_DEL_SISTEMA = {"carros", "mantenimientos", "usuarios"}


@pytest.fixture
def url(tmp_path):
    return f"sqlite:///{tmp_path / 'migraciones.db'}"


@pytest.fixture
def motor(url):
    motor = create_engine(url)
    yield motor
    motor.dispose()


def tablas(motor) -> set[str]:
    return set(inspect(motor).get_table_names()) - {"alembic_version"}


def test_las_migraciones_crean_todas_las_tablas(url, motor):
    aplicar_migraciones(url)
    assert tablas(motor) == TABLAS_DEL_SISTEMA


def test_el_esquema_de_las_migraciones_coincide_con_los_modelos(url, motor):
    """Si alguien cambia un modelo y olvida crear su migración, esta prueba falla."""
    aplicar_migraciones(url)

    with motor.connect() as conexion:
        contexto = MigrationContext.configure(conexion, opts={"compare_type": True})
        diferencias = compare_metadata(contexto, Base.metadata)

    assert diferencias == [], (
        "Los modelos y las migraciones no coinciden. Crea una migración con: "
        'alembic revision --autogenerate -m "descripción del cambio"'
    )


def test_aplicar_las_migraciones_dos_veces_no_falla(url, motor):
    aplicar_migraciones(url)
    aplicar_migraciones(url)
    assert tablas(motor) == TABLAS_DEL_SISTEMA


def test_las_migraciones_se_pueden_revertir(url, motor):
    aplicar_migraciones(url)
    command.downgrade(configuracion_alembic(url), "base")
    assert tablas(motor) == set()


def test_las_migraciones_forman_una_sola_linea():
    """Dos migraciones con el mismo origen crean ramas; Alembic no sabría cuál aplicar."""
    guion = ScriptDirectory.from_config(configuracion_alembic())
    assert len(guion.get_heads()) == 1


def test_una_base_ya_con_datos_conserva_sus_registros(url, motor):
    aplicar_migraciones(url)
    with motor.begin() as conexion:
        conexion.exec_driver_sql(
            "INSERT INTO carros (numero, tipo, estado, estado_desde) "
            "VALUES ('C-001', 'POY', 'DISPONIBLE', '2026-11-12 12:00:00')"
        )

    aplicar_migraciones(url)  # la segunda vez no debe tocar los datos

    with motor.connect() as conexion:
        assert conexion.exec_driver_sql("SELECT numero FROM carros").scalars().all() == ["C-001"]
