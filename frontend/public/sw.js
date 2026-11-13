// Service worker de Container Tracking: deja usar la aplicación sin conexión, SOLO para consultar.
//
// Estrategia única: "la red primero". Se intenta la red y se guarda la respuesta; si no hay
// conexión, se entrega lo último guardado. Así, con internet siempre se ve lo más reciente, y
// sin él se ve lo último que se consultó. Registrar operaciones (POST, PATCH...) nunca pasa por
// aquí: el service worker solo toca las lecturas (GET), y esas operaciones exigen conexión.

// Si cambias esta versión, el service worker nuevo borra las cachés anteriores al activarse.
const CACHE_APLICACION = 'carros-app-v1'; // la pantalla (HTML, JS, CSS, íconos)
const CACHE_DATOS = 'carros-datos-v1'; // las consultas de la API (/carros y /cargas)

const ORIGEN_API = 'https://container-tracking-api.onrender.com';
const RUTAS_DE_DATOS = ['/carros', '/cargas'];
const PAGINA_INICIAL = '/index.html';

self.addEventListener('install', (evento) => {
  // Guarda lo mínimo para que la aplicación abra sin conexión; el resto se guarda al usarse.
  evento.waitUntil(
    caches
      .open('carros-app-v1')
      .then((cache) => cache.addAll([PAGINA_INICIAL, '/manifest.webmanifest', '/favicon.ico']))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener('activate', (evento) => {
  // Borra las cachés de versiones anteriores y toma el control de las pestañas abiertas.
  evento.waitUntil(
    caches
      .keys()
      .then((nombres) =>
        Promise.all(
          nombres
            .filter((nombre) => nombre !== CACHE_APLICACION && nombre !== CACHE_DATOS)
            .map((nombre) => caches.delete(nombre)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (evento) => {
  const peticion = evento.request;
  if (peticion.method !== 'GET') return; // las operaciones nunca se atienden desde la caché

  const url = new URL(peticion.url);
  const esDatosDeLaApi =
    url.origin === ORIGEN_API && RUTAS_DE_DATOS.some((ruta) => url.pathname.startsWith(ruta));
  const esDelSitio = url.origin === self.location.origin;
  if (!esDatosDeLaApi && !esDelSitio) return; // lo de terceros se deja al navegador

  evento.respondWith(redPrimero(peticion, esDatosDeLaApi ? CACHE_DATOS : CACHE_APLICACION));
});

async function redPrimero(peticion, nombreDeCache) {
  const cache = await caches.open(nombreDeCache);
  try {
    const respuesta = await fetch(peticion);
    if (respuesta.ok) await cache.put(peticion, respuesta.clone());
    return respuesta;
  } catch {
    // Sin conexión: lo último guardado; si es una pantalla que nunca se visitó, la página inicial.
    const guardada = await cache.match(peticion);
    if (guardada) return guardada;
    if (peticion.mode === 'navigate') {
      const inicial = await cache.match(PAGINA_INICIAL);
      if (inicial) return inicial;
    }
    return Response.error();
  }
}
