def ruta(carro_id, sufijo=""):
    return f"/carros/{carro_id}/mantenimiento{sufijo}"


def estado_de(client, carro_id):
    return client.get(f"/carros/{carro_id}").json()["estado"]


def test_iniciar_mantenimiento_registra_entrada_y_cambia_estado(client, crear_carro):
    carro = crear_carro("C-001")
    response = client.post(ruta(carro["id"]))
    assert response.status_code == 201
    assert response.json()["fecha_entrada"] is not None
    assert response.json()["fecha_salida"] is None
    assert estado_de(client, carro["id"]) == "en_mantenimiento"


def test_no_se_puede_iniciar_mantenimiento_de_un_carro_cargado(client, crear_carro, cargar):
    carro = crear_carro("C-001")
    cargar(carro["id"])
    assert client.post(ruta(carro["id"])).status_code == 409


def test_no_se_puede_iniciar_mantenimiento_dos_veces(client, crear_carro):
    carro = crear_carro("C-001")
    client.post(ruta(carro["id"]))
    assert client.post(ruta(carro["id"])).status_code == 409


def test_finalizar_mantenimiento_registra_salida_y_libera_el_carro(client, crear_carro):
    carro = crear_carro("C-001")
    client.post(ruta(carro["id"]))
    response = client.post(ruta(carro["id"], "/salida"))
    assert response.status_code == 200
    assert response.json()["fecha_salida"] is not None
    assert estado_de(client, carro["id"]) == "disponible"


def test_no_se_puede_finalizar_si_no_esta_en_mantenimiento(client, crear_carro):
    carro = crear_carro("C-001")
    assert client.post(ruta(carro["id"], "/salida")).status_code == 409


def test_un_carro_en_mantenimiento_no_se_puede_cargar(client, crear_carro, cargar):
    carro = crear_carro("C-001")
    client.post(ruta(carro["id"]))
    assert cargar(carro["id"]).status_code == 409


def test_historial_lista_los_mantenimientos_en_orden(client, crear_carro):
    carro = crear_carro("C-001")
    client.post(ruta(carro["id"]))
    client.post(ruta(carro["id"], "/salida"))
    client.post(ruta(carro["id"]))
    historial = client.get(ruta(carro["id"])).json()
    assert len(historial) == 2
    assert historial[0]["fecha_salida"] is not None
    assert historial[1]["fecha_salida"] is None


def test_mantenimiento_de_carro_inexistente_devuelve_404(client):
    assert client.post(ruta(999)).status_code == 404
    assert client.post(ruta(999, "/salida")).status_code == 404
    assert client.get(ruta(999)).status_code == 404
