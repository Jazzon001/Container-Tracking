"""Script del reporte (sin la base de datos): lee datos/movimientos_now.xlsx y escribe datos/reporte_carros.xlsx."""
import pytest
from excel_de_now import CABECERA, FILAS_BASICAS, excel
from openpyxl import load_workbook

from scripts import reporte_carros
from scripts.reporte_carros import main


@pytest.fixture
def archivos(tmp_path, monkeypatch):
    entrada, salida = tmp_path / "entrada.xlsx", tmp_path / "salida.xlsx"
    monkeypatch.setattr(reporte_carros, "ENTRADA", entrada)
    monkeypatch.setattr(reporte_carros, "SALIDA", salida)
    return entrada, salida


def test_escribe_el_reporte_con_sus_hojas(archivos, capsys):
    entrada, salida = archivos
    entrada.write_bytes(excel(FILAS_BASICAS))

    assert main() == 0

    libro = load_workbook(salida)
    assert libro.sheetnames == ["Resumen", "Contenedores", "Carros", "Anulados", "Cómo leer"]
    carros = [fila[0] for fila in libro["Carros"].iter_rows(min_row=2, values_only=True)]
    assert carros == ["P1", "P2"]  # la tarima no aparece como carro
    assert "2 carros físicos (2 lados A y B), 2 viajes (1 movimientos en tarima" in capsys.readouterr().out


def test_avisa_si_falta_el_archivo(archivos, capsys):
    assert main() == 1
    assert "movimientos de NOW" in capsys.readouterr().out


def test_avisa_si_el_archivo_no_es_de_movimientos(archivos, capsys):
    entrada, _ = archivos
    entrada.write_bytes(excel([], cabecera=["otra", "cosa"]))
    assert main() == 1
    assert "Faltan estas columnas" in capsys.readouterr().out


def test_avisa_si_el_archivo_no_es_un_excel(archivos, capsys):
    entrada, _ = archivos
    entrada.write_bytes(b"esto no es un excel")
    assert main() == 1
    assert "no es un Excel" in capsys.readouterr().out


def test_avisa_si_no_hay_movimientos(archivos, capsys):
    entrada, salida = archivos
    entrada.write_bytes(excel([], cabecera=CABECERA))
    assert main() == 1
    assert "no trae movimientos" in capsys.readouterr().out
    assert not salida.exists()


def test_las_rutas_son_fijas_y_estan_en_la_carpeta_datos():
    # El script no acepta rutas por la línea de comandos: no puede leer ni escribir en otro lugar.
    assert reporte_carros.ENTRADA.parent.name == "datos"
    assert reporte_carros.SALIDA.parent.name == "datos"
