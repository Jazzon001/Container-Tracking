"""Lectura del Excel de NOW y escritura del Excel del reporte, todo en memoria.

Lo que llega aquí es un archivo que alguien subió: se revisa antes de abrirlo (tamaño ya descomprimido y
número de filas) y cualquier problema se devuelve como un error claro, no como una caída.

El Excel del reporte está pensado para leerse sin explicación: una fila por contenedor elemento (cada
vez que se carga un carro), con la etapa en que está y las horas que pasó en cada una."""
import zipfile
from datetime import date, datetime, time
from io import BytesIO

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter
from openpyxl.utils.exceptions import InvalidFileException

from app.errores import ArchivoInvalido
from app.services.reporte_tiempos import (
    CALIDADES,
    PLANTILLA_TRANSFERENCIA,
    Movimiento,
    Reporte,
    Viaje,
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
LOS_MAS_ANTIGUOS = 10  # cuántos se listan en "los que más llevan esperando"


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


# ----------------------------------------------------------------------------------------------
# Escritura
# ----------------------------------------------------------------------------------------------


def _calidad_en_letras(calidad: int | None) -> str:
    """AA, A o B (la calidad de NOW); un número que no se conoce se muestra tal cual."""
    if calidad is None:
        return "sin dato"
    return CALIDADES.get(calidad, str(calidad))


def _negrita(hoja, fila: int) -> None:
    for celda in hoja[fila]:
        celda.font = Font(bold=True)


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


ESTADISTICAS = ("promedio", "mediana", "máximo")


def _separar_estadisticas(resumen: list[tuple[str, object]]):
    """Separa las cifras sueltas de las estadísticas ("Horas en WIP …: promedio"), que se muestran
    como una tabla con una fila por etapa y una columna por estadística."""
    cifras: list[tuple[str, object]] = []
    tabla: dict[str, dict[str, object]] = {}
    for indicador, valor in resumen:
        titulo, _, estadistica = indicador.rpartition(": ")
        if titulo and estadistica in ESTADISTICAS:
            tabla.setdefault(titulo, {})[estadistica] = valor
        else:
            cifras.append((indicador, valor))
    return cifras, tabla


def _seccion(hoja, titulo: str) -> None:
    hoja.append([])
    hoja.append([titulo])
    hoja.cell(row=hoja.max_row, column=1).font = Font(bold=True, size=12)


def _los_que_mas_llevan(hoja, titulo: str, viajes: list[Viaje], horas_de) -> None:
    """Los contenedores que más tiempo llevan en una etapa que todavía no terminan."""
    elegidos = sorted((v for v in viajes if horas_de(v) is not None), key=horas_de, reverse=True)[:LOS_MAS_ANTIGUOS]
    if not elegidos:
        return
    _seccion(hoja, titulo)
    hoja.append(["Carro", "Contenedor elemento", "Horas ahí", "Desde"])
    _negrita(hoja, hoja.max_row)
    for v in elegidos:
        hoja.append([v.carro, v.contenedor, horas(horas_de(v)), v.ultimo_movimiento])
        hoja.cell(row=hoja.max_row, column=4).number_format = FORMATO_FECHA


def _hoja_resumen(libro: Workbook, reporte: Reporte) -> None:
    hoja = libro.create_sheet("Resumen")
    hoja.append(["Reporte de carros a partir de los movimientos de NOW"])
    hoja["A1"].font = Font(bold=True, size=14)
    hoja.append([f"Medido al último movimiento del archivo: {reporte.corte:%d/%m/%Y %H:%M} (hora de NOW)"])
    hoja.append(["Cada fila de la hoja Contenedores es un contenedor elemento: cada vez que se carga un carro. Detalles en la hoja Cómo leer."])

    cifras, estadisticas = _separar_estadisticas(reporte.resumen)
    _seccion(hoja, "Cuántos hay y dónde están")
    for indicador, valor in cifras:
        hoja.append([indicador, valor])

    if estadisticas:
        _seccion(hoja, "Cuánto tiempo pasan (horas, solo de lo que ya terminó la etapa)")
        hoja.append(["Etapa", "Promedio", "Mediana", "Máximo"])
        _negrita(hoja, hoja.max_row)
        for titulo, valores in estadisticas.items():
            hoja.append([titulo] + [valores.get(e) for e in ESTADISTICAS])

    _los_que_mas_llevan(hoja, f"Los {LOS_MAS_ANTIGUOS} que más llevan en RCV01 esperando a intermedio", reporte.viajes,
                        lambda v: v.horas_en_rcv if v.sigue_en_rcv else None)
    _los_que_mas_llevan(hoja, f"Los {LOS_MAS_ANTIGUOS} que más llevan en WIP sin salir hacia DTY", reporte.viajes,
                        lambda v: v.horas_en_wip if v.sigue_en_wip else None)
    _los_que_mas_llevan(hoja, f"Los {LOS_MAS_ANTIGUOS} que más llevan en DTY sin liberarse en la aplicación", reporte.viajes,
                        lambda v: v.horas_en_dty if v.dty_abierto else None)

    for tabla in reporte.tablas:
        if not tabla.filas:
            continue
        _seccion(hoja, tabla.titulo)
        hoja.append([tabla.columna, "Contenedores", "Horas promedio", "Horas máximo"])
        _negrita(hoja, hoja.max_row)
        for fila in tabla.filas:
            hoja.append(list(fila))

    hoja.column_dimensions["A"].width = 70
    for letra in "BCD":
        hoja.column_dimensions[letra].width = 18


def _hoja_contenedores(libro: Workbook, viajes: list[Viaje]) -> None:
    hoja = _hoja(
        libro,
        "Contenedores",
        ["Carro", "Carro físico", "Lado", "Contenedor elemento", "Calidad",
         "Dónde está ahora", "Desde", "Lleva ahí (horas)",
         "Entró a RCV01 (producción, 016)", "Salió de RCV01 (hacia WIP)", "Salió del WIP (hacia DTY)", "WIP del que salió",
         "Horas en RCV01", "Horas en WIP", "Horas en POY (RCV01 + WIP)",
         "Cargado en la aplicación", "Liberado en la aplicación", "Horas hasta cargarlo en la aplicación", "Horas en DTY (hasta liberarse)",
         "Estado en la aplicación", "Recorrido"],
        [[v.carro, v.carro_fisico, v.lado, v.contenedor, _calidad_en_letras(v.calidad),
          v.etapa, v.ultimo_movimiento, horas(v.desde_ultimo_movimiento),
          v.notificado_en, v.salio_de_recepcion_en, v.salio_a_dty_en, v.wip_de_salida,
          # Las duraciones solo se llenan cuando la etapa ya terminó; lo que sigue en curso está en "Lleva ahí".
          horas(None if v.sigue_en_rcv else v.horas_en_rcv),
          horas(v.horas_en_wip if v.salio_a_dty else None),
          horas(v.horas_en_poy),
          v.cargada_en, v.recibida_en, horas(v.horas_hasta_escanear),
          horas(None if v.dty_abierto else v.horas_en_dty),
          v.situacion_sistema, v.recorrido]
         for v in viajes],
        [10, 11, 6, 24, 9, 40, 18, 12, 20, 20, 20, 12, 11, 11, 13, 20, 20, 16, 14, 34, 34],
    )
    _fechas(hoja, [7, 9, 10, 11, 16, 17])


def _hoja_carros(libro: Workbook, reporte: Reporte) -> None:
    _hoja(
        libro,
        "Carros",
        ["Carro físico", "Lado", "Carro", "Veces cargado (en NOW)", "Último contenedor elemento", "Calidad",
         "Dónde está ahora", "Lleva ahí (horas)", "Promedio de horas en RCV01", "Promedio de horas en WIP",
         "Veces cargado en la aplicación", "Último estado en la aplicación", "Horas en DTY (ese contenedor)", "Promedio de horas en DTY"],
        [[c.carro_fisico, c.lado, c.carro, c.viajes, c.ultimo_contenedor, _calidad_en_letras(c.calidad),
          c.etapa, horas(c.desde_ultimo_movimiento), horas(c.horas_promedio_en_rcv), horas(c.horas_promedio_en_wip),
          c.viajes_en_sistema, c.situacion_sistema,
          horas(None if c.dty_abierto else c.horas_en_dty), horas(c.horas_promedio_en_dty)]
         for c in reporte.carros],
        [11, 6, 9, 14, 24, 9, 40, 12, 14, 14, 16, 34, 16, 14],
    )


def _hoja_anulados(libro: Workbook, reporte: Reporte) -> None:
    hoja = _hoja(
        libro,
        "Anulados",
        ["Carro", "Contenedor elemento", "Ubicación", "Notificado (016)", "Anulado el (119)", "Horas hasta anularlo"],
        [[a.carro, a.contenedor, a.ubicacion, a.notificado_en, a.anulado_en,
          horas(a.anulado_en - a.notificado_en) if a.notificado_en else None]
         for a in reporte.anulados],
        [10, 24, 12, 20, 20, 16],
    )
    _fechas(hoja, [4, 5])


COMO_LEER = (
    ("Qué es una fila", "Cada fila de la hoja Contenedores es un contenedor elemento: el código de barras que se genera cada vez que se carga un carro. Un mismo carro aparece en varias filas, una por cada vez que se cargó."),
    ("Carros y lados", "Un carro se parte siempre en un lado A y un lado B (P056A y P056B): cada lado tiene su propio contenedor elemento. La columna Carro físico (P056) los junta."),
    ("Etapas", "1 · En RCV01: se notificó y espera a que intermedio lo mueva.  2 · En WIP: intermedio ya lo movió y falta que salga hacia DTY.  3 · En DTY: salió del WIP (NOW deja de rastrearlo).  4 · Salió de RCV02: volvió de DTY y falta que empaque libere el carro."),
    ("Desde y Lleva ahí", "Desde es el momento en que entró a la etapa actual y Lleva ahí son las horas que lleva en ella, medidas hasta el último movimiento del archivo."),
    ("Horas en RCV01, WIP y POY", "Solo se llenan cuando la etapa ya terminó. Horas en POY es la suma de RCV01 y WIP. Si el contenedor se notificó antes del rango del archivo, no se puede medir RCV01."),
    ("Horas en DTY", "Van de la salida del WIP en NOW a que intermedio o empaque libere el carro en la aplicación con su contenedor elemento. Solo existen si el carro se cargó y se liberó en la aplicación."),
    ("Calidad", "AA, A o B, según la columna Qlt de NOW (1, 2 y 3). Empaque la empaca como A, o calidad la revisa y la deja como B."),
    ("Cómo se lee NOW", "La plantilla 016 es la producción: deja el carro en RCV01 (la entrada). La 202 es una transferencia: cada fila es la SALIDA de esa ubicación. La salida de un WIP es siempre hacia DTY."),
    ("Anulados", "La plantilla 119 anula una notificación (la negativa de la 016, por un error del operador). Esos contenedores no cuentan y están en la hoja Anulados."),
    ("Otros procesos y tarimas", "Este reporte analiza el flujo de POY (carros que empiezan con P). Los carros de otros procesos (D, T, DT…) y las tarimas (TARPOY) solo se cuentan en el Resumen."),
)


def _hoja_como_leer(libro: Workbook) -> None:
    hoja = libro.create_sheet("Cómo leer")
    hoja.append(["Cómo leer este reporte"])
    hoja["A1"].font = Font(bold=True, size=14)
    for tema, texto in COMO_LEER:
        hoja.append([tema, texto])
        hoja.cell(row=hoja.max_row, column=1).font = Font(bold=True)
        hoja.cell(row=hoja.max_row, column=2).alignment = Alignment(wrap_text=True, vertical="top")
        hoja.cell(row=hoja.max_row, column=1).alignment = Alignment(vertical="top")
    hoja.column_dimensions["A"].width = 26
    hoja.column_dimensions["B"].width = 110


def escribir_excel(reporte: Reporte) -> bytes:
    """El reporte como un Excel (Resumen, Contenedores, Carros, Anulados y Cómo leer), en bytes."""
    libro = Workbook()
    libro.remove(libro.active)
    _hoja_resumen(libro, reporte)
    _hoja_contenedores(libro, reporte.viajes)
    _hoja_carros(libro, reporte)
    _hoja_anulados(libro, reporte)
    _hoja_como_leer(libro)

    salida = BytesIO()
    libro.save(salida)
    return salida.getvalue()
