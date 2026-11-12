import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect

from app.database import Base
from app.migraciones import aplicar_migraciones, configuracion_alembic

TABLAS_DEL_SISTEMA = {"carros", "cargas", "mantenimientos", "usuarios"}


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


def test_la_migracion_del_historial_conserva_los_carros_que_ya_iban_en_transito(url, motor):
    """Una base anterior al historial: sus carros en tránsito deben quedar con carga abierta."""
    cfg = configuracion_alembic(url)
    command.upgrade(cfg, "0001")
    with motor.begin() as conexion:
        conexion.exec_driver_sql(
            "INSERT INTO carros (numero, tipo, estado, contenedor_elemento, estado_desde) VALUES "
            "('C-001', 'POY', 'EN_TRANSITO', '100123', '2026-11-12 12:00:00'), "
            "('C-002', 'POY', 'DISPONIBLE', NULL, '2026-11-12 12:00:00'), "
            "('C-003', 'DTY', 'EN_MANTENIMIENTO', NULL, '2026-11-12 12:00:00')"
        )

    command.upgrade(cfg, "head")

    with motor.connect() as conexion:
        filas = conexion.exec_driver_sql(
            "SELECT carro_id, contenedor_elemento, cargada_en, recibida_en FROM cargas"
        ).all()
    assert len(filas) == 1  # solo el carro en tránsito
    assert filas[0][1] == "100123"
    assert str(filas[0][2]).startswith("2026-11-12 12:00:00")  # conserva desde cuándo iba así
    assert filas[0][3] is None


def test_la_migracion_del_historial_se_puede_revertir_sin_tocar_los_carros(url, motor):
    cfg = configuracion_alembic(url)
    aplicar_migraciones(url)
    with motor.begin() as conexion:
        conexion.exec_driver_sql(
            "INSERT INTO carros (numero, tipo, estado, estado_desde) "
            "VALUES ('C-001', 'POY', 'DISPONIBLE', '2026-11-12 12:00:00')"
        )

    command.downgrade(cfg, "0001")

    assert tablas(motor) == {"carros", "mantenimientos", "usuarios"}
    with motor.connect() as conexion:
        assert conexion.exec_driver_sql("SELECT numero FROM carros").scalars().all() == ["C-001"]


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
