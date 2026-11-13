from scripts import cobertura_para_sonar
from scripts.cobertura_para_sonar import main, reescribir_rutas

XML = """<?xml version="1.0" ?>
<coverage>
	<sources>
		<source>C:\\proyecto\\backend</source>
	</sources>
	<packages>
		<package name="app">
			<classes>
				<class name="database.py" filename="app/database.py"><lines/></class>
			</classes>
		</package>
		<package name="app.routers">
			<classes>
				<class name="auth.py" filename="app\\routers\\auth.py"><lines/></class>
			</classes>
		</package>
	</packages>
</coverage>
"""


def test_deja_cada_archivo_relativo_a_la_carpeta_del_backend():
    assert 'filename="app/database.py"' in reescribir_rutas(XML)


def test_usa_barras_normales_tambien_en_los_subpaquetes():
    assert 'filename="app/routers/auth.py"' in reescribir_rutas(XML)


def test_declara_la_carpeta_del_modulo_como_carpeta_base():
    resultado = reescribir_rutas(XML)
    assert "<source>.</source>" in resultado
    assert "C:\\proyecto" not in resultado


def test_no_toca_el_resto_del_reporte():
    assert '<class name="database.py"' in reescribir_rutas(XML)


def test_lee_coverage_xml_y_escribe_sonar_coverage_xml_en_la_carpeta_actual(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "coverage.xml").write_text(XML, encoding="utf-8")

    assert main() == 0
    assert 'filename="app/database.py"' in (tmp_path / "sonar-coverage.xml").read_text(encoding="utf-8")


def test_avisa_si_falta_el_reporte_de_entrada(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    assert main() == 1
    assert "coverage.xml" in capsys.readouterr().out
    assert not (tmp_path / "sonar-coverage.xml").exists()


def test_no_acepta_rutas_por_la_linea_de_comandos():
    # Las rutas son fijas: el script no puede leer ni escribir en otro lugar.
    assert cobertura_para_sonar.ENTRADA.name == "coverage.xml"
    assert cobertura_para_sonar.SALIDA.name == "sonar-coverage.xml"
