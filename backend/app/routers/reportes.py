import os

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencias import requiere_permiso
from app.errores import ArchivoDemasiadoGrande
from app.schemas import FilaCarroOut, FilaTablaOut, IndicadorOut, ReporteOut, TablaOut
from app.services.reporte_excel import escribir_excel
from app.services.reporte_tiempos import Reporte, etiqueta_calidad, horas
from app.services.reportes import generar_reporte

# Solo quien tiene el permiso `reportes` (el administrador) puede subir el archivo: el permiso se
# comprueba antes de leer el cuerpo de la petición.
router = APIRouter(prefix="/reportes", tags=["reportes"], dependencies=[Depends(requiere_permiso("reportes"))])

LIMITE_MB = 10
TIPO_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
# La diferencia de la planta con UTC (NOW guarda la hora local; este sistema, UTC). México central y
# Honduras no tienen horario de verano: -6 todo el año. Se puede cambiar con NOW_UTC_OFFSET_HORAS.
DESPLAZAMIENTO_POR_OMISION = -6


def desplazamiento_de_now() -> int:
    try:
        return int(os.environ.get("NOW_UTC_OFFSET_HORAS", DESPLAZAMIENTO_POR_OMISION))
    except ValueError:
        return DESPLAZAMIENTO_POR_OMISION


async def archivo_subido(request: Request) -> bytes:
    """El cuerpo de la petición (el Excel tal cual), sin pasar de LIMITE_MB. Se corta en cuanto se pasa,
    sin leer el resto."""
    limite = LIMITE_MB * 1024 * 1024
    declarado = request.headers.get("content-length")
    if declarado and declarado.isdigit() and int(declarado) > limite:
        raise ArchivoDemasiadoGrande(LIMITE_MB)
    partes, total = [], 0
    async for parte in request.stream():
        total += len(parte)
        if total > limite:
            raise ArchivoDemasiadoGrande(LIMITE_MB)
        partes.append(parte)
    return b"".join(partes)


def _a_salida(reporte: Reporte) -> ReporteOut:
    return ReporteOut(
        corte=f"{reporte.corte:%d/%m/%Y %H:%M}",
        resumen=[IndicadorOut(indicador=i, valor=v) for i, v in reporte.resumen],
        tablas=[
            TablaOut(
                titulo=t.titulo,
                columna=t.columna,
                filas=[FilaTablaOut(clave=str(c), viajes=n, promedio=p, maximo=m) for c, n, p, m in t.filas],
            )
            for t in reporte.tablas
        ],
        carros=[
            FilaCarroOut(
                carro_fisico=c.carro_fisico,
                lado=c.lado,
                carro=c.carro,
                viajes=c.viajes,
                ultimo_contenedor=c.ultimo_contenedor,
                calidad=etiqueta_calidad(c.calidad),
                situacion=c.situacion,
                horas_en_situacion=horas(c.desde_ultimo_movimiento),
                horas_promedio_en_rcv=horas(c.horas_promedio_en_rcv),
                horas_promedio_en_wip=horas(c.horas_promedio_en_wip),
                situacion_sistema=c.situacion_sistema,
                horas_en_dty=horas(c.horas_en_dty),
                dty_abierto=c.dty_abierto,
                horas_promedio_en_dty=horas(c.horas_promedio_en_dty),
            )
            for c in reporte.carros
        ],
    )


@router.post("/carros", response_model=ReporteOut)
def reporte_de_carros(contenido: bytes = Depends(archivo_subido), db: Session = Depends(get_db)):
    """El reporte de tiempos de los carros a partir del Excel de movimientos de NOW (el cuerpo de la
    petición), cruzado con las cargas de este sistema. El archivo no se guarda."""
    return _a_salida(generar_reporte(db, contenido, desplazamiento_de_now()))


@router.post("/carros/excel")
def reporte_de_carros_en_excel(contenido: bytes = Depends(archivo_subido), db: Session = Depends(get_db)):
    """Lo mismo, pero como un archivo Excel para descargar."""
    reporte = generar_reporte(db, contenido, desplazamiento_de_now())
    return Response(
        content=escribir_excel(reporte),
        media_type=TIPO_XLSX,
        headers={"Content-Disposition": 'attachment; filename="reporte_carros.xlsx"'},
    )
