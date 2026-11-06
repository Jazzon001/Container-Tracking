# ADR 0003: Autenticación con JWT propio y autorización por roles

- **Estado:** Aceptada
- **Fecha:** 2026-11-06

## Contexto

El sistema tiene cinco tipos de usuario (POY, Almacén, DTY, Twisting y Administrador) y cada uno solo debe poder hacer lo que corresponde a su proceso: por ejemplo, solo POY carga carros y solo Almacén los recibe. Se necesita iniciar sesión desde computadora y celular, con una solución simple de mantener.

## Decisión

1. **Inicio de sesión con usuario y contraseña** (`POST /auth/login`) que devuelve un **token JWT** (HS256) válido por 8 horas, una jornada de trabajo. El cliente lo envía en el encabezado `Authorization: Bearer <token>`.
2. **La clave de firma** se lee de la variable de entorno `JWT_SECRET`. Nunca se escribe en el código ni en el repositorio. Sin ella, la aplicación falla con un mensaje claro en lugar de usar una clave por defecto.
3. **Contraseñas** guardadas solo como hash PBKDF2-SHA256 con sal aleatoria (600 000 iteraciones), con la biblioteca estándar de Python. No se almacena ni se devuelve la contraseña.
4. **Roles fijos** (`Rol`). La autorización se declara en cada ruta con `requiere_roles(...)`; el administrador siempre tiene permiso.
5. **El rol se lee de la base de datos** en cada petición, no del token. Si se cambia el rol de un usuario, el cambio aplica de inmediato.
6. **Primer administrador** mediante un script (`python -m scripts.crear_usuario`) que pide la contraseña por teclado, porque la API exige ser administrador para crear usuarios.
7. **401 contra 403:** 401 si no hay sesión o el token no es válido; 403 si hay sesión pero el rol no permite la operación.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Supabase Auth | Ata la autenticación a un proveedor y complica las pruebas locales; ya se decidió usar Supabase solo como base de datos (ADR 0001). |
| Sesiones con cookie en el servidor | Obliga a guardar estado de sesión y complica un frontend desplegado en otro dominio. |
| `bcrypt` o `passlib` para las contraseñas | Agregan una dependencia; PBKDF2 de la biblioteca estándar es suficiente y reconocido. |
| Tabla de permisos configurable (RBAC completo) | Hoy hay cinco roles fijos y reglas claras; sería sobreingeniería (YAGNI). |
| Registro público de usuarios | Es un sistema interno: solo el administrador crea usuarios. |

## Consecuencias

- **Positivo:** sin dependencias de terceros para autenticar; las reglas de permisos se leen en un solo vistazo en cada router y se prueban con una matriz de roles.
- **Positivo:** el mensaje de error del login no revela si el usuario existe.
- **A vigilar:** un JWT no se puede revocar antes de que venza. Para este alcance se acepta; si hiciera falta cerrar sesiones a la fuerza, habría que agregar una lista de tokens revocados.
- **A vigilar:** cambiar `JWT_SECRET` invalida todos los tokens emitidos.
- **A vigilar:** el sistema debe servirse solo por HTTPS, para que la contraseña y el token no viajen en claro (Vercel y Render ya lo hacen).
- **Pendiente:** Twisting hoy solo consulta. Se le asignarán operaciones cuando se defina su flujo de carros vacíos.

## Principios que lo justifican

- **Responsabilidad única (SOLID):** `seguridad.py` (hash y tokens), `services/usuarios.py` (reglas) y `dependencias.py` (HTTP) cambian por motivos distintos.
- **Abierto/cerrado (SOLID):** proteger una ruta nueva es agregar una dependencia, sin modificar las existentes.
- **KISS y YAGNI:** roles fijos y biblioteca estándar en lugar de un sistema de permisos genérico.
