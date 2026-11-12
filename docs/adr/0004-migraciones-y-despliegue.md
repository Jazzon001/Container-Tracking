# ADR 0004: Migraciones con Alembic y despliegue en Render, Vercel y Supabase

- **Estado:** Aceptada
- **Fecha:** 2026-11-12

## Contexto

Hasta ahora las tablas se creaban con `create_all` al arrancar. Eso solo crea tablas que no existen: no agrega columnas a las que ya existen, así que cada cambio del modelo obligaba a **borrar la base**. Ocurrió tres veces durante el desarrollo. En producción (Supabase) habrá datos reales de UTEXA y no se puede borrar nada. Además, el sistema se va a publicar en línea con servicios gratuitos que tienen restricciones propias (Render solo usa IPv4, el plan gratuito duerme el servicio, etc.).

## Decisión

1. **Migraciones con Alembic** como única fuente de verdad del esquema, en `backend/migrations/`. La migración `0001` crea el esquema actual. Cada cambio futuro del modelo lleva su migración.
2. **Se aplican solas al arrancar la API** (y en los scripts de administración) con `aplicar_migraciones()`. Es idempotente: si la base ya está al día, no hace nada. Se elimina `create_all`.
3. **Una prueba vigila que los modelos y las migraciones coincidan** (`compare_metadata`). Si alguien cambia un modelo y olvida la migración, el CI falla.
4. **PostgreSQL con psycopg 3.** `DATABASE_URL` acepta el formato que entrega Supabase (`postgresql://...`) y se normaliza para indicar el driver. El motor usa `pool_pre_ping` porque las bases en la nube cierran conexiones inactivas.
5. **Supabase por el *Session pooler***, no por la conexión directa: la directa usa IPv6 y Render gratuito solo IPv4.
6. **Render para la API** (descrita en `render.yaml`, con `JWT_SECRET` generado por la plataforma y `DATABASE_URL`/`CORS_ORIGINS` como secretos), **Vercel para el frontend** (`frontend/vercel.json`).
7. **La URL de la API en Angular** sale de `src/environments`: el build de producción reemplaza el archivo de desarrollo por el de producción (`fileReplacements`). Es una dirección pública, no un secreto.
8. **Las migraciones ya están probadas en SQLite**; para PostgreSQL se verificó el SQL generado en modo sin conexión (`alembic upgrade head --sql`).

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Seguir con `create_all` y borrar la base al cambiar el modelo | Imposible con datos reales en producción. |
| Migraciones manuales con scripts SQL propios | Reinventa Alembic, sin comparación automática con los modelos. |
| Aplicar las migraciones con un comando aparte en cada despliegue | Es fácil olvidarlo. El *pre-deploy command* de Render es de pago. |
| Aplicarlas en el arranque con varias instancias a la vez | Podría haber carreras. Con una sola instancia (nuestro caso) no hay riesgo; si el sistema escalara, se pasaría a un paso de despliegue dedicado. |
| Conexión directa a Supabase | Falla en Render gratuito por IPv6. |
| Variables de entorno de Angular en tiempo de compilación mediante un script | Más piezas para algo que es una URL pública; `fileReplacements` es el mecanismo estándar. |

## Consecuencias

- **Positivo:** los cambios del modelo llegan a producción sin perder datos, y el historial del esquema queda en Git.
- **Positivo:** un desarrollador nuevo arranca la API y obtiene la base lista, sin pasos extra.
- **A vigilar:** el SQL de PostgreSQL se verificó sin conexión, pero **no se ejecutó contra un PostgreSQL real** durante el desarrollo; el primer arranque en Supabase es la prueba definitiva.
- **A vigilar:** las migraciones de SQLite y PostgreSQL pueden diferir en detalles. Alembic reconstruye tablas en SQLite (`render_as_batch`) para poder alterarlas.
- **A vigilar:** los planes gratuitos tienen límites: Render duerme el servicio tras 15 minutos sin tráfico y Supabase pausa proyectos inactivos una semana.
- **A vigilar:** si el sistema crece a varias instancias, las migraciones al arrancar deben pasar a un paso de despliegue separado.

## Principios que lo justifican

- **Responsabilidad única (SOLID):** `migraciones.py` solo sabe aplicar migraciones; `database.py`, conectar.
- **Inversión de dependencias (SOLID):** la aplicación depende de `DATABASE_URL`, no de un motor concreto.
- **DRY:** una sola fuente de verdad del esquema y una sola configuración de la URL de la API.
- **KISS y YAGNI:** nada de orquestación de despliegues; un solo plano de Render y un solo `vercel.json`.
