"""Script del reporte: lectura del Excel de NOW y escritura del reporte. Datos inventados."""
from datetime import datetime

import pytest
from openpyxl import Workbook, load_workbook

from scripts import reporte_carros
from scripts.reporte_carros import ArchivoInvalido, leer_movimientos, main

CABECERA = ["Transaction date", "Transaction time", "IT", "Location", "Cnr", "Container element", "Qlt", "Tmp"]


def excel(ruta, filas, cabecera=CABECERA):
    libro = Workbook()
    hoja = libro.active
    hoja.append(cabecera)
    for fila in filas:
        hoja.append(fila)
    libro.save(ruta)


def fila(dia, hora, ubicacion, carro, contenedor, plantilla="202"):
    # Igual que NOW: la fecha va en una columna y la hora en otra (con una fecha cualquiera).
    return [datetime(2026, 11, dia), datetime(1970, 1, 1, hora, 30), "PPY", ubicacion, carro, contenedor, 2.0, plantilla]


FILAS = [
    fila(1, 8, "RCV01", "P1", "A1"),
    fila(1, 12, "WIPB4", "P1", "A1"),
    fila(1, 9, "RCV01", "P2", "B2"),
    fila(1, 10, "EMP", "TARPOY", "T-99"),
]


@pytest.fixture
def archivos(tmp_path, monkeypatch):
    entrada, salida = tmp_path / "entrada.xlsx", tmp_path / "salida.xlsx"
    monkeypatch.setattr(reporte_carros, "ENTRADA", entrada)
    monkeypatch.setattr(reporte_carros, "SALIDA", salida)
    return entrada, salida


class TestLeer:
    def test_combina_la_fecha_y_la_hora_de_cada_movimiento(self, tmp_path):
        excel(tmp_path / "a.xlsx", FILAS)
        movimientos = leer_movimientos(tmp_path / "a.xlsx")
        assert movimientos[0].instante == datetime(2026, 11, 1, 8, 30)
        assert (movimientos[0].ubicacion, movimientos[0].carro, movimientos[0].contenedor) == ("RCV01", "P1", "A1")

    def test_lee_la_calidad_y_funciona_sin_ella(self, tmp_path):
        excel(tmp_path / "a.xlsx", FILAS)
        assert leer_movimientos(tmp_path / "a.xlsx")[0].calidad == 2

        sin_calidad = [f[:6] for f in FILAS]
        excel(tmp_path / "b.xlsx", sin_calidad, cabecera=CABECERA[:6])
        assert leer_movimientos(tmp_path / "b.xlsx")[0].calidad is None

    def test_una_calidad_que_no_es_numero_se_ignora(self, tmp_path):
        filas = [f[:6] + ["n/a", "202"] for f in FILAS]
        excel(tmp_path / "a.xlsx", filas)
        assert leer_movimientos(tmp_path / "a.xlsx")[0].calidad is None

    def test_lee_la_plantilla_de_cada_movimiento(self, tmp_path):
        excel(tmp_path / "a.xlsx", [fila(1, 6, "RCV01", "P1", "A1", plantilla="016")] + FILAS)
        movimientos = leer_movimientos(tmp_path / "a.xlsx")
        assert movimientos[0].plantilla == "016" and movimientos[0].es_entrada
        assert movimientos[1].plantilla == "202"

    def test_la_plantilla_numerica_se_normaliza_y_sin_plantilla_se_asume_202(self, tmp_path):
        excel(tmp_path / "a.xlsx", [fila(1, 6, "RCV01", "P1", "A1", plantilla=16), fila(1, 7, "WIPA4", "P1", "A1", plantilla=None)])
        movimientos = leer_movimientos(tmp_path / "a.xlsx")
        assert [m.plantilla for m in movimientos] == ["016", "202"]

        sin_columna = [f[:7] for f in FILAS]
        excel(tmp_path / "b.xlsx", sin_columna, cabecera=CABECERA[:7])
        assert leer_movimientos(tmp_path / "b.xlsx")[0].plantilla == "202"

    def test_una_plantilla_que_no_es_numero_se_conserva(self, tmp_path):
        excel(tmp_path / "a.xlsx", [fila(1, 6, "RCV01", "P1", "A1", plantilla="ABC")])
        assert leer_movimientos(tmp_path / "a.xlsx")[0].plantilla == "ABC"

    def test_ignora_las_filas_en_blanco(self, tmp_path):
        excel(tmp_path / "a.xlsx", FILAS + [[None] * 8])
        assert len(leer_movimientos(tmp_path / "a.xlsx")) == 4

    def test_avisa_que_columnas_faltan(self, tmp_path):
        excel(tmp_path / "a.xlsx", [], cabecera=["Transaction date", "Location"])
        with pytest.raises(ArchivoInvalido, match="Transaction time"):
            leer_movimientos(tmp_path / "a.xlsx")

    def test_avisa_si_el_archivo_esta_vacio(self, tmp_path):
        Workbook().save(tmp_path / "vacio.xlsx")
        with pytest.raises(ArchivoInvalido, match="vacío"):
            leer_movimientos(tmp_path / "vacio.xlsx")


class TestMain:
    def test_escribe_el_reporte_con_tres_hojas(self, archivos, capsys):
        entrada, salida = archivos
        excel(entrada, FILAS)

        assert main() == 0

        libro = load_workbook(salida)
        assert libro.sheetnames == ["Resumen", "Por carro", "Viajes"]
        carros = [fila[0] for fila in libro["Por carro"].iter_rows(min_row=2, values_only=True)]
        assert carros == ["P1", "P2"]  # la tarima no aparece como carro
        assert "2 carros físicos (2 lados A y B), 2 viajes (1 movimientos en tarima" in capsys.readouterr().out

    def test_el_resumen_explica_como_leer_el_archivo(self, archivos):
        entrada, salida = archivos
        excel(entrada, FILAS)
        main()

        textos = [str(c.value) for fila in load_workbook(salida)["Resumen"].iter_rows() for c in fila if c.value]
        assert any("es la SALIDA de esa ubicación" in t for t in textos)
        assert "Movimientos de producto en tarima (sin carro)" in textos

    def test_avisa_si_falta_el_archivo(self, archivos, capsys):
        assert main() == 1
        assert "movimientos de NOW" in capsys.readouterr().out

    def test_avisa_si_el_archivo_no_es_de_movimientos(self, archivos, capsys):
        entrada, _ = archivos
        excel(entrada, [], cabecera=["otra", "cosa"])
        assert main() == 1
        assert "Faltan estas columnas" in capsys.readouterr().out

    def test_avisa_si_no_hay_movimientos(self, archivos, capsys):
        entrada, salida = archivos
        excel(entrada, [])
        assert main() == 1
        assert "no trae movimientos" in capsys.readouterr().out
        assert not salida.exists()

    def test_no_acepta_rutas_por_la_linea_de_comandos(self):
        # Las rutas son fijas: el script no puede leer ni escribir en otro lugar.
        assert reporte_carros.ENTRADA.parent.name == "datos"
        assert reporte_carros.SALIDA.parent.name == "datos"
