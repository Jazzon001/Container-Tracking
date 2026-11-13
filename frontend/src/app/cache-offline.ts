/** Nombre de la caché donde public/sw.js guarda las consultas de la API (/carros y /cargas). */
const CACHE_DE_DATOS = 'carros-datos';

/**
 * Borra los datos que el service worker guardó para usar sin conexión. Se llama al cerrar
 * sesión: quien use el mismo equipo después no debe ver los carros de la sesión anterior.
 * Nunca falla: si no hay caché o no se puede acceder a ella, simplemente no hay nada que borrar.
 */
export async function olvidarDatosEnCache(): Promise<void> {
  try {
    if (typeof caches === 'undefined') return;
    const nombres = await caches.keys();
    await Promise.all(
      nombres.filter((nombre) => nombre.includes(CACHE_DE_DATOS)).map((nombre) => caches.delete(nombre)),
    );
  } catch {
    // sin acceso a la caché: no hay nada que borrar
  }
}
