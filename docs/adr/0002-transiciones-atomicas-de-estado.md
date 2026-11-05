# ADR 0002: Capa de servicio y transiciones de estado atómicas

- **Estado:** Aceptada
- **Fecha:** 2026-11-05

## Contexto

Un carro pasa por estados (`disponible`, `en_transito`, `en_mantenimiento`) y el sistema debe garantizar que **un carro no se asigne dos veces a la vez** cuando varios usuarios operan simultáneamente. Además, las reglas de negocio no deben mezclarse con el código HTTP, para poder probarlas y cambiarlas por separado.

## Decisión

1. **Capa de servicio.** Las reglas viven en `app/services/`, como funciones sin conocimiento de HTTP. Los routers solo reciben la petición, llaman al servicio y devuelven la respuesta.
2. **Errores de negocio propios** (`CarroNoEncontrado`, `EstadoInvalido`, `ContenedorEnUso`). Un único manejador en `main.py` los traduce a códigos HTTP (404 y 409).
3. **Transición atómica.** Para cambiar el estado de un carro se usa un `UPDATE ... WHERE estado = <estado esperado>` y se revisa cuántas filas cambió. Si fueron cero, otro usuario ya lo cambió (o el carro no existe) y se rechaza la operación. La función `transicionar_estado` concentra esta lógica para todas las operaciones.
4. **Restricciones únicas en la base de datos** (`numero` y `contenedor_elemento`), como segunda barrera contra duplicados.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Leer el estado, validar con un `if` y luego guardar | Dos peticiones simultáneas pueden pasar la validación a la vez y asignar el mismo carro dos veces. |
| Bloqueos explícitos de fila (`SELECT ... FOR UPDATE`) | SQLite no los soporta de la misma forma; el `UPDATE` condicional funciona en ambos motores. |
| Clases por regla o patrón de máquina de estados | Hoy hay pocas transiciones; sería sobreingeniería (YAGNI). |

## Consecuencias

- **Positivo:** la concurrencia queda resuelta en un solo lugar y en la base de datos, no en el código de la aplicación.
- **Positivo:** las reglas se prueban sin levantar HTTP y los routers se mantienen delgados.
- **A vigilar:** si las transiciones crecen mucho (más estados y roles), habrá que revisar si conviene modelarlas de forma más explícita.

## Principios que lo justifican

- **Responsabilidad única (SOLID):** router, servicio y modelo cambian por razones distintas.
- **DRY:** `transicionar_estado` se reutiliza en carga, entrega y mantenimiento.
- **KISS y YAGNI:** funciones simples en lugar de jerarquías de clases.
