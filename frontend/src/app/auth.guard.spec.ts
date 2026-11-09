import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, Router, RouterStateSnapshot, provideRouter } from '@angular/router';
import { authGuard } from './auth.guard';
import { AuthService } from './auth.service';

describe('authGuard', () => {
  function ejecutar(autenticado: boolean) {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: { autenticado: signal(autenticado) } },
      ],
    });
    return TestBed.runInInjectionContext(() =>
      authGuard({} as ActivatedRouteSnapshot, {} as RouterStateSnapshot),
    );
  }

  it('deja pasar si hay sesión iniciada', () => {
    expect(ejecutar(true)).toBe(true);
  });

  it('redirige al login si no hay sesión', () => {
    const resultado = ejecutar(false);
    const router = TestBed.inject(Router);
    expect(router.serializeUrl(resultado as ReturnType<Router['createUrlTree']>)).toBe('/login');
  });
});
