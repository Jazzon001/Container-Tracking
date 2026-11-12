import openpyxl
import pytest
from sqlalchemy import select

from app.errores import ArchivoInvalido
from app.models import Carro, EstadoCarro, TipoCarro
from app.services.importacion import importar_carros, leer_carros

CABECERA = ("IT", "Code", "Short descr.", "UoM")


def crear_excel(ruta, filas, hoja="Containers", cabecera=CABECERA):
    libro = openpyxl.Workbook()
    libro.active.title = hoja
    libro.active.append(cabecera)
    for fila in filas:
        libro.active.append(fila)
    libro.save(ruta)
    return ruta


@pytest.fixture
def excel(tmp_path):
    def _crear(filas, **opciones):
        return crear_excel(tmp_path / "carros.xlsx", filas, **opciones)

    return _crear


class TestLeerCarros:
    def test_asigna_el_tipo_segun_el_tipo_de_producto_de_now(self, excel):
        lectura = leer_carros(excel([("C01", "P001A"), ("C02", "D001"), ("C03", "T001")]))

        assert [(c.numero, c.tipo) for c in lectura.carros] == [
            ("P001A", TipoCarro.POY),
            ("D001", TipoCarro.DTY),
            ("T001", TipoCarro.TWISTING),
        ]
        assert lectura.problemas == []

    def test_recorta_espacios_y_acepta_minusculas_en_el_tipo(self, excel):
        lectura = leer_carros(excel([(" c01 ", "  P001A  ")]))
        assert [(c.numero, c.tipo) for c in lectura.carros] == [("P001A", TipoCarro.POY)]

    def test_ubica_las_columnas_por_su_nombre_y_no_por_su_posicion(self, excel):
        # Aquí "Code" va primero y "IT" al final, al revés que en el archivo de NOW.
        lectura = leer_carros(excel([("P001A", "x", "C01")], cabecera=("Code", "Otra", "IT")))

        assert [(c.numero, c.tipo) for c in lectura.carros] == [("P001A", TipoCarro.POY)]
        assert lectura.problemas == []

    def test_ignora_las_filas_en_blanco(self, excel):
        lectura = leer_carros(excel([("C01", "P001A"), (None, None), ("", ""), ("C01", "P002A")]))
        assert [c.numero for c in lectura.carros] == ["P001A", "P002A"]
        assert lectura.problemas == []

    def test_reporta_un_codigo_vacio_con_su_numero_de_fila(self, excel):
        lectura = leer_carros(excel([("C01", "P001A"), ("C01", None)]))
        assert [(p.fila, p.motivo) for p in lectura.problemas] == [(3, "Falta el código")]

    def test_reporta_un_tipo_de_producto_desconocido(self, excel):
        lectura = leer_carros(excel([("C09", "X001")]))
        assert lectura.carros == []
        assert "Tipo de producto desconocido: 'C09'" in lectura.problemas[0].motivo

    def test_reporta_un_codigo_repetido_y_conserva_el_primero(self, excel):
        lectura = leer_carros(excel([("C01", "P001A"), ("C02", "P001A")]))
        assert [(c.numero, c.tipo) for c in lectura.carros] == [("P001A", TipoCarro.POY)]
        assert lectura.problemas[0].fila == 3
        assert "ya aparece en la fila 2" in lectura.problemas[0].motivo

    def test_reporta_un_codigo_demasiado_largo(self, excel):
        lectura = leer_carros(excel([("C01", "X" * 51)]))
        assert lectura.carros == []
        assert "supera 50 caracteres" in lectura.problemas[0].motivo

    def test_un_problema_no_detiene_la_lectura_de_las_demas_filas(self, excel):
        lectura = leer_carros(excel([("C01", None), ("C01", "P002A"), ("C09", "X"), ("C02", "D001")]))
        assert [c.numero for c in lectura.carros] == ["P002A", "D001"]
        assert len(lectura.problemas) == 2

    def test_falla_si_falta_la_hoja_containers(self, excel):
        with pytest.raises(ArchivoInvalido, match="hoja 'Containers'"):
            leer_carros(excel([("C01", "P001A")], hoja="Otra"))

    def test_falla_si_faltan_columnas(self, excel):
        with pytest.raises(ArchivoInvalido, match="Faltan las columnas: IT"):
            leer_carros(excel([("P001A",)], cabecera=("Code",)))

    def test_falla_si_el_archivo_no_existe(self, tmp_path):
        with pytest.raises(ArchivoInvalido, match="No se pudo abrir"):
            leer_carros(tmp_path / "no-existe.xlsx")

    def test_falla_si_el_archivo_no_es_un_excel(self, tmp_path):
        falso = tmp_path / "carros.xlsx"
        falso.write_text("esto no es un excel")
        with pytest.raises(ArchivoInvalido, match="No se pudo abrir"):
            leer_carros(falso)


class TestImportarCarros:
    @pytest.fixture
    def lectura(self, excel):
        return leer_carros(excel([("C01", "P001A"), ("C01", "P002A"), ("C02", "D001"), ("C03", "T001")]))

    def test_sin_guardar_solo_informa_y_no_escribe_nada(self, sesion_de_pruebas, lectura):
        with sesion_de_pruebas() as db:
            resumen = importar_carros(db, lectura, guardar=False)
            assert db.scalars(select(Carro)).all() == []

        assert resumen.guardado is False
        assert resumen.total_nuevos == 4

    def test_guarda_todos_los_carros_como_disponibles_con_su_tipo(self, sesion_de_pruebas, lectura):
        with sesion_de_pruebas() as db:
            importar_carros(db, lectura, guardar=True)
            carros = db.scalars(select(Carro).order_by(Carro.id)).all()

        assert [(c.numero, c.tipo, c.estado) for c in carros] == [
            ("P001A", TipoCarro.POY, EstadoCarro.DISPONIBLE),
            ("P002A", TipoCarro.POY, EstadoCarro.DISPONIBLE),
            ("D001", TipoCarro.DTY, EstadoCarro.DISPONIBLE),
            ("T001", TipoCarro.TWISTING, EstadoCarro.DISPONIBLE),
        ]

    def test_cuenta_los_nuevos_por_tipo(self, sesion_de_pruebas, lectura):
        with sesion_de_pruebas() as db:
            resumen = importar_carros(db, lectura, guardar=True)

        assert resumen.nuevos == {TipoCarro.POY: 2, TipoCarro.DTY: 1, TipoCarro.TWISTING: 1}
        assert resumen.guardado is True

    def test_repetir_la_importacion_no_duplica_carros(self, sesion_de_pruebas, lectura):
        with sesion_de_pruebas() as db:
            importar_carros(db, lectura, guardar=True)
            segunda = importar_carros(db, lectura, guardar=True)
            total = len(db.scalars(select(Carro)).all())

        assert total == 4
        assert segunda.total_nuevos == 0
        assert segunda.existentes == 4

    def test_no_modifica_un_carro_que_ya_existe(self, sesion_de_pruebas, lectura):
        with sesion_de_pruebas() as db:
            importar_carros(db, lectura, guardar=True)
            existente = db.scalars(select(Carro).where(Carro.numero == "P001A")).one()
            existente.estado = EstadoCarro.EN_TRANSITO
            db.commit()

            importar_carros(db, lectura, guardar=True)
            db.refresh(existente)

        assert existente.estado == EstadoCarro.EN_TRANSITO

    def test_importa_solo_los_nuevos_cuando_hay_mezcla(self, sesion_de_pruebas, excel):
        with sesion_de_pruebas() as db:
            importar_carros(db, leer_carros(excel([("C01", "P001A")])), guardar=True)
            resumen = importar_carros(
                db, leer_carros(excel([("C01", "P001A"), ("C01", "P002A")])), guardar=True
            )

        assert resumen.total_nuevos == 1
        assert resumen.existentes == 1

    def test_el_resumen_incluye_los_problemas_de_la_lectura(self, sesion_de_pruebas, excel):
        lectura = leer_carros(excel([("C01", "P001A"), ("C09", "X")]))
        with sesion_de_pruebas() as db:
            resumen = importar_carros(db, lectura, guardar=False)

        assert len(resumen.problemas) == 1
