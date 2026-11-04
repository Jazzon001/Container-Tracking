def crear_carro(client, numero):
    return client.post("/carros", json={"numero": numero}).json()


def cargar(client, carro_id, contenedor):
    return client.post(f"/carros/{carro_id}/carga", json={"contenedor_elemento": contenedor})


def test_cargar_carro_disponible_lo_pone_en_transito(client):
    carro = crear_carro(client, "C-001")
    response = cargar(client, carro["id"], "100123")
    assert response.status_code == 200
    assert response.json()["estado"] == "en_transito"
    assert response.json()["contenedor_elemento"] == "100123"


def test_cargar_recorta_espacios_del_codigo(client):
    carro = crear_carro(client, "C-001")
    assert cargar(client, carro["id"], "  100123 ").json()["contenedor_elemento"] == "100123"


def test_cargar_carro_inexistente_devuelve_404(client):
    assert cargar(client, 999, "100123").status_code == 404


def test_no_se_puede_cargar_un_carro_ya_cargado(client):
    carro = crear_carro(client, "C-001")
    cargar(client, carro["id"], "100123")
    response = cargar(client, carro["id"], "100456")
    assert response.status_code == 409
    # El carro conserva su primera carga.
    assert client.get(f"/carros/{carro['id']}").json()["contenedor_elemento"] == "100123"


def test_un_contenedor_no_puede_estar_en_dos_carros(client):
    primero = crear_carro(client, "C-001")
    segundo = crear_carro(client, "C-002")
    cargar(client, primero["id"], "100123")
    response = cargar(client, segundo["id"], "100123")
    assert response.status_code == 409
    # El segundo carro sigue libre para usarse con otro contenedor.
    assert client.get(f"/carros/{segundo['id']}").json()["estado"] == "disponible"
    assert cargar(client, segundo["id"], "100456").status_code == 200


def test_cargar_rechaza_codigo_vacio_o_ausente(client):
    carro = crear_carro(client, "C-001")
    assert cargar(client, carro["id"], "   ").status_code == 422
    assert client.post(f"/carros/{carro['id']}/carga", json={}).status_code == 422
