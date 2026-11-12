"""Importa carros desde el Excel de NOW (hoja "Containers": columnas IT y Code).

Uso (desde la carpeta backend, con el entorno virtual activo):
    python -m scripts.importar_carros ..\\datos\\Carros.xlsx            (solo revisa)
    python -m scripts.importar_carros ..\\datos\\Carros.xlsx --guardar   (guarda)

Sin --guardar no se escribe nada: muestra qué pasaría. Se puede repetir sin duplicar.
"""
import argparse
import sys
from pathlib import Path

from app import models  # noqa: F401  (importarlo registra las tablas en Base)
from app.database import Base, SessionLocal, engine
from app.errores import ErrorDeNegocio
from app.models import TipoCarro
from app.services.importacion import importar_carros, leer_carros

MAXIMO_PROBLEMAS_MOSTRADOS = 20
ETIQUETAS = {TipoCarro.POY: "POY (C01)", TipoCarro.DTY: "DTY (C02)", TipoCarro.TWISTING: "Twisting (C03)"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Importa carros desde el Excel de NOW.")
    parser.add_argument("archivo", type=Path)
    parser.add_argument("--guardar", action="store_true", help="guarda los carros nuevos")
    argumentos = parser.parse_args()

    try:
        lectura = leer_carros(argumentos.archivo)
    except ErrorDeNegocio as error:
        print(error)
        return 1

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        resumen = importar_carros(db, lectura, argumentos.guardar)

    verbo = "Guardados" if resumen.guardado else "Se guardarían"
    print(f"{verbo} {resumen.total_nuevos} carros nuevos:")
    for tipo in TipoCarro:
        print(f"  {ETIQUETAS[tipo]}: {resumen.nuevos[tipo]}")
    print(f"Ya existían (se omiten): {resumen.existentes}")
    print(f"Filas con problemas: {len(resumen.problemas)}")
    for problema in resumen.problemas[:MAXIMO_PROBLEMAS_MOSTRADOS]:
        print(f"  fila {problema.fila}: {problema.motivo}")
    if len(resumen.problemas) > MAXIMO_PROBLEMAS_MOSTRADOS:
        print(f"  ... y {len(resumen.problemas) - MAXIMO_PROBLEMAS_MOSTRADOS} más")

    if not resumen.guardado:
        print("\nNo se guardó nada. Para guardar, repite el comando con --guardar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
