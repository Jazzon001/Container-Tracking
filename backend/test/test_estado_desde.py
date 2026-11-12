import time
from datetime import datetime, timedelta, timezone


def instante(texto: str) -> datetime:
    return datetime.fromisoformat(texto.replace("Z", "+00:00"))


def estado_desde(client, carro_id) -> datetime:
    return instante(client.get(f"/carros/{carro_id}").json()["estado_desde"])


def pausa():
    # Separa los instantes lo suficiente para poder compararlos.
    time.sleep(0.02)


def test_un_carro_nuevo_registra_cuando_quedo_disponible(crear_carro):
    carro = crear_carro("C-001")
    assert abs(datetime.now(timezone.utc) - instante(carro["estado_desde"])) < timedelta(seconds=30)


def test_la_fecha_se_entrega_en_utc_con_zona_horaria(crear_carro):
    carro = crear_carro("C-001")
    assert instante(carro["estado_desde"]).utcoffset() == timedelta(0)


def test_el_listado_incluye_la_fecha(client, crear_carro):
    crear_carro("C-001")
    assert "estado_desde" in client.get("/carros").json()[0]


def test_cargar_actualiza_la_fecha(client, crear_carro, cargar):
    carro = crear_carro("C-001")
    antes = estado_desde(client, carro["id"])
    pausa()
    cargar(carro["id"])
    assert estado_desde(client, carro["id"]) > antes


def test_entregar_actualiza_la_fecha(client, crear_carro, cargar):
    carro = crear_carro("C-001")
    cargar(carro["id"])
    antes = estado_desde(client, carro["id"])
    pausa()
    client.post(f"/carros/{carro['id']}/entrega")
    assert estado_desde(client, carro["id"]) > antes


def test_mantenimiento_actualiza_la_fecha_al_entrar_y_al_salir(client, crear_carro):
    carro = crear_carro("C-001")
    inicial = estado_desde(client, carro["id"])
    pausa()
    client.post(f"/carros/{carro['id']}/mantenimiento")
    en_mantenimiento = estado_desde(client, carro["id"])
    pausa()
    client.post(f"/carros/{carro['id']}/mantenimiento/salida")

    assert inicial < en_mantenimiento < estado_desde(client, carro["id"])


def test_una_operacion_rechazada_no_cambia_la_fecha(client, crear_carro, cargar):
    carro = crear_carro("C-001")
    cargar(carro["id"], "100123")
    antes = estado_desde(client, carro["id"])
    pausa()

    assert cargar(carro["id"], "100456").status_code == 409
    assert estado_desde(client, carro["id"]) == antes


def test_las_fechas_de_mantenimiento_tambien_son_utc(client, crear_carro):
    carro = crear_carro("C-001")
    entrada = client.post(f"/carros/{carro['id']}/mantenimiento").json()["fecha_entrada"]
    assert instante(entrada).utcoffset() == timedelta(0)
