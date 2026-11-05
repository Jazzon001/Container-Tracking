def test_cargar_carro_disponible_lo_pone_en_transito(crear_carro, cargar):
    carro = crear_carro("C-001")
    response = cargar(carro["id"], "100123")
    assert response.status_code == 200
    assert response.json()["estado"] == "en_transito"
    assert response.json()["contenedor_elemento"] == "100123"


def test_cargar_recorta_espacios_del_codigo(crear_carro, cargar):
    carro = crear_carro("C-001")
    assert cargar(carro["id"], "  100123 ").json()["contenedor_elemento"] == "100123"


def test_cargar_carro_inexistente_devuelve_404(cargar):
    assert cargar(999, "100123").status_code == 404


def test_no_se_puede_cargar_un_carro_ya_cargado(client, crear_carro, cargar):
    carro = crear_carro("C-001")
    cargar(carro["id"], "100123")
    response = cargar(carro["id"], "100456")
    assert response.status_code == 409
    # El carro conserva su primera carga.
    assert client.get(f"/carros/{carro['id']}").json()["contenedor_elemento"] == "100123"


def test_un_contenedor_no_puede_estar_en_dos_carros(client, crear_carro, cargar):
    primero = crear_carro("C-001")
    segundo = crear_carro("C-002")
    cargar(primero["id"], "100123")
    response = cargar(segundo["id"], "100123")
    assert response.status_code == 409
    # El segundo carro sigue libre para usarse con otro contenedor.
    assert client.get(f"/carros/{segundo['id']}").json()["estado"] == "disponible"
    assert cargar(segundo["id"], "100456").status_code == 200


def test_cargar_rechaza_codigo_vacio_o_ausente(client, crear_carro, cargar):
    carro = crear_carro("C-001")
    assert cargar(carro["id"], "   ").status_code == 422
    assert client.post(f"/carros/{carro['id']}/carga", json={}).status_code == 422
