# ADR 0008: Perfiles por proceso y alcance de los carros

- **Estado:** Aceptada
- **Fecha:** 2026-11-16
- **Relacionada con:** [ADR 0003](0003-autenticacion-jwt-y-roles.md) (autenticación y roles), que esta decisión amplía.

## Contexto

Hasta ahora había cinco roles generales (POY, Almacén, DTY, Twisting y Administrador) y cualquier usuario veía los carros de todos los procesos. El cliente necesita que cada persona vea solo los carros de su proceso y que cada puesto haga solo lo suyo: quien **carga** un carro (lo saca del stock disponible) no es quien lo **libera** (lo devuelve al stock).

## Decisión

1. **Doce perfiles**, ocho nuevos y los anteriores (ver más abajo), con una sola tabla que los describe: `backend/app/permisos.py`. Cada perfil tiene un **proceso** (de qué carros) y tres permisos:

   | Perfil | Proceso | Cargar | Liberar | Mantenimiento |
   |---|---|---|---|---|
   | Digitador POY | POY | sí | sí | sí |
   | Intermedio POY, Empacador POY | POY | no | sí | sí |
   | Digitador DTY | DTY | sí | sí | sí |
   | Empacador DTY, Twisting | DTY | no | sí | sí |
   | Digitador Twisting | Twisting | sí | sí | sí |
   | Empacador Twisting | Twisting | no | sí | sí |
   | Administrador | todos | sí | sí | sí |

   El **digitador** ve el menú completo de sus carros; los demás, todo menos *Cargar*. El perfil **Twisting** pertenece a DTY: libera los carros de DTY, porque es quien consume su producto.
2. **El alcance lo aplica el servidor**, no la pantalla: la lista de carros y el historial solo traen los del proceso del perfil; pedir un carro de otro proceso responde **404**, como si no existiera, para no revelar qué carros hay. Cargar, liberar y registrar mantenimiento sobre un carro de otro proceso también responde 404. Si el perfil no tiene el permiso, responde **403** (igual que antes).
3. **"Liberar" es la operación que ya existía** (`POST /carros/{id}/entrega`, pantalla *Recibir*): no se creó una operación nueva ni se cambió su ruta ni su texto. Lo único que cambió es quién puede hacerla.
4. **Se conservan los perfiles anteriores** para no romper a los usuarios ya creados (entre ellos el usuario demo del entregable 11):
   - `poy` y `dty` se comportan como *Digitador POY* y *Digitador DTY*.
   - `twisting` es el perfil *Twisting* descrito arriba (antes solo consultaba).
   - `almacen` conserva exactamente lo que hacía (ve todos los carros y los recibe). No pertenece a ningún proceso; queda pendiente decidir si se retira cuando haya perfiles de empacador e intermedio en uso.
5. **Migración `0004`:** solo agrega siete valores al tipo `rol`. No cambia ni borra datos. En PostgreSQL usa `ALTER TYPE ... ADD VALUE IF NOT EXISTS` fuera de la transacción; en SQLite ensancha la columna. Se probó contra PostgreSQL 18 real partiendo de las migraciones anteriores, con un usuario ya creado y las políticas RLS activas.
6. **El frontend tiene una copia de la tabla** (`perfiles.ts`) solo para mostrar u ocultar opciones del menú y de las rutas. Una prueba por cada perfil, escrita a mano en los dos lados, evita que se desincronicen. Si una cambia, la otra también.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Que el login devuelva los permisos y el frontend no tenga tabla | Si Vercel publica antes que Render, o al revés, el menú se rompe durante el despliegue. Con la tabla en el frontend, funciona con cualquier combinación de versiones. |
| Dos columnas: área y función (`rol` + `perfil`) | Dos fuentes de verdad para decir quién es alguien, y obliga a cambiar el modelo y todos los usuarios. Un solo valor por usuario es más simple (KISS). |
| Renombrar los roles anteriores con una migración de datos | Más riesgo (modifica usuarios en producción) sin ganancia: un alias en la tabla de permisos cuesta una línea. |
| Tabla de permisos editable desde la base de datos (RBAC completo) | Hoy hay doce perfiles fijos y reglas claras; sería sobreingeniería (YAGNI), igual que en el ADR 0003. |
| Responder 403 al tocar un carro de otro proceso | Confirmaría que ese carro existe. Con 404 el perfil no puede explorar los carros ajenos. |

## Consecuencias

- **Positivo:** cada persona ve solo sus carros y solo ve las opciones de su puesto; las reglas de quién puede qué se leen en un solo archivo y se prueban perfil por perfil (`test_permisos.py` y `test_alcance_por_proceso.py`).
- **Positivo:** nada de lo anterior cambia de lugar: ni las rutas, ni el login, ni las cabeceras de seguridad, ni la cookie de sesión, ni el service worker.
- **A vigilar:** el usuario `poy` (anterior) ahora también puede liberar carros de POY, y `dty` puede cargar y liberar carros de DTY, porque se equiparan al digitador. Antes `poy` solo cargaba y `dty` solo registraba mantenimiento.
- **A vigilar:** el perfil *Twisting* ahora puede liberar carros de DTY y registrar su mantenimiento; antes solo consultaba.
- **A vigilar:** quien carga un carro y quien lo libera ahora son perfiles distintos, pero el sistema no exige que sean personas distintas. Si hiciera falta (segregación de funciones), sería una regla nueva.
- **Para volver atrás:** la migración `0004` es inofensiva si se deja (los valores sin usar no estorban a la versión anterior). Antes de volver al código anterior hay que cambiar a los usuarios que tengan un perfil nuevo a uno anterior.

## Cómo crear usuarios con los perfiles nuevos

Con el administrador, por `POST /usuarios` (en `/docs`) o desde la terminal con `python -m scripts.crear_usuario <usuario> <perfil>`. Los perfiles válidos son: `digitador_poy`, `intermedio_poy`, `empacador_poy`, `digitador_dty`, `empacador_dty`, `twisting`, `digitador_twt`, `empacador_twt`, además de `admin` y los anteriores.

## Principios aplicados

- **SOLID (responsabilidad única):** la tabla de permisos es el único lugar que decide quién puede qué; las rutas solo preguntan.
- **KISS y YAGNI:** un valor por usuario y una tabla fija, sin un sistema genérico de permisos.
- **DRY:** el alcance se aplica en una dependencia (`carro_accesible`) y no se repite en cada ruta.
