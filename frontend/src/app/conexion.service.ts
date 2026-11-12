import { Injectable, signal } from '@angular/core';

/** Si el equipo tiene conexión a internet. Avisa en el momento en que se pierde o se recupera. */
@Injectable({ providedIn: 'root' })
export class ConexionService {
  private readonly _enLinea = signal(typeof navigator === 'undefined' ? true : navigator.onLine);
  readonly enLinea = this._enLinea.asReadonly();

  constructor() {
    // El servicio dura toda la sesión de la aplicación: no hace falta quitar estos oyentes.
    window.addEventListener('online', () => this._enLinea.set(true));
    window.addEventListener('offline', () => this._enLinea.set(false));
  }
}
