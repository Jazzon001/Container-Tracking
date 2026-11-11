def test_busca_un_carro_por_su_numero(client, crear_carro):
    crear_carro("C-001")
    crear_carro("C-002")
    resultado = client.get("/carros?numero=C-002").json()
    assert [carro["numero"] for carro in resultado] == ["C-002"]


def test_un_numero_inexistente_devuelve_lista_vacia(client, crear_carro):
    crear_carro("C-001")
    assert client.get("/carros?numero=C-999").json() == []


def test_la_busqueda_es_exacta(client, crear_carro):
    crear_carro("C-001")
    crear_carro("C-0011")
    resultado = client.get("/carros?numero=C-001").json()
    assert [carro["numero"] for carro in resultado] == ["C-001"]


def test_el_numero_se_combina_con_el_estado(client, crear_carro, cargar):
    carro = crear_carro("C-001")
    cargar(carro["id"])
    assert len(client.get("/carros?numero=C-001&estado=en_transito").json()) == 1
    assert client.get("/carros?numero=C-001&estado=disponible").json() == []
