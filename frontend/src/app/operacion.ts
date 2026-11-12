import { signal } from '@angular/core';
import { Observable } from 'rxjs';
import { mensajeDeApi } from './api-error';

/**
 * Estado y resultado de una acción que el usuario manda a la API (cargar, recibir,
 * registrar mantenimiento...). Las pantallas de captura repetían esta lógica; aquí
 * vive en un solo lugar: evita envíos dobles y muestra el éxito o el motivo del fallo.
 */
export class Operacion {
  readonly mensaje = signal('');
  readonly error = signal('');
  readonly enviando = signal(false);

  /** Rechaza el envío antes de llamar a la API (por ejemplo, un campo vacío). */
  fallar(texto: string): void {
    this.mensaje.set('');
    this.error.set(texto);
  }

  /**
   * Ejecuta la llamada y muestra su resultado.
   * @param alTerminarBien se ejecuta solo si la API aceptó la operación (limpiar campos, recargar...).
   */
  ejecutar<T>(
    llamada: Observable<T>,
    textoDeExito: (resultado: T) => string,
    textoDeFallo: string,
    alTerminarBien?: () => void,
  ): void {
    this.mensaje.set('');
    this.error.set('');
    this.enviando.set(true);
    llamada.subscribe({
      next: (resultado) => {
        this.mensaje.set(textoDeExito(resultado));
        this.enviando.set(false);
        alTerminarBien?.();
      },
      error: (fallo) => {
        this.error.set(mensajeDeApi(fallo, textoDeFallo));
        this.enviando.set(false);
      },
    });
  }
}
