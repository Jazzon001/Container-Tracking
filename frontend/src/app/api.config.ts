import { InjectionToken } from '@angular/core';
import { environment } from '../environments/environment';

/**
 * URL base de la API. Sale de `src/environments`: en desarrollo apunta al servidor local
 * y en producción (`ng build`) se reemplaza por la de Render. Se inyecta (en lugar de
 * escribirla en cada servicio) para cambiarla en un solo lugar y sustituirla en las pruebas.
 */
export const API_URL = new InjectionToken<string>('API_URL', {
  providedIn: 'root',
  factory: () => environment.apiUrl,
});
