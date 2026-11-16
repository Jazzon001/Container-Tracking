import { Injectable } from '@angular/core';

/** Guarda en el equipo un archivo que ya está en memoria, como si se hubiera descargado de un enlace. */
@Injectable({ providedIn: 'root' })
export class DescargaService {
  guardar(contenido: Blob, nombre: string): void {
    const direccion = URL.createObjectURL(contenido);
    const enlace = document.createElement('a');
    enlace.href = direccion;
    enlace.download = nombre;
    enlace.click();
    URL.revokeObjectURL(direccion);
  }
}
