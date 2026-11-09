import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { API_URL } from './api.config';
import { AuthService } from './auth.service';

/**
 * Adjunta el token a las peticiones hacia nuestra API (y solo a ellas, para no
 * filtrarlo a otros sitios). Si la API responde 401 con una sesión iniciada, el
 * token venció: se cierra la sesión y se vuelve al inicio de sesión.
 */
export const authInterceptor: HttpInterceptorFn = (peticion, siguiente) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const token = auth.token();
  const esDeNuestraApi = peticion.url.startsWith(inject(API_URL));

  const conToken =
    token && esDeNuestraApi
      ? peticion.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
      : peticion;

  return siguiente(conToken).pipe(
    catchError((error: unknown) => {
      if (error instanceof HttpErrorResponse && error.status === 401 && token && esDeNuestraApi) {
        auth.logout();
        router.navigateByUrl('/login');
      }
      return throwError(() => error);
    }),
  );
};
