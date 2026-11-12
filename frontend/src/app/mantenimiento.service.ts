import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, switchMap } from 'rxjs';
import { API_URL } from './api.config';
import { CarrosService } from './carros.service';
import { Mantenimiento } from './mantenimiento.model';

@Injectable({ providedIn: 'root' })
export class MantenimientoService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = inject(API_URL);
  private readonly carros = inject(CarrosService);

  /** Un carro disponible entra a mantenimiento; se registra la fecha de entrada. */
  iniciarPorNumero(numero: string): Observable<Mantenimiento> {
    return this.carros
      .buscarPorNumero(numero)
      .pipe(
        switchMap((carro) =>
          this.http.post<Mantenimiento>(`${this.apiUrl}/carros/${carro.id}/mantenimiento`, {}),
        ),
      );
  }

  /** El carro sale de mantenimiento y vuelve a estar disponible; se registra la fecha de salida. */
  finalizar(carroId: number): Observable<Mantenimiento> {
    return this.http.post<Mantenimiento>(`${this.apiUrl}/carros/${carroId}/mantenimiento/salida`, {});
  }
}
