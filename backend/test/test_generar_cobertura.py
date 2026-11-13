from scripts.generar_cobertura import normalizar_registros, resumen_istanbul, sumar, unir

BACKEND = """SF:app\\main.py
DA:1,1
DA:2,0
LF:2
LH:1
end_of_record
"""

FRONTEND = """TN:
SF:src\\app\\auth.service.ts
FN:6,mensajeDeApi
FNF:1
FNH:1
DA:6,1
DA:7,1
DA:8,1
DA:9,1
LF:4
LH:4
BRF:2
BRH:1
end_of_record
"""


class TestNormalizar:
    def test_antepone_la_carpeta_a_cada_archivo(self):
        assert "SF:backend/app/main.py" in normalizar_registros(BACKEND, "backend")

    def test_convierte_las_barras_de_windows(self):
        resultado = normalizar_registros(FRONTEND, "frontend")
        assert "SF:frontend/src/app/auth.service.ts" in resultado
        assert "\\" not in resultado

    def test_no_toca_las_demas_lineas(self):
        assert "DA:2,0" in normalizar_registros(BACKEND, "backend")


class TestSumar:
    def test_suma_lineas_funciones_y_ramas(self):
        totales = sumar(BACKEND + FRONTEND)
        assert totales == {"LF": 6, "LH": 5, "FNF": 1, "FNH": 1, "BRF": 2, "BRH": 1}

    def test_un_reporte_vacio_suma_cero(self):
        assert sumar("") == {"LF": 0, "LH": 0, "FNF": 0, "FNH": 0, "BRF": 0, "BRH": 0}


class TestResumenIstanbul:
    def test_tiene_el_formato_de_istanbul(self):
        resumen = resumen_istanbul(BACKEND + FRONTEND)
        assert set(resumen) == {"total"}
        assert set(resumen["total"]) == {"lines", "statements", "functions", "branches"}
        assert set(resumen["total"]["lines"]) == {"total", "covered", "skipped", "pct"}

    def test_calcula_el_porcentaje_de_lineas(self):
        lineas = resumen_istanbul(BACKEND + FRONTEND)["total"]["lines"]
        assert lineas["total"] == 6
        assert lineas["covered"] == 5
        assert lineas["pct"] == 83.33

    def test_sin_funciones_ni_ramas_el_porcentaje_es_100(self):
        resumen = resumen_istanbul(BACKEND)["total"]
        assert resumen["functions"]["pct"] == 100
        assert resumen["branches"]["pct"] == 100


class TestUnir:
    def test_junta_los_dos_reportes_con_sus_carpetas(self):
        unido = unir(BACKEND, FRONTEND)
        assert "SF:backend/app/main.py" in unido
        assert "SF:frontend/src/app/auth.service.ts" in unido

    def test_la_cobertura_del_conjunto_sale_de_todas_las_lineas(self):
        assert resumen_istanbul(unir(BACKEND, FRONTEND))["total"]["lines"]["pct"] == 83.33
