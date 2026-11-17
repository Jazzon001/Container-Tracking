"""Lectura del Excel de NOW y escritura del Excel del reporte, todo en memoria.

Lo que llega aquí es un archivo que alguien subió: se revisa antes de abrirlo (tamaño ya descomprimido y
número de filas) y cualquier problema se devuelve como un error claro, no como una caída."""
import zipfile
from datetime import date, datetime, time
from io import BytesIO

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter
from openpyxl.utils.exceptions import InvalidFileException

from app.errores import ArchivoInvalido
from app.services.reporte_tiempos import (
    PLANTILLA_TRANSFERENCIA,
    Movimiento,
    Reporte,
    etiqueta_calidad,
    horas,
)

COLUMNAS_NECESARIAS = ("Transaction date", "Transaction time", "Location", "Cnr", "Container element")
# Opcional: la calidad (Qlt) de NOW. Si el archivo no la trae, el reporte sale sin ella.
COLUMNA_CALIDAD = "Qlt"
# Opcional: la plantilla de la transacción (016 producción, 202 transferencia). Sin ella, todo se trata como 202.
COLUMNA_PLANTILLA = "Tmp"
FORMATO_FECHA = "dd/mm/yyyy hh:mm"

LIMITE_DESCOMPRIMIDO = 100 * 1024 * 1024  # un .xlsx de miles de filas descomprime a pocos MB
LIMITE_FILAS = 200_000


def _combinar(fecha: date | datetime, hora: time | datetime) -> datetime:
    try:
        dia = fecha.date() if isinstance(fecha, datetime) else fecha
        momento = hora.time() if isinstance(hora, datetime) else hora
        return datetime.combine(dia, momento)
    except TypeError:
        raise ArchivoInvalido("Hay filas con una fecha u hora que no se entiende.") from None


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


def _revisar(contenido: bytes) -> None:
    try:
        with zipfile.ZipFile(BytesIO(contenido)) as comprimido:
            descomprimido = sum(parte.file_size for parte in comprimido.infolist())
    except zipfile.BadZipFile:
        raise ArchivoInvalido("El archivo no es un Excel (.xlsx) válido.") from None
    if descomprimido > LIMITE_DESCOMPRIMIDO:
        raise ArchivoInvalido("El archivo es demasiado grande una vez descomprimido.")


def leer_movimientos(contenido: bytes) -> list[Movimiento]:
    """Las filas de la primera hoja del Excel de NOW (el contenido del archivo, en bytes)."""
    _revisar(contenido)
    try:
        libro = load_workbook(BytesIO(contenido), read_only=True, data_only=True)
    except (InvalidFileException, KeyError, OSError, ValueError):
        raise ArchivoInvalido("El archivo no es un Excel (.xlsx) válido.") from None
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
            if len(movimientos) >= LIMITE_FILAS:
                raise ArchivoInvalido(f"El archivo tiene más de {LIMITE_FILAS} filas.")
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


NOTAS = (
    "Plantilla 016 = producción: deja el carro puesto en RCV01 (la entrada). Plantilla 202 = transferencia: cada fila es la SALIDA de esa ubicación.",
    "Una fila 202 en RCV01 = salió de recepción hacia un WIP. Una fila 202 en WIPxx = salió de ese WIP hacia DTY, donde se deja de rastrear.",
    "Un viaje es la vida de un contenedor elemento; un carro hace muchos viajes.",
    "RCV02 es la última localización antes de que empaque libere el carro: ahí llegan los carros con producto POY de grado B que sale de DTY.",
    "Los carros se parten siempre en un lado A y un lado B (P056A y P056B): cada lado tiene su contenedor elemento y sus viajes.",
    "Calidad (Qlt de NOW): 1 = AA, 2 = A, 3 = B. Empaque la empaca como A o calidad la revisa y la deja como 3 (B), si aplica.",
    "Plantilla 119 = anulación de una notificación (la negativa de la 016, por un error del operador): ese contenedor no cuenta como viaje y aparece en la hoja Anulados.",
    "Este reporte analiza el flujo de POY (carros que empiezan con P). Los carros de otros procesos (D, T, DT…) tienen otro flujo y por ahora solo se cuentan.",
    "Si de un contenedor no se ve su 016, se notificó antes del rango del archivo: no se calculan sus horas en RCV01.",
    "Las duraciones de lo que sigue abierto (en RCV01 o en WIP) se miden hasta el último movimiento del archivo y no entran en los promedios.",
    "Las horas en DTY van de la salida del WIP en NOW a la liberación del carro en este sistema (intermedio o empaque, con el contenedor elemento).",
    "Un viaje sin registro en este sistema no tiene horas en DTY: el carro no se cargó o no se liberó aquí.",
)


def _hoja_resumen(libro: Workbook, reporte: Reporte) -> None:
    hoja = libro.create_sheet("Resumen")
    hoja.append(["Reporte de carros a partir de los movimientos de NOW"])
    hoja["A1"].font = Font(bold=True, size=14)
    hoja.append([f"Medido al último movimiento del archivo: {reporte.corte:%d/%m/%Y %H:%M}"])
    hoja.append([])
    for indicador, valor in reporte.resumen:
        hoja.append([indicador, valor])
    for tabla in reporte.tablas:
        hoja.append([])
        hoja.append([tabla.titulo])
        hoja.cell(row=hoja.max_row, column=1).font = Font(bold=True)
        hoja.append([tabla.columna, "Viajes", "Horas promedio", "Horas máximo"])
        for celda in hoja[hoja.max_row]:
            celda.font = Font(bold=True)
        for fila in tabla.filas:
            hoja.append(list(fila))
    hoja.append([])
    for nota in NOTAS:
        hoja.append([nota])
    hoja.column_dimensions["A"].width = 66
    for letra in "BCD":
        hoja.column_dimensions[letra].width = 16


def escribir_excel(reporte: Reporte) -> bytes:
    """El reporte como un Excel con tres hojas (Resumen, Por carro y Viajes), en bytes."""
    libro = Workbook()
    libro.remove(libro.active)
    _hoja_resumen(libro, reporte)

    _hoja(
        libro,
        "Por carro",
        ["Carro físico", "Lado", "Carro (NOW)", "Viajes", "Último contenedor elemento", "Calidad (Qlt)",
         "Situación (NOW)", "Horas en esa situación", "Horas promedio en RCV01", "Horas promedio en WIP",
         "En este sistema (último viaje registrado)", "Viajes registrados en el sistema", "Horas en DTY (ese viaje)", "Horas promedio en DTY"],
        [[c.carro_fisico, c.lado, c.carro, c.viajes, c.ultimo_contenedor, etiqueta_calidad(c.calidad),
          c.situacion, horas(c.desde_ultimo_movimiento), horas(c.horas_promedio_en_rcv),
          horas(c.horas_promedio_en_wip), c.situacion_sistema, f"{c.viajes_en_sistema} de {c.viajes}",
          horas(c.horas_en_dty), horas(c.horas_promedio_en_dty)]
         for c in reporte.carros],
        [12, 6, 12, 8, 24, 12, 58, 14, 14, 14, 34, 16, 14, 14],
    )

    hoja_viajes = _hoja(
        libro,
        "Viajes",
        ["Carro (NOW)", "Contenedor elemento", "Calidad (Qlt)", "Notificado en RCV01 (016)", "Salió de recepción el",
         "Salió de WIP hacia DTY el", "WIP de salida", "Horas en RCV01", "Horas en WIP", "Horas en POY",
         "Escaneado en el sistema", "Liberado en el sistema", "Horas hasta escanear", "Horas en DTY",
         "En este sistema", "Situación (NOW)", "Horas desde el último movimiento", "Recorrido"],
        [[v.carro, v.contenedor, etiqueta_calidad(v.calidad), v.notificado_en, v.salio_de_recepcion_en,
          v.salio_a_dty_en, v.wip_de_salida, horas(v.horas_en_rcv), horas(v.horas_en_wip), horas(v.horas_en_poy),
          v.cargada_en, v.recibida_en, horas(v.horas_hasta_escanear), horas(v.horas_en_dty),
          v.situacion_sistema, v.situacion, horas(v.desde_ultimo_movimiento), v.recorrido]
         for v in reporte.viajes],
        [12, 24, 12, 20, 18, 20, 12, 12, 12, 12, 20, 20, 14, 12, 34, 50, 18, 34],
    )
    _fechas(hoja_viajes, [4, 5, 6, 11, 12])

    hoja_anulados = _hoja(
        libro,
        "Anulados",
        ["Carro (NOW)", "Contenedor elemento", "Ubicación", "Notificado (016)", "Anulado el (119)", "Horas hasta la anulación"],
        [[a.carro, a.contenedor, a.ubicacion, a.notificado_en, a.anulado_en,
          horas(a.anulado_en - a.notificado_en) if a.notificado_en else None]
         for a in reporte.anulados],
        [12, 24, 12, 20, 20, 16],
    )
    _fechas(hoja_anulados, [4, 5])

    salida = BytesIO()
    libro.save(salida)
    return salida.getvalue()
