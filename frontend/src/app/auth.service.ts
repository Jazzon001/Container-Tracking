import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';
import { API_URL } from './api.config';

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

const CLAVE_TOKEN = 'container_tracking_token';

// El almacenamiento puede no estar disponible (modo privado, permisos): la app
// debe seguir funcionando, solo que sin recordar la sesión.
function leerToken(): string | null {
  try {
    return localStorage.getItem(CLAVE_TOKEN);
  } catch {
    return null;
  }
}

function escribirToken(token: string | null): void {
  try {
    if (token === null) localStorage.removeItem(CLAVE_TOKEN);
    else localStorage.setItem(CLAVE_TOKEN, token);
  } catch {
    // sin almacenamiento: la sesión dura solo mientras la pestaña esté abierta
  }
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = inject(API_URL);
  private readonly _token = signal<string | null>(leerToken());

  readonly token = this._token.asReadonly();
  readonly autenticado = computed(() => this._token() !== null);

  login(username: string, password: string): Observable<TokenResponse> {
    return this.http
      .post<TokenResponse>(`${this.apiUrl}/auth/login`, { username, password })
      .pipe(tap((respuesta) => this.guardar(respuesta.access_token)));
  }

  logout(): void {
    this.guardar(null);
  }

  private guardar(token: string | null): void {
    escribirToken(token);
    this._token.set(token);
  }
}
