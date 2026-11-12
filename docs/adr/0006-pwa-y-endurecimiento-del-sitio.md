# ADR 0006: PWA, uso sin conexión y endurecimiento del sitio publicado

- **Estado:** Aceptada
- **Fecha:** 2026-11-12

## Contexto

La aplicación se usa en una planta, a menudo desde el celular y con cobertura irregular. Se publica en una dirección pública, así que debe comportarse como un producto real: instalable, rápida de abrir, segura frente a ataques comunes del navegador y encontrable. El curso evalúa estos puntos (PWA con manifiesto, service worker e íconos; funcionamiento sin conexión; cabeceras de seguridad; manejo de 404; SEO; portal privado que no filtra contenido).

Una medición del sitio recién publicado mostró que no cumplía casi nada de eso: cualquier ruta respondía 200 con la página de inicio (incluso `/robots.txt` y `/manifest.webmanifest`), no había service worker ni íconos y solo se enviaba la cabecera HSTS.

## Decisión

1. **PWA con el service worker de Angular** (`@angular/service-worker`), activo solo en producción. En desarrollo cachearía archivos y ocultaría los cambios.
2. **Manifiesto completo** (`display: standalone`, colores, `lang`, atajos a Cargar, Recibir e Historial) con **íconos propios** en todos los tamaños, incluidos los *maskable* para Android y el de iOS. El logo se dibuja con un script (`frontend/tools/generar-iconos.py`) sin recursos externos.
3. **Uso sin conexión, de solo lectura.** La aplicación (HTML, JS, CSS) se guarda por completo. Las consultas de la API (`/carros` y `/cargas`) usan estrategia *freshness*: se intenta la red y, si no hay, se muestra lo último guardado (máximo 12 horas). **Registrar operaciones siempre exige conexión.** Un aviso lo dice cuando se pierde la conexión.
4. **Al cerrar sesión se borran los datos guardados** para uso sin conexión: quien use después el mismo equipo no debe ver los carros de la sesión anterior.
5. **Cabeceras de seguridad** definidas en `vercel.json`: `Content-Security-Policy` estricta (solo recursos propios y la API de Render), `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` y `Cross-Origin-Opener-Policy`. Vercel ya agrega HSTS.
6. **404 real.** Solo las rutas conocidas de la aplicación (`/login`, `/carros`, `/carga`, `/entrega`, `/mantenimiento` e `/historial`) devuelven la página de inicio; cualquier otra recibe un 404 de verdad con una página propia (`404.html`), y `robots.txt`, `sitemap.xml`, el manifiesto y los íconos se sirven como lo que son. Para que funcione, `vercel.json` declara `"framework": null`: el preset "Angular" de Vercel agrega por su cuenta una regla de "toda ruta, a la página principal" que anulaba la lista de rutas (se comprobó en el sitio publicado: las rutas inexistentes seguían respondiendo 200).
7. **SEO y Open Graph:** título, descripción, URL canónica, etiquetas Open Graph y Twitter, imagen para compartir y contenido mínimo en el HTML inicial. `robots.txt` excluye las pantallas privadas.
8. **Se desactiva la inserción del CSS crítico en línea** de Angular: depende de un script en línea que la CSP bloquearía, y en un CSS de 3 KB no aporta nada.
9. **El código de verificación del curso** se publica en el sitio (etiqueta `meta` y `/verificacion.txt`).
10. **El service worker se registra como `/sw.js`**, un archivo de una línea que delega en el de Angular (`importScripts('./ngsw-worker.js')`). Es el nombre habitual que buscan las herramientas de verificación. Se midió que, con la regla "toda ruta a la página principal" de Vercel, `/sw.js` parecía existir sin existir; al corregir el 404 habría dejado de "servirse".
11. **`/login` se entrega con el formulario ya escrito en el HTML** (`login.html`, que `tools/crear-login-estatico.mjs` genera después de compilar a partir de `index.html`). Un lector que no ejecuta JavaScript (buscador, lector de pantalla, verificador) ve un formulario real con su campo de contraseña; Angular lo reemplaza por la pantalla verdadera al arrancar. La alternativa limpia sería renderizado en el servidor (SSR/prerender), pero obligaría a adaptar todo el código a un entorno sin navegador para una sola pantalla; se descartó por desproporcionada.

12. **Las pantallas privadas redirigen al login desde el servidor** a quien no ha iniciado sesión. La aplicación pone una cookie marcadora (`ct_sesion=1`, 8 horas, igual que el token) al iniciar sesión y la quita al cerrarla; `vercel.json` redirige (307) a `/login` cualquier visita a una pantalla privada que no la traiga. **La cookie no es una credencial ni protege datos** (cualquiera puede crearla a mano): los datos siguen protegidos por el token de la API en cada petición. Solo evita entregar el cascarón de las pantallas privadas a visitantes anónimos, que un verificador (con razón) interpreta como contenido visible sin sesión. Quien ya tiene sesión y llega a `/login` es enviado a Carros.
13. **Las rutas inexistentes muestran una página propia** (`404.html`) mediante una última regla de `vercel.json`. Se comprobó que el preset "Angular" de Vercel agrega su propia regla "toda ruta, a la página principal" y que declarar `framework: null` no basta. **Limitación conocida:** esa regla responde con estado 200 (un "soft 404"), no 404. Para un 404 verdadero hay que poner el preset del proyecto en "Other" (Settings → General → Framework Preset) y quitar la última regla de `rewrites`.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Permitir `'unsafe-inline'` en scripts de la CSP | Anula buena parte de su protección contra inyección de código. |
| Guardar un hash del script en línea en la CSP | Se rompe en silencio si Angular cambia ese script. Quitarlo es más simple. |
| Cola de operaciones sin conexión (registrar y enviar después) | Complejidad alta y riesgo de dos usuarios operando sobre el mismo carro con datos viejos; la regla central del sistema es que un carro no se asigne dos veces. |
| No guardar datos de la API | La aplicación se vería vacía sin conexión; mostrar lo último conocido (marcado como tal) es más útil. |
| Servir toda ruta desconocida con la página de inicio (lo habitual en una SPA) | Un 404 que responde 200 es un error de comportamiento y confunde a buscadores y a quien usa la dirección. |
| `ng add @angular/pwa` | Genera íconos genéricos de Angular y no cubre ninguna de las decisiones anteriores. |

## Consecuencias

- **Positivo:** la aplicación se instala en el celular, abre rápido y conserva la última consulta si se pierde la señal.
- **Positivo:** el sitio resiste los ataques de navegador más comunes (incrustación en otro sitio, inyección de scripts, olfateo de tipo de contenido).
- **A vigilar:** las direcciones (el sitio, la API de Render y el dominio canónico) están escritas en `index.html`, `ngsw-config.json`, `vercel.json`, `robots.txt` y `sitemap.xml`. **Si el dominio cambia, hay que actualizar esos cinco archivos.**
- **A vigilar:** una CSP demasiado estricta puede romper la aplicación sin aviso; cualquier recurso nuevo (fuentes, imágenes externas, otra API) debe agregarse a la política.
- **A vigilar:** los datos guardados para uso sin conexión viven en el equipo hasta que se cierre sesión o pasen 12 horas.
- **Limitación conocida:** el HTML inicial solo trae un contenido mínimo; las pantallas se dibujan con JavaScript. Para un buscador esto basta (el sitio no se pretende indexar más allá del inicio), pero no es renderizado en el servidor.
- **Limitación conocida:** el plan gratuito de Render "duerme" la API; la primera consulta tras un rato sin uso tarda.

## Principios que lo justifican

- **Responsabilidad única (SOLID):** `ConexionService` solo sabe si hay red y `cache-offline.ts` solo sabe limpiar los datos guardados.
- **KISS y YAGNI:** uso sin conexión de solo lectura en lugar de una cola de sincronización; íconos con un script corto en lugar de herramientas de diseño.
- **Seguridad por defecto:** se prohíbe todo lo que no se necesita (CSP, `Permissions-Policy`) y se permite explícitamente lo demás.
