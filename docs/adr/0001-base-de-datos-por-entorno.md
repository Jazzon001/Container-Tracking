# ADR 0001: Base de datos configurable por entorno

- **Estado:** Aceptada
- **Fecha:** 2026-11-05

## Contexto

El sistema necesita una base de datos relacional con buena concurrencia (al menos 4 usuarios simultáneos y sin asignar un carro dos veces). Durante el desarrollo y en el CI se necesitan pruebas rápidas que no dependan de un servicio externo ni toquen datos reales. En producción se usará Supabase, que ofrece PostgreSQL administrado con plan gratuito.

## Decisión

- La aplicación lee la URL de conexión de la variable de entorno `DATABASE_URL`.
- Si no está definida, usa **SQLite local** (`container_tracking.db`).
- Las pruebas usan **SQLite en memoria**, nueva en cada prueba.
- En producción, `DATABASE_URL` apunta a **Supabase (PostgreSQL)**. Supabase se usa solo como base de datos, no para autenticación.
- El acceso a datos se hace con SQLAlchemy, que abstrae las diferencias entre ambos motores.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| PostgreSQL local para desarrollo | Exige instalar y mantener un servidor en cada equipo y en el CI, sin beneficio hoy. |
| Solo SQLite en todos los entornos | No ofrece la concurrencia que pide el requisito en producción. |
| Base de datos gratuita de Render | Caduca a los 30 días. |

## Consecuencias

- **Positivo:** pruebas rápidas, CI sin servicios externos y cambio de entorno sin tocar código.
- **Positivo:** la cadena de conexión nunca se versiona; vive solo en variables de entorno.
- **A vigilar:** SQLite y PostgreSQL no se comportan idéntico en todo. Antes del despliegue conviene correr las pruebas también contra PostgreSQL.
- **Pendiente:** hoy las tablas se crean con `create_all`. Al pasar a producción habrá que decidir cómo versionar los cambios del esquema (por ejemplo, con migraciones).

## Principios que lo justifican

- **KISS:** sin infraestructura extra para desarrollar.
- **Inversión de dependencias (SOLID):** la lógica depende de una sesión de base de datos inyectada (`get_db`), no de un motor concreto.
