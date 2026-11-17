# Reporte de qué ha pasado con cada carro (a partir de NOW)

Convierte la exportación de movimientos de stock de NOW en una tabla que muestra, por carro y por viaje, dónde se le ve, desde cuándo y cuánto estuvo en cada etapa (RCV01 y WIP). Es la primera versión del módulo 3 (reporte de tiempos).

## Cómo generarlo

### En la aplicación (administrador)

Entra a **Reporte**, elige el Excel de NOW y pulsa **Generar reporte**. Verás el resumen, las tablas por WIP y calidad, y una tabla por carro con búsqueda; **Descargar Excel** baja el mismo reporte. Esta forma **cruza con las cargas del sistema** (horas en DTY y horas hasta escanear). El archivo no se guarda. Detalles y decisiones en el [ADR 0009](adr/0009-modulo-de-analisis.md).

### Con el script, sin la aplicación

1. En NOW, exporta los movimientos de stock a Excel (la consulta *Stock transaction Inquiry*) con **las plantillas `016`, `202` y `119`**, tipo de artículo `PPY` y el almacén lógico `WH103`. Si exportas sin el filtro de tipo de artículo, el archivo trae también carros de otros procesos (`D…`, `T…`, `DT…`): el reporte los cuenta aparte y no los analiza. Debe traer las columnas `Transaction date`, `Transaction time`, `Location`, `Cnr` (el carro), `Container element` y `Tmp` (la plantilla); la calidad (`Qlt`) es opcional.
2. Copia el archivo a `datos/movimientos_now.xlsx`. La carpeta `datos/` no se sube a GitHub.
3. Desde `backend`, con el entorno virtual activo:

```powershell
python -m scripts.reporte_carros
```

Escribe `datos/reporte_carros.xlsx`. El script no recibe rutas por argumentos: siempre lee y escribe en esos lugares, y **no cruza con las cargas del sistema** (para eso, la pantalla Reporte). Sin la columna `Tmp`, todo se trata como `202` y no se pueden medir las horas en `RCV01`.

## Cómo se lee el archivo de NOW

| Plantilla y ubicación | Significa |
|---|---|
| `016` en `RCV01` | **Entrada**: el ERP registra la producción y deja el carro puesto en `RCV01`. Se genera el contenedor elemento, el código de barras que se escanea en este sistema para registrar el carro como cargado. |
| `119` | **Anulación** de una notificación: la negativa de la `016`, cuando el operador se equivocó al registrar el carro. Ese contenedor elemento **no cuenta como viaje** y se lista en la hoja *Anulados*. |
| `202` en `RCV01` | **Salida** de recepción hacia un WIP (la hace el equipo de intermedio). |
| `202` en `WIPxx` | **Salida** de ese WIP, siempre hacia **DTY**, donde se deja de rastrear el carro. |
| `202` en `RCV02` | Salida de la **última localización antes de que empaque libere el carro**: ahí llegan los carros con producto POY de **grado B que sale del proceso de DTY**. No tiene `016`; el viaje ya había salido de su WIP hacia DTY. |

La plantilla `202` es una **transferencia**: cada fila registra la salida del contenedor de la ubicación de la fila. Con las filas de un contenedor se reconstruye el recorrido y se miden tres tiempos:

```
016 (entra a RCV01) ──── horas en RCV01 ──── 202 en RCV01 ──── horas en WIP ──── 202 en WIPxx (sale hacia DTY)
└──────────────────────────────── horas en POY ────────────────────────────────┘
```

Un **viaje** es la vida de un contenedor elemento. Un mismo carro hace muchos viajes, uno por cada vez que se carga. Los carros **siempre se parten en un lado A y un lado B** (`P056A` y `P056B`): cada lado tiene su propio contenedor elemento y sus propios viajes, y el reporte los deja juntos (columnas *Carro físico* y *Lado*). Cuando DTY entrega el carro físicamente, `intermedio_poy` o `empacador_poy` lo libera en este sistema y vuelve a aparecer como disponible en el stock. Ese regreso no viene en el archivo.

**Esta lectura se comprobó con los datos:** en ningún contenedor la salida de `RCV01` es anterior a su `016` (0 casos en 1199), y de 872 casos en que un carro hace un viaje y luego otro, en ninguno el segundo empieza antes de que el primero saliera hacia DTY.

## Qué trae el Excel del reporte

Está pensado para leerse sin explicación: **cada fila es un contenedor elemento** (cada vez que se carga un carro), con la etapa en que está y las horas que pasó en cada una. En el Excel no se usa la palabra "viaje".

| Hoja | Qué muestra |
|---|---|
| **Resumen** | Cuántos contenedores hay y dónde están ahora; una tabla con las horas promedio, mediana y máximo de cada etapa; **los 10 que más llevan esperando** en RCV01, en WIP y en DTY sin liberarse; y las horas por WIP de salida y por calidad. |
| **Contenedores** | **La hoja principal.** Una fila por contenedor elemento: carro, lado, calidad, **dónde está ahora** (`1 · En RCV01`, `2 · En WIP`, `3 · En DTY` o `4 · Salió de RCV02`), desde cuándo y **cuántas horas lleva ahí**; después, la fecha de cada etapa (entró a RCV01, salió de RCV01, salió del WIP) y las **horas en RCV01, en WIP y en POY**; y lo que registró la aplicación (cuándo se cargó, cuándo se liberó, horas en DTY). |
| **Carros** | Una fila por lado de carro: cuántas veces se cargó (en NOW y en la aplicación), dónde está su último contenedor y los promedios de horas. |
| **Anulados** | Los contenedores anulados con la plantilla `119` (carro, cuándo se notificó, cuándo se anuló y cuánto tardó el operador en corregirlo). |
| **Cómo leer** | Una explicación corta de cada columna y de cómo se lee NOW. |

Las horas de una etapa solo se llenan cuando la etapa **ya terminó**. Lo que sigue en curso se ve en *Lleva ahí (horas)*. Así, un promedio nunca mezcla duraciones finales con esperas que siguen abiertas.

## Reglas que conviene conocer

- **Solo se analiza el flujo de POY:** los carros cuyo código empieza con `P` (`P056A`). Los de otros procesos (`D064`, `T020`, `DT07`…) tienen otro flujo, con ubicaciones como `WIPE` y `K01`, que este reporte todavía no modela: se cuentan en el Resumen y no entran en ninguna tabla ni promedio.
- **Un contenedor con una `119` no es un viaje**, aunque tenga otras filas. Una `119` cuya `016` fue anterior al archivo también lo excluye.

- Lo que sigue abierto (en `RCV01` o en WIP) se mide hasta el **último movimiento del archivo**, que es la fecha que dice el Resumen, y **no entra en los promedios**: no es una duración final.
- Si de un contenedor no se ve su `016`, se notificó antes del rango del archivo: no se calculan sus horas en `RCV01`. Para tener más viajes completos, exporta desde una fecha anterior.
- Un contenedor con varias filas `016` (el carro lleva más de un lote, y NOW registra la producción en varias líneas del mismo instante) cuenta como una sola entrada, desde la primera. Es normal, aunque no pasa todos los días.
- "**En DTY**" significa que NOW registró su salida de WIP y que, hasta el corte, ese carro no ha vuelto a notificarse en `RCV01`. **No dice que siga en DTY**: puede haber regresado vacío y no haberse cargado todavía. El regreso no viene en el archivo.
- Las **tarimas** (movimientos de un "carro" cuyo código empieza con `TAR`, como `TARPOY`, confirmado) no son carros: se cuentan aparte en el Resumen. Son producto que se acomodó en tarima por falta de carro.
- **Calidad (`Qlt` de NOW):** `1` es calidad **AA**, `2` es **A** y `3` es **B**. Empaque la empaca como A, o calidad la revisa y la deja como `3` (B), si aplica. La calidad no cambia dentro de un mismo contenedor elemento en el archivo probado.

## Qué falta

- **Más viajes registrados en el sistema.** El cruce ya está hecho, pero depende de que se escanee cada contenedor elemento al cargar y de que intermedio o empaque libere el carro con él. Un viaje sin registro no tiene horas en DTY.
- **La zona horaria.** El cruce supone que la planta está en UTC-6 todo el año. Si no es así, hay que cambiar `NOW_UTC_OFFSET_HORAS` en Render.

## Cómo se cruza con este sistema

Por contenedor elemento, con la tabla `cargas` (el código que escaneó el digitador y la liberación que registró intermedio o empaque):

- **Horas hasta escanear:** de la notificación (`016`) a que se escaneó el contenedor elemento al cargar el carro.
- **Horas en DTY:** de la salida del WIP en NOW a la **liberación** en este sistema. Si el carro se cargó en el sistema pero todavía no se libera, las horas corren hasta el último movimiento del archivo y se marcan "sin liberar" (no entran en los promedios).
- Si la liberación fuera anterior a la salida del WIP, o el escaneo anterior a la `016`, no se mide (sería un dato incoherente).

## Principios aplicados

- **SRP:** `app/services/reporte_tiempos.py` calcula y no conoce Excel; `scripts/reporte_carros.py` lee y escribe el archivo.
- **KISS y YAGNI:** sin tablas nuevas, sin migraciones y sin pantalla hasta que haga falta; las pruebas usan datos inventados, nunca datos de UTEXA.
