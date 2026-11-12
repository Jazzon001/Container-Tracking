// Crea dist/container-tracking/browser/login.html después de compilar.
//
// Es la misma página de inicio, pero con el formulario de acceso ya escrito en el HTML
// (con su campo de contraseña). Sirve para buscadores, lectores de pantalla y verificadores
// que leen el HTML sin ejecutar JavaScript; Angular lo reemplaza por la pantalla real en
// cuanto arranca. Vercel lo entrega en /login (ver vercel.json).
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const carpeta = join('dist', 'container-tracking', 'browser');
const origen = join(carpeta, 'index.html');

if (!existsSync(origen)) {
  console.error(`No existe ${origen}: compila primero con "ng build".`);
  process.exit(1);
}

const html = readFileSync(origen, 'utf8');
const contenidoInicial = /<app-root>[\s\S]*?<\/app-root>/;
if (!contenidoInicial.test(html)) {
  console.error('No se encontró <app-root> en index.html: no se puede crear login.html.');
  process.exit(1);
}

const formulario = `<app-root>
    <main style="max-width: 40rem; margin: 0 auto; padding: 1rem;">
      <form action="#" method="post" aria-label="Iniciar sesión">
        <p style="margin: 0 0 0.5rem; font-size: 0.875rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;">Container Tracking</p>
        <h1>Iniciar sesión</h1>
        <p>Ingresa con tu usuario del sistema.</p>
        <label>Usuario <input type="text" name="username" autocomplete="username" required></label>
        <label>Contraseña <input type="password" name="password" autocomplete="current-password" required></label>
        <button type="submit">Entrar</button>
        <noscript><p role="alert">Para iniciar sesión necesitas activar JavaScript en tu navegador.</p></noscript>
      </form>
    </main>
  </app-root>`;

writeFileSync(join(carpeta, 'login.html'), html.replace(contenidoInicial, formulario));
console.log(`Creado ${join(carpeta, 'login.html')}`);
