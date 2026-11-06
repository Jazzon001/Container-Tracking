def datos(**cambios):
    base = {"username": "maria", "password": "clave-segura-123", "rol": "poy"}
    return {**base, **cambios}


def test_el_administrador_crea_un_usuario(client):
    response = client.post("/usuarios", json=datos())
    assert response.status_code == 201
    assert response.json()["username"] == "maria"
    assert response.json()["rol"] == "poy"


def test_la_respuesta_no_expone_la_contrasena_ni_su_hash(client):
    respuesta = client.post("/usuarios", json=datos()).json()
    assert set(respuesta) == {"id", "username", "rol"}


def test_no_se_permiten_usuarios_repetidos(client):
    client.post("/usuarios", json=datos())
    assert client.post("/usuarios", json=datos()).status_code == 409


def test_rechaza_un_rol_desconocido(client):
    assert client.post("/usuarios", json=datos(rol="jefe")).status_code == 422


def test_rechaza_una_contrasena_corta(client):
    assert client.post("/usuarios", json=datos(password="corta")).status_code == 422


def test_rechaza_un_nombre_de_usuario_vacio(client):
    assert client.post("/usuarios", json=datos(username="   ")).status_code == 422


def test_un_usuario_que_no_es_administrador_no_puede_crear_usuarios(cliente_como):
    from app.models import Rol

    assert cliente_como(Rol.POY).post("/usuarios", json=datos()).status_code == 403
