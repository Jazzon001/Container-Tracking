import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';
import { Accion } from './perfiles';

/** Solo deja entrar a la ruta si hay sesión iniciada; si no, manda al login. */
export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  return auth.autenticado() ? true : inject(Router).createUrlTree(['/login']);
};

/** Solo deja entrar a quien tiene el permiso indicado; a los demás, a la lista de carros. */
export const permisoGuard =
  (accion: Accion): CanActivateFn =>
  () =>
    inject(AuthService).puede(accion) ? true : inject(Router).createUrlTree(['/carros']);
