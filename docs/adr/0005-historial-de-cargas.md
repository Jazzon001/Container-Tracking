# ADR 0005: Historial de cargas como tabla propia

- **Estado:** Aceptada
- **Fecha:** 2026-11-12

## Contexto

Cuando POY carga un carro, el sistema guarda el código del contenedor elemento en el propio carro (`Carro.contenedor_elemento`). Ese código es **único** mientras el carro viaja, y **se borra al recibirlo** para poder reutilizarlo en el siguiente viaje. Con solo eso, el sistema olvida qué contenedor iba en qué carro y cuánto tardó.

El cliente necesita justamente eso: el módulo 3 del proyecto es un reporte del tiempo que cada contenedor elemento estuvo en cada proceso, para encontrar cuellos de botella. Sin un historial, los datos de los primeros meses de uso no se podrían recuperar después.

## Decisión

1. Una tabla **`cargas`**, un registro por viaje: carro, contenedor elemento, `cargada_en` y `recibida_en` (nulo mientras el carro sigue en tránsito).
2. **El estado actual no cambia:** `Carro` sigue diciendo dónde está el carro y qué contenedor lleva ahora. `Carga` es el registro de lo que ya pasó. Cada tabla responde una pregunta distinta.
3. **Se escribe en la misma transacción** que el cambio de estado: al cargar se abre el registro y al recibir se cierra, o se guardan ambos o ninguno. El instante es el mismo que `estado_desde`, calculado una sola vez.
4. **El contenedor elemento no es único en `cargas`**, porque un código se vuelve a usar en otros viajes. Solo se indexa para buscar.
5. **Se consulta con `GET /cargas`** (filtros exactos por carro y por contenedor, y un `limite` de 100 por defecto y 1000 como máximo) y la pantalla **Historial**. Cualquier rol con sesión puede consultarlo.
6. **La migración `0002` conserva los datos existentes:** los carros que ya iban en tránsito reciben un registro abierto, con su `estado_desde` como fecha de carga.
7. **Recibir un carro sin registro abierto no es un error** (datos anteriores al historial).

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| No borrar `contenedor_elemento` al recibir | Se rompe la unicidad (dos carros podrían tener el mismo código en momentos distintos) y no se podría reutilizar el código. |
| Un registro de eventos genérico (un "diario" de todo lo que pasa) | Es más flexible pero hoy no hay otro consumidor; sobreingeniería (YAGNI). Se puede agregar cuando haga falta. |
| Calcular los tiempos solo con el Excel de NOW | NOW deja de mostrar el carro al consumirse el producto; justamente por eso existe este sistema. |
| Un índice único parcial ("un solo registro abierto por carro") | El cambio de estado atómico ya lo garantiza; el índice sería una segunda barrera sin un caso que lo exija hoy. |

## Consecuencias

- **Positivo:** los datos de trazabilidad se acumulan desde el primer día y alimentarán el reporte de tiempos (módulo 3).
- **Positivo:** responde preguntas del negocio ya hoy: ¿cuánto tardó este carro en volver?, ¿dónde estuvo este contenedor?
- **A vigilar:** la tabla crece con cada viaje (más de mil carros, varios viajes al mes). Por eso la consulta tiene límite; si el volumen lo pide, habrá que paginar o archivar.
- **A vigilar:** solo cubre el tramo POY → Almacén. Las etapas de NOW (liberación de calidad, custodia, entrada a DTY) llegarán con el Excel del módulo 3.
- **Limitación conocida:** no se registra **quién** cargó o recibió. Si fuera un requisito de trazabilidad, se agregaría el usuario a cada registro con otra migración.

## Principios que lo justifican

- **Responsabilidad única (SOLID):** `Carro` modela el presente y `Carga` el pasado.
- **DRY:** el instante del cambio se calcula una sola vez y se usa para el estado y para el historial.
- **YAGNI:** sin eventos genéricos ni índices que nadie necesita todavía.
