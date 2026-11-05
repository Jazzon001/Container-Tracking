from scripts.exportar_modelo import describir_modelo


def tabla(nombre):
    return next(t for t in describir_modelo()["tablas"] if t["nombre"] == nombre)


def test_el_modelo_incluye_las_tablas_del_dominio():
    nombres = {t["nombre"] for t in describir_modelo()["tablas"]}
    assert {"carros", "mantenimientos"} <= nombres


def test_mantenimientos_referencia_a_carros():
    columna = next(c for c in tabla("mantenimientos")["columnas"] if c["nombre"] == "carro_id")
    assert columna["clave_foranea"] == ["carros.id"]


def test_numero_y_contenedor_elemento_son_unicos():
    unicos = {c["nombre"] for c in tabla("carros")["columnas"] if c["unico"]}
    assert {"numero", "contenedor_elemento"} <= unicos
