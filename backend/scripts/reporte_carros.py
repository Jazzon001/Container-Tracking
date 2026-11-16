"""Genera el reporte de qué ha pasado con cada carro, a partir de los movimientos de NOW.

Uso (desde la carpeta backend, con el entorno virtual activo):
    python -m scripts.reporte_carros

Lee `datos/movimientos_now.xlsx` (la exportación de movimientos de stock de NOW, con las
columnas "Transaction date", "Transaction time", "Location", "Cnr" y "Container element") y
escribe `datos/reporte_carros.xlsx` con tres hojas: Resumen, Por carro y Viajes.

No recibe rutas por argumentos, y la carpeta `datos/` no se sube a GitHub.
"""
import sys
from datetime import date, datetime, time
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter

from app.services.reporte_tiempos import (
    FilaCarro,
    PLANTILLA_TRANSFERENCIA,
    Movimiento,
    Viaje,
    agrupar_viajes,
    es_tarima,
    etiqueta_calidad,
    horas,
    horas_en_rcv_por_calidad,
    horas_en_wip_por_calidad,
    horas_en_wip_por_wip,
    por_carro,
    resumen,
)

RAIZ = Path(__file__).resolve().parents[2]
ENTRADA = RAIZ / "datos" / "movimientos_now.xlsx"
SALIDA = RAIZ / "datos" / "reporte_carros.xlsx"

COLUMNAS_NECESARIAS = ("Transaction date", "Transaction time", "Location", "Cnr", "Container element")
# Opcional: la calidad (Qlt) de NOW. Si el archivo no la trae, el reporte sale sin ella.
COLUMNA_CALIDAD = "Qlt"
# Opcional: la plantilla de la transacción (016 producción, 202 transferencia). Sin ella, todo se trata como 202.
COLUMNA_PLANTILLA = "Tmp"
FORMATO_FECHA = "dd/mm/yyyy hh:mm"


class ArchivoInvalido(Exception):
    """El Excel no tiene la forma de una exportación de movimientos de NOW."""


def _combinar(fecha: date | datetime, hora: time | datetime) -> datetime:
    dia = fecha.date() if isinstance(fecha, datetime) else fecha
    momento = hora.time() if isinstance(hora, datetime) else hora
    return datetime.combine(dia, momento)


def _plantilla(valor) -> str:
    if valor is None or str(valor).strip() == "":
        return PLANTILLA_TRANSFERENCIA
    try:
        return str(int(float(valor))).zfill(3)  # 16, 16.0 y "016" son la misma plantilla
    except (TypeError, ValueError):
        return str(valor).strip()


def _calidad(valor) -> int | None:
    try:
        return int(float(valor))
    except (TypeError, ValueError):
        return None


def leer_movimientos(ruta: Path) -> list[Movimiento]:
    libro = load_workbook(ruta, read_only=True, data_only=True)
    try:
        filas = libro.worksheets[0].iter_rows(values_only=True)
        cabecera = next(filas, None)
        if cabecera is None:
            raise ArchivoInvalido("El archivo está vacío.")
        posicion = {nombre: i for i, nombre in enumerate(cabecera) if nombre}
        faltan = [c for c in COLUMNAS_NECESARIAS if c not in posicion]
        if faltan:
            raise ArchivoInvalido(f"Faltan estas columnas en la primera hoja: {', '.join(faltan)}.")

        movimientos = []
        for fila in filas:
            contenedor = fila[posicion["Container element"]]
            if contenedor is None:
                continue  # fila en blanco
            movimientos.append(
                Movimiento(
                    instante=_combinar(fila[posicion["Transaction date"]], fila[posicion["Transaction time"]]),
                    ubicacion=str(fila[posicion["Location"]]).strip(),
                    carro=str(fila[posicion["Cnr"]]).strip(),
                    contenedor=str(contenedor).strip(),
                    calidad=_calidad(fila[posicion[COLUMNA_CALIDAD]]) if COLUMNA_CALIDAD in posicion else None,
                    plantilla=_plantilla(fila[posicion[COLUMNA_PLANTILLA]]) if COLUMNA_PLANTILLA in posicion else PLANTILLA_TRANSFERENCIA,
                )
            )
        return movimientos
    finally:
        libro.close()


def _hoja(libro: Workbook, titulo: str, cabecera: list[str], filas: list[list], anchos: list[int]):
    hoja = libro.create_sheet(titulo)
    hoja.append(cabecera)
    for celda in hoja[1]:
        celda.font = Font(bold=True)
        celda.alignment = Alignment(wrap_text=True, vertical="top")
    for fila in filas:
        hoja.append(fila)
    for numero, ancho in enumerate(anchos, start=1):
        hoja.column_dimensions[get_column_letter(numero)].width = ancho
    hoja.freeze_panes = "A2"
    if filas:
        hoja.auto_filter.ref = hoja.dimensions
    return hoja


def _fechas(hoja, columnas: list[int]) -> None:
    for fila in hoja.iter_rows(min_row=2):
        for numero in columnas:
            fila[numero - 1].number_format = FORMATO_FECHA


def _tabla_de_espera(hoja, titulo: str, primera_columna: str, filas: list[tuple]) -> None:
    hoja.append([titulo])
    hoja.cell(row=hoja.max_row, column=1).font = Font(bold=True)
    hoja.append([primera_columna, "Viajes", "Horas promedio", "Horas máximo"])
    for celda in hoja[hoja.max_row]:
        celda.font = Font(bold=True)
    for fila in filas:
        hoja.append(list(fila))


def escribir_reporte(ruta: Path, viajes: list[Viaje], carros: list[FilaCarro], tarimas: int, corte: datetime) -> None:
    libro = Workbook()
    libro.remove(libro.active)

    hoja = libro.create_sheet("Resumen")
    hoja.append(["Reporte de carros a partir de los movimientos de NOW"])
    hoja["A1"].font = Font(bold=True, size=14)
    hoja.append([f"Medido al último movimiento del archivo: {corte:%d/%m/%Y %H:%M}"])
    hoja.append([])
    for indicador, valor in resumen(viajes, tarimas):
        hoja.append([indicador, valor])
    hoja.append([])
    _tabla_de_espera(hoja, "Horas en RCV01 según la calidad (Qlt de NOW)", "Calidad (Qlt)", horas_en_rcv_por_calidad(viajes))
    hoja.append([])
    _tabla_de_espera(hoja, "Horas en WIP según el WIP del que salieron hacia DTY", "WIP", horas_en_wip_por_wip(viajes))
    hoja.append([])
    _tabla_de_espera(hoja, "Horas en WIP según la calidad (Qlt de NOW)", "Calidad (Qlt)", horas_en_wip_por_calidad(viajes))
    hoja.append([])
    for nota in (
        "Plantilla 016 = producción: deja el carro puesto en RCV01 (la entrada). Plantilla 202 = transferencia: cada fila es la SALIDA de esa ubicación.",
        "Una fila 202 en RCV01 = salió de recepción hacia un WIP. Una fila 202 en WIPxx = salió de ese WIP hacia DTY, donde se deja de rastrear.",
        "Un viaje es la vida de un contenedor elemento; un carro hace muchos viajes.",
        "RCV02 recibe el producto POY de grado B que sale del proceso de DTY.",
        "Los carros se parten siempre en un lado A y un lado B (P056A y P056B): cada lado tiene su contenedor elemento y sus viajes.",
        "Calidad (Qlt de NOW): 1 = AA, 2 = A, 3 = B. Empaque la empaca como A o calidad la revisa y la deja como 3 (B), si aplica.",
        "Si de un contenedor no se ve su 016, se notificó antes del rango del archivo: no se calculan sus horas en RCV01.",
        "Las duraciones de lo que sigue abierto (en RCV01 o en WIP) se miden hasta el último movimiento del archivo y no entran en los promedios.",
    ):
        hoja.append([nota])
    hoja.column_dimensions["A"].width = 62
    for letra in "BCD":
        hoja.column_dimensions[letra].width = 16

    _hoja(
        libro,
        "Por carro",
        ["Carro físico", "Lado", "Carro (NOW)", "Viajes", "Último contenedor elemento", "Calidad (Qlt)", "Situación",
         "Horas en esa situación", "Horas promedio en RCV01", "Horas promedio en WIP"],
        [[c.carro_fisico, c.lado, c.carro, c.viajes, c.ultimo_contenedor, etiqueta_calidad(c.calidad), c.situacion,
          horas(c.desde_ultimo_movimiento),
          horas(c.horas_promedio_en_rcv), horas(c.horas_promedio_en_wip)]
         for c in carros],
        [12, 6, 12, 8, 24, 12, 58, 14, 14, 14],
    )

    hoja_viajes = _hoja(
        libro,
        "Viajes",
        ["Carro (NOW)", "Contenedor elemento", "Calidad (Qlt)", "Notificado en RCV01 (016)", "Salió de recepción el",
         "Salió de WIP hacia DTY el", "WIP de salida", "Horas en RCV01", "Horas en WIP", "Horas en POY",
         "Situación", "Horas desde el último movimiento", "Recorrido"],
        [[v.carro, v.contenedor, etiqueta_calidad(v.calidad), v.notificado_en, v.salio_de_recepcion_en, v.salio_a_dty_en,
          v.wip_de_salida, horas(v.horas_en_rcv), horas(v.horas_en_wip), horas(v.horas_en_poy),
          v.situacion, horas(v.desde_ultimo_movimiento), v.recorrido]
         for v in viajes],
        [12, 24, 12, 20, 18, 20, 12, 12, 12, 12, 50, 18, 34],
    )
    _fechas(hoja_viajes, [4, 5, 6])

    libro.save(ruta)


def main() -> int:
    if not ENTRADA.exists():
        print(f"No existe {ENTRADA}. Copia ahí la exportación de movimientos de NOW.")
        return 1
    try:
        movimientos = leer_movimientos(ENTRADA)
    except ArchivoInvalido as error:
        print(error)
        return 1
    if not movimientos:
        print("El archivo no trae movimientos.")
        return 1

    corte = max(m.instante for m in movimientos)
    viajes = agrupar_viajes(movimientos, corte)
    carros = por_carro(viajes)
    tarimas = sum(1 for m in movimientos if es_tarima(m))
    escribir_reporte(SALIDA, viajes, carros, tarimas, corte)

    fisicos = len({c.carro_fisico for c in carros})
    print(f"{fisicos} carros físicos ({len(carros)} lados A y B), {len(viajes)} viajes ({tarimas} movimientos en tarima aparte).")
    print(f"Reporte escrito en {SALIDA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
