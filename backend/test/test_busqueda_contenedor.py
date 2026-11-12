def test_busca_el_carro_que_lleva_un_contenedor_elemento(client, crear_carro, cargar):
    primero = crear_carro("C-001")
    segundo = crear_carro("C-002")
    cargar(primero["id"], "100123")
    cargar(segundo["id"], "100456")

    resultado = client.get("/carros?contenedor_elemento=100456").json()

    assert [carro["numero"] for carro in resultado] == ["C-002"]


def test_un_contenedor_que_no_esta_en_ningun_carro_devuelve_lista_vacia(client, crear_carro, cargar):
    carro = crear_carro("C-001")
    cargar(carro["id"], "100123")
    assert client.get("/carros?contenedor_elemento=999999").json() == []


def test_la_busqueda_por_contenedor_es_exacta(client, crear_carro, cargar):
    carro = crear_carro("C-001")
    cargar(carro["id"], "100123")
    assert client.get("/carros?contenedor_elemento=1001").json() == []


def test_tras_recibir_el_carro_ya_no_se_encuentra_por_ese_contenedor(client, crear_carro, cargar):
    carro = crear_carro("C-001")
    cargar(carro["id"], "100123")
    client.post(f"/carros/{carro['id']}/entrega")

    assert client.get("/carros?contenedor_elemento=100123").json() == []


def test_un_carro_vacio_no_aparece_al_buscar_por_contenedor(client, crear_carro):
    crear_carro("C-001")  # disponible: no lleva ningún contenedor
    assert client.get("/carros?contenedor_elemento=100123").json() == []
