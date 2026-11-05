def entregar(client, carro_id):
    return client.post(f"/carros/{carro_id}/entrega")


def test_entregar_carro_en_transito_lo_deja_disponible(client, crear_carro, cargar):
    carro = crear_carro("C-001")
    cargar(carro["id"], "100123")
    response = entregar(client, carro["id"])
    assert response.status_code == 200
    assert response.json()["estado"] == "disponible"
    assert response.json()["contenedor_elemento"] is None


def test_entregar_carro_disponible_devuelve_409(client, crear_carro):
    carro = crear_carro("C-001")
    assert entregar(client, carro["id"]).status_code == 409


def test_entregar_carro_inexistente_devuelve_404(client):
    assert entregar(client, 999).status_code == 404


def test_tras_entregar_el_contenedor_puede_usarse_de_nuevo(client, crear_carro, cargar):
    carro = crear_carro("C-001")
    cargar(carro["id"], "100123")
    entregar(client, carro["id"])
    otro = crear_carro("C-002")
    assert cargar(otro["id"], "100123").status_code == 200
