# ADR 0009: Módulo de análisis: el Excel de NOW cruzado con las cargas del sistema

- **Estado:** Aceptada
- **Fecha:** 2026-11-16

## Contexto

El módulo 3 del proyecto pide un reporte del tiempo que cada contenedor elemento estuvo en cada etapa, a partir de un Excel descargado de NOW y de los registros propios. NOW deja de rastrear el carro cuando sale hacia DTY, y justamente por eso existe este sistema: cuando intermedio o empaque libera el carro con su contenedor elemento se sabe cuánto tiempo estuvo en DTY.

## Decisión

1. **Cómo se lee NOW** (ver `docs/REPORTE-CARROS.md`): la plantilla `016` deja el carro en `RCV01` (entrada) y la `202` es una transferencia donde cada fila es la **salida** de esa ubicación (de `RCV01` hacia un WIP, o de un WIP hacia DTY). Se comprobó con los datos: ninguna salida de `RCV01` es anterior a su `016`.
2. **`RCV02`** es la última localización antes de que empaque libere el carro (ahí llega el producto de grado B que sale de DTY): una fila `202` en `RCV02` marca que el viaje ya volvió de DTY y que falta la liberación de empaque. No cuenta como recepción ni altera las horas en `RCV01` o en WIP.
3. **Un viaje por contenedor elemento**, y un carro físico se parte siempre en lado A y lado B: el reporte los deja juntos. Calidad `Qlt`: 1 = AA, 2 = A, 3 = B.
4. **Tres tiempos con NOW** (horas en `RCV01`, en WIP y en POY) y **dos con este sistema**: de la notificación (`016`) al escaneo, y de la **salida del WIP a la liberación** del carro (horas en DTY). Lo que sigue abierto se mide hasta el último movimiento del archivo y **no entra en los promedios**.
5. **La lógica es pura** (`app/services/reporte_tiempos.py`): recibe movimientos y registros y devuelve el reporte; no conoce Excel, HTTP ni la base. La lectura y escritura del Excel están en `reporte_excel.py`, y el cruce con la base en `reportes.py`.
6. **`POST /reportes/carros`** (JSON) y **`POST /reportes/carros/excel`** (descarga). El Excel viaja **tal cual en el cuerpo** de la petición (`application/octet-stream`), no como formulario multipart: así no se agrega la dependencia `python-multipart` ni hay que regenerar el archivo de dependencias fijadas del CI.
7. **Solo el administrador** (nuevo permiso `reportes`, en las dos tablas de perfiles). El permiso se comprueba **antes** de leer el archivo.
8. **El archivo se trata como no confiable:** límite de 10 MB (se corta en cuanto se pasa, también si no se declara el tamaño), revisión del tamaño ya descomprimido (contra archivos comprimidos que explotan), límite de 200 000 filas y errores claros (422) en vez de caídas. Se procesa en memoria y **no se guarda**.
9. **La hora:** NOW guarda la hora local de la planta y este sistema, UTC. El cruce convierte con un desplazamiento, `NOW_UTC_OFFSET_HORAS`, que por omisión es **-6** (México central y Honduras no tienen horario de verano). **Si la planta está en otra zona, hay que cambiar esa variable en Render**; si no, las horas en DTY saldrían corridas.
10. **Pantalla `Reporte`** (solo administrador): elige el Excel, genera el reporte (resumen, tablas por WIP y calidad, y una tabla por carro con búsqueda) y lo descarga como Excel. La ruta `/reporte` se agregó a las reglas de `vercel.json` como las demás pantallas privadas (sin sesión redirige al login) y a `robots.txt`.
11. **No se tocó ninguna cabecera de seguridad** ni la política de contenido: la descarga se hace con una dirección `blob:` creada en el navegador.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Subir el archivo como formulario (multipart) | Obliga a agregar `python-multipart` y a regenerar las dependencias fijadas con hashes. Enviar el archivo en el cuerpo es igual de simple y no cambia nada del despliegue. |
| Guardar el Excel y los resultados en la base | Datos reales de UTEXA en la base sin necesidad: el reporte se calcula en memoria en menos de un segundo. Se puede guardar después si hace falta comparar fechas (YAGNI). |
| Medir "fuera de POY" con las filas de NOW (de salir hacia DTY a la siguiente `016`) | Mezcla la estancia en DTY con el regreso y con lo que tarda POY en volver a cargar el carro. El dato bueno es el de la liberación en este sistema. |
| Que intermedio y empaque también vean el reporte | Es un análisis para quien administra. Es un permiso aparte, así que abrirlo después es cambiar una línea en cada tabla de perfiles. |
| Convertir la hora con zonas horarias (`zoneinfo`) | Exige el paquete `tzdata` en Windows. Un desplazamiento fijo basta mientras la planta no tenga horario de verano. |

## Consecuencias

- **Positivo:** el tiempo en DTY, que NOW no puede dar, sale de los registros propios. Cuanto más se use el sistema (escanear al cargar y liberar con el contenedor elemento), más viajes completos tendrá el reporte.
- **A vigilar:** hoy casi ningún viaje del Excel tiene registro en el sistema (en las pruebas, 1 de 1472): las horas en DTY crecerán conforme se use. Un viaje sin registro no tiene horas en DTY.
- **A vigilar:** el cruce se hace por contenedor elemento. Si un mismo código se cargara más de una vez, se toma la carga más reciente.
- **A vigilar:** la zona horaria (punto 9).
- **Sigue pendiente:** la llegada a `RCV01` solo se conoce por la `016`, y el regreso del carro desde DTY solo se conoce por la liberación.

## Principios aplicados

- **SRP:** cálculo, Excel y base de datos separados; el router solo recibe, delega y responde.
- **KISS y YAGNI:** un solo formato de entrada, sin tablas nuevas, sin migraciones y sin dependencias nuevas.
- **Seguridad:** permiso antes que lectura, límites de tamaño y de filas, archivo en memoria y errores controlados.
