# Reporte de qué ha pasado con cada carro (a partir de NOW)

Convierte la exportación de movimientos de stock de NOW en una tabla que muestra, por carro y por viaje, dónde se le ve, desde cuándo y cuánto estuvo en cada etapa (RCV01 y WIP). Es la primera versión del módulo 3 (reporte de tiempos).

## Cómo generarlo

### En la aplicación (administrador)

Entra a **Reporte**, elige el Excel de NOW y pulsa **Generar reporte**. Verás el resumen, las tablas por WIP y calidad, y una tabla por carro con búsqueda; **Descargar Excel** baja el mismo reporte. Esta forma **cruza con las cargas del sistema** (horas en DTY y horas hasta escanear). El archivo no se guarda. Detalles y decisiones en el [ADR 0009](adr/0009-modulo-de-analisis.md).

### Con el script, sin la aplicación

1. En NOW, exporta los movimientos de stock a Excel (la consulta *Stock transaction Inquiry*) con **las plantillas `016` y `202`**, tipo de artículo `PPY` y el almacén lógico `WH103`. Debe traer las columnas `Transaction date`, `Transaction time`, `Location`, `Cnr` (el carro), `Container element` y `Tmp` (la plantilla); la calidad (`Qlt`) es opcional.
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
| `202` en `RCV01` | **Salida** de recepción hacia un WIP (la hace el equipo de intermedio). |
| `202` en `WIPxx` | **Salida** de ese WIP, siempre hacia **DTY**, donde se deja de rastrear el carro. |
| `202` en `RCV02` | Salida de la recepción del producto POY de **grado B que sale del proceso de DTY** (no tiene `016`). |

La plantilla `202` es una **transferencia**: cada fila registra la salida del contenedor de la ubicación de la fila. Con las filas de un contenedor se reconstruye el recorrido y se miden tres tiempos:

```
016 (entra a RCV01) ──── horas en RCV01 ──── 202 en RCV01 ──── horas en WIP ──── 202 en WIPxx (sale hacia DTY)
└──────────────────────────────── horas en POY ────────────────────────────────┘
```

Un **viaje** es la vida de un contenedor elemento. Un mismo carro hace muchos viajes, uno por cada vez que se carga. Los carros **siempre se parten en un lado A y un lado B** (`P056A` y `P056B`): cada lado tiene su propio contenedor elemento y sus propios viajes, y el reporte los deja juntos (columnas *Carro físico* y *Lado*). Cuando DTY entrega el carro físicamente, `intermedio_poy` o `empacador_poy` lo libera en este sistema y vuelve a aparecer como disponible en el stock. Ese regreso no viene en el archivo.

**Esta lectura se comprobó con los datos:** en ningún contenedor la salida de `RCV01` es anterior a su `016` (0 casos en 1199), y de 872 casos en que un carro hace un viaje y luego otro, en ninguno el segundo empieza antes de que el primero saliera hacia DTY.

## Qué trae el Excel del reporte

| Hoja | Qué muestra |
|---|---|
| **Resumen** | Carros y viajes; cuántos siguen en `RCV01`, cuántos en WIP y cuántos ya salieron hacia DTY (con el que más lleva en cada etapa); promedio, mediana y máximo de horas en `RCV01`, en WIP y en POY; y las horas por WIP de salida y por calidad. |
| **Por carro** | Una fila por carro: viajes, último contenedor elemento, calidad, situación actual ("En RCV01…", "En WIP…" o "En DTY (salió de WIPB1)"), horas en esa situación y horas promedio en `RCV01` y en WIP. |
| **Viajes** | Una fila por contenedor elemento: cuándo se notificó (`016`), cuándo salió de recepción y de WIP, horas en cada etapa, situación y todo su recorrido. |

## Reglas que conviene conocer

- Lo que sigue abierto (en `RCV01` o en WIP) se mide hasta el **último movimiento del archivo**, que es la fecha que dice el Resumen, y **no entra en los promedios**: no es una duración final.
- Si de un contenedor no se ve su `016`, se notificó antes del rango del archivo: no se calculan sus horas en `RCV01`. Para tener más viajes completos, exporta desde una fecha anterior.
- Un contenedor con varias filas `016` (NOW parte a veces la producción en varias líneas del mismo instante) cuenta desde la primera.
- "**En DTY**" significa que NOW registró su salida de WIP y que, hasta el corte, ese carro no ha vuelto a notificarse en `RCV01`. **No dice que siga en DTY**: puede haber regresado vacío y no haberse cargado todavía. El regreso no viene en el archivo.
- Las **tarimas** (movimientos de un "carro" cuyo código empieza con `TAR`, como `TARPOY`) no son carros: se cuentan aparte en el Resumen. Son producto que se acomodó en tarima por falta de carro.
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
