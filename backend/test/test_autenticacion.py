import pytest

from app.models import Rol

RUTAS_PROTEGIDAS = [
    ("get", "/carros"),
    ("post", "/carros"),
    ("get", "/carros/1"),
    ("post", "/carros/1/carga"),
    ("post", "/carros/1/entrega"),
    ("post", "/carros/1/mantenimiento"),
    ("post", "/carros/1/mantenimiento/salida"),
    ("get", "/carros/1/mantenimiento"),
    ("post", "/usuarios"),
]


@pytest.fixture
def con_usuario(client):
    """Crea un usuario real (con contraseña) usando el endpoint de administración."""
    client.post(
        "/usuarios", json={"username": "maria", "password": "clave-segura-123", "rol": "poy"}
    )


def login(cliente, username, password):
    return cliente.post("/auth/login", json={"username": username, "password": password})


def test_login_correcto_devuelve_un_token(cliente_anonimo, con_usuario):
    response = login(cliente_anonimo, "maria", "clave-segura-123")
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_el_token_del_login_permite_consultar_carros(cliente_anonimo, con_usuario):
    token = login(cliente_anonimo, "maria", "clave-segura-123").json()["access_token"]
    response = cliente_anonimo.get("/carros", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_login_con_contrasena_incorrecta_devuelve_401(cliente_anonimo, con_usuario):
    assert login(cliente_anonimo, "maria", "contrasena-equivocada").status_code == 401


def test_login_con_usuario_inexistente_devuelve_401(cliente_anonimo):
    assert login(cliente_anonimo, "nadie", "clave-segura-123").status_code == 401


def test_el_mensaje_de_login_no_revela_si_el_usuario_existe(cliente_anonimo, con_usuario):
    sin_usuario = login(cliente_anonimo, "nadie", "clave-segura-123").json()
    mala_clave = login(cliente_anonimo, "maria", "contrasena-equivocada").json()
    assert sin_usuario == mala_clave


@pytest.mark.parametrize("metodo, ruta", RUTAS_PROTEGIDAS)
def test_las_rutas_protegidas_exigen_sesion(cliente_anonimo, metodo, ruta):
    assert getattr(cliente_anonimo, metodo)(ruta).status_code == 401


def test_un_token_invalido_devuelve_401(cliente_anonimo):
    response = cliente_anonimo.get("/carros", headers={"Authorization": "Bearer basura"})
    assert response.status_code == 401


def test_un_token_de_un_usuario_inexistente_devuelve_401(cliente_anonimo):
    from app.seguridad import crear_token

    token = crear_token("fantasma")
    response = cliente_anonimo.get("/carros", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_health_no_requiere_sesion(cliente_anonimo):
    assert cliente_anonimo.get("/health").status_code == 200


def test_todos_los_roles_pueden_consultar_carros(cliente_como):
    for rol in Rol:
        assert cliente_como(rol).get("/carros").status_code == 200
