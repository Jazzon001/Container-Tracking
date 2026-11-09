import { InjectionToken } from '@angular/core';

/**
 * URL base de la API. Por defecto apunta al servidor local de FastAPI.
 * Se inyecta (en lugar de escribirla en cada servicio) para cambiarla en un solo
 * lugar al desplegar y para sustituirla fácilmente en las pruebas.
 */
export const API_URL = new InjectionToken<string>('API_URL', {
  providedIn: 'root',
  factory: () => 'http://127.0.0.1:8000',
});
