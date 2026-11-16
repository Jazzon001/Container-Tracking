"""Reporte de tiempos de los carros a partir de los movimientos que exporta NOW.

Cómo se lee el archivo (exportación de movimientos de stock):

  - Plantilla **016**: la que usa el ERP para registrar la producción. Usa el carro y lo deja puesto
    en `RCV01`: es la **entrada** a recepción (la notificación).
  - Plantilla **202**: una transferencia. Cada fila registra la **salida** del contenedor de la
    ubicación de la fila:
      * una fila 202 en `RCV01` es la salida de recepción hacia un WIP (lo mueve intermedio);
      * una fila 202 en `WIPxx` es la salida de ese WIP, siempre hacia DTY, donde se deja de rastrear.
  - `RCV02` es la recepción del producto POY de grado B que sale del proceso de DTY.

Con las filas de un contenedor se reconstruye: RCV01 (entrada) → WIP (salida de RCV01) → DTY (salida del
WIP). El archivo puede no traer la entrada (016) si fue anterior a su rango de fechas.

Después se cruza con lo que registró este sistema: cuándo se escaneó el contenedor elemento al cargar el
carro y cuándo lo liberó intermedio o empaque. De la salida hacia DTY a esa liberación es el tiempo que el
carro estuvo en DTY.

Un **viaje** es la vida de un contenedor elemento: un mismo carro hace muchos viajes, uno por cada
vez que se carga. El módulo no conoce Excel, HTTP ni la base de datos: recibe datos y devuelve viajes.
"""
from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from statistics import mean, median

PREFIJO_RECEPCION = "RCV"
PREFIJO_WIP = "WIP"
# Las tarimas (producto sin carro) vienen en el mismo archivo con un "carro" que empieza así.
PREFIJO_TARIMA = "TAR"
LADOS = ("A", "B")
# La calidad (Qlt de NOW): 1 es AA, 2 es A y 3 es B. Empaque la empaca como A, o calidad la revisa y
# la deja como 3 (B), si aplica.
CALIDADES = {1: "AA", 2: "A", 3: "B"}
PLANTILLA_ENTRADA = "016"  # producción: deja el carro en RCV01
PLANTILLA_TRANSFERENCIA = "202"  # salida de la ubicación de la fila


@dataclass(frozen=True)
class Movimiento:
    """Una fila de NOW. Con la plantilla 016 es la entrada a `ubicacion`; con la 202, la salida."""

    instante: datetime
    ubicacion: str
    carro: str
    contenedor: str
    calidad: int | None = None  # la columna Qlt de NOW (1 = AA, 2 = A, 3 = B)
    plantilla: str = PLANTILLA_TRANSFERENCIA

    @property
    def es_entrada(self) -> bool:
        return self.plantilla == PLANTILLA_ENTRADA


@dataclass(frozen=True)
class Registro:
    """Lo que este sistema guardó de un contenedor elemento. Las horas van en UTC, sin zona."""

    cargada_en: datetime
    recibida_en: datetime | None


@dataclass(frozen=True)
class Viaje:
    carro: str
    contenedor: str
    calidad: int | None
    primer_movimiento: datetime
    notificado_en: datetime | None  # entrada a RCV01 (plantilla 016); None si fue antes del archivo
    salio_de_recepcion_en: datetime | None
    salio_a_dty_en: datetime | None
    wip_de_salida: str | None  # el WIP del que salió hacia DTY
    horas_en_rcv: timedelta | None  # de la notificación a salir de recepción (o hasta el corte, si sigue)
    horas_en_wip: timedelta | None  # de salir de recepción a salir hacia DTY (o hasta el corte, si sigue)
    horas_en_poy: timedelta | None  # de la notificación a salir hacia DTY (solo si se ven ambas)
    recorrido: str
    ultimo_movimiento: datetime
    desde_ultimo_movimiento: timedelta
    situacion: str
    # Lo que sigue viene del cruce con este sistema. Las horas están en la hora de NOW.
    en_sistema: bool = False
    cargada_en: datetime | None = None  # cuándo se escaneó el contenedor elemento en este sistema
    recibida_en: datetime | None = None  # cuándo lo liberó intermedio o empaque
    horas_hasta_escanear: timedelta | None = None  # de la notificación (016) al escaneo
    horas_en_dty: timedelta | None = None  # de salir hacia DTY a la liberación (o hasta el corte, si falta)
    dty_abierto: bool = False  # salió hacia DTY, se cargó en el sistema y todavía no se libera

    @property
    def salio_a_dty(self) -> bool:
        return self.salio_a_dty_en is not None

    @property
    def sigue_en_rcv(self) -> bool:
        """Notificado y todavía sin salir de recepción."""
        return self.notificado_en is not None and self.salio_de_recepcion_en is None

    @property
    def sigue_en_wip(self) -> bool:
        """Salió de recepción y todavía no se ve su salida de WIP."""
        return self.salio_de_recepcion_en is not None and self.salio_a_dty_en is None

    @property
    def situacion_sistema(self) -> str:
        if not self.en_sistema:
            return "Sin registro en este sistema"
        if self.recibida_en is None:
            return "Cargado en el sistema, sin liberar"
        return "Liberado en el sistema"


@dataclass(frozen=True)
class FilaCarro:
    carro: str
    viajes: int
    ultimo_contenedor: str
    calidad: int | None
    situacion: str
    desde_ultimo_movimiento: timedelta
    horas_promedio_en_rcv: timedelta | None
    horas_promedio_en_wip: timedelta | None
    situacion_sistema: str
    horas_en_dty: timedelta | None  # del último viaje
    dty_abierto: bool
    horas_promedio_en_dty: timedelta | None  # de los viajes ya liberados

    @property
    def carro_fisico(self) -> str:
        return separar_lado(self.carro)[0]

    @property
    def lado(self) -> str:
        return separar_lado(self.carro)[1]


@dataclass(frozen=True)
class Tabla:
    """Una tabla de horas agrupada por algo (un WIP, una calidad…)."""

    titulo: str
    columna: str
    filas: list[tuple[object, int, float, float]]  # (clave, viajes, horas promedio, horas máximo)


@dataclass(frozen=True)
class Reporte:
    corte: datetime
    viajes: list[Viaje]
    carros: list[FilaCarro]
    tarimas: int
    resumen: list[tuple[str, object]]
    tablas: list[Tabla]


def separar_lado(carro: str) -> tuple[str, str]:
    """Un carro físico se parte siempre en un lado A y un lado B (`P056A` y `P056B`): devuelve
    (`P056`, `A`). Un código sin lado se devuelve entero y con lado vacío."""
    if len(carro) > 1 and carro[-1].upper() in LADOS:
        return carro[:-1], carro[-1].upper()
    return carro, ""


def etiqueta_calidad(calidad: int | None) -> str:
    if calidad is None:
        return "sin dato"
    return f"{calidad} ({CALIDADES[calidad]})" if calidad in CALIDADES else str(calidad)


def es_recepcion(ubicacion: str) -> bool:
    return ubicacion.startswith(PREFIJO_RECEPCION)


def es_wip(ubicacion: str) -> bool:
    return ubicacion.startswith(PREFIJO_WIP)


def es_tarima(movimiento: Movimiento) -> bool:
    return movimiento.carro.upper().startswith(PREFIJO_TARIMA)


def agrupar_viajes(movimientos: list[Movimiento], corte: datetime | None = None) -> list[Viaje]:
    """Un viaje por contenedor elemento. `corte` es el momento al que se miden las esperas
    todavía abiertas; por omisión, el último movimiento del archivo."""
    movimientos = [m for m in movimientos if not es_tarima(m)]
    if not movimientos:
        return []
    corte = corte or max(m.instante for m in movimientos)

    por_contenedor: dict[str, list[Movimiento]] = defaultdict(list)
    for m in movimientos:
        por_contenedor[m.contenedor].append(m)
    return sorted(
        (_viaje(sorted(lista, key=lambda m: m.instante), corte) for lista in por_contenedor.values()),
        key=lambda v: (v.carro, v.primer_movimiento),
    )


def _situacion(salidas: list[Movimiento]) -> str:
    if not salidas:
        return "En RCV01 (notificado; esperando a que intermedio lo mueva)"
    ultima = salidas[-1]
    if es_wip(ultima.ubicacion):
        return f"En DTY (salió de {ultima.ubicacion})"
    if ultima.ubicacion == "RCV01":
        return "En WIP (salió de RCV01; aún no sale hacia DTY)"
    if es_recepcion(ultima.ubicacion):
        return f"Salió de {ultima.ubicacion} (grado B de DTY); aún no se ve su siguiente movimiento"
    return f"Salió de {ultima.ubicacion}"


def _viaje(lista: list[Movimiento], corte: datetime) -> Viaje:
    primero = lista[0]
    entrada = next((m for m in lista if m.es_entrada), None)
    salidas = [m for m in lista if not m.es_entrada]
    de_recepcion = next((m for m in salidas if es_recepcion(m.ubicacion)), None)
    salio_a_dty = bool(salidas) and es_wip(salidas[-1].ubicacion)
    instante_dty = salidas[-1].instante if salio_a_dty else None

    horas_en_rcv = None
    if entrada is not None:
        horas_en_rcv = (de_recepcion.instante if de_recepcion else corte) - entrada.instante
    horas_en_wip = None
    if de_recepcion is not None:
        horas_en_wip = (instante_dty or corte) - de_recepcion.instante
    horas_en_poy = instante_dty - entrada.instante if entrada is not None and instante_dty else None

    recorrido = [m.ubicacion for i, m in enumerate(lista) if i == 0 or m.ubicacion != lista[i - 1].ubicacion]
    if salio_a_dty:
        recorrido.append("DTY")
    elif de_recepcion is not None:
        recorrido.append("(en WIP)")

    return Viaje(
        carro=primero.carro,
        contenedor=primero.contenedor,
        calidad=primero.calidad,
        primer_movimiento=primero.instante,
        notificado_en=entrada.instante if entrada else None,
        salio_de_recepcion_en=de_recepcion.instante if de_recepcion else None,
        salio_a_dty_en=instante_dty,
        wip_de_salida=salidas[-1].ubicacion if salio_a_dty else None,
        horas_en_rcv=horas_en_rcv,
        horas_en_wip=horas_en_wip,
        horas_en_poy=horas_en_poy,
        recorrido=" → ".join(recorrido),
        ultimo_movimiento=lista[-1].instante,
        desde_ultimo_movimiento=corte - lista[-1].instante,
        situacion=_situacion(salidas),
    )


def cruzar_con_registros(
    viajes: list[Viaje],
    registros: dict[str, Registro],
    desplazamiento_horas: int,
    corte: datetime,
) -> list[Viaje]:
    """Agrega a cada viaje lo que este sistema guardó de su contenedor elemento.

    NOW guarda la hora local de la planta y este sistema la guarda en UTC: `desplazamiento_horas` es
    la diferencia de la planta con UTC (por ejemplo, -6). Todo se compara en hora de NOW."""

    def a_hora_de_now(utc: datetime) -> datetime:
        return utc + timedelta(hours=desplazamiento_horas)

    cruzados = []
    for viaje in viajes:
        registro = registros.get(viaje.contenedor)
        if registro is None:
            cruzados.append(viaje)
            continue

        cargada = a_hora_de_now(registro.cargada_en)
        recibida = a_hora_de_now(registro.recibida_en) if registro.recibida_en else None

        hasta_escanear = None
        if viaje.notificado_en is not None and cargada >= viaje.notificado_en:
            hasta_escanear = cargada - viaje.notificado_en

        horas_en_dty, abierto = None, False
        if viaje.salio_a_dty_en is not None:
            fin = recibida or corte
            if fin >= viaje.salio_a_dty_en:  # una liberación anterior a la salida no tiene sentido
                horas_en_dty, abierto = fin - viaje.salio_a_dty_en, recibida is None

        cruzados.append(
            replace(
                viaje,
                en_sistema=True,
                cargada_en=cargada,
                recibida_en=recibida,
                horas_hasta_escanear=hasta_escanear,
                horas_en_dty=horas_en_dty,
                dty_abierto=abierto,
            )
        )
    return cruzados


def _promedio(valores: list[timedelta]) -> timedelta | None:
    return sum(valores, timedelta()) / len(valores) if valores else None


def _viajes_de_cada_carro(viajes: list[Viaje]) -> dict[str, list[Viaje]]:
    agrupados: dict[str, list[Viaje]] = defaultdict(list)
    for viaje in viajes:
        agrupados[viaje.carro].append(viaje)
    return agrupados


def _horas_en_dty_liberado(viaje: Viaje) -> timedelta | None:
    """Las horas en DTY, solo si el carro ya se liberó (si no, la espera sigue abierta)."""
    return None if viaje.dty_abierto else viaje.horas_en_dty


def _liberados(viajes: list[Viaje]) -> list[Viaje]:
    """Los viajes de los que se conoce cuánto tiempo estuvieron en DTY."""
    return [v for v in viajes if _horas_en_dty_liberado(v) is not None]


def por_carro(viajes: list[Viaje]) -> list[FilaCarro]:
    """Una fila por carro: cuántos viajes hizo y dónde se le ve ahora (según su último viaje)."""
    filas = []
    # Un lado junto al otro: P056A, P056B, P057A, ...
    for carro, lista in sorted(_viajes_de_cada_carro(viajes).items(), key=lambda par: separar_lado(par[0])):
        ultimo = max(lista, key=lambda v: v.ultimo_movimiento)
        filas.append(
            FilaCarro(
                carro=carro,
                viajes=len(lista),
                ultimo_contenedor=ultimo.contenedor,
                calidad=ultimo.calidad,
                situacion=ultimo.situacion,
                desde_ultimo_movimiento=ultimo.desde_ultimo_movimiento,
                horas_promedio_en_rcv=_promedio([v.horas_en_rcv for v in lista if v.horas_en_rcv is not None and not v.sigue_en_rcv]),
                horas_promedio_en_wip=_promedio([v.horas_en_wip for v in lista if v.salio_a_dty and v.horas_en_wip is not None]),
                situacion_sistema=ultimo.situacion_sistema,
                horas_en_dty=ultimo.horas_en_dty,
                dty_abierto=ultimo.dty_abierto,
                horas_promedio_en_dty=_promedio([v.horas_en_dty for v in _liberados(lista)]),
            )
        )
    return filas


def horas(valor: timedelta | None) -> float | None:
    return None if valor is None else round(valor.total_seconds() / 3600, 1)


def _horas(valores: list[timedelta]) -> list[float]:
    return [v.total_seconds() / 3600 for v in valores]


def _estadisticas(titulo: str, valores: list[timedelta]) -> list[tuple[str, object]]:
    if not valores:
        return []
    h = _horas(valores)
    return [
        (f"{titulo}: promedio", round(mean(h), 1)),
        (f"{titulo}: mediana", round(median(h), 1)),
        (f"{titulo}: máximo", round(max(h), 1)),
    ]


def resumen(viajes: list[Viaje], tarimas: int = 0) -> list[tuple[str, object]]:
    """Las cifras clave, como pares (indicador, valor) para mostrarlas tal cual."""
    en_rcv = [v for v in viajes if v.sigue_en_rcv]
    en_wip = [v for v in viajes if v.sigue_en_wip and v.horas_en_wip is not None]
    en_dty = [v for v in viajes if v.dty_abierto and v.horas_en_dty is not None]
    filas: list[tuple[str, object]] = [
        ("Carros físicos (lados A y B juntos)", len({separar_lado(v.carro)[0] for v in viajes})),
        ("Lados de carro (cada A o B, como en NOW)", len({v.carro for v in viajes})),
        ("Viajes (contenedores elemento)", len(viajes)),
        ("Viajes que siguen en RCV01 (notificados, sin moverse)", len(en_rcv)),
        ("Viajes que siguen en WIP (aún no salen hacia DTY)", len(en_wip)),
        ("Viajes que ya salieron hacia DTY", sum(1 for v in viajes if v.salio_a_dty)),
    ]
    if en_rcv:
        mas_antiguo = max(en_rcv, key=lambda v: v.horas_en_rcv)
        filas.append(("El que más lleva en RCV01 sin moverse", f"{mas_antiguo.carro}: {horas(mas_antiguo.horas_en_rcv)} h"))
    if en_wip:
        mas_antiguo = max(en_wip, key=lambda v: v.horas_en_wip)
        filas.append(("El que más lleva en WIP sin salir", f"{mas_antiguo.carro}: {horas(mas_antiguo.horas_en_wip)} h"))
    # Las estadísticas solo usan los viajes ya cerrados en cada etapa: lo que sigue abierto no es una duración final.
    filas += _estadisticas("Horas en RCV01 hasta salir hacia WIP", [v.horas_en_rcv for v in viajes if v.horas_en_rcv is not None and not v.sigue_en_rcv])
    filas += _estadisticas("Horas en WIP hasta salir hacia DTY", [v.horas_en_wip for v in viajes if v.salio_a_dty and v.horas_en_wip is not None])
    filas += _estadisticas("Horas en POY (de RCV01 a salir hacia DTY)", [v.horas_en_poy for v in viajes if v.horas_en_poy is not None])

    # Lo que sale del cruce con este sistema.
    filas.append(("Viajes registrados en este sistema", f"{sum(1 for v in viajes if v.en_sistema)} de {len(viajes)}"))
    filas += _estadisticas("Horas de la notificación (016) a escanear el carro", [v.horas_hasta_escanear for v in viajes if v.horas_hasta_escanear is not None])
    filas += _estadisticas("Horas en DTY (de salir del WIP a liberar el carro)", [v.horas_en_dty for v in _liberados(viajes)])
    filas.append(("Viajes en DTY cargados en el sistema y aún sin liberar", len(en_dty)))
    if en_dty:
        mas_antiguo = max(en_dty, key=lambda v: v.horas_en_dty)
        filas.append(("El que más lleva en DTY sin liberar", f"{mas_antiguo.carro}: {horas(mas_antiguo.horas_en_dty)} h"))
    if tarimas:
        filas.append(("Movimientos de producto en tarima (sin carro)", tarimas))
    return filas


def _horas_agrupadas(viajes: list[Viaje], valor, clave) -> list[tuple[object, int, float, float]]:
    """Por cada valor de `clave(viaje)`: cuántos viajes, y las horas promedio y máxima de `valor(viaje)`.
    Solo cuentan los viajes donde `valor` existe."""
    agrupados: dict[object, list[float]] = defaultdict(list)
    for v in viajes:
        medida = valor(v)
        if medida is not None:
            agrupados[clave(v)].append(medida.total_seconds() / 3600)
    return [
        (k, len(h), round(mean(h), 1), round(max(h), 1))
        for k, h in sorted(agrupados.items(), key=lambda par: str(par[0]))
    ]


def _cerradas_en_wip(v: Viaje) -> timedelta | None:
    return v.horas_en_wip if v.salio_a_dty else None


def _calidad(v: Viaje) -> str:
    return etiqueta_calidad(v.calidad)


def horas_en_wip_por_wip(viajes: list[Viaje]) -> list[tuple[object, int, float, float]]:
    """Por el WIP del que salieron hacia DTY."""
    return _horas_agrupadas(viajes, _cerradas_en_wip, lambda v: v.wip_de_salida)


def horas_en_wip_por_calidad(viajes: list[Viaje]) -> list[tuple[object, int, float, float]]:
    return _horas_agrupadas(viajes, _cerradas_en_wip, _calidad)


def horas_en_rcv_por_calidad(viajes: list[Viaje]) -> list[tuple[object, int, float, float]]:
    return _horas_agrupadas(viajes, lambda v: None if v.sigue_en_rcv else v.horas_en_rcv, _calidad)


def horas_en_dty_por_wip(viajes: list[Viaje]) -> list[tuple[object, int, float, float]]:
    """Por el WIP del que salieron hacia DTY: cuánto tardó en liberarse el carro."""
    return _horas_agrupadas(viajes, _horas_en_dty_liberado, lambda v: v.wip_de_salida)


def armar_reporte(
    movimientos: list[Movimiento],
    registros: dict[str, Registro] | None = None,
    desplazamiento_horas: int = 0,
) -> Reporte:
    """Todo el reporte a partir de las filas de NOW y, si se tienen, los registros de este sistema."""
    corte = max((m.instante for m in movimientos), default=datetime.min)
    viajes = agrupar_viajes(movimientos, corte)
    if registros:
        viajes = cruzar_con_registros(viajes, registros, desplazamiento_horas, corte)
    tarimas = sum(1 for m in movimientos if es_tarima(m))
    tablas = [
        Tabla("Horas en RCV01 según la calidad (Qlt de NOW)", "Calidad (Qlt)", horas_en_rcv_por_calidad(viajes)),
        Tabla("Horas en WIP según el WIP del que salieron hacia DTY", "WIP", horas_en_wip_por_wip(viajes)),
        Tabla("Horas en WIP según la calidad (Qlt de NOW)", "Calidad (Qlt)", horas_en_wip_por_calidad(viajes)),
        Tabla("Horas en DTY hasta liberar el carro, según el WIP de salida", "WIP", horas_en_dty_por_wip(viajes)),
    ]
    return Reporte(corte, viajes, por_carro(viajes), tarimas, resumen(viajes, tarimas), tablas)
