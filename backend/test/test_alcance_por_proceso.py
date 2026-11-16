"""Un perfil solo ve y toca los carros de su proceso: POY con POY, DTY con DTY, y así."""
import pytest

from app.models import Rol

PROCESOS = {
    Rol.DIGITADOR_POY: "poy",
    Rol.INTERMEDIO_POY: "poy",
    Rol.EMPACADOR_POY: "poy",
    Rol.DIGITADOR_DTY: "dty",
    Rol.EMPACADOR_DTY: "dty",
    Rol.TWISTING: "dty",
    Rol.DIGITADOR_TWT: "twisting",
    Rol.EMPACADOR_TWT: "twisting",
}


@pytest.fixture
def tres_carros(crear_carro):
    return {
        "poy": crear_carro("P-001", "poy"),
        "dty": crear_carro("D-001", "dty"),
        "twisting": crear_carro("T-001", "twisting"),
    }


def ajeno_a(rol, tres_carros):
    return next(c for tipo, c in tres_carros.items() if tipo != PROCESOS[rol])


@pytest.mark.parametrize("rol", list(PROCESOS))
def test_la_lista_solo_trae_los_carros_del_proceso(rol, cliente_como, tres_carros):
    numeros = [c["numero"] for c in cliente_como(rol).get("/carros").json()]
    assert numeros == [tres_carros[PROCESOS[rol]]["numero"]]


@pytest.mark.parametrize("rol", list(PROCESOS))
def test_pedir_carros_de_otro_proceso_no_trae_ninguno(rol, cliente_como, tres_carros):
    otro = ajeno_a(rol, tres_carros)["tipo"]
    assert cliente_como(rol).get("/carros", params={"tipo": otro}).json() == []


def test_pedir_el_propio_proceso_funciona(cliente_como, tres_carros):
    respuesta = cliente_como(Rol.DIGITADOR_DTY).get("/carros", params={"tipo": "dty"})
    assert [c["numero"] for c in respuesta.json()] == ["D-001"]


@pytest.mark.parametrize("rol", list(PROCESOS))
def test_el_carro_de_otro_proceso_se_trata_como_inexistente(rol, cliente_como, tres_carros):
    cliente = cliente_como(rol)
    id_ = ajeno_a(rol, tres_carros)["id"]

    assert cliente.get(f"/carros/{id_}").status_code == 404
    assert cliente.get(f"/carros/{id_}/mantenimiento").status_code == 404
    assert cliente.post(f"/carros/{id_}/entrega").status_code == 404
    assert cliente.post(f"/carros/{id_}/mantenimiento").status_code == 404
    assert cliente.post(f"/carros/{id_}/mantenimiento/salida").status_code == 404


@pytest.mark.parametrize("rol", [Rol.DIGITADOR_POY, Rol.DIGITADOR_DTY, Rol.DIGITADOR_TWT])
def test_el_digitador_no_puede_cargar_carros_de_otro_proceso(rol, cliente_como, tres_carros):
    ajeno = ajeno_a(rol, tres_carros)
    respuesta = cliente_como(rol).post(
        f"/carros/{ajeno['id']}/carga", json={"contenedor_elemento": "100123"}
    )
    assert respuesta.status_code == 404
    # Y el carro ajeno sigue intacto.
    assert cliente_como(Rol.ADMIN).get(f"/carros/{ajeno['id']}").json()["estado"] == "disponible"


def test_el_carro_propio_se_puede_consultar(cliente_como, tres_carros):
    respuesta = cliente_como(Rol.INTERMEDIO_POY).get(f"/carros/{tres_carros['poy']['id']}")
    assert respuesta.status_code == 200


def test_el_historial_solo_trae_las_cargas_del_proceso(cliente_como, tres_carros):
    admin = cliente_como(Rol.ADMIN)
    for tipo, codigo in (("poy", "111"), ("dty", "222"), ("twisting", "333")):
        admin.post(f"/carros/{tres_carros[tipo]['id']}/carga", json={"contenedor_elemento": codigo})

    for rol, codigo in ((Rol.EMPACADOR_POY, "111"), (Rol.TWISTING, "222"), (Rol.EMPACADOR_TWT, "333")):
        cargas = cliente_como(rol).get("/cargas").json()
        assert [c["contenedor_elemento"] for c in cargas] == [codigo]
    assert len(admin.get("/cargas").json()) == 3


def test_el_administrador_y_almacen_ven_todos_los_carros(cliente_como, tres_carros):
    assert len(cliente_como(Rol.ADMIN).get("/carros").json()) == 3
    assert len(cliente_como(Rol.ALMACEN).get("/carros").json()) == 3


def test_el_digitador_carga_y_el_intermedio_libera_el_mismo_carro(cliente_como, tres_carros):
    carro_id = tres_carros["poy"]["id"]
    carga = cliente_como(Rol.DIGITADOR_POY).post(
        f"/carros/{carro_id}/carga", json={"contenedor_elemento": "100123"}
    )
    assert carga.status_code == 200 and carga.json()["estado"] == "en_transito"

    libera = cliente_como(Rol.INTERMEDIO_POY).post(f"/carros/{carro_id}/entrega")
    assert libera.status_code == 200 and libera.json()["estado"] == "disponible"


def test_twisting_libera_los_carros_de_dty(cliente_como, tres_carros):
    carro_id = tres_carros["dty"]["id"]
    cliente_como(Rol.DIGITADOR_DTY).post(
        f"/carros/{carro_id}/carga", json={"contenedor_elemento": "100123"}
    )

    respuesta = cliente_como(Rol.TWISTING).post(f"/carros/{carro_id}/entrega")
    assert respuesta.status_code == 200 and respuesta.json()["estado"] == "disponible"
