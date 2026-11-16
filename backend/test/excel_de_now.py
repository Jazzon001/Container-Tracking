"""Excel inventado con la forma de la exportación de movimientos de NOW, para las pruebas del reporte."""
from datetime import datetime
from io import BytesIO

from openpyxl import Workbook

CABECERA = ["Transaction date", "Transaction time", "IT", "Location", "Cnr", "Container element", "Qlt", "Tmp"]


def fila(dia, hora, ubicacion, carro, contenedor, plantilla="202", calidad=2.0, minuto=30):
    """Una fila de NOW: la fecha va en una columna y la hora en otra (con una fecha cualquiera)."""
    return [datetime(2026, 11, dia), datetime(1970, 1, 1, hora, minuto), "PPY", ubicacion, carro, contenedor, calidad, plantilla]


def excel(filas, cabecera=CABECERA) -> bytes:
    libro = Workbook()
    hoja = libro.active
    hoja.append(cabecera)
    for f in filas:
        hoja.append(f)
    salida = BytesIO()
    libro.save(salida)
    return salida.getvalue()


# Contenedor A1 (carro P1A): entra a RCV01 el 1 a las 6:30, sale a las 8:30 y del WIPB4 hacia DTY a las 12:30.
# Contenedor B2 (carro P2B): entra a RCV01 el 1 a las 9:30 y no se mueve.
# Una tarima, que no es un carro.
FILAS_BASICAS = [
    fila(1, 6, "RCV01", "P1A", "A1", plantilla="016"),
    fila(1, 8, "RCV01", "P1A", "A1"),
    fila(1, 12, "WIPB4", "P1A", "A1"),
    fila(1, 9, "RCV01", "P2B", "B2", plantilla="016"),
    fila(1, 10, "EMP", "TARPOY", "T-99"),
]
