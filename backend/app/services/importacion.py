"""Importación de carros desde el Excel que se descarga de NOW (maestro de contenedores).

Separa dos pasos para poder revisar antes de guardar: `leer_carros` solo lee y valida
el archivo; `importar_carros` compara con la base y, si se pide, guarda.
"""
from dataclasses import dataclass, field
from pathlib import Path
from zipfile import BadZipFile

import openpyxl
from openpyxl.utils.exceptions import InvalidFileException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errores import ArchivoInvalido
from app.models import Carro, TipoCarro

HOJA = "Containers"
COLUMNA_TIPO = "IT"  # tipo de producto en NOW
COLUMNA_CODIGO = "Code"  # código del contenedor (número del carro)
LONGITUD_MAXIMA = 50

# Tipo de producto de NOW -> proceso al que pertenece el carro.
TIPOS_POR_CODIGO = {
    "C01": TipoCarro.POY,
    "C02": TipoCarro.DTY,
    "C03": TipoCarro.TWISTING,
}


@dataclass
class CarroLeido:
    numero: str
    tipo: TipoCarro


@dataclass
class Problema:
    fila: int
    motivo: str


@dataclass
class Lectura:
    carros: list[CarroLeido] = field(default_factory=list)
    problemas: list[Problema] = field(default_factory=list)


@dataclass
class Resumen:
    nuevos: dict[TipoCarro, int]
    existentes: int
    problemas: list[Problema]
    guardado: bool

    @property
    def total_nuevos(self) -> int:
        return sum(self.nuevos.values())


def leer_carros(ruta: Path) -> Lectura:
    """Lee y valida el archivo. Las filas con problemas se reportan, no detienen la lectura."""
    try:
        libro = openpyxl.load_workbook(ruta, read_only=True, data_only=True)
    except (OSError, BadZipFile, InvalidFileException):
        raise ArchivoInvalido(f"No se pudo abrir '{ruta}' como un archivo Excel (.xlsx)")

    try:
        if HOJA not in libro.sheetnames:
            raise ArchivoInvalido(f"El archivo no tiene la hoja '{HOJA}'")
        filas = libro[HOJA].iter_rows(values_only=True)
        columnas = _ubicar_columnas(next(filas, None))
        return _leer_filas(filas, *columnas)
    finally:
        libro.close()


def _ubicar_columnas(cabecera: tuple | None) -> tuple[int, int]:
    nombres = [str(celda).strip() if celda is not None else "" for celda in cabecera or ()]
    faltantes = [c for c in (COLUMNA_TIPO, COLUMNA_CODIGO) if c not in nombres]
    if faltantes:
        raise ArchivoInvalido(f"Faltan las columnas: {', '.join(faltantes)}")
    return nombres.index(COLUMNA_TIPO), nombres.index(COLUMNA_CODIGO)


def _leer_filas(filas, columna_tipo: int, columna_codigo: int) -> Lectura:
    lectura = Lectura()
    vistos: dict[str, int] = {}
    for numero_fila, fila in enumerate(filas, start=2):
        if all(celda in (None, "") for celda in fila):
            continue  # fila en blanco
        tipo_now = str(fila[columna_tipo] or "").strip().upper()
        codigo = str(fila[columna_codigo] or "").strip()

        if not codigo:
            motivo = "Falta el código"
        elif len(codigo) > LONGITUD_MAXIMA:
            motivo = f"El código '{codigo}' supera {LONGITUD_MAXIMA} caracteres"
        elif tipo_now not in TIPOS_POR_CODIGO:
            motivo = f"Tipo de producto desconocido: '{tipo_now}'"
        elif codigo in vistos:
            motivo = f"Código repetido '{codigo}' (ya aparece en la fila {vistos[codigo]})"
        else:
            vistos[codigo] = numero_fila
            lectura.carros.append(CarroLeido(codigo, TIPOS_POR_CODIGO[tipo_now]))
            continue
        lectura.problemas.append(Problema(numero_fila, motivo))
    return lectura


def importar_carros(db: Session, lectura: Lectura, guardar: bool) -> Resumen:
    """Agrega los carros que aún no existen (todos quedan disponibles). Repetirlo no duplica nada."""
    existentes = set(db.scalars(select(Carro.numero)))
    nuevos = [carro for carro in lectura.carros if carro.numero not in existentes]

    if guardar:
        db.add_all(Carro(numero=carro.numero, tipo=carro.tipo) for carro in nuevos)
        db.commit()

    por_tipo = {tipo: sum(1 for c in nuevos if c.tipo == tipo) for tipo in TipoCarro}
    return Resumen(
        nuevos=por_tipo,
        existentes=len(lectura.carros) - len(nuevos),
        problemas=lectura.problemas,
        guardado=guardar,
    )
