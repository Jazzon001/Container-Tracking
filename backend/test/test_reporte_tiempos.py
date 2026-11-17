"""Reporte de tiempos de los carros. Todos los datos son inventados.

Cómo se lee NOW: la plantilla 016 es la producción (deja el carro puesto en RCV01: la entrada) y la 202
es una transferencia (cada fila es la SALIDA de esa ubicación: de RCV01 hacia un WIP, o de un WIP hacia DTY).
"""
from datetime import datetime, timedelta

from app.services.reporte_tiempos import (
    Movimiento,
    Registro,
    agrupar_viajes,
    anulaciones,
    armar_reporte,
    cruzar_con_registros,
    es_tarima,
    es_wip,
    etiqueta_calidad,
    horas,
    horas_en_dty_por_wip,
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


class TestRcv02:
    """RCV02 es la última localización antes de que empaque libere el carro: ahí llegan los carros con
    producto de grado B que sale de DTY."""

    # Viaje completo: entra a RCV01 a las 6, sale a las 8, sale del WIPA4 hacia DTY a las 12 y, de vuelta,
    # sale de RCV02 el día 2 a las 7.
    COMPLETO = [
        entrada(1, 6, "P5", "G1", calidad=3),
        mov(1, 8, "RCV01", "P5", "G1", calidad=3),
        mov(1, 12, "WIPA4", "P5", "G1", calidad=3),
        mov(2, 7, "RCV02", "P5", "G1", calidad=3),
    ]
    # Solo se ve su salida de RCV02 (el resto fue antes del archivo).
    SOLO_RCV02 = [mov(1, 9, "RCV02", "P6", "G2", calidad=3)]

    def test_la_salida_de_rcv02_no_cambia_lo_que_se_mide_hasta_salir_hacia_dty(self):
        v = viaje("G1", self.COMPLETO)
        assert v.salio_a_dty and v.wip_de_salida == "WIPA4"
        assert v.salio_a_dty_en == datetime(2026, 11, 1, 12)
        assert v.horas_en_rcv == timedelta(hours=2)
        assert v.horas_en_wip == timedelta(hours=4)

    def test_anota_cuando_salio_de_rcv02(self):
        v = viaje("G1", self.COMPLETO)
        assert v.paso_por_rcv02
        assert v.salio_de_rcv02_en == datetime(2026, 11, 2, 7)

    def test_el_recorrido_pone_dty_entre_el_ultimo_wip_y_rcv02(self):
        assert viaje("G1", self.COMPLETO).recorrido == "RCV01 → WIPA4 → DTY → RCV02"

    def test_la_situacion_dice_que_falta_que_empaque_lo_libere(self):
        v = viaje("G1", self.COMPLETO)
        assert v.situacion == "Salió de RCV02 (la última localización); falta que empaque libere el carro"

    def test_solo_con_la_salida_de_rcv02_no_se_inventan_horas_en_rcv01_ni_en_wip(self):
        v = viaje("G2", self.SOLO_RCV02)
        assert v.paso_por_rcv02 and not v.salio_a_dty
        assert v.horas_en_rcv is None and v.horas_en_wip is None
        assert v.recorrido == "RCV02"
        assert "RCV02" in v.situacion and "empaque" in v.situacion

    def test_no_cuenta_como_si_siguiera_en_wip_ni_en_rcv01(self):
        v = viaje("G2", self.SOLO_RCV02)
        assert not v.sigue_en_wip and not v.sigue_en_rcv

    def test_el_resumen_cuenta_los_viajes_que_pasaron_por_rcv02(self):
        datos = dict(resumen(agrupar_viajes(self.COMPLETO + self.SOLO_RCV02)))
        assert datos["Viajes que ya pasaron por RCV02 (falta que empaque libere el carro)"] == 2

    def test_los_demas_viajes_no_pasaron_por_rcv02(self):
        assert not viaje("A1").paso_por_rcv02


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


class TestCruceConElSistema:
    """NOW guarda la hora local de la planta y el sistema la guarda en UTC: con -6, UTC = local + 6 h."""

    DESPLAZAMIENTO = -6

    def utc(self, dia, hora):
        """La hora local de NOW (dia, hora) expresada en UTC."""
        return datetime(2026, 11, dia, hora) + timedelta(hours=6)

    def registros(self):
        return {
            # A1: se escaneó a las 7 (1 h después de la 016) y se liberó a las 20, tras salir hacia DTY a las 12.
            "A1": Registro(self.utc(1, 7), self.utc(1, 20)),
            # B2: se escaneó a las 10 (1 h después de la 016) y todavía no sale de RCV01.
            "B2": Registro(self.utc(1, 10), None),
            # D4: se escaneó a las 5 (1 h después de la 016), salió hacia DTY a las 9 el día 2 y no se ha liberado.
            "D4": Registro(self.utc(2, 5), None),
        }

    def cruzados(self):
        viajes = agrupar_viajes(MOVIMIENTOS, CORTE)
        return {v.contenedor: v for v in cruzar_con_registros(viajes, self.registros(), self.DESPLAZAMIENTO, CORTE)}

    def test_un_viaje_sin_registro_en_el_sistema_no_cambia(self):
        c3 = self.cruzados()["C3"]
        assert not c3.en_sistema
        assert c3.cargada_en is None and c3.horas_en_dty is None
        assert c3.situacion_sistema == "Sin registro en este sistema"

    def test_las_horas_del_sistema_se_pasan_a_la_hora_de_now(self):
        a1 = self.cruzados()["A1"]
        assert a1.cargada_en == datetime(2026, 11, 1, 7)
        assert a1.recibida_en == datetime(2026, 11, 1, 20)

    def test_mide_cuanto_tardo_en_escanearse_desde_la_notificacion(self):
        assert self.cruzados()["A1"].horas_hasta_escanear == timedelta(hours=1)
        assert self.cruzados()["B2"].horas_hasta_escanear == timedelta(hours=1)

    def test_mide_las_horas_en_dty_de_la_salida_del_wip_a_la_liberacion(self):
        a1 = self.cruzados()["A1"]
        assert a1.horas_en_dty == timedelta(hours=8)  # sale a las 12 y se libera a las 20
        assert not a1.dty_abierto
        assert a1.situacion_sistema == "Liberado en el sistema"

    def test_si_aun_no_se_libera_las_horas_corren_hasta_el_corte(self):
        d4 = self.cruzados()["D4"]
        assert d4.horas_en_dty == CORTE - datetime(2026, 11, 2, 9)
        assert d4.dty_abierto
        assert d4.situacion_sistema == "Cargado en el sistema, sin liberar"

    def test_sin_salida_hacia_dty_no_hay_horas_en_dty(self):
        b2 = self.cruzados()["B2"]
        assert b2.en_sistema and b2.horas_en_dty is None and not b2.dty_abierto

    def test_una_liberacion_anterior_a_la_salida_no_se_mide(self):
        registros = {"A1": Registro(self.utc(1, 7), self.utc(1, 10))}  # liberado a las 10, antes de salir a las 12
        viajes = cruzar_con_registros(agrupar_viajes(MOVIMIENTOS, CORTE), registros, self.DESPLAZAMIENTO, CORTE)
        a1 = next(v for v in viajes if v.contenedor == "A1")
        assert a1.horas_en_dty is None and not a1.dty_abierto

    def test_un_escaneo_anterior_a_la_notificacion_no_se_mide(self):
        registros = {"A1": Registro(self.utc(1, 5), None)}  # escaneado a las 5, antes de la 016 de las 6
        viajes = cruzar_con_registros(agrupar_viajes(MOVIMIENTOS, CORTE), registros, self.DESPLAZAMIENTO, CORTE)
        assert next(v for v in viajes if v.contenedor == "A1").horas_hasta_escanear is None

    def test_el_desplazamiento_cambia_la_hora_de_now(self):
        registros = {"A1": Registro(datetime(2026, 11, 1, 13), None)}
        cero = cruzar_con_registros(agrupar_viajes(MOVIMIENTOS, CORTE), registros, 0, CORTE)
        assert next(v for v in cero if v.contenedor == "A1").cargada_en == datetime(2026, 11, 1, 13)

    def test_por_carro_trae_la_situacion_en_el_sistema_del_ultimo_viaje(self):
        filas = {f.carro: f for f in por_carro(list(self.cruzados().values()))}
        p1 = filas["P1"]  # su último viaje es D4
        assert p1.situacion_sistema == "Cargado en el sistema, sin liberar"
        assert p1.dty_abierto and p1.horas_en_dty == CORTE - datetime(2026, 11, 2, 9)
        assert p1.horas_promedio_en_dty == timedelta(hours=8)  # solo cuenta A1, que ya se liberó
        assert filas["P3"].situacion_sistema == "Sin registro en este sistema"

    def test_si_el_ultimo_viaje_no_tiene_registro_se_usa_el_ultimo_que_si_lo_tiene(self):
        # P1 hizo A1 (con registro, liberado) y D4 (sin registro): la fila del carro no debe decir "sin registro".
        registros = {"A1": self.registros()["A1"]}
        viajes = cruzar_con_registros(agrupar_viajes(MOVIMIENTOS, CORTE), registros, self.DESPLAZAMIENTO, CORTE)
        p1 = next(f for f in por_carro(viajes) if f.carro == "P1")
        assert p1.ultimo_contenedor == "D4"  # el último de NOW sigue siendo D4
        assert p1.situacion_sistema == "Liberado en el sistema"
        assert p1.viajes_en_sistema == 1 and p1.viajes == 2
        assert p1.horas_en_dty == timedelta(hours=8) and not p1.dty_abierto

    def test_cuenta_los_viajes_registrados_de_cada_carro(self):
        filas = {f.carro: f for f in por_carro(list(self.cruzados().values()))}
        assert filas["P1"].viajes_en_sistema == 2  # A1 y D4
        assert filas["P2"].viajes_en_sistema == 1
        assert filas["P3"].viajes_en_sistema == 0

    def test_el_resumen_trae_lo_del_cruce(self):
        datos = dict(resumen(list(self.cruzados().values())))
        assert datos["Viajes registrados en este sistema"] == "3 de 6"
        assert datos["Horas de la notificación (016) a escanear el carro: promedio"] == 1.0
        assert datos["Horas en DTY (de salir del WIP a liberar el carro): promedio"] == 8.0
        assert datos["Viajes en DTY cargados en el sistema y aún sin liberar"] == 1
        assert datos["El que más lleva en DTY sin liberar"] == "P1: 9.0 h"

    def test_horas_en_dty_por_wip_solo_cuenta_los_liberados(self):
        assert horas_en_dty_por_wip(list(self.cruzados().values())) == [("WIPB4", 1, 8.0, 8.0)]


class TestArmarReporte:
    def test_sin_registros_no_hay_cruce(self):
        reporte = armar_reporte(MOVIMIENTOS)
        datos = dict(reporte.resumen)
        assert datos["Viajes registrados en este sistema"] == "0 de 6"
        assert "Viajes en DTY cargados en el sistema y aún sin liberar" in datos
        assert not any(v.en_sistema for v in reporte.viajes)

    def test_el_corte_es_el_ultimo_movimiento_del_archivo(self):
        assert armar_reporte(MOVIMIENTOS).corte == datetime(2026, 11, 2, 9)

    def test_trae_las_tablas_de_horas(self):
        titulos = [t.titulo for t in armar_reporte(MOVIMIENTOS).tablas]
        assert "Horas en DTY hasta liberar el carro, según el WIP de salida" in titulos
        assert len(titulos) == 4

    def test_cuenta_las_tarimas(self):
        assert armar_reporte(MOVIMIENTOS + [mov(1, 8, "EMP", "TARPOY", "T-1")]).tarimas == 1

    def test_sin_movimientos_no_falla(self):
        reporte = armar_reporte([])
        assert reporte.viajes == [] and reporte.carros == []


def anular(dia, hora, ubicacion, carro, contenedor, calidad=None):
    """La plantilla 119: anula la notificación (la negativa de la 016)."""
    return mov(dia, hora, ubicacion, carro, contenedor, calidad, plantilla="119")


class TestAnulaciones:
    """Un contenedor con una 119 se notificó por error: no cuenta como viaje."""

    # E1 (P1A): notificado a las 6 y anulado a las 7. F2 (P1A): un viaje normal. G3 (P2B): solo se ve su 119.
    DATOS = [
        entrada(1, 6, "P1A", "E1"),
        anular(1, 7, "RCV01", "P1A", "E1"),
        entrada(1, 8, "P1A", "F2"),
        mov(1, 10, "RCV01", "P1A", "F2"),
        anular(1, 9, "RCV01", "P2B", "G3"),
    ]

    def test_un_contenedor_con_119_no_cuenta_como_viaje(self):
        viajes = agrupar_viajes(self.DATOS)
        assert [v.contenedor for v in viajes] == ["F2"]

    def test_la_119_sin_su_016_en_el_archivo_tambien_lo_excluye(self):
        assert "G3" not in [v.contenedor for v in agrupar_viajes(self.DATOS)]

    def test_un_carro_cuyo_unico_viaje_se_anulo_no_aparece_en_por_carro(self):
        assert [f.carro for f in por_carro(agrupar_viajes(self.DATOS))] == ["P1A"]

    def test_si_se_anula_el_ultimo_viaje_el_carro_muestra_el_anterior(self):
        datos = [
            entrada(1, 6, "P1A", "A"), mov(1, 8, "RCV01", "P1A", "A"), mov(1, 12, "WIPB4", "P1A", "A"),
            entrada(2, 6, "P1A", "B"), anular(2, 7, "RCV01", "P1A", "B"),
        ]
        [fila] = por_carro(agrupar_viajes(datos))
        assert fila.ultimo_contenedor == "A" and fila.viajes == 1
        assert fila.situacion == "En DTY (salió de WIPB4)"

    def test_lista_los_anulados_con_cuando_se_notifico_y_cuando_se_anulo(self):
        anulados = anulaciones(self.DATOS)
        assert [(a.carro, a.contenedor) for a in anulados] == [("P1A", "E1"), ("P2B", "G3")]
        e1, g3 = anulados
        assert e1.notificado_en == datetime(2026, 11, 1, 6) and e1.anulado_en == datetime(2026, 11, 1, 7)
        assert e1.ubicacion == "RCV01"
        assert g3.notificado_en is None  # su 016 fue anterior al archivo

    def test_sin_anulaciones_no_hay_anulados(self):
        assert anulaciones(MOVIMIENTOS) == []

    def test_el_resumen_cuenta_los_anulados_solo_si_hay(self):
        assert dict(resumen(agrupar_viajes(self.DATOS), anulados=2))[
            "Contenedores anulados con la plantilla 119 (no cuentan como viaje)"
        ] == 2
        assert "Contenedores anulados con la plantilla 119 (no cuentan como viaje)" not in dict(resumen(agrupar_viajes(self.DATOS)))

    def test_armar_reporte_trae_los_anulados_y_no_los_cuenta_como_viaje(self):
        reporte = armar_reporte(self.DATOS)
        assert len(reporte.viajes) == 1 and len(reporte.anulados) == 2
        assert dict(reporte.resumen)["Viajes (contenedores elemento)"] == 1


class TestCarrosDeOtrosProcesos:
    """El reporte analiza el flujo de POY (carros P…). Los D, T y DT tienen otro flujo: solo se cuentan."""

    DATOS = [
        entrada(1, 6, "P1A", "A1"),
        entrada(1, 7, "D064", "D1"),
        entrada(1, 8, "D065", "D2"),
        entrada(1, 9, "T020", "T1"),
        entrada(1, 9, "DT07", "X1"),
        mov(1, 10, "EMP", "TARPOY", "TAR-1"),
    ]

    def test_solo_los_carros_de_poy_son_viajes(self):
        assert [v.carro for v in agrupar_viajes(self.DATOS)] == ["P1A"]

    def test_las_tarimas_no_cuentan_como_otro_proceso(self):
        assert armar_reporte(self.DATOS).otros_contenedores == 4
        assert armar_reporte(self.DATOS).tarimas == 1

    def test_el_resumen_los_cuenta_aparte(self):
        datos = dict(armar_reporte(self.DATOS).resumen)
        assert datos["Contenedores de carros de otros procesos (D, T, DT…), sin analizar"] == 4
        assert datos["Viajes (contenedores elemento)"] == 1

    def test_un_contenedor_anulado_de_otro_proceso_no_se_lista_como_anulado(self):
        datos = self.DATOS + [anular(2, 8, "WIPE", "D064", "D1")]
        assert armar_reporte(datos).anulados == []
