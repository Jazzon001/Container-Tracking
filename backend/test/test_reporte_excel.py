"""Lectura del Excel de NOW y escritura del Excel del reporte. Datos inventados."""
import zipfile
from datetime import datetime
from io import BytesIO

import pytest
from excel_de_now import CABECERA, FILAS_BASICAS, excel, fila
from openpyxl import Workbook, load_workbook

from app.errores import ArchivoInvalido
from app.services import reporte_excel
from app.services.reporte_excel import escribir_excel, leer_movimientos
from app.services.reporte_tiempos import armar_reporte


class TestLeer:
    def test_combina_la_fecha_y_la_hora_de_cada_movimiento(self):
        primero = leer_movimientos(excel(FILAS_BASICAS))[0]
        assert primero.instante == datetime(2026, 11, 1, 6, 30)
        assert (primero.ubicacion, primero.carro, primero.contenedor) == ("RCV01", "P1A", "A1")

    def test_lee_la_calidad_y_funciona_sin_ella(self):
        assert leer_movimientos(excel(FILAS_BASICAS))[0].calidad == 2
        sin_calidad = [f[:6] for f in FILAS_BASICAS]
        assert leer_movimientos(excel(sin_calidad, cabecera=CABECERA[:6]))[0].calidad is None

    def test_una_calidad_que_no_es_numero_se_ignora(self):
        filas = [f[:6] + ["n/a", "202"] for f in FILAS_BASICAS]
        assert leer_movimientos(excel(filas))[0].calidad is None

    def test_lee_la_plantilla_de_cada_movimiento(self):
        movimientos = leer_movimientos(excel(FILAS_BASICAS))
        assert movimientos[0].plantilla == "016" and movimientos[0].es_entrada
        assert movimientos[1].plantilla == "202"

    def test_la_plantilla_numerica_se_normaliza_y_sin_plantilla_se_asume_202(self):
        filas = [fila(1, 6, "RCV01", "P1A", "A1", plantilla=16), fila(1, 7, "WIPA4", "P1A", "A1", plantilla=None)]
        assert [m.plantilla for m in leer_movimientos(excel(filas))] == ["016", "202"]

        sin_columna = [f[:7] for f in FILAS_BASICAS]
        assert leer_movimientos(excel(sin_columna, cabecera=CABECERA[:7]))[0].plantilla == "202"

    def test_una_plantilla_que_no_es_numero_se_conserva(self):
        assert leer_movimientos(excel([fila(1, 6, "RCV01", "P1A", "A1", plantilla="ABC")]))[0].plantilla == "ABC"

    def test_ignora_las_filas_en_blanco(self):
        assert len(leer_movimientos(excel(FILAS_BASICAS + [[None] * 8]))) == 5

    def test_avisa_que_columnas_faltan(self):
        with pytest.raises(ArchivoInvalido, match="Transaction time"):
            leer_movimientos(excel([], cabecera=["Transaction date", "Location"]))

    def test_avisa_si_el_archivo_esta_vacio(self):
        libro, salida = Workbook(), BytesIO()
        libro.save(salida)
        with pytest.raises(ArchivoInvalido, match="vacío"):
            leer_movimientos(salida.getvalue())

    def test_avisa_si_hay_una_fecha_que_no_se_entiende(self):
        filas = [["no es fecha", "ni hora", "PPY", "RCV01", "P1A", "A1", 2.0, "202"]]
        with pytest.raises(ArchivoInvalido, match="fecha u hora"):
            leer_movimientos(excel(filas))


class TestArchivosQueNoSonDeFiar:
    def test_un_archivo_que_no_es_un_zip_se_rechaza(self):
        with pytest.raises(ArchivoInvalido, match="no es un Excel"):
            leer_movimientos(b"esto no es un excel")

    def test_un_zip_que_no_es_un_excel_se_rechaza(self):
        zip_cualquiera = BytesIO()
        with zipfile.ZipFile(zip_cualquiera, "w") as z:
            z.writestr("hola.txt", "hola")
        with pytest.raises(ArchivoInvalido, match="no es un Excel"):
            leer_movimientos(zip_cualquiera.getvalue())

    def test_un_archivo_que_descomprime_a_demasiado_se_rechaza(self, monkeypatch):
        monkeypatch.setattr(reporte_excel, "LIMITE_DESCOMPRIMIDO", 100)
        with pytest.raises(ArchivoInvalido, match="demasiado grande"):
            leer_movimientos(excel(FILAS_BASICAS))

    def test_un_archivo_con_demasiadas_filas_se_rechaza(self, monkeypatch):
        monkeypatch.setattr(reporte_excel, "LIMITE_FILAS", 2)
        with pytest.raises(ArchivoInvalido, match="más de 2 filas"):
            leer_movimientos(excel(FILAS_BASICAS))


class TestEscribir:
    def libro(self):
        return load_workbook(BytesIO(escribir_excel(armar_reporte(leer_movimientos(excel(FILAS_BASICAS))))))

    def test_trae_sus_hojas(self):
        assert self.libro().sheetnames == ["Resumen", "Por carro", "Viajes", "Anulados"]

    def test_por_carro_deja_los_lados_juntos_y_con_su_carro_fisico(self):
        filas = list(self.libro()["Por carro"].iter_rows(min_row=2, values_only=True))
        assert [(f[0], f[1], f[2]) for f in filas] == [("P1", "A", "P1A"), ("P2", "B", "P2B")]

    def test_viajes_trae_las_fechas_del_recorrido(self):
        viajes = list(self.libro()["Viajes"].iter_rows(min_row=2, values_only=True))
        a1 = next(v for v in viajes if v[1] == "A1")
        assert a1[3] == datetime(2026, 11, 1, 6, 30)  # notificado en RCV01 (016)
        assert a1[17] == "RCV01 → WIPB4 → DTY"

    def test_el_resumen_explica_como_leer_el_archivo(self):
        textos = [str(c.value) for fila in self.libro()["Resumen"].iter_rows() for c in fila if c.value]
        assert any("es la SALIDA de esa ubicación" in t for t in textos)
        assert "Movimientos de producto en tarima (sin carro)" in textos
        assert any("liberación del carro en este sistema" in t for t in textos)


class TestAnulados:
    FILAS = FILAS_BASICAS + [
        fila(1, 7, "RCV01", "P3A", "E1", plantilla="016"),
        fila(1, 8, "RCV01", "P3A", "E1", plantilla="119", minuto=45),
        fila(1, 9, "WIPE", "D064", "D1", plantilla="016"),
    ]

    def libro(self):
        return load_workbook(BytesIO(escribir_excel(armar_reporte(leer_movimientos(excel(self.FILAS))))))

    def test_lee_la_plantilla_119_como_una_anulacion(self):
        movimientos = leer_movimientos(excel(self.FILAS))
        assert [m.plantilla for m in movimientos if m.contenedor == "E1"] == ["016", "119"]
        assert next(m for m in movimientos if m.plantilla == "119").es_anulacion

    def test_la_hoja_anulados_lista_los_contenedores_anulados(self):
        filas = list(self.libro()["Anulados"].iter_rows(min_row=2, values_only=True))
        assert len(filas) == 1
        carro, contenedor, ubicacion, notificado, anulado, horas_hasta = filas[0]
        assert (carro, contenedor, ubicacion) == ("P3A", "E1", "RCV01")
        assert notificado == datetime(2026, 11, 1, 7, 30) and anulado == datetime(2026, 11, 1, 8, 45)
        assert horas_hasta == 1.2  # 1 h 15 min

    def test_el_anulado_y_el_de_otro_proceso_no_estan_entre_los_viajes_ni_los_carros(self):
        libro = self.libro()
        viajes = [f[1] for f in libro["Viajes"].iter_rows(min_row=2, values_only=True)]
        assert "E1" not in viajes and "D1" not in viajes
        carros = [f[2] for f in libro["Por carro"].iter_rows(min_row=2, values_only=True)]
        assert carros == ["P1A", "P2B"]

    def test_el_resumen_cuenta_los_anulados_y_los_de_otros_procesos(self):
        resumen = {f[0]: f[1] for f in self.libro()["Resumen"].iter_rows(values_only=True) if f[0]}
        assert resumen["Contenedores anulados con la plantilla 119 (no cuentan como viaje)"] == 1
        assert resumen["Contenedores de carros de otros procesos (D, T, DT…), sin analizar"] == 1

    def test_sin_anulados_la_hoja_existe_vacia(self):
        libro = load_workbook(BytesIO(escribir_excel(armar_reporte(leer_movimientos(excel(FILAS_BASICAS))))))
        assert list(libro["Anulados"].iter_rows(min_row=2, values_only=True)) == []
