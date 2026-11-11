import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService, Rol } from './auth.service';

/** Solo deja entrar a la ruta si hay sesión iniciada; si no, manda al login. */
export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  return auth.autenticado() ? true : inject(Router).createUrlTree(['/login']);
};

/** Solo deja entrar a los roles indicados (y al administrador); a los demás, a la lista de carros. */
export const rolGuard =
  (...roles: Rol[]): CanActivateFn =>
  () =>
    inject(AuthService).puede(...roles) ? true : inject(Router).createUrlTree(['/carros']);
