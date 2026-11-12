import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';
import { RegistroCarga } from './registro-carga.model';

export interface FiltrosHistorial {
  /** Número del carro (búsqueda exacta). */
  numero?: string;
  /** Código del contenedor elemento (búsqueda exacta). */
  contenedor?: string;
}

/** Cuántos registros se piden por defecto: los más recientes. */
export const LIMITE_HISTORIAL = 100;

@Injectable({ providedIn: 'root' })
export class HistorialService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = inject(API_URL);

  /** Los viajes más recientes primero. Los filtros vacíos se ignoran. */
  listar(filtros: FiltrosHistorial = {}, limite = LIMITE_HISTORIAL): Observable<RegistroCarga[]> {
    let params = new HttpParams().set('limite', limite);
    if (filtros.numero) params = params.set('numero', filtros.numero);
    if (filtros.contenedor) params = params.set('contenedor_elemento', filtros.contenedor);
    return this.http.get<RegistroCarga[]>(`${this.apiUrl}/cargas`, { params });
  }
}
