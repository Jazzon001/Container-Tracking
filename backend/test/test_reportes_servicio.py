"""Registros del sistema que se cruzan con el Excel de NOW. Datos inventados."""
from datetime import datetime, timedelta, timezone

from app.models import Carga, Carro, TipoCarro
from app.services import reportes
from app.services.reportes import _sin_zona, cargar_registros


def crear_cargas(sesion, cargas):
    """cargas: lista de (contenedor, cargada_en, recibida_en) para un mismo carro."""
    with sesion() as db:
        carro = Carro(numero="P1A", tipo=TipoCarro.POY)
        db.add(carro)
        db.flush()
        for contenedor, cargada, recibida in cargas:
            db.add(Carga(carro_id=carro.id, contenedor_elemento=contenedor, cargada_en=cargada, recibida_en=recibida))
        db.commit()


def test_una_fecha_con_zona_se_pasa_a_utc_sin_zona():
    seis_menos = timezone(timedelta(hours=-6))
    assert _sin_zona(datetime(2026, 11, 1, 6, tzinfo=seis_menos)) == datetime(2026, 11, 1, 12)


def test_una_fecha_sin_zona_o_nula_no_cambia():
    assert _sin_zona(datetime(2026, 11, 1, 6)) == datetime(2026, 11, 1, 6)
    assert _sin_zona(None) is None


def test_trae_solo_los_contenedores_pedidos(sesion_de_pruebas):
    crear_cargas(
        sesion_de_pruebas,
        [("A1", datetime(2026, 11, 1, 13), None), ("OTRO", datetime(2026, 11, 1, 14), None)],
    )
    with sesion_de_pruebas() as db:
        registros = cargar_registros(db, {"A1", "NO-EXISTE"})
    assert set(registros) == {"A1"}
    assert registros["A1"].cargada_en == datetime(2026, 11, 1, 13)
    assert registros["A1"].recibida_en is None


def test_si_un_codigo_se_cargo_varias_veces_gana_la_carga_mas_reciente(sesion_de_pruebas):
    crear_cargas(
        sesion_de_pruebas,
        [
            ("A1", datetime(2026, 11, 1, 13), datetime(2026, 11, 1, 20)),
            ("A1", datetime(2026, 11, 5, 9), None),
        ],
    )
    with sesion_de_pruebas() as db:
        assert cargar_registros(db, {"A1"})["A1"].cargada_en == datetime(2026, 11, 5, 9)


def test_consulta_en_lotes_cuando_son_muchos_contenedores(sesion_de_pruebas, monkeypatch):
    monkeypatch.setattr(reportes, "LOTE", 2)
    crear_cargas(sesion_de_pruebas, [(f"C{i}", datetime(2026, 11, 1, 13), None) for i in range(5)])
    with sesion_de_pruebas() as db:
        registros = cargar_registros(db, {f"C{i}" for i in range(5)})
    assert len(registros) == 5


def test_sin_contenedores_no_consulta_nada(sesion_de_pruebas):
    with sesion_de_pruebas() as db:
        assert cargar_registros(db, set()) == {}
