def test_crear_carro_devuelve_201_y_estado_disponible(client):
    response = client.post("/carros", json={"numero": "C-001"})
    assert response.status_code == 201
    datos = response.json()
    assert datos["numero"] == "C-001"
    assert datos["estado"] == "disponible"
    assert datos["id"] == 1


def test_no_permite_carros_con_numero_repetido(client):
    client.post("/carros", json={"numero": "C-001"})
    response = client.post("/carros", json={"numero": "C-001"})
    assert response.status_code == 409


def test_rechaza_numero_vacio(client):
    assert client.post("/carros", json={"numero": ""}).status_code == 422
    assert client.post("/carros", json={"numero": "   "}).status_code == 422


def test_rechaza_peticion_sin_numero(client):
    assert client.post("/carros", json={}).status_code == 422


def test_listar_carros(client):
    assert client.get("/carros").json() == []
    client.post("/carros", json={"numero": "C-001"})
    client.post("/carros", json={"numero": "C-002"})
    numeros = [c["numero"] for c in client.get("/carros").json()]
    assert numeros == ["C-001", "C-002"]


def test_obtener_carro_por_id(client):
    creado = client.post("/carros", json={"numero": "C-001"}).json()
    response = client.get(f"/carros/{creado['id']}")
    assert response.status_code == 200
    assert response.json()["numero"] == "C-001"


def test_obtener_carro_inexistente_devuelve_404(client):
    assert client.get("/carros/999").status_code == 404
