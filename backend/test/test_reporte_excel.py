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


def hoja(libro, nombre):
    """Las filas de una hoja como diccionarios {encabezado: valor}, para no depender del orden de las columnas."""
    filas = list(libro[nombre].iter_rows(values_only=True))
    return [dict(zip(filas[0], fila)) for fila in filas[1:]]


class TestEscribir:
    def libro(self):
        return load_workbook(BytesIO(escribir_excel(armar_reporte(leer_movimientos(excel(FILAS_BASICAS))))))

    def test_trae_sus_hojas(self):
        assert self.libro().sheetnames == ["Resumen", "Contenedores", "Carros", "Anulados", "Cómo leer"]

    def test_contenedores_es_una_fila_por_contenedor_elemento(self):
        filas = hoja(self.libro(), "Contenedores")
        assert [f["Contenedor elemento"] for f in filas] == ["A1", "B2"]

    def test_cada_contenedor_dice_en_que_etapa_esta(self):
        etapas = {f["Contenedor elemento"]: f["Dónde está ahora"] for f in hoja(self.libro(), "Contenedores")}
        assert etapas["A1"] == "3 · En DTY"
        assert etapas["B2"] == "1 · En RCV01 (esperando a intermedio)"

    def test_trae_las_fechas_de_cada_etapa(self):
        a1 = next(f for f in hoja(self.libro(), "Contenedores") if f["Contenedor elemento"] == "A1")
        assert a1["Entró a RCV01 (producción, 016)"] == datetime(2026, 11, 1, 6, 30)
        assert a1["Salió de RCV01 (hacia WIP)"] == datetime(2026, 11, 1, 8, 30)
        assert a1["Salió del WIP (hacia DTY)"] == datetime(2026, 11, 1, 12, 30)
        assert a1["WIP del que salió"] == "WIPB4"
        assert a1["Recorrido"] == "RCV01 → WIPB4 → DTY"

    def test_trae_las_horas_de_cada_etapa_ya_terminada(self):
        a1 = next(f for f in hoja(self.libro(), "Contenedores") if f["Contenedor elemento"] == "A1")
        assert (a1["Horas en RCV01"], a1["Horas en WIP"], a1["Horas en POY (RCV01 + WIP)"]) == (2.0, 4.0, 6.0)

    def test_lo_que_sigue_en_curso_no_se_mezcla_con_las_etapas_terminadas(self):
        b2 = next(f for f in hoja(self.libro(), "Contenedores") if f["Contenedor elemento"] == "B2")
        assert b2["Horas en RCV01"] is None and b2["Horas en WIP"] is None  # RCV01 sigue abierta
        assert b2["Lleva ahí (horas)"] == 3.0  # de las 9:30 a las 12:30
        assert b2["Desde"] == datetime(2026, 11, 1, 9, 30)

    def test_la_calidad_va_en_letras(self):
        assert {f["Calidad"] for f in hoja(self.libro(), "Contenedores")} == {"A"}  # las filas de prueba son calidad 2

    def test_sin_registro_en_la_aplicacion_lo_dice_con_palabras(self):
        estados = {f["Estado en la aplicación"] for f in hoja(self.libro(), "Contenedores")}
        assert estados == {"Sin registro en este sistema"}

    def test_carros_deja_los_lados_juntos_y_dice_cuantas_veces_se_cargo(self):
        filas = hoja(self.libro(), "Carros")
        assert [(f["Carro físico"], f["Lado"], f["Carro"]) for f in filas] == [("P1", "A", "P1A"), ("P2", "B", "P2B")]
        assert [f["Veces cargado (en NOW)"] for f in filas] == [1, 1]
        assert [f["Veces cargado en la aplicación"] for f in filas] == [0, 0]  # un número, no "0 de 1"

    def test_no_usa_la_palabra_viaje_en_ninguna_parte(self):
        textos = []
        for nombre in self.libro().sheetnames:
            for fila in self.libro()[nombre].iter_rows(values_only=True):
                textos += [str(c) for c in fila if isinstance(c, str)]
        assert not [t for t in textos if "viaje" in t.lower()]

    def test_el_resumen_agrupa_las_horas_en_una_tabla_por_etapa(self):
        filas = [f for f in self.libro()["Resumen"].iter_rows(values_only=True) if f[0]]
        encabezado = next(i for i, f in enumerate(filas) if f[:4] == ("Etapa", "Promedio", "Mediana", "Máximo"))
        etapas = [f[0] for f in filas[encabezado + 1 :] if isinstance(f[1], (int, float))]
        assert "Horas en RCV01 hasta salir hacia WIP" in etapas
        assert "Horas en WIP hasta salir hacia DTY" in etapas

    def test_el_resumen_lista_los_que_mas_llevan_esperando(self):
        textos = [str(f[0]) for f in self.libro()["Resumen"].iter_rows(values_only=True) if f[0]]
        assert any(t.startswith("Los 10 que más llevan en RCV01") for t in textos)

    def test_como_leer_explica_las_etapas_y_la_plantilla_de_nowa(self):
        temas = [f[0] for f in self.libro()["Cómo leer"].iter_rows(min_row=2, values_only=True)]
        assert {"Qué es una fila", "Etapas", "Horas en DTY", "Cómo se lee NOW", "Anulados"} <= set(temas)


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
        [anulado] = hoja(self.libro(), "Anulados")
        assert (anulado["Carro"], anulado["Contenedor elemento"], anulado["Ubicación"]) == ("P3A", "E1", "RCV01")
        assert anulado["Notificado (016)"] == datetime(2026, 11, 1, 7, 30)
        assert anulado["Anulado el (119)"] == datetime(2026, 11, 1, 8, 45)
        assert anulado["Horas hasta anularlo"] == 1.2  # 1 h 15 min

    def test_el_anulado_y_el_de_otro_proceso_no_estan_entre_los_contenedores_ni_los_carros(self):
        libro = self.libro()
        assert [f["Contenedor elemento"] for f in hoja(libro, "Contenedores")] == ["A1", "B2"]
        assert [f["Carro"] for f in hoja(libro, "Carros")] == ["P1A", "P2B"]

    def test_el_resumen_cuenta_los_anulados_y_los_de_otros_procesos(self):
        resumen = {f[0]: f[1] for f in self.libro()["Resumen"].iter_rows(values_only=True) if f[0]}
        assert resumen["Contenedores anulados con la plantilla 119 (no se cuentan)"] == 1
        assert resumen["Contenedores de carros de otros procesos (D, T, DT…), sin analizar"] == 1

    def test_sin_anulados_la_hoja_existe_vacia(self):
        libro = load_workbook(BytesIO(escribir_excel(armar_reporte(leer_movimientos(excel(FILAS_BASICAS))))))
        assert hoja(libro, "Anulados") == []
