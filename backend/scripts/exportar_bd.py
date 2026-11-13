"""Exporta el esquema REAL de la base de datos a docs/db-export.json.

A diferencia de `exportar_modelo` (que lee los modelos de la aplicación), este script lee
la base de datos que está en uso: sus tablas, columnas, llaves, índices, relaciones, cuántas
filas tiene cada tabla y las políticas de seguridad por filas (RLS) declaradas.

Uso (desde la carpeta backend, con el entorno virtual activo y DATABASE_URL apuntando a la
base de producción; la cadena es secreta, defínela solo en tu terminal):
    python -m scripts.exportar_bd

Por seguridad, se niega a exportar una base que no sea PostgreSQL, para no publicar por
error el esquema de tu base local. Usa --permitir-otro-motor solo para pruebas.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

DESTINO = Path(__file__).resolve().parents[2] / "docs" / "db-export.json"


def _tipo(columna_tipo, motor: Engine) -> str:
    try:
        return columna_tipo.compile(dialect=motor.dialect).lower()
    except Exception:  # un tipo que el dialecto no sabe describir
        return str(columna_tipo).lower()


def _politicas_por_tabla(motor: Engine) -> dict[str, list[str]]:
    """Políticas de seguridad por filas. Solo PostgreSQL las tiene."""
    if motor.dialect.name != "postgresql":
        return {}
    consulta = text(
        "SELECT tablename, policyname FROM pg_policies "
        "WHERE schemaname = current_schema() ORDER BY tablename, policyname"
    )
    politicas: dict[str, list[str]] = {}
    with motor.connect() as conexion:
        for tabla, politica in conexion.execute(consulta):
            politicas.setdefault(tabla, []).append(politica)
    return politicas


def describir_bd(motor: Engine) -> dict:
    inspector = inspect(motor)
    politicas = _politicas_por_tabla(motor)
    comillas = motor.dialect.identifier_preparer.quote
    tablas = []

    with motor.connect() as conexion:
        for nombre in sorted(inspector.get_table_names()):
            llaves = set(inspector.get_pk_constraint(nombre)["constrained_columns"])
            columnas = []
            for columna in inspector.get_columns(nombre):
                descripcion = {"nombre": columna["name"], "tipo": _tipo(columna["type"], motor)}
                if columna["name"] in llaves:
                    descripcion["pk"] = True
                descripcion["nulo"] = bool(columna["nullable"])
                columnas.append(descripcion)

            relaciones = [
                {"columna": propia, "referencia": f"{llave['referred_table']}.{ajena}"}
                for llave in inspector.get_foreign_keys(nombre)
                for propia, ajena in zip(llave["constrained_columns"], llave["referred_columns"])
            ]
            indices = sorted(i["name"] for i in inspector.get_indexes(nombre) if i["name"])
            filas = conexion.execute(text(f"SELECT count(*) FROM {comillas(nombre)}")).scalar_one()

            tablas.append(
                {
                    "nombre": nombre,
                    "filas": filas,
                    "columnas": columnas,
                    "indices": indices,
                    "relaciones": relaciones,
                    "politicas_rls": politicas.get(nombre, []),
                }
            )

    return {
        "generado_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "motor": "postgres" if motor.dialect.name == "postgresql" else motor.dialect.name,
        "tablas": tablas,
    }


def resumen(exportacion: dict) -> dict:
    """Los números que pide declarar el formulario del curso, calculados del propio archivo."""
    tablas = exportacion["tablas"]
    con_mas_filas = max(tablas, key=lambda t: t["filas"])
    return {
        "tablas": len(tablas),
        "relaciones": sum(len(t["relaciones"]) for t in tablas),
        "tabla_con_mas_filas": con_mas_filas["nombre"],
        "tablas_con_datos": [t["nombre"] for t in tablas if t["filas"] > 0],
        "tablas_con_politicas": [t["nombre"] for t in tablas if t["politicas_rls"]],
        "tablas_sin_llave_primaria": [
            t["nombre"] for t in tablas if not any(c.get("pk") for c in t["columnas"])
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Exporta el esquema real de la base de datos.")
    parser.add_argument("--salida", type=Path, default=DESTINO)
    parser.add_argument("--permitir-otro-motor", action="store_true")
    argumentos = parser.parse_args()

    from app.database import engine  # se importa aquí: usa DATABASE_URL del entorno

    if engine.dialect.name != "postgresql" and not argumentos.permitir_otro_motor:
        print(
            f"La base configurada es {engine.dialect.name}, no PostgreSQL. ¿Definiste DATABASE_URL "
            "con la cadena de producción en esta terminal? No se exportó nada."
        )
        return 1

    exportacion = describir_bd(engine)
    argumentos.salida.parent.mkdir(parents=True, exist_ok=True)
    argumentos.salida.write_text(
        json.dumps(exportacion, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    datos = resumen(exportacion)
    print(f"Exportado a {argumentos.salida}")
    print(f"  Motor: {exportacion['motor']}   Generado: {exportacion['generado_at']}")
    print(f"  Tablas: {datos['tablas']}")
    print(f"  Relaciones (llaves foráneas): {datos['relaciones']}")
    print(f"  Tabla con más filas: {datos['tabla_con_mas_filas']}")
    print(f"  Tablas con datos: {', '.join(datos['tablas_con_datos']) or 'ninguna'}")
    print(f"  Tablas con políticas RLS: {', '.join(datos['tablas_con_politicas']) or 'ninguna'}")
    if datos["tablas_sin_llave_primaria"]:
        print(f"  ATENCIÓN, sin llave primaria: {', '.join(datos['tablas_sin_llave_primaria'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
