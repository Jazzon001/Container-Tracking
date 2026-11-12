/**
 * Cookie "marcadora" de que hay una sesión iniciada. Vercel la lee en el servidor para
 * redirigir al inicio de sesión a quien abra una pantalla privada sin haber entrado, en
 * lugar de entregarle el cascarón de la aplicación (ver `vercel.json`).
 *
 * NO es una credencial ni protege datos: vale "1" y cualquiera puede crearla a mano. Los
 * datos siguen protegidos por el token de la API, que se valida en cada petición. Esta
 * cookie solo evita servir pantallas privadas a visitantes anónimos.
 */
export const COOKIE_DE_SESION = 'ct_sesion';

/** Dura lo mismo que el token (8 horas): al vencer uno, vence el otro. */
const DURACION_EN_SEGUNDOS = 8 * 60 * 60;

function escribir(valor: string, duracion: number): void {
  try {
    const segura = location.protocol === 'https:' ? '; Secure' : '';
    document.cookie = `${COOKIE_DE_SESION}=${valor}; path=/; max-age=${duracion}; SameSite=Lax${segura}`;
  } catch {
    // sin acceso a las cookies: la aplicación sigue funcionando, solo sin la redirección
  }
}

export function marcarSesionIniciada(): void {
  escribir('1', DURACION_EN_SEGUNDOS);
}

export function marcarSesionCerrada(): void {
  escribir('', 0);
}
