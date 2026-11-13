from scripts.cobertura_para_sonar import main, reescribir_rutas

XML = """<?xml version="1.0" ?>
<coverage>
	<sources>
		<source>C:\\proyecto\\backend\\app</source>
	</sources>
	<packages>
		<package name=".">
			<classes>
				<class name="database.py" filename="database.py"><lines/></class>
			</classes>
		</package>
		<package name="routers">
			<classes>
				<class name="auth.py" filename="routers\\auth.py"><lines/></class>
			</classes>
		</package>
	</packages>
</coverage>
"""


def test_antepone_la_carpeta_del_backend_a_cada_archivo():
    assert 'filename="backend/app/database.py"' in reescribir_rutas(XML)


def test_usa_barras_normales_tambien_en_los_subpaquetes():
    assert 'filename="backend/app/routers/auth.py"' in reescribir_rutas(XML)


def test_declara_la_raiz_del_repositorio_como_carpeta_base():
    resultado = reescribir_rutas(XML)
    assert "<source>.</source>" in resultado
    assert "C:\\proyecto" not in resultado


def test_no_toca_el_resto_del_reporte():
    assert '<class name="database.py"' in reescribir_rutas(XML)


def test_escribe_el_archivo_de_salida(tmp_path):
    entrada, salida = tmp_path / "coverage.xml", tmp_path / "sonar-coverage.xml"
    entrada.write_text(XML, encoding="utf-8")

    assert main([str(entrada), str(salida)]) == 0
    assert 'filename="backend/app/database.py"' in salida.read_text(encoding="utf-8")


def test_pide_los_dos_argumentos():
    assert main(["solo-uno.xml"]) == 1
