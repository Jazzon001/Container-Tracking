import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';
import { Carro } from './carro.model';

@Injectable({ providedIn: 'root' })
export class CarrosService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = inject(API_URL);

  /** Trae todos los carros. La pantalla los filtra y cuenta por su cuenta. */
  listar(): Observable<Carro[]> {
    return this.http.get<Carro[]>(`${this.apiUrl}/carros`);
  }
}
