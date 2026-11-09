import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';
import { Carro, EstadoCarro } from './carro.model';

@Injectable({ providedIn: 'root' })
export class CarrosService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = inject(API_URL);

  /** Lista los carros; con `estado` solo los que están en ese estado. */
  listar(estado?: EstadoCarro): Observable<Carro[]> {
    const params = estado ? new HttpParams().set('estado', estado) : undefined;
    return this.http.get<Carro[]>(`${this.apiUrl}/carros`, { params });
  }
}
