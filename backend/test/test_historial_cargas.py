import time
from datetime import datetime

import pytest

from app.models import Carro, EstadoCarro, Rol, TipoCarro


def entregar(client, carro_id):
    return client.post(f"/carros/{carro_id}/entrega")


def historial(client, consulta=""):
    return client.get(f"/cargas{consulta}").json()


def instante(texto: str) -> datetime:
    return datetime.fromisoformat(texto.replace("Z", "+00:00"))


class TestRegistroDelHistorial:
    def test_empieza_vacio(self, client):
        assert historial(client) == []

    def test_cargar_un_carro_abre_un_registro(self, client, crear_carro, cargar):
        carro = crear_carro("C-001")
        cargar(carro["id"], "100123")

        [registro] = historial(client)
        assert registro["carro_id"] == carro["id"]
        assert registro["carro_numero"] == "C-001"
        assert registro["contenedor_elemento"] == "100123"
        assert registro["recibida_en"] is None

    def test_recibir_el_carro_cierra_su_registro(self, client, crear_carro, cargar):
        carro = crear_carro("C-001")
        cargar(carro["id"], "100123")
        entregar(client, carro["id"])

        [registro] = historial(client)
        assert registro["recibida_en"] is not None
        assert instante(registro["recibida_en"]) >= instante(registro["cargada_en"])

    def test_el_historial_conserva_el_contenedor_aunque_el_carro_lo_libere(self, client, crear_carro, cargar):
        carro = crear_carro("C-001")
        cargar(carro["id"], "100123")
        entregar(client, carro["id"])

        assert client.get(f"/carros/{carro['id']}").json()["contenedor_elemento"] is None
        assert historial(client)[0]["contenedor_elemento"] == "100123"

    def test_los_instantes_del_historial_coinciden_con_los_del_carro(self, client, crear_carro, cargar):
        carro = crear_carro("C-001")
        cargar(carro["id"], "100123")
        assert historial(client)[0]["cargada_en"] == client.get(f"/carros/{carro['id']}").json()["estado_desde"]

        entregar(client, carro["id"])
        assert historial(client)[0]["recibida_en"] == client.get(f"/carros/{carro['id']}").json()["estado_desde"]

    def test_las_fechas_se_entregan_en_utc(self, client, crear_carro, cargar):
        carro = crear_carro("C-001")
        cargar(carro["id"], "100123")
        entregar(client, carro["id"])

        registro = historial(client)[0]
        assert instante(registro["cargada_en"]).utcoffset().total_seconds() == 0
        assert instante(registro["recibida_en"]).utcoffset().total_seconds() == 0

    def test_cada_viaje_es_un_registro_aunque_se_reutilice_el_contenedor(self, client, crear_carro, cargar):
        carro = crear_carro("C-001")
        for _ in range(3):
            cargar(carro["id"], "100123")
            entregar(client, carro["id"])

        registros = historial(client)
        assert len(registros) == 3
        assert all(r["recibida_en"] is not None for r in registros)

    def test_un_carro_recibido_no_deja_registros_abiertos(self, client, crear_carro, cargar):
        carro = crear_carro("C-001")
        cargar(carro["id"], "100123")
        entregar(client, carro["id"])
        cargar(carro["id"], "100456")

        abiertos = [r for r in historial(client) if r["recibida_en"] is None]
        assert [r["contenedor_elemento"] for r in abiertos] == ["100456"]


class TestOperacionesRechazadas:
    def test_una_carga_rechazada_por_estado_no_deja_registro(self, client, crear_carro, cargar):
        carro = crear_carro("C-001")
        cargar(carro["id"], "100123")
        assert cargar(carro["id"], "100456").status_code == 409

        assert [r["contenedor_elemento"] for r in historial(client)] == ["100123"]

    def test_una_carga_con_un_contenedor_en_uso_no_deja_registro(self, client, crear_carro, cargar):
        primero = crear_carro("C-001")
        segundo = crear_carro("C-002")
        cargar(primero["id"], "100123")
        assert cargar(segundo["id"], "100123").status_code == 409

        assert [r["carro_numero"] for r in historial(client)] == ["C-001"]

    def test_recibir_un_carro_que_no_esta_en_transito_no_cambia_el_historial(self, client, crear_carro, cargar):
        carro = crear_carro("C-001")
        cargar(carro["id"], "100123")
        entregar(client, carro["id"])
        antes = historial(client)

        assert entregar(client, carro["id"]).status_code == 409
        assert historial(client) == antes

    def test_un_carro_en_transito_desde_antes_del_historial_se_puede_recibir(self, client, sesion_de_pruebas):
        """Datos anteriores al historial: está en tránsito pero no tiene registro abierto."""
        with sesion_de_pruebas() as db:
            db.add(
                Carro(
                    numero="VIEJO-1",
                    tipo=TipoCarro.POY,
                    estado=EstadoCarro.EN_TRANSITO,
                    contenedor_elemento="555",
                )
            )
            db.commit()
        carro = client.get("/carros?numero=VIEJO-1").json()[0]

        assert entregar(client, carro["id"]).status_code == 200
        assert historial(client) == []


class TestConsulta:
    @pytest.fixture
    def tres_viajes(self, client, crear_carro, cargar):
        uno = crear_carro("C-001")
        dos = crear_carro("C-002")
        cargar(uno["id"], "100111")
        time.sleep(0.02)
        cargar(dos["id"], "100222")
        time.sleep(0.02)
        entregar(client, uno["id"])
        cargar(uno["id"], "100333")

    def test_muestra_primero_las_cargas_mas_recientes(self, client, tres_viajes):
        assert [r["contenedor_elemento"] for r in historial(client)] == ["100333", "100222", "100111"]

    def test_filtra_por_contenedor_elemento(self, client, tres_viajes):
        assert [r["carro_numero"] for r in historial(client, "?contenedor_elemento=100222")] == ["C-002"]

    def test_filtra_por_numero_de_carro(self, client, tres_viajes):
        registros = historial(client, "?numero=C-001")
        assert [r["contenedor_elemento"] for r in registros] == ["100333", "100111"]

    def test_combina_los_filtros(self, client, tres_viajes):
        assert len(historial(client, "?numero=C-001&contenedor_elemento=100111")) == 1
        assert historial(client, "?numero=C-002&contenedor_elemento=100111") == []

    def test_la_busqueda_es_exacta(self, client, tres_viajes):
        assert historial(client, "?contenedor_elemento=1001") == []
        assert historial(client, "?numero=C-00") == []

    def test_el_limite_recorta_la_lista(self, client, tres_viajes):
        assert len(historial(client, "?limite=2")) == 2

    @pytest.mark.parametrize("limite", [0, -1, 1001])
    def test_rechaza_limites_fuera_de_rango(self, client, limite):
        assert client.get(f"/cargas?limite={limite}").status_code == 422


class TestPermisos:
    def test_exige_iniciar_sesion(self, cliente_anonimo):
        assert cliente_anonimo.get("/cargas").status_code == 401

    @pytest.mark.parametrize("rol", list(Rol))
    def test_cualquier_rol_puede_consultar_el_historial(self, cliente_como, rol):
        assert cliente_como(rol).get("/cargas").status_code == 200
