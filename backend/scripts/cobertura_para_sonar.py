"""Reescribe el coverage.xml del backend para que SonarCloud reconozca los archivos.

coverage.py escribe cada archivo relativo a la carpeta medida (`database.py`), pero SonarCloud
analiza el repositorio completo desde la raíz y espera `backend/app/database.py`. Sin este
ajuste no relaciona la cobertura con el código y la da por inexistente.

Uso (desde la carpeta backend):
    python -m scripts.cobertura_para_sonar coverage.xml sonar-coverage.xml
"""
import re
import sys
from pathlib import Path

PREFIJO = "backend/app/"


def reescribir_rutas(xml: str, prefijo: str = PREFIJO) -> str:
    """Antepone `prefijo` a cada archivo y declara como carpeta base la raíz del repositorio."""
    xml = re.sub(
        r'filename="([^"]*)"',
        lambda coincidencia: f'filename="{prefijo}{coincidencia.group(1).replace(chr(92), "/")}"',
        xml,
    )
    return re.sub(r"<sources>.*?</sources>", "<sources><source>.</source></sources>", xml, flags=re.S)


def main(argumentos: list[str]) -> int:
    if len(argumentos) != 2:
        print("Uso: python -m scripts.cobertura_para_sonar <entrada.xml> <salida.xml>")
        return 1
    entrada, salida = Path(argumentos[0]), Path(argumentos[1])
    salida.write_text(reescribir_rutas(entrada.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"Escrito {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
