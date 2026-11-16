"""Genera el reporte de qué ha pasado con cada carro, a partir de los movimientos de NOW.

Uso (desde la carpeta backend, con el entorno virtual activo):
    python -m scripts.reporte_carros

Lee `datos/movimientos_now.xlsx` (la exportación de movimientos de stock de NOW, con las
columnas "Transaction date", "Transaction time", "Location", "Cnr" y "Container element") y
escribe `datos/reporte_carros.xlsx` con tres hojas: Resumen, Por carro y Viajes.

Este script no cruza con las cargas de la aplicación (no usa la base de datos). Para eso, el
administrador sube el mismo Excel en la pantalla Reporte de la aplicación.

No recibe rutas por argumentos, y la carpeta `datos/` no se sube a GitHub.
"""
import sys
from pathlib import Path

from app.errores import ArchivoInvalido
from app.services.reporte_excel import escribir_excel, leer_movimientos
from app.services.reporte_tiempos import armar_reporte

RAIZ = Path(__file__).resolve().parents[2]
ENTRADA = RAIZ / "datos" / "movimientos_now.xlsx"
SALIDA = RAIZ / "datos" / "reporte_carros.xlsx"


def main() -> int:
    if not ENTRADA.exists():
        print(f"No existe {ENTRADA}. Copia ahí la exportación de movimientos de NOW.")
        return 1
    try:
        movimientos = leer_movimientos(ENTRADA.read_bytes())
    except ArchivoInvalido as error:
        print(error)
        return 1
    if not movimientos:
        print("El archivo no trae movimientos.")
        return 1

    reporte = armar_reporte(movimientos)
    SALIDA.write_bytes(escribir_excel(reporte))

    fisicos = len({c.carro_fisico for c in reporte.carros})
    print(
        f"{fisicos} carros físicos ({len(reporte.carros)} lados A y B), {len(reporte.viajes)} viajes "
        f"({reporte.tarimas} movimientos en tarima aparte)."
    )
    print(f"Reporte escrito en {SALIDA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
