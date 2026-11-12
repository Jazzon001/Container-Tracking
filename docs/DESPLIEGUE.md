# Guía de despliegue

Cómo publicar el sistema en línea con tres servicios gratuitos:

| Pieza | Servicio | Qué aloja |
|---|---|---|
| Base de datos | **Supabase** | PostgreSQL |
| API (backend) | **Render** | FastAPI |
| Interfaz (frontend) | **Vercel** | Angular |

**Orden obligatorio:** Supabase → Render → Vercel → volver a Render. Cada paso necesita una dirección que genera el anterior.

> Los nombres de menús y botones de estos servicios cambian con el tiempo. Si algo no coincide exactamente, busca la opción equivalente.

## 0. Antes de empezar

- Una cuenta en [Supabase](https://supabase.com), [Render](https://render.com) y [Vercel](https://vercel.com). Lo más cómodo es registrarse con tu cuenta de GitHub, así pueden leer el repositorio.
- Que tu último `push` esté en GitHub y el CI esté en verde.
- Un **gestor de contraseñas** (o un archivo cifrado) donde guardar las contraseñas que vas a crear. **No las escribas en archivos del proyecto.**

## 1. Supabase: la base de datos

1. **Crea un proyecto** nuevo. Elige la región más cercana a tus usuarios y una **contraseña de base de datos larga y aleatoria**; guárdala en tu gestor de contraseñas.
2. Cuando esté listo, abre el botón **Connect** del proyecto y copia la cadena de conexión **"Session pooler"**. Se ve así:

   ```
   postgresql://postgres.<referencia>:[TU-CONTRASEÑA]@aws-0-<region>.pooler.supabase.com:5432/postgres
   ```

3. Reemplaza `[TU-CONTRASEÑA]` por la contraseña del paso 1. Si tiene caracteres especiales (`@`, `/`, `#`, `%`...), hay que **codificarlos** (`@` → `%40`, `/` → `%2F`, `#` → `%23`, `%` → `%25`). Lo más simple es generar una contraseña solo con letras y números.

**¿Por qué "Session pooler" y no la conexión directa?** La conexión directa de Supabase usa direcciones IPv6, y Render gratis solo usa IPv4. El *pooler* funciona con IPv4. Si ves el error `Network is unreachable`, es esto.

No hace falta crear tablas: la API las crea sola al arrancar (migraciones).

## 2. Render: la API

1. En Render: **New +** → **Blueprint** → elige tu repositorio. Render lee el archivo `render.yaml` de la raíz y propone el servicio `container-tracking-api`.
2. Te pide dos valores:
   - `DATABASE_URL`: pega la cadena del paso 1 (ya con la contraseña).
   - `CORS_ORIGINS`: por ahora escribe `http://localhost:4200`. Lo cambiarás en el paso 4.
3. Pulsa **Apply** y espera a que el despliegue termine (unos minutos la primera vez).
4. Anota la dirección pública del servicio: `https://container-tracking-api.onrender.com` (o la que te asigne). Comprueba que abre `.../health` y muestra `{"status":"ok"}`.

`JWT_SECRET` lo genera Render solo, con un valor distinto al de tu computadora. No tienes que escribirlo.

## 3. Datos iniciales: administrador y carros

Se hacen **desde tu computadora**, apuntando a la base de Supabase. La contraseña de la base viaja solo por tu terminal, nunca por un archivo. En `backend`, con el entorno virtual activo:

```powershell
$env:DATABASE_URL = "postgresql://postgres.<referencia>:<CONTRASEÑA>@aws-0-<region>.pooler.supabase.com:5432/postgres"
python -m scripts.crear_usuario admin admin
python -m scripts.importar_carros ..\datos\Carros.xlsx
python -m scripts.importar_carros ..\datos\Carros.xlsx --guardar
Remove-Item Env:DATABASE_URL
```

- Usa para el administrador una **contraseña larga y distinta a la de pruebas** (nunca `12345678`).
- El primer `importar_carros` solo revisa; el segundo guarda. Debes ver `POY: 1012`, `DTY: 512` y `Twisting: 42`.
- El último comando borra la variable de tu terminal, para no apuntar a producción por accidente.
- Si ves `Network is unreachable`, estás usando la conexión directa en lugar del *Session pooler*.

## 4. Vercel: la interfaz

1. **Antes de crear el proyecto**, abre `frontend/src/environments/environment.production.ts` y cambia `apiUrl` por la dirección de tu servicio en Render (sin `/` al final). Haz commit y push.
2. En Vercel: **Add New → Project** → importa tu repositorio.
3. En **Root Directory** elige `frontend`. El resto (comando de compilación, carpeta de salida y la regla para que las rutas de Angular funcionen al recargar) ya está en `frontend/vercel.json`.
4. **Deploy**. Al terminar, Vercel te da una dirección como `https://container-tracking.vercel.app`.

## 5. Render otra vez: permitir al frontend

El navegador solo deja que tu página llame a la API si la API lo permite (CORS).

1. En Render, entra al servicio → **Environment** → cambia `CORS_ORIGINS` por la dirección de Vercel, **sin `/` al final**: `https://container-tracking.vercel.app`.
2. Si quieres permitir varias direcciones, sepáralas con comas.
3. Guarda: Render reinicia el servicio.

## 6. Verificación final

- [ ] `https://<tu-api>.onrender.com/health` responde `{"status":"ok"}`.
- [ ] La página de Vercel abre el inicio de sesión.
- [ ] Puedes entrar con tu administrador y ves los 1566 carros.
- [ ] Desde el celular, la página se ve bien y funciona.
- [ ] Creas un usuario de POY y uno de Almacén (`POST /usuarios` en `.../docs`, con tu administrador) y pruebas cargar y recibir un carro.
- [ ] En la pestaña **Actions** de GitHub, el CI sigue en verde.

## Problemas frecuentes

| Síntoma | Causa y solución |
|---|---|
| La primera petición tarda 30–60 s | Render gratis "duerme" el servicio tras 15 minutos sin uso. Abre `/health` antes de una demostración para despertarlo. |
| El login dice "No se pudo conectar con el servidor" | La URL de `environment.production.ts` está mal, o la API está dormida o caída. |
| El navegador muestra un error de **CORS** | `CORS_ORIGINS` no coincide exactamente con la dirección de Vercel (revisa `https`, mayúsculas y que no termine en `/`). |
| Render: `Network is unreachable` | Usaste la conexión directa de Supabase; usa **Session pooler**. |
| Render: `password authentication failed` | Contraseña incorrecta o con caracteres especiales sin codificar. |
| Render: falla el arranque con un error de migración | Mira los *Logs* de Render. Una base que alguien modificó a mano puede chocar con las migraciones. |
| Una ruta inexistente responde 200 en lugar de 404 | El preset "Angular" de Vercel agrega una regla de "toda ruta, a la página principal". En Vercel: **Settings → General → Framework Preset → Other**, guarda y vuelve a desplegar. |
| La app dejó de responder después de días sin uso | Supabase gratis **pausa** proyectos tras una semana sin actividad: reactívalo desde su panel. |
| Cambié el modelo y producción falla | Falta subir la migración. Se crea con `alembic revision --autogenerate` (ver la guía de pruebas) y se aplica sola al desplegar. |

## Seguridad: lista de comprobación

- `JWT_SECRET` lo genera Render; no reutilices la clave de tu `backend/.env`.
- La contraseña del administrador de producción es larga y distinta a las de prueba.
- La cadena de Supabase vive solo en Render y, un momento, en tu terminal. Nunca en el repositorio ni en `backend/.env`.
- `datos/` (los Excel con datos de UTEXA) no se sube a GitHub.
- Las páginas `/docs` y `/openapi.json` de la API son públicas. Muestran la forma de la API, no datos, y todas las operaciones exigen iniciar sesión.
- Vercel y Render dan HTTPS automáticamente: la contraseña y el token viajan cifrados.

## Qué se comprueba en el sitio publicado

La verificación del curso (entregable "Producto publicado en un dominio real") revisa la dirección de Vercel, la pantalla de inicio de sesión, una pantalla privada y el `/health` de la API. Esto es lo que cubre cada parte del repositorio:

| Se comprueba | Dónde está |
|---|---|
| PWA: manifiesto, service worker e íconos | `frontend/public/manifest.webmanifest`, `ngsw-config.json`, `frontend/public/icons/` |
| Responsive con `@media` | `frontend/src/styles.css` |
| SEO y Open Graph | `frontend/src/index.html` y la imagen `icons/og-image.png` |
| Cabeceras de seguridad | `frontend/vercel.json` |
| 404 manejado | `frontend/vercel.json` (última regla de `rewrites`) y `frontend/public/404.html`: página propia, con estado 200 |
| `robots.txt` y mapa del sitio | `frontend/public/robots.txt` y `sitemap.xml` |
| Inicio de sesión real | La pantalla `/login`; su HTML trae el formulario con campo de contraseña (`login.html`, generado por `tools/crear-login-estatico.mjs` al compilar) |
| Service worker | `/sw.js` (delega en el de Angular) |
| Portal privado que no filtra contenido sin sesión | `/carros`: sin la cookie de sesión, el servidor redirige (307) a `/login`; los datos vienen de la API y exigen token (ver el ADR 0006) |
| Healthcheck de la API en JSON | `https://<tu-api>.onrender.com/health` |
| Código de verificación publicado | `README.md`, la etiqueta `meta name="verificacion"` y `/verificacion.txt` |

**Antes de verificar**, abre `https://<tu-api>.onrender.com/health` para despertar la API (Render gratis duerme): si está dormida, el chequeo puede agotar el tiempo.

**Si cambias de dominio**, actualiza las direcciones escritas en estos archivos: `frontend/src/index.html`, `frontend/ngsw-config.json`, `frontend/vercel.json` (política de seguridad), `frontend/public/robots.txt` y `frontend/public/sitemap.xml`.

## Dominio propio (opcional)

Vercel y Render permiten asignar un dominio propio (por ejemplo `carros.tuempresa.com`) desde su panel. Si lo haces, actualiza `apiUrl` en `environment.production.ts` y `CORS_ORIGINS` en Render con las direcciones nuevas.
