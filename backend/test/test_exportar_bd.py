import json
import re

import pytest
from sqlalchemy import create_engine

from app.migraciones import aplicar_migraciones
from scripts import exportar_bd
from scripts.exportar_bd import describir_bd, main, resumen


@pytest.fixture
def motor(tmp_path):
    url = f"sqlite:///{tmp_path / 'real.db'}"
    aplicar_migraciones(url)
    motor = create_engine(url)
    with motor.begin() as conexion:
        conexion.exec_driver_sql(
            "INSERT INTO carros (numero, tipo, estado, estado_desde) VALUES "
            "('C-001', 'POY', 'DISPONIBLE', '2026-11-13 12:00:00'), "
            "('C-002', 'DTY', 'DISPONIBLE', '2026-11-13 12:00:00')"
        )
        conexion.exec_driver_sql(
            "INSERT INTO usuarios (username, password_hash, rol) VALUES ('admin', 'x', 'ADMIN')"
        )
    yield motor
    motor.dispose()


@pytest.fixture
def exportacion(motor):
    return describir_bd(motor)


def tabla(exportacion, nombre):
    return next(t for t in exportacion["tablas"] if t["nombre"] == nombre)


class TestFormato:
    def test_trae_las_tres_claves_de_primer_nivel(self, exportacion):
        assert set(exportacion) == {"generado_at", "motor", "tablas"}

    def test_la_fecha_tiene_el_formato_pedido(self, exportacion):
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", exportacion["generado_at"])

    def test_cada_tabla_trae_las_claves_pedidas(self, exportacion):
        claves = {"nombre", "filas", "columnas", "indices", "relaciones", "politicas_rls"}
        assert all(set(t) == claves for t in exportacion["tablas"])

    def test_las_columnas_traen_nombre_tipo_y_si_aceptan_nulos(self, exportacion):
        for columna in tabla(exportacion, "carros")["columnas"]:
            assert {"nombre", "tipo", "nulo"} <= set(columna)
            assert isinstance(columna["nulo"], bool)

    def test_pk_solo_aparece_en_las_columnas_que_son_llave_primaria(self, exportacion):
        columnas = {c["nombre"]: c for c in tabla(exportacion, "carros")["columnas"]}
        assert columnas["id"]["pk"] is True
        assert "pk" not in columnas["numero"]

    def test_las_relaciones_apuntan_a_tabla_punto_columna(self, exportacion):
        assert tabla(exportacion, "cargas")["relaciones"] == [
            {"columna": "carro_id", "referencia": "carros.id"}
        ]


class TestContenido:
    def test_incluye_todas_las_tablas_de_la_base(self, exportacion):
        nombres = {t["nombre"] for t in exportacion["tablas"]}
        assert nombres == {"alembic_version", "carros", "cargas", "mantenimientos", "usuarios"}

    def test_cuenta_las_filas_reales_de_cada_tabla(self, exportacion):
        assert tabla(exportacion, "carros")["filas"] == 2
        assert tabla(exportacion, "usuarios")["filas"] == 1
        assert tabla(exportacion, "cargas")["filas"] == 0

    def test_todas_las_tablas_tienen_llave_primaria(self, exportacion):
        assert resumen(exportacion)["tablas_sin_llave_primaria"] == []

    def test_lista_los_indices(self, exportacion):
        assert "ix_carros_numero" in tabla(exportacion, "carros")["indices"]

    def test_en_sqlite_no_hay_politicas_rls(self, exportacion):
        assert all(t["politicas_rls"] == [] for t in exportacion["tablas"])

    def test_el_motor_se_declara(self, exportacion):
        assert exportacion["motor"] == "sqlite"


class TestResumen:
    def test_calcula_los_numeros_que_pide_el_formulario(self, exportacion):
        datos = resumen(exportacion)
        assert datos["tablas"] == 5
        assert datos["relaciones"] == 2
        assert datos["tabla_con_mas_filas"] == "carros"

    def test_las_tablas_con_datos_son_las_que_tienen_filas(self, exportacion):
        # alembic_version guarda la versión de las migraciones: siempre tiene una fila.
        assert set(resumen(exportacion)["tablas_con_datos"]) == {"alembic_version", "carros", "usuarios"}


class TestMain:
    def test_no_exporta_si_la_base_no_es_postgresql(self, monkeypatch, motor, tmp_path, capsys):
        monkeypatch.setattr("app.database.engine", motor)
        monkeypatch.setattr(exportar_bd, "DESTINO", tmp_path / "salida.json")
        monkeypatch.setattr("sys.argv", ["exportar_bd"])

        assert main() == 1
        assert "no PostgreSQL" in capsys.readouterr().out
        assert not (tmp_path / "salida.json").exists()

    def test_escribe_el_archivo_y_resume_lo_exportado(self, monkeypatch, motor, tmp_path, capsys):
        destino = tmp_path / "docs" / "db-export.json"
        monkeypatch.setattr("app.database.engine", motor)
        monkeypatch.setattr(exportar_bd, "DESTINO", destino)
        monkeypatch.setattr("sys.argv", ["exportar_bd", "--permitir-otro-motor"])

        assert main() == 0
        assert json.loads(destino.read_text(encoding="utf-8"))["motor"] == "sqlite"
        assert "Tablas con datos" in capsys.readouterr().out
