"""Exporta el modelo de datos a JSON, leído directamente de los modelos de la app.

Uso (desde la carpeta backend, con el entorno virtual activo):
    python -m scripts.exportar_modelo

Así el archivo docs/modelo-de-datos.json nunca se desactualiza a mano.
"""
import json
from pathlib import Path

from app import models  # noqa: F401  (importarlo registra las tablas en Base)
from app.database import Base

DESTINO = Path(__file__).resolve().parents[2] / "docs" / "modelo-de-datos.json"


def describir_modelo() -> dict:
    tablas = []
    for tabla in Base.metadata.sorted_tables:
        columnas = [
            {
                "nombre": columna.name,
                "tipo": str(columna.type),
                "nulo": columna.nullable,
                "clave_primaria": columna.primary_key,
                "unico": bool(columna.unique),
                "clave_foranea": [fk.target_fullname for fk in columna.foreign_keys],
            }
            for columna in tabla.columns
        ]
        tablas.append({"nombre": tabla.name, "columnas": columnas})
    return {"tablas": tablas}


if __name__ == "__main__":
    DESTINO.parent.mkdir(exist_ok=True)
    DESTINO.write_text(
        json.dumps(describir_modelo(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Modelo exportado a {DESTINO}")
