def numeros(response):
    return [carro["numero"] for carro in response.json()]


def test_sin_filtro_lista_todos_los_carros(client, crear_carro, cargar):
    crear_carro("C-001")
    cargado = crear_carro("C-002")
    cargar(cargado["id"])
    assert numeros(client.get("/carros")) == ["C-001", "C-002"]


def test_filtra_carros_disponibles(client, crear_carro, cargar):
    crear_carro("C-001")
    cargado = crear_carro("C-002")
    cargar(cargado["id"])
    assert numeros(client.get("/carros?estado=disponible")) == ["C-001"]


def test_filtra_carros_en_transito(client, crear_carro, cargar):
    crear_carro("C-001")
    cargado = crear_carro("C-002")
    cargar(cargado["id"])
    assert numeros(client.get("/carros?estado=en_transito")) == ["C-002"]


def test_estado_desconocido_devuelve_422(client):
    assert client.get("/carros?estado=perdido").status_code == 422
