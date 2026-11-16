"""Quién puede hacer qué. Esta tabla es la especificación de los perfiles, escrita a mano.

Para cada perfil: de qué proceso son sus carros y si puede cargar, liberar y registrar
mantenimiento. El administrador puede todo. Las pruebas usan un carro del proceso del perfil,
para comprobar el permiso y no el alcance (el alcance se prueba en test_alcance_por_proceso.py).
"""
import pytest

from app.models import Rol

#            proceso    cargar  liberar  mantener
PERFILES = {
    Rol.ADMIN: ("poy", True, True, True),
    Rol.DIGITADOR_POY: ("poy", True, True, True),
    Rol.INTERMEDIO_POY: ("poy", False, True, True),
    Rol.EMPACADOR_POY: ("poy", False, True, True),
    Rol.DIGITADOR_DTY: ("dty", True, True, True),
    Rol.EMPACADOR_DTY: ("dty", False, True, True),
    Rol.TWISTING: ("dty", False, True, True),
    Rol.DIGITADOR_TWT: ("twisting", True, True, True),
    Rol.EMPACADOR_TWT: ("twisting", False, True, True),
    # Nombres anteriores: se conservan para no romper a los usuarios ya creados.
    Rol.POY: ("poy", True, True, True),
    Rol.DTY: ("dty", True, True, True),
    Rol.ALMACEN: ("poy", False, True, False),
}

# Cada operación y la columna de PERFILES que dice si el perfil puede hacerla.
OPERACIONES = {
    "cargar": (
        lambda c, id: c.post(f"/carros/{id}/carga", json={"contenedor_elemento": "100123"}),
        1,
    ),
    "liberar": (lambda c, id: c.post(f"/carros/{id}/entrega"), 2),
    "iniciar_mantenimiento": (lambda c, id: c.post(f"/carros/{id}/mantenimiento"), 3),
    "finalizar_mantenimiento": (lambda c, id: c.post(f"/carros/{id}/mantenimiento/salida"), 3),
}


def test_todos_los_perfiles_estan_especificados():
    assert set(PERFILES) == set(Rol)


@pytest.mark.parametrize("rol", list(PERFILES))
@pytest.mark.parametrize("operacion", list(OPERACIONES))
def test_cada_perfil_solo_hace_lo_que_le_corresponde(operacion, rol, cliente_como, crear_carro):
    tipo = PERFILES[rol][0]
    carro = crear_carro("C-001", tipo)
    accion, columna = OPERACIONES[operacion]
    puede = PERFILES[rol][columna]

    respuesta = accion(cliente_como(rol), carro["id"])

    # Si tiene permiso, la operación puede fallar por otras razones (por ejemplo 409),
    # pero nunca por falta de permiso.
    assert (respuesta.status_code != 403) == puede


@pytest.mark.parametrize("rol", [rol for rol in Rol if rol != Rol.ADMIN])
def test_solo_el_administrador_crea_carros_y_usuarios(rol, cliente_como):
    cliente = cliente_como(rol)
    assert cliente.post("/carros", json={"numero": "C-999", "tipo": "poy"}).status_code == 403
    usuario = {"username": "nuevo", "password": "clave-segura-123", "rol": "poy"}
    assert cliente.post("/usuarios", json=usuario).status_code == 403


@pytest.mark.parametrize("rol", list(Rol))
def test_todos_los_perfiles_pueden_consultar(rol, cliente_como):
    cliente = cliente_como(rol)
    assert cliente.get("/carros").status_code == 200
    assert cliente.get("/cargas").status_code == 200
