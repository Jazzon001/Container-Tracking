"""Reporte de tiempos de los carros. Todos los datos son inventados.

Cómo se lee NOW: la plantilla 016 es la producción (deja el carro puesto en RCV01: la entrada) y la 202
es una transferencia (cada fila es la SALIDA de esa ubicación: de RCV01 hacia un WIP, o de un WIP hacia DTY).
"""
from datetime import datetime, timedelta

from app.services.reporte_tiempos import (
    Movimiento,
    agrupar_viajes,
    es_recepcion,
    es_tarima,
    es_wip,
    etiqueta_calidad,
    horas,
    horas_en_rcv_por_calidad,
    horas_en_wip_por_calidad,
    horas_en_wip_por_wip,
    por_carro,
    resumen,
    separar_lado,
)


def mov(dia, hora, ubicacion, carro, contenedor, calidad=None, plantilla="202"):
    return Movimiento(datetime(2026, 11, dia, hora), ubicacion, carro, contenedor, calidad, plantilla)


def entrada(dia, hora, carro, contenedor, calidad=None):
    """La producción (016): deja el carro puesto en RCV01."""
    return mov(dia, hora, "RCV01", carro, contenedor, calidad, plantilla="016")


# A1 (carro P1): entra a RCV01 el 1 a las 6, sale de RCV01 a las 8 y del WIPB4 hacia DTY a las 12.
# B2 (P2): entra a RCV01 el 1 a las 9 y no se mueve.
# C3 (P3): solo se ve su salida del WIPA1 (se notificó antes del archivo).
# D4 (P1, el 2): entra a las 4, sale de RCV01 a las 6, del WIPC1 a las 8 y del WIPB1 a las 9.
# E5 (P4): entra el 1 a las 9, sale de RCV01 a las 10 y no se ve su salida del WIP.
# F6 (P5): solo se ve su salida de RCV01 el 1 a las 9 (se notificó antes del archivo) y sigue en WIP.
MOVIMIENTOS = [
    entrada(1, 6, "P1", "A1"),
    mov(1, 8, "RCV01", "P1", "A1"),
    mov(1, 12, "WIPB4", "P1", "A1"),
    entrada(1, 9, "P2", "B2"),
    mov(1, 10, "WIPA1", "P3", "C3"),
    entrada(2, 4, "P1", "D4"),
    mov(2, 6, "RCV01", "P1", "D4"),
    mov(2, 8, "WIPC1", "P1", "D4"),
    mov(2, 9, "WIPB1", "P1", "D4"),
    entrada(1, 9, "P4", "E5"),
    mov(1, 10, "RCV01", "P4", "E5"),
    mov(1, 9, "RCV01", "P5", "F6"),
]
CORTE = datetime(2026, 11, 2, 18)


def viaje(contenedor, movimientos=MOVIMIENTOS):
    return next(v for v in agrupar_viajes(movimientos, CORTE) if v.contenedor == contenedor)


class TestViajes:
    def test_un_viaje_por_contenedor_elemento(self):
        assert len(agrupar_viajes(MOVIMIENTOS, CORTE)) == 6

    def test_la_016_es_la_entrada_a_rcv01(self):
        v = viaje("A1")
        assert v.notificado_en == datetime(2026, 11, 1, 6)
        assert v.primer_movimiento == datetime(2026, 11, 1, 6)

    def test_la_202_en_recepcion_es_la_salida_hacia_un_wip(self):
        assert viaje("A1").salio_de_recepcion_en == datetime(2026, 11, 1, 8)

    def test_la_202_en_un_wip_es_la_salida_hacia_dty(self):
        v = viaje("A1")
        assert v.salio_a_dty and not v.sigue_en_wip and not v.sigue_en_rcv
        assert v.salio_a_dty_en == datetime(2026, 11, 1, 12)
        assert v.wip_de_salida == "WIPB4"
        assert v.recorrido == "RCV01 → WIPB4 → DTY"
        assert v.situacion == "En DTY (salió de WIPB4)"

    def test_mide_las_horas_en_rcv01_en_wip_y_en_poy(self):
        v = viaje("A1")
        assert v.horas_en_rcv == timedelta(hours=2)  # de la 016 a salir de RCV01
        assert v.horas_en_wip == timedelta(hours=4)  # de salir de RCV01 a salir del WIP
        assert v.horas_en_poy == timedelta(hours=6)  # de la 016 a salir hacia DTY

    def test_solo_con_la_016_sigue_en_rcv01_hasta_el_corte(self):
        v = viaje("B2")
        assert v.sigue_en_rcv and not v.sigue_en_wip and not v.salio_a_dty
        assert v.horas_en_rcv == CORTE - datetime(2026, 11, 1, 9)
        assert v.horas_en_wip is None and v.horas_en_poy is None
        assert v.recorrido == "RCV01"
        assert v.situacion == "En RCV01 (notificado; esperando a que intermedio lo mueva)"

    def test_si_salio_de_rcv01_y_no_de_wip_sigue_en_wip_hasta_el_corte(self):
        v = viaje("E5")
        assert v.sigue_en_wip and not v.sigue_en_rcv
        assert v.horas_en_rcv == timedelta(hours=1)
        assert v.horas_en_wip == CORTE - datetime(2026, 11, 1, 10)
        assert v.horas_en_poy is None
        assert v.recorrido == "RCV01 → (en WIP)"
        assert v.situacion == "En WIP (salió de RCV01; aún no sale hacia DTY)"

    def test_sin_la_016_no_se_inventan_las_horas_en_rcv01(self):
        v = viaje("F6")
        assert v.notificado_en is None and v.horas_en_rcv is None and v.horas_en_poy is None
        assert v.horas_en_wip == CORTE - datetime(2026, 11, 1, 9)

    def test_sin_la_016_ni_la_salida_de_recepcion_solo_se_sabe_que_salio_hacia_dty(self):
        v = viaje("C3")
        assert v.salio_a_dty and v.wip_de_salida == "WIPA1"
        assert v.horas_en_rcv is None and v.horas_en_wip is None and v.horas_en_poy is None
        assert v.recorrido == "WIPA1 → DTY"

    def test_pasar_de_un_wip_a_otro_cuenta_todo_como_tiempo_en_wip(self):
        v = viaje("D4")
        assert v.recorrido == "RCV01 → WIPC1 → WIPB1 → DTY"
        assert v.wip_de_salida == "WIPB1"
        assert v.horas_en_wip == timedelta(hours=3)

    def test_mide_cuanto_lleva_desde_su_ultimo_movimiento(self):
        assert viaje("D4").desde_ultimo_movimiento == CORTE - datetime(2026, 11, 2, 9)

    def test_el_corte_por_omision_es_el_ultimo_movimiento(self):
        v = next(v for v in agrupar_viajes(MOVIMIENTOS) if v.contenedor == "D4")
        assert v.desde_ultimo_movimiento == timedelta(0)

    def test_ordena_los_movimientos_aunque_vengan_desordenados(self):
        revueltos = [MOVIMIENTOS[2], MOVIMIENTOS[0], MOVIMIENTOS[1]]
        assert viaje("A1", revueltos).recorrido == "RCV01 → WIPB4 → DTY"

    def test_varias_016_del_mismo_contenedor_cuentan_desde_la_primera(self):
        # NOW parte a veces la producción de un contenedor en varias líneas en el mismo instante.
        partidas = [entrada(1, 6, "P9", "Z"), entrada(1, 6, "P9", "Z"), entrada(1, 6, "P9", "Z")]
        v = viaje("Z", partidas)
        assert v.notificado_en == datetime(2026, 11, 1, 6)
        assert v.sigue_en_rcv and v.recorrido == "RCV01"

    def test_sin_movimientos_no_hay_viajes(self):
        assert agrupar_viajes([]) == []

    def test_las_tarimas_no_son_carros(self):
        tarima = mov(1, 8, "EMP", "TARPOY", "T-99")
        assert es_tarima(tarima)
        assert agrupar_viajes([tarima]) == []
        assert not es_tarima(MOVIMIENTOS[0])

    def test_una_ubicacion_que_no_es_recepcion_ni_wip_se_describe_tal_cual(self):
        v = agrupar_viajes([mov(1, 8, "XYZ", "P9", "Z")])[0]
        assert v.situacion == "Salió de XYZ"
        assert not v.salio_a_dty and not v.sigue_en_wip and not v.sigue_en_rcv


class TestRecepcionDeGradoB:
    """RCV02 recibe el producto POY de grado B que sale de DTY: es otra recepción, sin 016."""

    DATOS = [
        mov(1, 8, "RCV02", "P5", "G1", calidad=3),
        mov(1, 11, "WIPA4", "P5", "G1", calidad=3),
        mov(1, 9, "RCV02", "P6", "G2", calidad=3),
    ]

    def test_rcv02_cuenta_como_recepcion(self):
        assert es_recepcion("RCV01") and es_recepcion("RCV02")
        assert not es_recepcion("WIPA4") and es_wip("WIPA4")

    def test_mide_las_horas_en_wip_desde_rcv02_igual_que_desde_rcv01(self):
        assert viaje("G1", self.DATOS).horas_en_wip == timedelta(hours=3)

    def test_si_se_queda_en_rcv02_lo_dice_con_su_significado(self):
        v = viaje("G2", self.DATOS)
        assert v.sigue_en_wip
        assert "RCV02" in v.situacion and "grado B" in v.situacion


class TestCalidad:
    DATOS = [
        entrada(1, 7, "P1", "A", calidad=1),
        mov(1, 8, "RCV01", "P1", "A", calidad=1),
        mov(1, 10, "WIPA4", "P1", "A", calidad=1),
        entrada(1, 6, "P2", "B", calidad=2),
        mov(1, 8, "RCV01", "P2", "B", calidad=2),
        mov(1, 14, "WIPA4", "P2", "B", calidad=2),
        mov(1, 8, "RCV01", "P3", "C"),
        mov(1, 9, "WIPA4", "P3", "C"),
    ]

    def test_la_calidad_viaja_con_el_viaje_y_con_el_carro(self):
        viajes = agrupar_viajes(self.DATOS)
        assert {v.contenedor: v.calidad for v in viajes} == {"A": 1, "B": 2, "C": None}
        assert {f.carro: f.calidad for f in por_carro(viajes)} == {"P1": 1, "P2": 2, "P3": None}

    def test_horas_en_wip_por_calidad(self):
        assert horas_en_wip_por_calidad(agrupar_viajes(self.DATOS)) == [
            ("1 (AA)", 1, 2.0, 2.0),
            ("2 (A)", 1, 6.0, 6.0),
            ("sin dato", 1, 1.0, 1.0),
        ]

    def test_horas_en_rcv01_por_calidad_solo_con_los_que_ya_salieron_y_tienen_016(self):
        assert horas_en_rcv_por_calidad(agrupar_viajes(self.DATOS)) == [
            ("1 (AA)", 1, 1.0, 1.0),
            ("2 (A)", 1, 2.0, 2.0),
        ]


class TestPorCarro:
    def filas(self):
        return {f.carro: f for f in por_carro(agrupar_viajes(MOVIMIENTOS, CORTE))}

    def test_una_fila_por_carro_con_sus_viajes(self):
        filas = self.filas()
        assert set(filas) == {"P1", "P2", "P3", "P4", "P5"}
        assert filas["P1"].viajes == 2 and filas["P2"].viajes == 1

    def test_la_situacion_sale_del_ultimo_viaje(self):
        filas = self.filas()
        assert filas["P1"].ultimo_contenedor == "D4"
        assert filas["P1"].situacion == "En DTY (salió de WIPB1)"
        assert filas["P2"].situacion.startswith("En RCV01")
        assert filas["P4"].situacion.startswith("En WIP")

    def test_promedia_las_horas_en_rcv01_y_en_wip_de_los_viajes_ya_cerrados(self):
        p1 = self.filas()["P1"]
        assert p1.horas_promedio_en_rcv == timedelta(hours=2)  # (2 h + 2 h) / 2
        assert p1.horas_promedio_en_wip == timedelta(hours=3.5)  # (4 h + 3 h) / 2

    def test_lo_que_sigue_abierto_no_entra_en_los_promedios(self):
        filas = self.filas()
        assert filas["P2"].horas_promedio_en_rcv is None  # sigue en RCV01
        assert filas["P4"].horas_promedio_en_rcv == timedelta(hours=1)  # ya salió de RCV01
        assert filas["P4"].horas_promedio_en_wip is None  # sigue en WIP
        assert filas["P3"].horas_promedio_en_wip is None  # no se vio su salida de recepción


class TestResumen:
    def datos(self):
        return dict(resumen(agrupar_viajes(MOVIMIENTOS, CORTE), tarimas=2))

    def test_cuenta_carros_y_viajes(self):
        datos = self.datos()
        assert datos["Lados de carro (cada A o B, como en NOW)"] == 5
        assert datos["Carros físicos (lados A y B juntos)"] == 5  # ninguno de estos códigos tiene lado
        assert datos["Viajes (contenedores elemento)"] == 6

    def test_cuenta_donde_esta_cada_viaje(self):
        datos = self.datos()
        assert datos["Viajes que siguen en RCV01 (notificados, sin moverse)"] == 1
        assert datos["Viajes que siguen en WIP (aún no salen hacia DTY)"] == 2
        assert datos["Viajes que ya salieron hacia DTY"] == 3

    def test_dice_cual_es_el_que_mas_lleva_en_cada_etapa(self):
        datos = self.datos()
        assert datos["El que más lleva en RCV01 sin moverse"] == "P2: 33.0 h"
        assert datos["El que más lleva en WIP sin salir"] == "P5: 33.0 h"

    def test_estadisticas_solo_de_lo_ya_cerrado(self):
        datos = self.datos()
        # RCV01: A1 2 h, D4 2 h, E5 1 h. WIP: A1 4 h, D4 3 h. POY: A1 6 h, D4 5 h.
        assert datos["Horas en RCV01 hasta salir hacia WIP: promedio"] == 1.7
        assert datos["Horas en RCV01 hasta salir hacia WIP: mediana"] == 2.0
        assert datos["Horas en WIP hasta salir hacia DTY: promedio"] == 3.5
        assert datos["Horas en WIP hasta salir hacia DTY: máximo"] == 4.0
        assert datos["Horas en POY (de RCV01 a salir hacia DTY): promedio"] == 5.5
        assert not any("fuera de POY" in indicador for indicador in datos)  # lo medirá el propio sistema al liberar

    def test_avisa_de_las_tarimas_solo_si_hay(self):
        assert self.datos()["Movimientos de producto en tarima (sin carro)"] == 2
        assert "Movimientos de producto en tarima (sin carro)" not in dict(
            resumen(agrupar_viajes(MOVIMIENTOS, CORTE))
        )

    def test_sin_viajes_no_falla(self):
        assert dict(resumen([]))["Viajes (contenedores elemento)"] == 0

    def test_horas_en_wip_por_wip_de_salida(self):
        assert horas_en_wip_por_wip(agrupar_viajes(MOVIMIENTOS, CORTE)) == [
            ("WIPB1", 1, 3.0, 3.0),
            ("WIPB4", 1, 4.0, 4.0),
        ]


class TestLadosYCalidad:
    def test_un_carro_fisico_se_parte_en_lado_a_y_lado_b(self):
        assert separar_lado("P056A") == ("P056", "A")
        assert separar_lado("P056B") == ("P056", "B")
        assert separar_lado("p056b") == ("p056", "B")

    def test_un_codigo_sin_lado_se_devuelve_entero(self):
        assert separar_lado("P056") == ("P056", "")
        assert separar_lado("A") == ("A", "")

    def test_los_dos_lados_cuentan_como_un_solo_carro_fisico(self):
        datos = [mov(1, 8, "RCV01", "P056A", "X1"), mov(1, 8, "RCV01", "P056B", "X2"), mov(1, 9, "RCV01", "P057A", "X3")]
        resultado = dict(resumen(agrupar_viajes(datos)))
        assert resultado["Carros físicos (lados A y B juntos)"] == 2
        assert resultado["Lados de carro (cada A o B, como en NOW)"] == 3

    def test_por_carro_deja_un_lado_junto_al_otro(self):
        datos = [mov(1, 8, "RCV01", c, f"X{i}") for i, c in enumerate(["P057A", "P056B", "P056A", "P057B"])]
        filas = por_carro(agrupar_viajes(datos))
        assert [f.carro for f in filas] == ["P056A", "P056B", "P057A", "P057B"]
        assert [(f.carro_fisico, f.lado) for f in filas][:2] == [("P056", "A"), ("P056", "B")]

    def test_la_calidad_1_es_aa_la_2_es_a_y_la_3_es_b(self):
        assert etiqueta_calidad(1) == "1 (AA)"
        assert etiqueta_calidad(2) == "2 (A)"
        assert etiqueta_calidad(3) == "3 (B)"

    def test_una_calidad_que_no_se_conoce_se_muestra_tal_cual(self):
        assert etiqueta_calidad(9) == "9"
        assert etiqueta_calidad(None) == "sin dato"


def test_horas_redondea_a_un_decimal_y_acepta_nulo():
    assert horas(timedelta(minutes=100)) == 1.7
    assert horas(None) is None
