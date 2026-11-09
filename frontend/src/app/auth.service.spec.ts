import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { API_URL } from './api.config';
import { AuthService } from './auth.service';

describe('AuthService', () => {
  let http: HttpTestingController;

  function crearServicio(): AuthService {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_URL, useValue: 'http://api.test' },
      ],
    });
    http = TestBed.inject(HttpTestingController);
    return TestBed.inject(AuthService);
  }

  beforeEach(() => localStorage.clear());

  it('arranca sin sesión', () => {
    const auth = crearServicio();
    expect(auth.autenticado()).toBe(false);
    expect(auth.token()).toBeNull();
  });

  it('envía usuario y contraseña a /auth/login', () => {
    const auth = crearServicio();
    auth.login('maria', 'clave-segura-123').subscribe();

    const peticion = http.expectOne('http://api.test/auth/login');
    expect(peticion.request.method).toBe('POST');
    expect(peticion.request.body).toEqual({ username: 'maria', password: 'clave-segura-123' });
    peticion.flush({ access_token: 'abc', token_type: 'bearer' });
  });

  it('guarda el token al iniciar sesión', () => {
    const auth = crearServicio();
    auth.login('maria', 'clave-segura-123').subscribe();
    http.expectOne('http://api.test/auth/login').flush({ access_token: 'abc', token_type: 'bearer' });

    expect(auth.autenticado()).toBe(true);
    expect(auth.token()).toBe('abc');
  });

  it('no guarda nada si las credenciales son incorrectas', () => {
    const auth = crearServicio();
    auth.login('maria', 'mala').subscribe({ error: () => {} });
    http.expectOne('http://api.test/auth/login').flush({}, { status: 401, statusText: 'Unauthorized' });

    expect(auth.autenticado()).toBe(false);
  });

  it('recuerda la sesión después de recargar la página', () => {
    localStorage.setItem('container_tracking_token', 'guardado');
    const auth = crearServicio();
    expect(auth.token()).toBe('guardado');
    expect(auth.autenticado()).toBe(true);
  });

  it('cierra la sesión y borra el token guardado', () => {
    localStorage.setItem('container_tracking_token', 'guardado');
    const auth = crearServicio();
    auth.logout();

    expect(auth.autenticado()).toBe(false);
    expect(localStorage.getItem('container_tracking_token')).toBeNull();
  });
});
