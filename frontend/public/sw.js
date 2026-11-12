// Punto de entrada del service worker de la aplicación (/sw.js).
// Todo el trabajo (guardar la aplicación y las consultas para uso sin conexión) lo hace el
// service worker de Angular, que Angular genera al compilar según ngsw-config.json.
importScripts('./ngsw-worker.js');
