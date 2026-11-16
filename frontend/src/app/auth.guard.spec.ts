import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, Router, RouterStateSnapshot, provideRouter } from '@angular/router';
import { vi } from 'vitest';
import { authGuard, permisoGuard } from './auth.guard';
import { AuthService } from './auth.service';

function ejecutar(guardia: typeof authGuard, auth: object) {
  TestBed.configureTestingModule({
    providers: [provideRouter([]), { provide: AuthService, useValue: auth }],
  });
  return TestBed.runInInjectionContext(() =>
    guardia({} as ActivatedRouteSnapshot, {} as RouterStateSnapshot),
  );
}

function urlDe(resultado: unknown): string {
  return TestBed.inject(Router).serializeUrl(resultado as ReturnType<Router['createUrlTree']>);
}

describe('authGuard', () => {
  it('deja pasar si hay sesión iniciada', () => {
    expect(ejecutar(authGuard, { autenticado: signal(true) })).toBe(true);
  });

  it('redirige al login si no hay sesión', () => {
    expect(urlDe(ejecutar(authGuard, { autenticado: signal(false) }))).toBe('/login');
  });
});

describe('permisoGuard', () => {
  it('deja pasar si el usuario tiene el permiso que pide la ruta', () => {
    const puede = vi.fn().mockReturnValue(true);
    expect(ejecutar(permisoGuard('cargar'), { puede })).toBe(true);
    expect(puede).toHaveBeenCalledWith('cargar');
  });

  it('manda a la lista de carros si el perfil no tiene el permiso', () => {
    const puede = vi.fn().mockReturnValue(false);
    expect(urlDe(ejecutar(permisoGuard('liberar'), { puede }))).toBe('/carros');
  });
});
