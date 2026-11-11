import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';
import { API_URL } from './api.config';

export type Rol = 'poy' | 'almacen' | 'dty' | 'twisting' | 'admin';

export interface TokenResponse {
  access_token: string;
  token_type: string;
  rol: Rol;
}

const CLAVE_TOKEN = 'container_tracking_token';
const CLAVE_ROL = 'container_tracking_rol';

// El almacenamiento puede no estar disponible (modo privado, permisos): la app
// debe seguir funcionando, solo que sin recordar la sesión.
function leer(clave: string): string | null {
  try {
    return localStorage.getItem(clave);
  } catch {
    return null;
  }
}

function escribir(clave: string, valor: string | null): void {
  try {
    if (valor === null) localStorage.removeItem(clave);
    else localStorage.setItem(clave, valor);
  } catch {
    // sin almacenamiento: la sesión dura solo mientras la pestaña esté abierta
  }
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = inject(API_URL);
  private readonly _token = signal<string | null>(leer(CLAVE_TOKEN));
  private readonly _rol = signal<Rol | null>(leer(CLAVE_ROL) as Rol | null);

  readonly token = this._token.asReadonly();
  readonly rol = this._rol.asReadonly();
  readonly autenticado = computed(() => this._token() !== null);

  login(username: string, password: string): Observable<TokenResponse> {
    return this.http
      .post<TokenResponse>(`${this.apiUrl}/auth/login`, { username, password })
      .pipe(tap((respuesta) => this.guardar(respuesta.access_token, respuesta.rol)));
  }

  logout(): void {
    this.guardar(null, null);
  }

  /**
   * ¿Puede el usuario actual hacer lo que hacen estos roles? El administrador siempre.
   * Sirve para mostrar u ocultar opciones; la API valida el permiso de todos modos.
   */
  puede(...roles: Rol[]): boolean {
    const rol = this._rol();
    return rol !== null && (rol === 'admin' || roles.includes(rol));
  }

  private guardar(token: string | null, rol: Rol | null): void {
    escribir(CLAVE_TOKEN, token);
    escribir(CLAVE_ROL, rol);
    this._token.set(token);
    this._rol.set(rol);
  }
}
