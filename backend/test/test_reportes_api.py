"""POST /reportes/carros: el Excel de NOW cruzado con las cargas del sistema. Solo el administrador."""
from io import BytesIO

import pytest
from excel_de_now import FILAS_BASICAS, excel, fila
from openpyxl import load_workbook

from app.models import Rol
from app.routers import reportes

URL = "/reportes/carros"
URL_EXCEL = "/reportes/carros/excel"
BINARIO = {"Content-Type": "application/octet-stream"}


def subir(cliente, contenido=None, url=URL):
    return cliente.post(url, content=excel(FILAS_BASICAS) if contenido is None else contenido, headers=BINARIO)


class TestPermisos:
    @pytest.mark.parametrize("url", [URL, URL_EXCEL])
    def test_sin_sesion_responde_401(self, cliente_anonimo, url):
        assert subir(cliente_anonimo, url=url).status_code == 401

    @pytest.mark.parametrize("url", [URL, URL_EXCEL])
    @pytest.mark.parametrize("rol", [rol for rol in Rol if rol != Rol.ADMIN])
    def test_solo_el_administrador_puede(self, cliente_como, rol, url):
        assert subir(cliente_como(rol), url=url).status_code == 403

    def test_el_permiso_se_comprueba_antes_de_leer_el_archivo(self, cliente_como):
        # Un perfil sin permiso no puede ni obligar al servidor a revisar un archivo.
        respuesta = subir(cliente_como(Rol.DIGITADOR_POY), contenido=b"esto no es un excel")
        assert respuesta.status_code == 403


class TestReporte:
    def test_devuelve_el_resumen_las_tablas_y_los_carros(self, client):
        respuesta = subir(client)
        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert set(cuerpo) == {"corte", "resumen", "tablas", "carros"}
        assert cuerpo["corte"] == "01/11/2026 12:30"  # el último movimiento del archivo
        indicadores = {i["indicador"]: i["valor"] for i in cuerpo["resumen"]}
        assert indicadores["Viajes (contenedores elemento)"] == 2
        assert indicadores["Movimientos de producto en tarima (sin carro)"] == 1

    def test_los_carros_traen_sus_lados_juntos(self, client):
        carros = subir(client).json()["carros"]
        assert [(c["carro_fisico"], c["lado"], c["carro"]) for c in carros] == [("P1", "A", "P1A"), ("P2", "B", "P2B")]
        assert carros[0]["situacion"] == "En DTY (salió de WIPB4)"
        assert carros[1]["situacion"].startswith("En RCV01")

    def test_sin_cargas_en_el_sistema_dice_que_no_hay_registro(self, client):
        carros = subir(client).json()["carros"]
        assert {c["situacion_sistema"] for c in carros} == {"Sin registro en este sistema"}

    def test_cruza_con_las_cargas_del_sistema(self, client, crear_carro, cargar):
        carro = crear_carro("P1A")
        assert cargar(carro["id"], "A1").status_code == 200  # el digitador escaneó el contenedor A1

        carros = {c["carro"]: c for c in subir(client).json()["carros"]}
        assert carros["P1A"]["situacion_sistema"] == "Cargado en el sistema, sin liberar"
        assert carros["P1A"]["dty_abierto"] is True
        assert carros["P2B"]["situacion_sistema"] == "Sin registro en este sistema"

    def test_un_carro_liberado_en_el_sistema_ya_no_esta_abierto(self, client, crear_carro, cargar, monkeypatch):
        monkeypatch.setenv("NOW_UTC_OFFSET_HORAS", "0")  # las fechas de NOW de este Excel son de 2026-11-01
        carro = crear_carro("P1A")
        cargar(carro["id"], "A1")
        client.post(f"/carros/{carro['id']}/entrega")

        fila = next(c for c in subir(client).json()["carros"] if c["carro"] == "P1A")
        assert fila["situacion_sistema"] == "Liberado en el sistema"

    def test_un_carro_con_un_viaje_viejo_registrado_no_aparece_sin_registro(self, client, crear_carro, cargar):
        # P1A hace dos viajes en NOW (A1 y A2); solo A1 se cargó en el sistema.
        filas = FILAS_BASICAS + [fila(2, 6, "RCV01", "P1A", "A2", plantilla="016"), fila(2, 8, "RCV01", "P1A", "A2")]
        carro = crear_carro("P1A")
        cargar(carro["id"], "A1")

        carros = {c["carro"]: c for c in subir(client, contenido=excel(filas)).json()["carros"]}
        assert carros["P1A"]["situacion_sistema"] == "Cargado en el sistema, sin liberar"
        assert carros["P1A"]["viajes_en_sistema"] == 1 and carros["P1A"]["viajes"] == 2

    def test_no_guarda_el_archivo_ni_cambia_los_carros(self, client, crear_carro):
        crear_carro("P1A")
        antes = client.get("/carros").json()
        subir(client)
        assert client.get("/carros").json() == antes


class TestExcel:
    def test_descarga_un_excel_con_tres_hojas(self, client):
        respuesta = subir(client, url=URL_EXCEL)
        assert respuesta.status_code == 200
        assert respuesta.headers["content-type"] == reportes.TIPO_XLSX
        assert "reporte_carros.xlsx" in respuesta.headers["content-disposition"]
        assert load_workbook(BytesIO(respuesta.content)).sheetnames == ["Resumen", "Por carro", "Viajes"]


class TestArchivosInvalidos:
    @pytest.mark.parametrize("url", [URL, URL_EXCEL])
    def test_un_archivo_que_no_es_excel_responde_422(self, client, url):
        respuesta = subir(client, contenido=b"esto no es un excel", url=url)
        assert respuesta.status_code == 422
        assert "no es un Excel" in respuesta.json()["detail"]

    def test_un_cuerpo_vacio_responde_422(self, client):
        assert subir(client, contenido=b"").status_code == 422

    def test_un_excel_con_otras_columnas_dice_cuales_faltan(self, client):
        respuesta = subir(client, contenido=excel([], cabecera=["otra", "cosa"]))
        assert respuesta.status_code == 422
        assert "Faltan estas columnas" in respuesta.json()["detail"]

    def test_un_archivo_mas_grande_que_el_limite_responde_413(self, client, monkeypatch):
        monkeypatch.setattr(reportes, "LIMITE_MB", 0)
        respuesta = subir(client)
        assert respuesta.status_code == 413
        assert "0 MB" in respuesta.json()["detail"]

    def test_el_limite_tambien_corta_si_no_se_declara_el_tamano(self, client, monkeypatch):
        monkeypatch.setattr(reportes, "LIMITE_MB", 0)

        def en_partes():
            yield b"abc"
            yield b"def"

        assert client.post(URL, content=en_partes(), headers=BINARIO).status_code == 413


class TestDesplazamiento:
    def test_por_omision_es_menos_seis(self, monkeypatch):
        monkeypatch.delenv("NOW_UTC_OFFSET_HORAS", raising=False)
        assert reportes.desplazamiento_de_now() == -6

    def test_se_puede_cambiar_con_una_variable_de_entorno(self, monkeypatch):
        monkeypatch.setenv("NOW_UTC_OFFSET_HORAS", "-5")
        assert reportes.desplazamiento_de_now() == -5

    def test_un_valor_que_no_es_numero_se_ignora(self, monkeypatch):
        monkeypatch.setenv("NOW_UTC_OFFSET_HORAS", "seis")
        assert reportes.desplazamiento_de_now() == -6
