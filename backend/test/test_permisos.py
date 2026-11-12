"""Quién puede hacer qué. El administrador puede todo, por eso no se lista aparte."""
import pytest

from app.models import Rol

OPERACIONES = {
    "crear_carro": (
        lambda c, id: c.post("/carros", json={"numero": "C-999", "tipo": "poy"}),
        {Rol.ADMIN},
    ),
    "cargar": (
        lambda c, id: c.post(f"/carros/{id}/carga", json={"contenedor_elemento": "100123"}),
        {Rol.POY},
    ),
    "entregar": (
        lambda c, id: c.post(f"/carros/{id}/entrega"),
        {Rol.ALMACEN},
    ),
    "iniciar_mantenimiento": (
        lambda c, id: c.post(f"/carros/{id}/mantenimiento"),
        {Rol.POY, Rol.DTY},
    ),
    "finalizar_mantenimiento": (
        lambda c, id: c.post(f"/carros/{id}/mantenimiento/salida"),
        {Rol.POY, Rol.DTY},
    ),
}


@pytest.mark.parametrize("rol", list(Rol))
@pytest.mark.parametrize("operacion", list(OPERACIONES))
def test_solo_los_roles_permitidos_pueden_operar(operacion, rol, cliente_como, crear_carro):
    carro = crear_carro("C-001")
    accion, permitidos = OPERACIONES[operacion]
    puede = rol in permitidos or rol == Rol.ADMIN

    respuesta = accion(cliente_como(rol), carro["id"])

    # Si tiene permiso, la operación puede fallar por otras razones (por ejemplo 409),
    # pero nunca por falta de permiso.
    assert (respuesta.status_code != 403) == puede
