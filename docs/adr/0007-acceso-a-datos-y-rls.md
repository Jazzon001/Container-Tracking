# ADR 0007: La API como única puerta a los datos, con seguridad por filas que niega el acceso directo

- **Estado:** Aceptada
- **Fecha:** 2026-11-13

## Contexto

La base de datos está en Supabase (PostgreSQL). Supabase expone por defecto las tablas del esquema `public` a través de su propia API de datos, con claves públicas (`anon`). Este sistema **no usa esa API**: toda la lectura y escritura pasa por la API propia (FastAPI), que valida el token y el rol de cada usuario (ADR 0003).

Eso deja una puerta que nadie vigila: si alguien obtuviera la clave pública del proyecto, podría intentar leer o escribir las tablas directamente, saltándose los roles del sistema. Los datos son operativos de una planta y las reglas de negocio (un carro no se asigna dos veces) viven en la API.

## Decisión

1. **La API propia es la única vía de acceso a los datos.**
2. **Se activa la seguridad por filas (RLS)** en todas las tablas del esquema, y cada una declara una política que **niega cualquier lectura o escritura** (`FOR ALL USING (false) WITH CHECK (false)`), con el nombre `<tabla>_sin_acceso_directo`.
3. **La aplicación no se ve afectada:** se conecta con el rol dueño de las tablas, que no está sujeto a las políticas. Las reglas por rol de la API (POY, Almacén, DTY, Twisting, Administrador) siguen siendo el control de acceso de los usuarios.
4. Se aplica con una **migración** (`0003`), que no hace nada en SQLite (donde no existe esta función).
5. **Se exporta el esquema real de la base** (tablas, llaves, índices, relaciones, filas y políticas) a `docs/db-export.json` con `python -m scripts.exportar_bd`, para poder revisarlo y auditarlo. El script se niega a exportar una base que no sea PostgreSQL, para no publicar por error la base local.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Políticas por usuario basadas en la autenticación de Supabase (`auth.uid()`) | Obligaría a usar Supabase Auth, que se descartó en el ADR 0003 para no atar el sistema a un proveedor. |
| No hacer nada (dejar las tablas sin RLS) | Deja abierta una puerta innecesaria; el propio panel de Supabase la marca como riesgo. |
| Quitar los permisos a los roles públicos (`REVOKE`) | Logra algo parecido, pero RLS deja la intención escrita en la base y la política visible y exportable. |
| Desactivar la API de datos desde el panel de Supabase | Es un ajuste manual fuera del repositorio, fácil de revertir sin querer y sin rastro en las migraciones. |

## Consecuencias

- **Positivo:** defensa en profundidad: aunque se filtrara la clave pública del proyecto, las tablas no se pueden leer ni escribir por esa vía.
- **Positivo:** la política es parte del código (migración), se aplica sola en cada entorno de PostgreSQL y se puede auditar con el export.
- **A vigilar:** si algún día la aplicación se conectara con un rol que **no** sea el dueño de las tablas, vería las tablas vacías sin error. Si eso ocurre, hay que revisar con qué rol se conecta.
- **A vigilar:** cualquier tabla nueva debe incluir su propia política en su migración; una prueba del export lo muestra, pero no lo impide.
- **Limitación conocida:** las políticas son "todo o nada" (niegan a todos los roles que no son el dueño). No hay políticas finas por usuario porque el control fino vive en la API.
- **Limitación conocida:** la migración se comprobó en SQLite (no hace nada) y mirando el SQL de PostgreSQL que genera, no ejecutándola en un PostgreSQL de pruebas. El primer arranque en Supabase es la prueba real.

## Principios que lo justifican

- **Defensa en profundidad y mínimo privilegio:** cada capa niega por defecto lo que no necesita.
- **Responsabilidad única (SOLID):** los usuarios dependen de la API; la base solo habla con la API.
- **KISS y YAGNI:** una política simple de "negar todo" en lugar de un sistema de políticas finas que nadie necesita.
