import pytest


@pytest.mark.parametrize("tipo", ["poy", "dty", "twisting"])
def test_un_carro_se_crea_con_su_tipo(client, tipo):
    carro = client.post("/carros", json={"numero": "X-001", "tipo": tipo}).json()
    assert carro["tipo"] == tipo


def test_el_tipo_es_obligatorio(client):
    assert client.post("/carros", json={"numero": "C-001"}).status_code == 422


def test_rechaza_un_tipo_desconocido(client):
    assert client.post("/carros", json={"numero": "C-001", "tipo": "empaque"}).status_code == 422


def test_el_listado_incluye_el_tipo(client, crear_carro):
    crear_carro("C-001", "dty")
    assert client.get("/carros").json()[0]["tipo"] == "dty"


def test_filtra_carros_por_tipo(client, crear_carro):
    crear_carro("P-1", "poy")
    crear_carro("D-1", "dty")
    crear_carro("D-2", "dty")
    crear_carro("T-1", "twisting")

    numeros = lambda tipo: [c["numero"] for c in client.get(f"/carros?tipo={tipo}").json()]
    assert numeros("poy") == ["P-1"]
    assert numeros("dty") == ["D-1", "D-2"]
    assert numeros("twisting") == ["T-1"]


def test_el_tipo_se_combina_con_el_estado(client, crear_carro, cargar):
    carro = crear_carro("P-1", "poy")
    crear_carro("P-2", "poy")
    crear_carro("D-1", "dty")
    cargar(carro["id"])

    disponibles_poy = client.get("/carros?tipo=poy&estado=disponible").json()
    assert [c["numero"] for c in disponibles_poy] == ["P-2"]


def test_tipo_desconocido_en_el_filtro_devuelve_422(client):
    assert client.get("/carros?tipo=empaque").status_code == 422
