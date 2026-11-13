"""Reescribe el coverage.xml del backend para que SonarCloud reconozca los archivos.

coverage.py declara como carpeta base una ruta absoluta de la máquina que corrió las pruebas
(`/home/runner/...`), que SonarCloud no puede usar. Este script la cambia por `.` (la carpeta
del módulo `backend`) y deja las rutas de los archivos relativas a ella (`app/database.py`).

Uso (desde la carpeta backend, después de correr pytest con --cov-report=xml):
    python -m scripts.cobertura_para_sonar

Lee `coverage.xml` y escribe `sonar-coverage.xml`, ambos en la carpeta actual. No recibe
rutas por argumentos: así no se puede usar para leer o escribir en otro lugar del disco.
"""
import re
import sys
from pathlib import Path

# SonarCloud detecta `backend` como un módulo propio (por backend/.coveragerc) y resuelve las
# rutas del reporte desde esa carpeta: `app/database.py`, sin anteponer `backend/`.
PREFIJO = ""
ENTRADA = Path("coverage.xml")
SALIDA = Path("sonar-coverage.xml")


def reescribir_rutas(xml: str, prefijo: str = PREFIJO) -> str:
    """Antepone `prefijo` a cada archivo y declara como carpeta base la raíz del repositorio."""
    xml = re.sub(
        r'filename="([^"]*)"',
        lambda coincidencia: f'filename="{prefijo}{coincidencia.group(1).replace(chr(92), "/")}"',
        xml,
    )
    return re.sub(r"<sources>.*?</sources>", "<sources><source>.</source></sources>", xml, flags=re.S)


def main() -> int:
    if not ENTRADA.exists():
        print(f"No existe {ENTRADA}: corre antes pytest con --cov-report=xml.")
        return 1
    SALIDA.write_text(reescribir_rutas(ENTRADA.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"Escrito {SALIDA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
