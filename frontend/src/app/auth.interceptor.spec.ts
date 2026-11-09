import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { vi } from 'vitest';
import { API_URL } from './api.config';
import { authInterceptor } from './auth.interceptor';
import { AuthService } from './auth.service';

describe('authInterceptor', () => {
  let cliente: HttpClient;
  let http: HttpTestingController;
  let auth: AuthService;
  let navegar: ReturnType<typeof vi.fn>;

  function preparar(tokenGuardado: string | null) {
    localStorage.clear();
    if (tokenGuardado) localStorage.setItem('container_tracking_token', tokenGuardado);
    navegar = vi.fn();
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        { provide: API_URL, useValue: 'http://api.test' },
        { provide: Router, useValue: { navigateByUrl: navegar } },
      ],
    });
    cliente = TestBed.inject(HttpClient);
    http = TestBed.inject(HttpTestingController);
    auth = TestBed.inject(AuthService);
  }

  it('agrega el token a las peticiones hacia la API', () => {
    preparar('abc');
    cliente.get('http://api.test/carros').subscribe();
    const peticion = http.expectOne('http://api.test/carros');
    expect(peticion.request.headers.get('Authorization')).toBe('Bearer abc');
  });

  it('no agrega el token a peticiones hacia otros sitios', () => {
    preparar('abc');
    cliente.get('http://otro-sitio.test/datos').subscribe();
    const peticion = http.expectOne('http://otro-sitio.test/datos');
    expect(peticion.request.headers.has('Authorization')).toBe(false);
  });

  it('no agrega encabezado si no hay sesión', () => {
    preparar(null);
    cliente.get('http://api.test/carros').subscribe();
    expect(http.expectOne('http://api.test/carros').request.headers.has('Authorization')).toBe(false);
  });

  it('cierra la sesión y vuelve al login si la API responde 401 con sesión iniciada', () => {
    preparar('vencido');
    cliente.get('http://api.test/carros').subscribe({ error: () => {} });
    http.expectOne('http://api.test/carros').flush({}, { status: 401, statusText: 'Unauthorized' });

    expect(auth.autenticado()).toBe(false);
    expect(navegar).toHaveBeenCalledWith('/login');
  });

  it('no redirige si el 401 es de un intento de login sin sesión previa', () => {
    preparar(null);
    cliente.post('http://api.test/auth/login', {}).subscribe({ error: () => {} });
    http.expectOne('http://api.test/auth/login').flush({}, { status: 401, statusText: 'Unauthorized' });

    expect(navegar).not.toHaveBeenCalled();
  });

  it('deja pasar el error para que el componente lo muestre', () => {
    preparar('abc');
    let status = 0;
    cliente.get('http://api.test/carros').subscribe({ error: (e) => (status = e.status) });
    http.expectOne('http://api.test/carros').flush({}, { status: 500, statusText: 'Error' });

    expect(status).toBe(500);
    expect(navegar).not.toHaveBeenCalled();
  });
});
