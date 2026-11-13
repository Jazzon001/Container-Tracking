import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
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

  function iniciarSesion(auth: AuthService, rol = 'poy') {
    auth.login('maria', 'clave-segura-123').subscribe();
    http
      .expectOne('http://api.test/auth/login')
      .flush({ access_token: 'abc', token_type: 'bearer', rol });
  }

  beforeEach(() => localStorage.clear());

  it('arranca sin sesión', () => {
    const auth = crearServicio();
    expect(auth.autenticado()).toBe(false);
    expect(auth.token()).toBeNull();
    expect(auth.rol()).toBeNull();
  });

  it('envía usuario y contraseña a /auth/login', () => {
    const auth = crearServicio();
    auth.login('maria', 'clave-segura-123').subscribe();

    const peticion = http.expectOne('http://api.test/auth/login');
    expect(peticion.request.method).toBe('POST');
    expect(peticion.request.body).toEqual({ username: 'maria', password: 'clave-segura-123' });
    peticion.flush({ access_token: 'abc', token_type: 'bearer', rol: 'poy' });
  });

  it('guarda el token y el rol al iniciar sesión', () => {
    const auth = crearServicio();
    iniciarSesion(auth, 'almacen');

    expect(auth.autenticado()).toBe(true);
    expect(auth.token()).toBe('abc');
    expect(auth.rol()).toBe('almacen');
  });

  it('no guarda nada si las credenciales son incorrectas', () => {
    const auth = crearServicio();
    auth.login('maria', 'mala').subscribe({ error: () => {} });
    http.expectOne('http://api.test/auth/login').flush({}, { status: 401, statusText: 'Unauthorized' });

    expect(auth.autenticado()).toBe(false);
    expect(auth.rol()).toBeNull();
  });

  it('recuerda la sesión después de recargar la página', () => {
    localStorage.setItem('container_tracking_token', 'guardado');
    localStorage.setItem('container_tracking_rol', 'dty');
    const auth = crearServicio();

    expect(auth.token()).toBe('guardado');
    expect(auth.rol()).toBe('dty');
    expect(auth.autenticado()).toBe(true);
  });

  it('cierra la sesión y borra lo guardado', () => {
    localStorage.setItem('container_tracking_token', 'guardado');
    localStorage.setItem('container_tracking_rol', 'dty');
    const auth = crearServicio();
    auth.logout();

    expect(auth.autenticado()).toBe(false);
    expect(auth.rol()).toBeNull();
    expect(localStorage.getItem('container_tracking_token')).toBeNull();
    expect(localStorage.getItem('container_tracking_rol')).toBeNull();
  });

  it('al cerrar sesión borra los datos guardados para uso sin conexión', async () => {
    const borrar = vi.fn().mockResolvedValue(true);
    vi.stubGlobal('caches', {
      keys: vi.fn().mockResolvedValue(['carros-datos-v1']),
      delete: borrar,
    });
    const auth = crearServicio();

    auth.logout();
    await new Promise((resolver) => setTimeout(resolver));

    expect(borrar).toHaveBeenCalledWith('carros-datos-v1');
    vi.unstubAllGlobals();
  });

  describe('cookie de sesión', () => {
    const hayCookie = () => document.cookie.split('; ').some((c) => c === 'ct_sesion=1');
    afterEach(() => TestBed.inject(AuthService).logout());

    it('no hay cookie sin sesión', () => {
      crearServicio();
      expect(hayCookie()).toBe(false);
    });

    it('se crea al iniciar sesión', () => {
      const auth = crearServicio();
      iniciarSesion(auth);
      expect(hayCookie()).toBe(true);
    });

    it('se borra al cerrar sesión', () => {
      const auth = crearServicio();
      iniciarSesion(auth);
      auth.logout();
      expect(hayCookie()).toBe(false);
    });

    it('se crea al recuperar una sesión guardada de antes', () => {
      localStorage.setItem('container_tracking_token', 'guardado');
      crearServicio();
      expect(hayCookie()).toBe(true);
    });
  });

  describe('puede', () => {
    it('permite al rol indicado', () => {
      const auth = crearServicio();
      iniciarSesion(auth, 'poy');
      expect(auth.puede('poy')).toBe(true);
      expect(auth.puede('almacen', 'poy')).toBe(true);
    });

    it('no permite a otro rol', () => {
      const auth = crearServicio();
      iniciarSesion(auth, 'poy');
      expect(auth.puede('almacen')).toBe(false);
    });

    it('permite todo al administrador', () => {
      const auth = crearServicio();
      iniciarSesion(auth, 'admin');
      expect(auth.puede('almacen')).toBe(true);
      expect(auth.puede('poy')).toBe(true);
    });

    it('no permite nada sin sesión', () => {
      const auth = crearServicio();
      expect(auth.puede('poy')).toBe(false);
    });
  });
});
