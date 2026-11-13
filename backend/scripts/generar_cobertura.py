"""Genera el reporte de cobertura del proyecto completo (backend y frontend) en la raíz.

Produce dos archivos, que se versionan en el repositorio:
    coverage/lcov.info              reporte unificado en formato lcov
    coverage/coverage-summary.json  resumen en formato Istanbul (total.lines.pct)

Uso (desde la carpeta backend, con el entorno virtual activo y las dependencias del
frontend instaladas con `npm install`):
    python -m scripts.generar_cobertura

Corre las pruebas del backend y del frontend con cobertura y une los dos reportes.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DESTINO = RAIZ / "coverage"
LCOV_DEL_FRONTEND = RAIZ / "frontend" / "coverage" / "container-tracking" / "lcov.info"


def normalizar_registros(lcov: str, carpeta: str) -> str:
    """Antepone la carpeta (backend o frontend) a cada archivo y usa siempre `/` en las rutas,
    para que el reporte unificado sea el mismo en Windows y en Linux."""
    lineas = []
    for linea in lcov.splitlines():
        if linea.startswith("SF:"):
            linea = f"SF:{carpeta}/{linea[3:].replace(chr(92), '/')}"
        lineas.append(linea)
    return "\n".join(lineas) + "\n"


def sumar(lcov: str) -> dict[str, int]:
    """Suma, de todos los archivos, líneas, funciones y ramas (totales y cubiertas)."""
    totales = {"LF": 0, "LH": 0, "FNF": 0, "FNH": 0, "BRF": 0, "BRH": 0}
    for linea in lcov.splitlines():
        clave, _, valor = linea.partition(":")
        if clave in totales:
            totales[clave] += int(valor)
    return totales


def _seccion(total: int, cubiertos: int) -> dict:
    porcentaje = round(cubiertos / total * 100, 2) if total else 100
    return {"total": total, "covered": cubiertos, "skipped": 0, "pct": porcentaje}


def resumen_istanbul(lcov: str) -> dict:
    """El resumen en el formato de Istanbul (el de `--coverageReporters=json-summary`).
    Las "statements" se miden con las mismas líneas: lcov no distingue entre ambas."""
    totales = sumar(lcov)
    lineas = _seccion(totales["LF"], totales["LH"])
    return {
        "total": {
            "lines": lineas,
            "statements": dict(lineas),
            "functions": _seccion(totales["FNF"], totales["FNH"]),
            "branches": _seccion(totales["BRF"], totales["BRH"]),
        }
    }


def unir(lcov_backend: str, lcov_frontend: str) -> str:
    return normalizar_registros(lcov_backend, "backend") + normalizar_registros(lcov_frontend, "frontend")


def _correr(comando: list[str], carpeta: Path) -> None:
    resultado = subprocess.run(comando, cwd=carpeta)
    if resultado.returncode != 0:
        raise SystemExit(f"Falló: {' '.join(comando)} (carpeta {carpeta})")


def _lcov_del_backend() -> Path:
    destino = Path(tempfile.mkdtemp()) / "backend.lcov"
    _correr(
        [sys.executable, "-m", "pytest", "-q", "--cov", f"--cov-report=lcov:{destino}"],
        RAIZ / "backend",
    )
    return destino


def _lcov_del_frontend() -> Path:
    npx = shutil.which("npx") or "npx"
    _correr(
        [npx, "ng", "test", "--no-watch", "--coverage", "--coverage-reporters=lcov"],
        RAIZ / "frontend",
    )
    return LCOV_DEL_FRONTEND


def main() -> int:
    # Sin argumentos de ruta: los reportes se leen y se escriben siempre en lugares fijos.
    backend = _lcov_del_backend()
    frontend = _lcov_del_frontend()
    unificado = unir(backend.read_text(encoding="utf-8"), frontend.read_text(encoding="utf-8"))

    DESTINO.mkdir(exist_ok=True)
    (DESTINO / "lcov.info").write_text(unificado, encoding="utf-8")
    resumen = resumen_istanbul(unificado)
    (DESTINO / "coverage-summary.json").write_text(
        json.dumps(resumen, indent=2) + "\n", encoding="utf-8"
    )

    total = resumen["total"]["lines"]
    print(f"Cobertura de líneas del proyecto: {total['pct']}% ({total['covered']} de {total['total']})")
    for nombre, lcov in (("backend", backend), ("frontend", frontend)):
        suma = sumar(lcov.read_text(encoding="utf-8"))
        print(f"  {nombre}: {_seccion(suma['LF'], suma['LH'])['pct']}% ({suma['LH']} de {suma['LF']})")
    print(f"Reportes escritos en {DESTINO}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
